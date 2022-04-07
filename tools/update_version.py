import argparse
import sys
from packaging import version
import re
from functools import partial
import glob
import os
from pathlib import PosixPath
from git import Repo
import json


def update_makefile(v, data):
    return re.sub(r'VERSION = ([0-9]+\.[0-9]+\.[0-9]+)', r'VERSION = {0}'.format(v), data)


def update_galaxy(v, data):
    return re.sub(r'version\: ([0-9]+\.[0-9]+\.[0-9]+)', r'version: {0}'.format(v), data)


def update_readme(v, data):
    return re.sub(r'( +)version\: ([0-9]+\.[0-9]+\.[0-9]+)', r'\1version: {0}'.format(v), data)


def update_module(v, data):
    m = re.match(r'(.*)version_added: (\'|"?)([0-9]+\.[0-9]+\.[0-9]+)(\'|"?)', data)
    if m and version.parse(v) < version.parse(m.group(3)):
        return re.sub(r'(.*)version_added\: (\'|"?)([0-9]+\.[0-9]+\.[0-9]+)(\'|"?)', r'\1version_added: "{0}"'.format(v), data)
    return data


def update_version(path, myfunc):
    out = []
    updated = False
    for d in path.read_text().split("\n"):
        upd = myfunc(d)
        if upd != d:
            updated = True
        out.append(upd)
    if updated:
        with open(path, "w") as fw:
            fw.write("\n".join(out))
    return updated


def get_next_release_version(path):
    repo = Repo(path)
    last_tag = repo.git.tag(sort='-creatordate').split('\n')[0]
    v = last_tag.split(".")
    v[-1] = str(int(v[-1]) + 1)
    return '.'.join(v)


def main():

    parser = argparse.ArgumentParser(
        description="Update the version in the following places\n\tThe version in galaxy.yml"
                    "\n\tThe README's requirements.yml example"
                    "\n\tThe VERSION in Makefile"
    )
    parser.add_argument(
        "--release-version",
        help="Release version to generate, e.g. 2.3.1"
    )
    parser.add_argument(
        "--collection-path",
        help="Path to the directory, default to the current directory",
        type=str,
        default=os.getcwd()
    )

    args = parser.parse_args()
    collection_path = os.path.abspath(args.collection_path)
    release_version = args.release_version or get_next_release_version(collection_path)

    try:
        version.Version(release_version)
    except version.InvalidVersion as e:
        sys.stderr.write("error reading version '{0}': {1}\n".format(release_version, e))
        sys.exit(1)

    result = dict(
        release_version=release_version,
        updated_files=[]
    )

    if update_version(PosixPath(collection_path) / PosixPath('README.md'), partial(update_readme, release_version)):
        result["updated_files"].append('README.md')
    if update_version(PosixPath(collection_path) / PosixPath('Makefile'), partial(update_makefile, release_version)):
        result["updated_files"].append('Makefile')
    if update_version(PosixPath(collection_path) / PosixPath('galaxy.yml'), partial(update_galaxy, release_version)):
        result["updated_files"].append('galaxy.yml')

    # validate version from modules
    for mod in glob.glob("plugins/modules/*.py"):
        if update_version(PosixPath(mod), partial(update_module, release_version)):
            result["updated_files"].append(os.path.basename(mod))
    print(json.dumps(result))


if __name__ == "__main__":
    main()
