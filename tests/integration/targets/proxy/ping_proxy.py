#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright: (c) 2021, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
import urllib3
import sys


def main():
    try:
        urllib3.disable_warnings()
        params = {'keep_alive': True, 'proxy_basic_auth': "ansible:test"}
        head = urllib3.util.make_headers(**params)
        proxy = urllib3.ProxyManager(proxy_url='http://localhost:3128/', proxy_headers=head)
        resp = proxy.request('GET', 'http://google.com/')
        sys.stdout.write("status => {}\n".format(resp.status))
        sys.exit(0)
    except Exception as e:
        sys.stderr.write("Raised => {}\n".format(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
