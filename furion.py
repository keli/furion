#!/usr/bin/env python

from socks5 import *
from config import FurionConfig
from multiprocessing import Process


if __name__ == "__main__":    
    try:
        FurionConfig.init('furion.cfg')
        class FurionHandler(Socks5RequestHandler, FurionConfig): pass
        
        if FurionConfig.local_ssl:
            svr = SecureSocks5Server(FurionConfig.pem_path, FurionConfig.local_addr, FurionHandler)
        else:
            svr = Socks5Server(FurionConfig.local_addr, FurionHandler)
        
        svr_proc = Process(target=svr.serve_forever)
        svr_proc.daemon = True
        svr_proc.start()

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
        
        svr_proc.join()        
        
    except KeyboardInterrupt:
        print "Exiting..."
        svr.server_close()
        svr_proc.terminate()
    
