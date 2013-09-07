import os
import sys
import time
import errno
import struct
import traceback
import threading
import select
import socket
import ssl
import SocketServer
import logging
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

from Queue import Queue
from types import *

from helpers import make_connection, my_inet_aton

####################################
## Constants
####################################

BUF_SIZE = 1024
TIME_OUT = 30
POOL_SIZE = 50

# Socks5 stages
INIT_STAGE = 0
AUTH_STAGE = 1
FINAL_STAGE = 2
CONN_ACCEPTED = 3        

# Socks5 auth codes
AUTH_SUCCESSFUL = '\x00'
AUTH_ERR_SERVER = '\x01'
AUTH_ERR_BANDWIDTH = '\x02'
AUTH_ERR_NOPLANFOUND = '\x03'
AUTH_ERR_USERNOTFOUND = '\x04'


####################################
## Exceptions
####################################

class Socks5Exception(Exception):
    """Base socks5 exception class"""
    pass
    
class Socks5NoAuthMethodAccepted(Socks5Exception):
    def __init__(self):
        Exception.__init__(self, "No auth method accepted.")
    
class Socks5AuthFailed(Socks5Exception):
    def __init__(self, reason=None):
        if reason:
            Exception.__init__(self, "Authentication failed: %s." % reason)
        else:
            Exception.__init__(self, "Authentication failed.")

class Socks5DnsFailed(Socks5Exception):
    def __init__(self):
        Exception.__init__(self, "DNS resolve failed.")

class Socks5ConnectionFailed(Socks5Exception):
    def __init__(self):
        Exception.__init__(self, "Connection to upstream/destination failed.")

class Socks5RemoteConnectionClosed(Socks5Exception):
    def __init__(self):
        Exception.__init__(self, "Remote connection closed.")
        
class Socks5SocketError(Socks5Exception):
    def __init__(self):
        Exception.__init__(self, "A socket error occurred when forwarding.")

class Socks5ConnectionClosed(Socks5Exception):
    def __init__(self):
        Exception.__init__(self, "Socks5 connection closed.")

class Socks5NotImplemented(Socks5Exception): 
    def __init__(self):
        Exception.__init__(self, "Protocol not implemented yet.")


####################################
## Servers
####################################

class SecureTCPServer(SocketServer.TCPServer):
    """TCP server with SSL"""
    
    allow_reuse_address = True

    def __init__(self, pem_path, server_address, handler_class):
        SocketServer.BaseServer.__init__(self, server_address, handler_class)

        af, socktype, proto, canonname, sa = socket.getaddrinfo(
            self.server_address[0], self.server_address[1], 0, socket.SOCK_STREAM)[0]
        sock = socket.socket(af, socktype, proto)
        #sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(TIME_OUT)

        # Don't do handshake on connect for ssl (which will block http://bugs.python.org/issue1251)
        self.socket = ssl.wrap_socket(sock, pem_path, pem_path, server_side=True, do_handshake_on_connect=False)
        self.server_bind()
        self.server_activate()


class ThreadPoolMixIn(SocketServer.ThreadingMixIn):
    """Thread pool mixin"""

    def serve_forever(self):
        self.requests = Queue(POOL_SIZE)

        for x in range(POOL_SIZE):
            t = threading.Thread(target = self.process_request_thread)
            t.setDaemon(1)
            t.start()

        while True:
            self.handle_request()

        self.server_close()

    def process_request_thread(self):
        while True:
            SocketServer.ThreadingMixIn.process_request_thread(self, *self.requests.get())

    def handle_request(self):
        try:
            request, client_address = self.get_request()
        except socket.error:
            return
        if self.verify_request(request, client_address):
            self.requests.put((request, client_address))


