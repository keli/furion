#!/usr/bin/env python

import sys
import time
import threading
import logging
import logging.handlers
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

        # Initialize logger
        log_format = '%(asctime)s [%(filename)s:%(lineno)d][%(levelname)s] %(message)s'
        logging.basicConfig(format=log_format)

        logger = logging.getLogger()

        if FurionConfig.log_path:
            formatter = logging.Formatter(log_format)
            log_handler = logging.handlers.RotatingFileHandler(FurionConfig.log_path)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)

        logger.setLevel(FurionConfig.log_level)

        if FurionConfig.upstream_list:
            # Setup threads for upstream checking
            t1 = threading.Thread(target = run_check, args = (FurionConfig,))
            t1.setDaemon(1)
            t1.start()

            t2 = threading.Thread(target = set_upstream, args = (FurionConfig,))
            t2.setDaemon(1)
            t2.start()

        # Trigger an upstream check
        NoticeQueue.put(time.time())

        class FurionHandler(Socks5RequestHandler, FurionConfig): pass
        
        if FurionConfig.local_ssl:
            svr = SecureSocks5Server(FurionConfig.pem_path, FurionConfig.local_addr, FurionHandler)
        else:
            svr = Socks5Server(FurionConfig.local_addr, FurionHandler)
        
        logging.info("Furion server listening on %s, SSL %s, AUTH %s." % \
            (FurionConfig.local_addr, \
            "ON" if FurionConfig.local_ssl else "OFF", \
            "ON" if FurionConfig.local_auth else "OFF"))

        svr.serve_forever()
        
    except KeyboardInterrupt:
        print "Exiting..."
        svr.server_close()
        sys.exit()

