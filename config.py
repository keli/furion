from __future__ import with_statement

import time
import socket

from StringIO import StringIO
import ConfigParser

from simpleauth import SimpleAuth

class FurionConfig(object):

    @classmethod
    def init(self, path):

        default_cfg = StringIO("""
[main]
local_ip = 127.0.0.1
local_port = 11080
local_ssl = off
pem_path = 
local_auth = off

[upstream]
upstream_ip =
upstream_port = 443
upstream_ssl = on
upstream_auth = on
upstream_username = 
upstream_password =

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

        self.upstream_ip = self.config.get('upstream', 'upstream_ip')
        self.upstream_port = self.config.getint('upstream', 'upstream_port')
        self.upstream_ssl = self.config.getboolean('upstream', 'upstream_ssl')
        self.upstream_auth = self.config.getboolean('upstream', 'upstream_auth')
        self.upstream_username = self.config.get('upstream', 'upstream_username')
        self.upstream_password = self.config.get('upstream', 'upstream_password')

        self.local_addr = (self.local_ip, self.local_port)
        self.upstream_addr = (self.upstream_ip, self.upstream_port) if self.upstream_ip else None