class Socks5Server(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    """Threading Socks5 server"""
    allow_reuse_address = True

class TPSocks5Server(ThreadPoolMixIn, SocketServer.TCPServer):
    """Thread Pool Socks5 server"""
    pass
    
class SecureSocks5Server(SocketServer.ThreadingMixIn, SecureTCPServer):
    """Secure Socks5 server"""
    pass

class TPSecureSocks5Server(ThreadPoolMixIn, SecureTCPServer):
    """Thread Pool Secure Socks5 server"""
    pass
    

####################################
## Socks5 handlers
####################################

class Socks5RequestHandler(SocketServer.StreamRequestHandler):
    """Socks5 request handler"""

    def setup(self):
        SocketServer.StreamRequestHandler.setup(self)
        
        self.bytes_in = 0
        self.bytes_out = 0
        
        self.member_id = 0
        
        self.client_name = None
        self.server_name = None
        
    def handle(self):
        """Main handler"""

        stage = INIT_STAGE
        leftover = ''

        try:    
            while stage < CONN_ACCEPTED:
                data = self.request.recv(BUF_SIZE)
                
                # Client closed connection
                if not data:
                    raise Socks5ConnectionClosed
                    
                data = leftover + data

                if len(data) < 3:
                    leftover = data
                    continue

                # Init stage
                if stage == INIT_STAGE:
                    # If no auth required                
                    if not self.local_auth and data == '\x05\x01\x00':
                        self.request.sendall('\x05\x00')
                        stage = FINAL_STAGE
                        continue
                    # if username/password auth required
                    elif self.local_auth and data == '\x05\x01\x02':
                        self.request.sendall('\x05\x02')
                        stage = AUTH_STAGE
                        continue
                    # no auth method accepted
                    else:
                        self.request.sendall('\x05\xFF')
                        #print hexstring(data)
                        raise Socks5NoAuthMethodAccepted
                        
                # Auth stage
                elif stage == AUTH_STAGE:
                    name_length, = struct.unpack('B', data[1])
                    if len(data[2:]) < name_length + 1:
                        leftover = data
                        continue
                    pass_length, = struct.unpack('B', data[2+name_length])
                    if len(data[2+name_length+1:]) < pass_length:
                        leftover = data
                        continue                    

                    username = data[2:2+name_length]
                    password = data[2+name_length+1:]

                    self.member_id, error_code = self.authority.auth(username, password)
                    
                    if error_code != AUTH_SUCCESSFUL:
                        self.request.sendall('\x01' + error_code)
                        logging.info('Auth failed for user: %s', username)
                        raise Socks5AuthFailed
                    else:
                        self.request.sendall('\x01\x00')
                        logging.info('Auth succeeded for user: %s', username)
                        stage = FINAL_STAGE
                        
                # Final stage
                elif stage == FINAL_STAGE:
                    if data < 6:
                        leftover = data
                        continue

                    # Only TCP connections and requests by DNS are allowed
                    if data[:2] != '\x05\x01' or data[3] != '\x03':
                        # Protocol error
                        self.request.sendall('\x05\x07')
                        raise Socks5NotImplemented
                    else:
                        length, = struct.unpack('B', data[4])
                        if len(data) < 5 + length + 2:
                            leftover = data
                            continue

                        domain = data[5:5+length]
                        port, = struct.unpack('!H', data[5+length:])

                        try:
                            # Connect to destination
                            dest = self.connect(domain, port, data)

                            # If connected to upstream/destination, let client know
                            dsockname = dest.getsockname()
                            client_ip = dsockname[0]
                            client_port = dsockname[1]
                            ip_bytes = my_inet_aton(client_ip)                            
                            port_bytes = struct.pack('!H', client_port)
                            self.request.sendall('\x05\x00\x00\x01' + ip_bytes + port_bytes)
                                
                            stage = CONN_ACCEPTED

                        except Exception, e:
                            logging.debug('Error when trying to resolve/connect to: %s, reason: %s', (domain, port), e)
                            #traceback.print_exc()
                            self.request.sendall('\x05\x01')
                            raise

            # Starting to forward data
            try:
                self.forward(self.request, dest)
            except Socks5Exception, e:
                logging.debug("Forwarding finished: %s", e)
            except Exception, e:
                logging.debug('Error when forwarding: %s', e)
                #traceback.print_exc()
            finally:
                dest.close()
                logging.info("%d bytes out, %d bytes in. Socks5 session finished %s <-> %s.", self.bytes_out, self.bytes_in, self.client_name, self.server_name)
                if self.local_auth and (self.bytes_in or self.bytes_out):
                    self.authority.usage(self.member_id, self.bytes_in + self.bytes_out)
        except Socks5Exception, e:
            logging.debug("Connection closed. Reason: %s", e)
        except Exception, e:
            logging.debug('Error when proxying: %s', e)
            #traceback.print_exc()
        finally:
            try:
                self.request.shutdown(socket.SHUT_RDWR)
            except:
                self.request.close()
            return

    def connect(self, domain, port, data):
        # Connect to upstream instead of destination
        if self.upstream_addr:
            sc = Socks5Client(self.upstream_addr, self.upstream_username, self.upstream_password, data)
            logging.info("Connecting to %s via upstream %s.", domain, self.upstream_addr)
            return sc.connect()
        else:
            # Connect to destination directly
            if port not in self.allowed_ports:
                raise Socks5SocketError("Port %d not allowed for %s" % (port, username))
            my_ip, my_port = self.request.getsockname()
            logging.info("Connecting to %s.", domain)
            return make_connection((domain, port), my_ip)

    def forward(self, client, server):
        """forward data between sockets"""
        self.client_name = client.getpeername()
        self.server_name = server.getpeername()
        
        while True:
            readables, writeables, exceptions = select.select(
                [client,server], [], [], TIME_OUT)

            # exception or timeout
            if exceptions or (readables, writeables, exceptions) == ([], [], []):
                raise Socks5ConnectionClosed

            data = ''

            for readable in readables:
                data = readable.recv(BUF_SIZE)
                
                if data:
                    if readable == client:
                        self.bytes_out += len(data)
                        server.send(data)
                    else:
                        self.bytes_in += len(data)
                        client.send(data)
                else:
                    if readable == client:
                        raise Socks5ConnectionClosed
                    else:
                        raise Socks5RemoteConnectionClosed

                    
class Socks5Client:
    """A socks5 client with optional SSL support"""
    def __init__(self, addr, username='', password='', data='', enable_ssl=True, bind_to=None, to_upstream=True):
        """
        @param data A tuple of remote address you plan to connect to, or packed data of it.
        """
        self.addr = addr
        self.enable_ssl = enable_ssl
        self.username = username
        self.password = password
        self.data = data
        self.bind_to = bind_to
        self.to_upstream = to_upstream
        
    def connect(self):
        dest = make_connection(self.addr, self.bind_to, self.to_upstream)
        # SSL enabled
        if self.enable_ssl:
            dest = ssl.wrap_socket(dest)

        # Server needs authentication
        if self.username and self.password:
            # Send auth method (username/password auth)
            dest.sendall('\x05\x01\x02')
            ans = dest.recv(BUF_SIZE)
            # Method accepted
            if ans == '\x05\x02':                                
                name_length = struct.pack('B', len(self.username))
                pass_length = struct.pack('B', len(self.password))
                # Start auth
                dest.sendall('\x01' + name_length + self.username + pass_length + self.password)
                ans = dest.recv(BUF_SIZE)
                # Auth failed
                if ans != '\x01\x00':
                    if not ans or ans[1] == AUTH_ERR_SERVER:
                        raise Socks5AuthFailed("An error occured on server")
                    elif ans[1] == AUTH_ERR_BANDWIDTH:
                        raise Socks5AuthFailed("Bandwidth usage exceeded quota")
                    elif ans[1] == AUTH_ERR_NOPLANFOUND:
                        raise Socks5AuthFailed("Can't find a subscribed plan for user")
                    elif ans[1] == AUTH_ERR_USERNOTFOUND:
                        raise Socks5AuthFailed("User not found or wrong password")
                    else:
                        raise Socks5AuthFailed
            else:
                raise Socks5AuthFailed("No accepted authentication method")
        # No auth needed
        else:
            dest.sendall('\x05\x01\x00')
            ans = dest.recv(BUF_SIZE)
            if ans != '\x05\x00':
                raise Socks5AuthFailed

        if type(self.data) is TupleType:
            domain, port = self.data
            port_str, = struct.pack('!H', port)
            len_str, = struct.pack('B', len(domain))
            data = '\x05\x01\x03' + len_str + domain + port_str
        else:
            data = self.data
        dest.sendall(data)
        ans = dest.recv(BUF_SIZE)
        if ans.startswith('\x05\x00'):
            return dest
        else:
            raise Socks5ConnectionFailed
