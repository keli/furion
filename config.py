from __future__ import with_statement

import time
import sys
import json

from os.path import exists
from StringIO import StringIO
import ConfigParser

from simpleauth import SimpleAuth


class FurionConfig(object):

    last_update = 0

    @classmethod
    def init(self, path):

        default_cfg = StringIO("""
[main]
local_ip = 127.0.0.1
local_port = 11080
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
        """)
        
        self.config = ConfigParser.ConfigParser()
        self.config.readfp(default_cfg)
        self.config.read(path)    

        auth_plugin = self.config.get('plugin', 'auth_plugin')

        self.authority = None
        if auth_plugin == 'simpleauth':
            self.authority = SimpleAuth()

        self.local_ip = self.config.get('main', 'local_ip')
        self.local_port = self.config.getint('main', 'local_port')

        self.local_ssl = self.config.getboolean('main', 'local_ssl')
        self.local_auth = self.config.getboolean('main', 'local_auth')
        self.pem_path = self.config.get('main', 'pem_path')
        if self.pem_path and not exists(self.pem_path):
            print 'Fatal error: pem "%s" cannot be found.' % self.pem_path
            time.sleep(3)
            sys.exit(-1)
        self.allowed_ports = [int(port) for port in self.config.get('main', 'allowed_ports').strip().split(',')]
        self.ping_server = self.config.getboolean('main', 'ping_server')
        self.dns_server = self.config.getboolean('main', 'dns_server')
        self.dns_server_port = self.config.getint('main', 'dns_server_port')
        self.dns_proxy = self.config.getboolean('main', 'dns_proxy')
        self.dns_proxy_port = self.config.getint('main', 'dns_proxy_port')
        self.remote_tcp_dns = self.config.get('main', 'remote_tcp_dns')
        self.log_level = self.config.getint('main', 'log_level')
        self.log_path = self.config.get('main', 'log_path')

        self.central_url = self.config.get('upstream', 'central_url')
        self.autoupdate_upstream_list = self.config.getboolean('upstream', 'autoupdate_upstream_list')
        self.update_frequency = self.config.get('upstream', 'update_frequency')
        self.upstream_list_path = self.config.get('upstream', 'upstream_list_path')

        if exists(self.upstream_list_path):
            self.upstream_list = json.loads(open(self.upstream_list_path).read())['upstream_list']
        else:
            self.upstream_list = None
        # self.upstream_ip = self.config.get('upstream', 'upstream_ip')
        # self.upstream_port = self.config.getint('upstream', 'upstream_port')
        # self.upstream_ssl = self.config.getboolean('upstream', 'upstream_ssl')
        # self.upstream_auth = self.config.getboolean('upstream', 'upstream_auth')
        # self.upstream_username = self.config.get('upstream', 'upstream_username')
        # self.upstream_password = self.config.get('upstream', 'upstream_password')

        self.local_addr = (self.local_ip, self.local_port)
        self.upstream_addr = None
        #self.upstream_addr = (self.upstream_ip, self.upstream_port) if self.upstream_ip else None
