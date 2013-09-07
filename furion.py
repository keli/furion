#!/usr/bin/env python

import sys
import time
import threading
import logging
import logging.handlers
from os.path import exists
from socks5 import *
from ping import PingHandler
from config import FurionConfig as cfg
from helpers import *
from servers import *

if __name__ == "__main__":    
    try:
        if not exists('furion.cfg'):
            print "Fatal error: furion.cfg is not found, exiting..."
            time.sleep(3)
            sys.exit(-1)

        cfg.init('furion.cfg')

        # Initialize logger
        log_format = '%(asctime)s [%(filename)s:%(lineno)d][%(levelname)s] %(message)s'
        logging.basicConfig(format=log_format)

        logger = logging.getLogger()

        if cfg.log_path:
            formatter = logging.Formatter(log_format)
            log_handler = logging.handlers.RotatingFileHandler(cfg.log_path)
            log_handler.setFormatter(formatter)
            logger.addHandler(log_handler)

        logger.setLevel(cfg.log_level)

        if cfg.upstream_list:
            # Setup threads for upstream checking
            t1 = threading.Thread(target = run_check, args = (cfg,))
            t1.setDaemon(1)
            t1.start()

            t2 = threading.Thread(target = set_upstream, args = (cfg,))
            t2.setDaemon(1)
            t2.start()

        # Trigger an upstream check
        NoticeQueue.put(time.time())

        # Start UDP ping server
        if cfg.ping_server:
            ping_svr = PingServer(cfg.local_addr, PingHandler)
            t3 = threading.Thread(target = ping_svr.serve_forever, args = (5,))
            t3.setDaemon(1)
            t3.start()

        class FurionHandler(Socks5RequestHandler, cfg): pass
        
        if cfg.local_ssl:
            svr = SecureSocks5Server(cfg.pem_path, cfg.local_addr, FurionHandler)
        else:
            svr = Socks5Server(cfg.local_addr, FurionHandler)
        
        logging.info("Furion server listening on %s, SSL %s, AUTH %s." % \
            (cfg.local_addr, \
            "ON" if cfg.local_ssl else "OFF", \
            "ON" if cfg.local_auth else "OFF"))

        svr.serve_forever()
        
    except KeyboardInterrupt:
        print "Exiting..."
        svr.server_close()
        sys.exit()

