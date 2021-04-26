# Copyright 2018 Red Hat | Ansible
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

import urllib3


def main():
    try:
        urllib3.disable_warnings()
        params = {'keep_alive': True, 'proxy_basic_auth': "ansible:test"}
        head = urllib3.util.make_headers(**params)
        print("-- make_headers --")
        proxy = urllib3.ProxyManager(proxy_url='http://localhost:3128/', proxy_headers=head)
        print("-- ProxyManager --")
        resp = proxy.request('GET', 'http://google.com/')
        print("-- GET (status={}) --\n{}".format(resp.status, resp.headers))
    except Exception as e:
        print("Raised => {}".format(e))


if __name__ == '__main__':
    main()
