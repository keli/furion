#!/usr/bin/env python

import sys
import time
from os.path import exists
from socks5 import *
from config import FurionConfig

if __name__ == "__main__":    
    try:
        if not exists('furion.cfg'):
            print "Fatal error: furion.cfg is not found, exiting..."
            time.sleep(3)
            sys.exit(-1)

        FurionConfig.init('furion.cfg')
        class FurionHandler(Socks5RequestHandler, FurionConfig): pass
        
        if FurionConfig.local_ssl:
            svr = SecureSocks5Server(FurionConfig.pem_path, FurionConfig.local_addr, FurionHandler)
        else:
            svr = Socks5Server(FurionConfig.local_addr, FurionHandler)
        
        print '=' * 78
        print "Furion server listening on %s, SSL %s, AUTH %s." % \
            (FurionConfig.local_addr, \
            "ON" if FurionConfig.local_ssl else "OFF", \
            "ON" if FurionConfig.local_auth else "OFF")

        print "Upstream proxy: %s, SSL %s, AUTH %s." % \
            (FurionConfig.upstream_addr, \
            "ON" if FurionConfig.upstream_ssl else "OFF", \
            "ON" if FurionConfig.upstream_auth else "OFF")
        print '=' * 78
        
        svr.serve_forever()
        
    except KeyboardInterrupt:
        print "Exiting..."
        svr.server_close()
        sys.exit()

