import logging
import socket
import time
import threading
from Queue import Queue

MIN_INTERVAL = 10
CONN_TIMEOUT = 10

# NoticeQueue is used for triggering an upstream check
NoticeQueue = Queue(1)
# Alive upstream servers are put into this queue
UpstreamQueue = Queue(100)

def make_connection(addr, bind_to=None, to_upstream=False):
    """ Make TCP connection and return socket
    """
    domain, port = addr
    
    for res in socket.getaddrinfo(domain, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        client = None
        try:
            client = socket.socket(af, socktype, proto)
            client.settimeout(CONN_TIMEOUT)
            # Specify outgoing IP on a multihome server
            if bind_to:
                client.bind((bind_to, 0))
            client.connect(sa)
            return client
        except Exception, e:
            if client is not None:
                client.close()
            logging.debug("Error occurred when making connection to dest: %s", e)
            # initiate an upstream check
            if to_upstream:
                logging.debug("Rechecking upstreams...")
                try:
                    NoticeQueue.put_nowait(time.time())
                except:
                    pass
    raise e

def run_check(cfg):
    """ Check alive upstream servers
    """
    while True:
        ts = NoticeQueue.get()
        if cfg.last_update == 0 or ts - cfg.last_update > MIN_INTERVAL:
            logging.debug("Checking upstream addresses...")
            addr_list = cfg.upstream_servers.strip().split(',')
            for addr in addr_list:
                addr_tmp = addr.strip().split(':')
                addr_tmp[1] = int(addr_tmp[1])
                addr_tuple = tuple(addr_tmp)
                # set a default upstream if none is set already
                if not cfg.upstream_addr:
                    cfg.upstream_addr = addr_tuple
                t = threading.Thread(target = check_alive, args = (addr_tuple,))
                t.setDaemon(1)
                t.start()

def check_alive(addr):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONN_TIMEOUT)
    try:
        sock.connect(addr)
        ts = time.time()
        UpstreamQueue.put((ts, addr))
        logging.info("Upstream %s is ALIVE", addr)        
    except Exception, e:
        if sock is not None:
            sock.close()
        logging.info("Upstream %s is DEAD", addr)

def set_upstream(cfg):
    while True:
        ts, addr = UpstreamQueue.get()
        if cfg.last_update == 0 or ts - cfg.last_update > MIN_INTERVAL:
            logging.info("Setting upstream to: %s", addr)
            cfg.last_update = ts
            cfg.upstream_addr = addr
        else:
            logging.info("Upstream %s is not used", addr)


# Some versions of windows don't have socket.inet_pton
if hasattr(socket, 'inet_pton'):
    def my_inet_aton(ip_string):
        af, _, _, _, _ = socket.getaddrinfo(ip_string, 80, 0, socket.SOCK_STREAM)[0]
        return socket.inet_pton(af, ip_string)
else:
    my_inet_aton = socket.inet_aton

def hexstring(s):
    return ' '.join(['%02X' % ord(c) for c in s])

# http://stackoverflow.com/a/14620633/1349791
class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self
