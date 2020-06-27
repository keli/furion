from .socks5 import Socks5Client
import struct
try:
    import socketserver
except ImportError:
    import SocketServer as socketserver
# from helpers import hexstring


class DNSQueryHandler(socketserver.BaseRequestHandler):
    """UDP DNS Proxy handler"""
    def handle(self):
        data = self.request[0].strip()
        sock = self.request[1]

        sc = Socks5Client(self.local_addr, data=(self.remote_tcp_dns, 53), enable_ssl=False)
        server = sc.connect()
        server.sendall(struct.pack('!H', len(data)) + data)
        result = server.recv(65535)
        server.close()
        sock.sendto(result[2:], self.client_address)

