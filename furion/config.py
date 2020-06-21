from __future__ import with_statement, print_function

import time
import sys
import json

from os.path import exists, dirname, basename, join, abspath
from io import StringIO

try:
    from configparser import ConfigParser
except ImportError:
    from ConfigParser import ConfigParser

from .helpers import get_upstream_from_central
from .simpleauth import SimpleAuth


default_config = u"""
[main]
local_ip = 127.0.0.1
local_port = 11080
rpc_port = 11081
local_ssl = off
pem_path =
local_auth = off
allowed_ports = 22,53,80,443
ping_server = off
dns_server = on
dns_server_port = 15353
dns_proxy = off
dns_proxy_port = 11053
remote_tcp_dns = 8.8.4.4
log_level = 20
log_path =

[upstream]
central_url =
autoupdate_upstream_list = off
update_frequency = weekly
upstream_list_path = upstream.json
# upstream_ip =
# upstream_port = 443
# upstream_ssl = on
# upstream_auth = on
# upstream_username =
# upstream_password =

[plugin]
auth_plugin =
"""


class FurionConfig(object):
    last_update = 0

    @classmethod
    def get_path(cls, path):
        if not path:
            return None
        if not exists(path) and basename(path) == path:
            return join(cls.config_dir, path)
        else:
            return path

    @classmethod
    def init(cls, path):

        default_cfg = StringIO(default_config)

        cls.config = ConfigParser()
        cls.config.readfp(default_cfg)
        cls.config.read(path)
        cls.config_dir = dirname(abspath(path))

        auth_plugin = cls.config.get('plugin', 'auth_plugin')

        cls.authority = None
        if auth_plugin == 'simpleauth':
            cls.password_path = cls.get_path(cls.config.get('simpleauth', 'password_path'))
            cls.authority = SimpleAuth(cls.password_path)

        cls.local_ip = cls.config.get('main', 'local_ip')
        cls.local_port = cls.config.getint('main', 'local_port')
        cls.rpc_port = cls.config.getint('main', 'rpc_port')

        cls.local_ssl = cls.config.getboolean('main', 'local_ssl')
        cls.local_auth = cls.config.getboolean('main', 'local_auth')
        cls.pem_path = cls.get_path(cls.config.get('main', 'pem_path'))
        if cls.pem_path and not exists(cls.pem_path):
            print('Fatal error: pem "%s" cannot be found.' % cls.pem_path)
            time.sleep(3)
            sys.exit(-1)
        ports = cls.config.get('main', 'allowed_ports').strip()
        if ports == 'all' or ports == '':
            cls.allowed_ports = []
        else:
            cls.allowed_ports = [int(port) for port in ports.split(',')]
        cls.ping_server = cls.config.getboolean('main', 'ping_server')
        cls.dns_server = cls.config.getboolean('main', 'dns_server')
        cls.dns_server_port = cls.config.getint('main', 'dns_server_port')
        cls.dns_proxy = cls.config.getboolean('main', 'dns_proxy')
        cls.dns_proxy_port = cls.config.getint('main', 'dns_proxy_port')
        cls.remote_tcp_dns = cls.config.get('main', 'remote_tcp_dns')
        cls.log_level = cls.config.getint('main', 'log_level')
        cls.log_path = cls.get_path(cls.config.get('main', 'log_path'))

        cls.central_url = cls.config.get('upstream', 'central_url')
        cls.autoupdate_upstream_list = cls.config.getboolean('upstream', 'autoupdate_upstream_list')
        cls.update_frequency = cls.config.get('upstream', 'update_frequency')
        cls.upstream_list_path = cls.get_path(cls.config.get('upstream', 'upstream_list_path'))

        cls.upstream_list = None
        if exists(cls.upstream_list_path):
            cls.upstream_list = json.loads(open(cls.upstream_list_path).read())['upstream_list']
        elif cls.autoupdate_upstream_list:
            get_upstream_from_central(cls)
        # cls.upstream_ip = cls.config.get('upstream', 'upstream_ip')
        # cls.upstream_port = cls.config.getint('upstream', 'upstream_port')
        # cls.upstream_ssl = cls.config.getboolean('upstream', 'upstream_ssl')
        # cls.upstream_auth = cls.config.getboolean('upstream', 'upstream_auth')
        # cls.upstream_username = cls.config.get('upstream', 'upstream_username')
        # cls.upstream_password = cls.config.get('upstream', 'upstream_password')

        cls.local_addr = (cls.local_ip, cls.local_port)
        cls.upstream_addr = None
        cls.upstream_ping = None
        # cls.upstream_addr = (cls.upstream_ip, cls.upstream_port) if cls.upstream_ip else None
