try:
    import socketserver
except ImportError:
    import SocketServer as socketserver
import pickle


class RPCRequestHandler(socketserver.BaseRequestHandler):
    """UDP RPC server handler"""
    def handle(self):
        data = self.request[0].strip()
        sock = self.request[1]

        sock.sendto(pickle.dumps(getattr(self, data, None)), self.client_address)