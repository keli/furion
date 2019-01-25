#!/usr/bin/env python

import sys
import getopt
import logging.handlers
from os.path import exists
from .socks5 import *
from .ping import PingHandler
from .dns import *
from .rpc import *
from .config import FurionConfig as cfg
from .helpers import *
from .servers import *


def usage():
    print('Usage: furion -c <furion.cfg>')


def setup_server():
    config_path = 'furion.cfg' if exists('furion.cfg') else '/etc/furion/furion.cfg'

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hc:")
    except getopt.GetoptError:
        usage()
        sys.exit(1)
    for opt, arg in opts:
        if opt == "-c":
            config_path = arg
        else:
            usage()
            sys.exit()

    # Initialize logger
    log_format = '%(asctime)s [%(filename)s:%(lineno)d][%(levelname)s] %(message)s'
    logging.basicConfig(format=log_format, filemode='w')

    logger = logging.getLogger()

    # Initialize config
    if not exists(config_path):
        print("Fatal error: %s is not found, exiting..." % config_path)
        time.sleep(3)
        sys.exit(-1)

    cfg.init(config_path)

    if cfg.log_path:
        formatter = logging.Formatter(log_format)
        log_handler = logging.handlers.RotatingFileHandler(cfg.log_path)
        log_handler.setFormatter(formatter)
        logger.addHandler(log_handler)

    logger.setLevel(cfg.log_level)

    try:
        import gevent
        import gevent.monkey
        gevent.monkey.patch_all()
    except ImportError:
        gevent = None

    if gevent:
        logging.info('Using gevent model...')
    else:
        logging.info('Using threading model...')

    if cfg.upstream_list:
        # Setup threads for upstream checking
        thr = threading.Thread(target=run_check, args=(cfg,))
        thr.setDaemon(1)
        thr.start()

        thr = threading.Thread(target=set_upstream, args=(cfg,))
        thr.setDaemon(1)
        thr.start()

    # Start UDP ping server
    if cfg.ping_server:
        ping_svr = PingServer(cfg.local_addr, PingHandler)
        thr = threading.Thread(target=ping_svr.serve_forever, args=(5,))
        thr.setDaemon(1)
        thr.start()

    # Start UDP DNS proxy
    if cfg.dns_proxy:
        class DNSHandler(DNSProxyHandler, cfg):
            pass
        dns_proxy = DNSServer((cfg.local_ip, cfg.dns_proxy_port), DNSHandler)
        thr = threading.Thread(target=dns_proxy.serve_forever, args=())
        thr.setDaemon(1)
        thr.start()

    # Start UDP DNS server
    if cfg.dns_server:
        class DNSHandler(DNSQueryHandler, cfg):
            pass
        dns_proxy = DNSServer((cfg.local_ip, cfg.dns_server_port), DNSHandler)
        thr = threading.Thread(target=dns_proxy.serve_forever, args=())
        thr.setDaemon(1)
        thr.start()

    # Start RPC server
    class RPCHandler(RPCRequestHandler, cfg):
        pass
    rpc_svr = RPCServer((cfg.local_ip, cfg.rpc_port), RPCHandler)
    thr = threading.Thread(target=rpc_svr.serve_forever, args=())
    thr.setDaemon(1)
    thr.start()

    # Re-check upstream every 30 minutes
    thr = threading.Thread(target=check_upstream_repeatedly, args=(1800,))
    thr.setDaemon(1)
    thr.start()

    class FurionHandler(Socks5RequestHandler, cfg):
        pass
    
    if cfg.local_ssl:
        svr = SecureSocks5Server(cfg.pem_path, cfg.local_addr, FurionHandler)
    else:
        svr = Socks5Server(cfg.local_addr, FurionHandler)
    
    logging.info("Furion server listening on %s, SSL %s, AUTH %s." %
                    (cfg.local_addr, "ON" if cfg.local_ssl else "OFF", "ON" if cfg.local_auth else "OFF"))

    return svr


def main():
    svr = setup_server()
    try:
        svr.serve_forever()        
    except KeyboardInterrupt:
        print("Exiting...")
        svr.server_close()
        sys.exit()
        

if __name__ == "__main__":    
    main()