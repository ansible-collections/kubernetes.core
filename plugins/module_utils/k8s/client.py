# Copyright: (c) 2021, Red Hat | Ansible
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import os
import hashlib
from distutils.version import LooseVersion
from typing import Any, Dict, List, Optional

from ansible.module_utils.six import iteritems, string_types

from ansible_collections.kubernetes.core.plugins.module_utils.args_common import (
    AUTH_ARG_MAP,
    AUTH_ARG_SPEC,
    AUTH_PROXY_HEADERS_SPEC,
)

try:
    from ansible_collections.kubernetes.core.plugins.module_utils import (
        k8sdynamicclient,
    )
    from ansible_collections.kubernetes.core.plugins.module_utils.client.discovery import (
        LazyDiscoverer,
    )
except ImportError:
    # Handled in module setup
    pass

try:
    import kubernetes
except ImportError:
    # Handled in module setup
    pass

try:
    import urllib3

    urllib3.disable_warnings()
except ImportError:
    # Handled in module setup
    pass


module = None
_pool = {}


def _requires_kubernetes_at_least(version: str):
    if module:
        module.requires("kubernetes", version)
    else:
        if LooseVersion(kubernetes.__version__) < LooseVersion(version):
            raise Exception(
                f"kubernetes >= {version} is required to use in-memory kubeconfig."
            )


def _create_auth_spec(module=None, **kwargs) -> Dict:
    auth: Dict = {}
    # If authorization variables aren't defined, look for them in environment variables
    for true_name, arg_name in AUTH_ARG_MAP.items():
        if module and module.params.get(arg_name) is not None:
            auth[true_name] = module.params.get(arg_name)
        elif arg_name in kwargs and kwargs.get(arg_name) is not None:
            auth[true_name] = kwargs.get(arg_name)
        elif arg_name == "proxy_headers":
            # specific case for 'proxy_headers' which is a dictionary
            proxy_headers = {}
            for key in AUTH_PROXY_HEADERS_SPEC.keys():
                env_value = os.getenv(
                    "K8S_AUTH_PROXY_HEADERS_{0}".format(key.upper()), None
                )
                if env_value is not None:
                    if AUTH_PROXY_HEADERS_SPEC[key].get("type") == "bool":
                        env_value = env_value.lower() not in ["0", "false", "no"]
                    proxy_headers[key] = env_value
            if proxy_headers is not {}:
                auth[true_name] = proxy_headers
        else:
            env_value = os.getenv(
                "K8S_AUTH_{0}".format(arg_name.upper()), None
            ) or os.getenv("K8S_AUTH_{0}".format(true_name.upper()), None)
            if env_value is not None:
                if AUTH_ARG_SPEC[arg_name].get("type") == "bool":
                    env_value = env_value.lower() not in ["0", "false", "no"]
                auth[true_name] = env_value

    return auth


def _load_config(auth: Dict) -> None:
    kubeconfig = auth.get("kubeconfig")
    optional_arg = {
        "context": auth.get("context"),
        "persist_config": auth.get("persist_config"),
    }
    if kubeconfig:
        if isinstance(kubeconfig, string_types):
            kubernetes.config.load_kube_config(config_file=kubeconfig, **optional_arg)
        elif isinstance(kubeconfig, dict):
            _requires_kubernetes_at_least("17.17.0")
            kubernetes.config.load_kube_config_from_dict(
                config_dict=kubeconfig, **optional_arg
            )
    else:
        kubernetes.config.load_kube_config(config_file=None, **optional_arg)


def _create_configuration(auth: Dict):
    def auth_set(*names: list) -> bool:
        return all(auth.get(name) for name in names)

    if auth_set("host"):
        # Removing trailing slashes if any from hostname
        auth["host"] = auth.get("host").rstrip("/")

    if auth_set("username", "password", "host") or auth_set("api_key", "host"):
        # We have enough in the parameters to authenticate, no need to load incluster or kubeconfig
        pass
    elif auth_set("kubeconfig") or auth_set("context"):
        try:
            _load_config(auth)
        except Exception as err:
            raise err

    else:
        # First try to do incluster config, then kubeconfig
        try:
            kubernetes.config.load_incluster_config()
        except kubernetes.config.ConfigException:
            try:
                _load_config(auth)
            except Exception as err:
                raise err

    # Override any values in the default configuration with Ansible parameters
    # As of kubernetes-client v12.0.0, get_default_copy() is required here
    try:
        configuration = kubernetes.client.Configuration().get_default_copy()
    except AttributeError:
        configuration = kubernetes.client.Configuration()

    for key, value in iteritems(auth):
        if key in AUTH_ARG_MAP.keys() and value is not None:
            if key == "api_key":
                setattr(
                    configuration, key, {"authorization": "Bearer {0}".format(value)}
                )
            elif key == "proxy_headers":
                headers = urllib3.util.make_headers(**value)
                setattr(configuration, key, headers)
            else:
                setattr(configuration, key, value)

    return configuration


def _configuration_digest(configuration) -> str:
    m = hashlib.sha256()
    for k in AUTH_ARG_MAP:
        if not hasattr(configuration, k):
            v = None
        else:
            v = getattr(configuration, k)
        if v and k in ["ssl_ca_cert", "cert_file", "key_file"]:
            with open(str(v), "r") as fd:
                content = fd.read()
                m.update(content.encode())
        else:
            m.update(str(v).encode())
    digest = m.hexdigest()

    return digest


def cache(func):
    def wrapper(*args):
        client = None
        digest = _configuration_digest(*args)
        if digest in _pool:
            client = _pool[digest]
        else:
            client = func(*args)
            _pool[digest] = client

        return client

    return wrapper


@cache
def create_api_client(configuration):
    return k8sdynamicclient.K8SDynamicClient(
        kubernetes.client.ApiClient(configuration), discoverer=LazyDiscoverer
    )


class K8SClient:
    """A Client class for K8S modules.

    This class has the primary purpose to proxy the kubernetes client and resource objects.
    If there is a need for other methods or attributes to be proxied, they can be added here.
    """

    def __init__(self, configuration, client, dry_run: bool = False) -> None:
        self.configuration = configuration
        self.client = client
        self.dry_run = dry_run

    @property
    def resources(self) -> List[Any]:
        return self.client.resources

    def _ensure_dry_run(self, params: Dict) -> Dict:
        if self.dry_run:
            params["dry_run"] = True
        return params

    def validate(self, resource, **params):
        pass

    def get(self, resource, **params):
        return resource.get(**params)

    def delete(self, resource, **params):
        return resource.delete(**self._ensure_dry_run(params))

    def apply(self, resource, definition, namespace, **params):
        return resource.apply(
            definition, namespace=namespace, **self._ensure_dry_run(params)
        )

    def create(self, resource, definition, **params):
        return resource.create(definition, **self._ensure_dry_run(params))

    def replace(self, resource, definition, **params):
        return resource.replace(definition, **self._ensure_dry_run(params))

    def patch(self, resource, definition, **params):
        return resource.patch(definition, **self._ensure_dry_run(params))


def get_api_client(module=None, **kwargs: Optional[Any]) -> K8SClient:
    auth_spec = _create_auth_spec(module, **kwargs)
    configuration = _create_configuration(auth_spec)
    client = create_api_client(configuration)

    k8s_client = K8SClient(
        configuration=configuration,
        client=client,
        dry_run=module.params.get("dry_run", False),
    )

    return k8s_client.client