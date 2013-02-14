#!/usr/bin/env python

import sys
import time
import threading
from os.path import exists
from socks5 import *
from config import FurionConfig
from helpers import *

if __name__ == "__main__":    
    try:
        if not exists('furion.cfg'):
            print "Fatal error: furion.cfg is not found, exiting..."
            time.sleep(3)
            sys.exit(-1)

        FurionConfig.init('furion.cfg')

        # Check available upstream
        if FurionConfig.upstream_servers:
            t1 = threading.Thread(target = run_check, args = (FurionConfig,))
            t1.setDaemon(1)
            t1.start()

            t2 = threading.Thread(target = set_upstream, args = (FurionConfig,))
            t2.setDaemon(1)
            t2.start()

            NoticeQueue.put(time.time())

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

        print "Default upstream proxy: %s, SSL %s, AUTH %s." % \
            (FurionConfig.upstream_addr, \
            "ON" if FurionConfig.upstream_ssl else "OFF", \
            "ON" if FurionConfig.upstream_auth else "OFF")
        print '=' * 78
        
        svr.serve_forever()
        
    except KeyboardInterrupt:
        print "Exiting..."
        svr.server_close()
        sys.exit()

