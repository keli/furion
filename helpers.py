import logging as log
import socket

log.basicConfig(level=log.DEBUG, format='%(asctime)s [%(filename)s:%(lineno)d][%(levelname)s] %(message)s')

def make_connection(addr, bind_to=None):
    """ Make TCP connection and return socket
    """
    domain, port = addr
    
    for res in socket.getaddrinfo(domain, port, 0, socket.SOCK_STREAM):
        af, socktype, proto, canonname, sa = res
        client = None
        try:
            client = socket.socket(af, socktype, proto)
            # Specify outgoing IP on a multihome server
            if bind_to:
                client.bind((bind_to, 0))
            client.connect(sa)
            return client
        except Exception, e:
            if client is not None:
                client.close()
    raise e

# Some versions of windows don't have socket.inet_pton
if hasattr(socket, 'inet_pton'):
    def my_inet_aton(ip_string):
        af, _, _, _, _ = socket.getaddrinfo(ip_string, 80, 0, socket.SOCK_STREAM)[0]
        return socket.inet_pton(af, ip_string)
else:
    my_inet_aton = socket.inet_aton

def hexstring(s):
    return ' '.join(['%02X' % ord(c) for c in s])
    
class SmartClass(object):
    def __init__(self, **kwargs):
        for key,value in kwargs.items():
            self.__setattr__(str(key), value)


