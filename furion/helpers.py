import os
import logging
import socket
import time
import ssl
import threading

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen
import json

try:
    from queue import Queue
except ImportError:
    from Queue import Queue
from .ping import ping

# https://github.com/gevent/gevent/issues/477
# Re-add sslwrap to Python 2.7.9
import inspect

__ssl__ = __import__('ssl')

try:
    _ssl = __ssl__._ssl
except AttributeError:
    _ssl = __ssl__._ssl2


def new_sslwrap(sock, server_side=False, keyfile=None, certfile=None, cert_reqs=__ssl__.CERT_NONE,
                ssl_version=__ssl__.PROTOCOL_SSLv23, ca_certs=None, ciphers=None):
    context = __ssl__.SSLContext(ssl_version)
    context.verify_mode = cert_reqs or __ssl__.CERT_NONE
    if ca_certs:
        context.load_verify_locations(ca_certs)
    if certfile:
        context.load_cert_chain(certfile, keyfile)
    if ciphers:
        context.set_ciphers(ciphers)

    caller_self = inspect.currentframe().f_back.f_locals['self']
    return context._wrap_socket(sock, server_side=server_side, ssl_sock=caller_self)


if not hasattr(_ssl, 'sslwrap'):
    _ssl.sslwrap = new_sslwrap


MIN_INTERVAL = 30
UPSTREAM_TIMEOUT = 10
CONN_TIMEOUT = 5

# NoticeQueue is used for triggering an upstream check
NoticeQueue = Queue(1)
# Alive upstream servers are put into this queue
UpstreamQueue = Queue(100)


def make_connection(addr, bind_to=None, to_upstream=False):
    """
    Make TCP connection and return socket.

    :param addr: (domain, port) tuple to connect to
    :param bind_to: ip address to bind to
    :param to_upstream: if the destination is an upstream server
    :return: socket
    """

    domain, port = addr
    if to_upstream:
        timeout = UPSTREAM_TIMEOUT
    else:
        timeout = CONN_TIMEOUT

    for res in socket.getaddrinfo(domain, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        client = None
        try:
            client = socket.socket(af, socktype, proto)
            client.settimeout(timeout)
            # Specify outgoing IP on a multihome server
            # if bind_to and bind_to != '127.0.0.1':
            # client.bind((bind_to, 0))
            client.connect(sa)
            return client
        except Exception as e:
            if client is not None:
                client.close()
            logging.debug("Error occurred when making connection to dest %s: %s", addr, e)
            return None


def get_upstream_from_central(cfg, timing='now'):
    if timing == 'weekly':
        st = os.stat(cfg.upstream_list_path)
        if time.time() - st.st_mtime < 86400 * 7:
            logging.info("Ignore request to get upstream from central...")
            return None
    if cfg.central_url and cfg.autoupdate_upstream_list:
        try:
            logging.info("Fetching upstream from central...")
            jsonstr = urlopen(cfg.central_url).read()
            jsonstr = jsonstr.decode('utf-8')
            cfg.upstream_list = json.loads(jsonstr)['upstream_list']
        except Exception as e:
            logging.exception("Failed to fetch upstream from central")
        else:
            logging.info("Saving upstream list...")
            open(cfg.upstream_list_path, 'w').write(jsonstr)
            return True
    else:
        logging.fatal("No central_url is configured or autoupdate is off.")
        return False


def run_check(cfg):
    """ Check alive upstream servers
    """
    if not cfg.upstream_list:
        get_upstream_from_central(cfg)
    else:
        if cfg.update_frequency == 'start':
            get_upstream_from_central(cfg)
        elif cfg.update_frequency == 'weekly':
            get_upstream_from_central(cfg, 'weekly')

    while True:
        ts = NoticeQueue.get()
        diff = ts - cfg.last_update
        if cfg.last_update == 0 or diff > MIN_INTERVAL:
            logging.info("Last check %d seconds ago, checking for live upstream...", diff)
            for upstream in cfg.upstream_list:
                # set a default upstream if none is set already
                if not cfg.upstream_addr:
                    cfg.upstream_addr = (upstream['ip'], upstream['port'])
                    cfg.upstream_username = upstream['username']
                    cfg.upstream_password = upstream['password']
                t = threading.Thread(target=check_alive, args=(upstream,))
                t.start()


def check_alive(upstream):
    dest = None
    try:
        addr = (upstream['ip'], upstream['port'])
        dest = make_connection(addr, None, True)
        # SSL enabled
        if dest and upstream['ssl']:
            dest = ssl.wrap_socket(dest)
            logging.debug("Upstream %s is ALIVE", addr)

        if not dest:
            logging.debug("Upstream %s is DEAD: Connection failed", addr)
    except Exception as e:
        if dest is not None:
            dest.close()
        logging.debug("Upstream %s is DEAD: %s", addr, e)
        return
    try:
        score = ping((upstream['ip'], upstream['port']))
        upstream['ping'] = score
        UpstreamQueue.put((time.time(), upstream))
    except Exception as e:
        logging.debug("Ping to %s failed: %s", addr, e)


def set_upstream(cfg):
    while True:
        ts, upstream = UpstreamQueue.get()
        addr = (upstream['ip'], upstream['port'])
        if cfg.last_update == 0 or ts - cfg.last_update > MIN_INTERVAL:
            logging.info("Setting upstream to: %s", addr)
            cfg.last_update = ts
            cfg.upstream_addr = addr
            cfg.upstream_auth = upstream['auth']
            cfg.upstream_ssl = upstream['ssl']
            cfg.upstream_username = upstream['username']
            cfg.upstream_password = upstream['password']
            cfg.upstream_ping = upstream['ping']
        else:
            logging.debug("Upstream %s is not used", addr)


def trigger_upstream_check():
    logging.debug("Triggering upstream check...")
    NoticeQueue.put_nowait(time.time())


def check_upstream_repeatedly(seconds):
    while True:
        trigger_upstream_check()
        time.sleep(seconds)


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
