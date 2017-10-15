import struct
import select
import socket
import ssl

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver
import logging

from .helpers import make_connection, my_inet_aton, hexstring, trigger_upstream_check

# https://github.com/gevent/gevent/issues/477
# Re-add sslwrap to Python 2.7.9

__ssl__ = __import__('ssl')

try:
    _ssl = __ssl__._ssl
except AttributeError:
    _ssl = __ssl__._ssl2

if not hasattr(_ssl, 'sslwrap'):
    from .helpers import new_sslwrap
    _ssl.sslwrap = new_sslwrap


# ###################################
# Constants
####################################

BUF_SIZE = 1024
TIME_OUT = 30

# Socks5 stages
INIT_STAGE = 0
AUTH_STAGE = 1
FINAL_STAGE = 2
CONN_ACCEPTED = 3

# Socks5 auth codes
AUTH_SUCCESSFUL = b'\x00'
AUTH_ERR_SERVER = b'\x01'
AUTH_ERR_BANDWIDTH = b'\x02'
AUTH_ERR_NOPLANFOUND = b'\x03'
AUTH_ERR_USERNOTFOUND = b'\x04'


####################################
# Exceptions
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


class Socks5PortForbidden(Socks5Exception):
    def __init__(self, port):
        Exception.__init__(self, "Port %d is not allowed" % port)


####################################
# Socks5 handlers
####################################

class Socks5RequestHandler(socketserver.StreamRequestHandler):
    """Socks5 request handler"""

    def setup(self):
        socketserver.StreamRequestHandler.setup(self)

        self.bytes_in = 0
        self.bytes_out = 0

        self.member_id = 0

        self.client_name = None
        self.server_name = None

    def handle(self):
        """Main handler"""

        stage = INIT_STAGE
        leftover = b''
        dest = None

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
                    if not self.local_auth and data == b'\x05\x01\x00':
                        self.request.sendall(b'\x05\x00')
                        stage = FINAL_STAGE
                        continue
                    # if username/password auth required
                    elif self.local_auth and data == b'\x05\x01\x02':
                        self.request.sendall(b'\x05\x02')
                        stage = AUTH_STAGE
                        continue
                    # no auth method accepted
                    else:
                        self.request.sendall(b'\x05\xFF')
                        #print(hexstring(data))
                        raise Socks5NoAuthMethodAccepted

                # Auth stage
                elif stage == AUTH_STAGE:
                    name_length, = struct.unpack('B', data[1])
                    if len(data[2:]) < name_length + 1:
                        leftover = data
                        continue
                    pass_length, = struct.unpack('B', data[2 + name_length])
                    if len(data[2 + name_length + 1:]) < pass_length:
                        leftover = data
                        continue

                    username = data[2:2 + name_length]
                    password = data[2 + name_length + 1:]

                    self.member_id, error_code = self.authority.auth(username, password)

                    if error_code != AUTH_SUCCESSFUL:
                        self.request.sendall(b'\x01' + error_code)
                        logging.info('Auth failed for user: %s', username)
                        raise Socks5AuthFailed
                    else:
                        self.request.sendall(b'\x01\x00')
                        logging.info('Auth succeeded for user: %s', username)
                        stage = FINAL_STAGE

                # Final stage
                elif stage == FINAL_STAGE:
                    if len(data) < 10:
                        leftover = data
                        continue
                    # Only TCP connections and IPV4 are allowed
                    if data[:2] != b'\x05\x01' or data[3:4] == b'\x04':
                        # Protocol error
                        self.request.sendall(b'\x05\x07')
                        raise Socks5NotImplemented
                    else:
                        domain = port = None
                        # Connect by domain name
                        if data[3:4] == b'\x03' or data[3:4] == b'\x02':
                            length, = struct.unpack('B', data[4:5])
                            domain = data[5:5 + length]
                            port, = struct.unpack('!H', data[5 + length:])
                        # Connect by ip address
                        elif data[3:4] == b'\x01':
                            domain = socket.inet_ntoa(data[4:8])
                            port, = struct.unpack('!H', data[8:])
                        try:
                            # Resolve domain to ip
                            if data[3:4] == b'\x02':
                                _, _, _, _, sa = \
                                filter(lambda x: x[0] == 2, socket.getaddrinfo(domain, port, 0, socket.SOCK_STREAM))[0]
                                ip, _ = sa
                                ip_bytes = my_inet_aton(ip)
                                port_bytes = struct.pack('!H', port)
                                self.request.sendall(b'\x05\x00\x00\x02' + ip_bytes + port_bytes)
                                # Return without actually connecting to domain
                                break
                            # Connect to destination
                            else:
                                dest = self.connect(domain, port, data)

                                # If connected to upstream/destination, let client know
                                dsockname = dest.getsockname()
                                client_ip = dsockname[0]
                                client_port = dsockname[1]
                                ip_bytes = my_inet_aton(client_ip)
                                port_bytes = struct.pack('!H', client_port)
                                self.request.sendall(b'\x05\x00\x00\x01' + ip_bytes + port_bytes)

                            stage = CONN_ACCEPTED

                        except Exception as e:
                            logging.exception('Error when trying to resolve/connect to: %s', (domain, port))
                            self.request.sendall(b'\x05\x01')
                            raise

            # Starting to forward data
            try:
                if dest:
                    result = self.forward(self.request, dest)
                    if result:
                        logging.debug("Forwarding finished")
                    else:
                        logging.debug('Exception/timeout when forwarding')
            except Exception as e:
                logging.exception('Error when forwarding')
            finally:
                if dest:
                    dest.close()
                logging.info("%d bytes out, %d bytes in. Socks5 session finished %s <-> %s.", self.bytes_out,
                             self.bytes_in, self.client_name, self.server_name)
                if self.local_auth and (self.bytes_in or self.bytes_out):
                    self.authority.usage(self.member_id, self.bytes_in + self.bytes_out)
        except Socks5Exception as e:
            logging.exception('Connection closed')
        except Exception as e:
            logging.exception('Error when proxying')
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
            sc = Socks5Client(self.upstream_addr, self.upstream_username, self.upstream_password,
                              data, enable_ssl=self.upstream_ssl)
            logging.info("Connecting to %s via upstream %s.", domain, self.upstream_addr)
            return sc.connect()
        else:
            # Connect to destination directly
            if len(self.allowed_ports) > 0 and port not in self.allowed_ports:
                raise Socks5PortForbidden(port)
            my_ip, my_port = self.request.getsockname()
            logging.info("Connecting to %s.", domain)
            return make_connection((domain, port), my_ip)

    def forward(self, client, server):
        """forward data between sockets"""
        self.client_name = client.getpeername()
        self.server_name = server.getpeername()

        while True:
            readables, writeables, exceptions = select.select(
                [client, server], [], [], TIME_OUT)

            # exception or timeout
            if exceptions or (readables, writeables, exceptions) == ([], [], []):
                return False

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
                    return True


class Socks5Client:
    """A socks5 client with optional SSL support"""

    def __init__(self, addr, username='', password='', data='',
                 enable_ssl=True, bind_to=None, to_upstream=True, dns_only=False):
        """
        :param addr: socket server address tuple
        :param username: username
        :param password: password
        :param data: a tuple of remote address you plan to connect to, or packed data of it.
        :param enable_ssl: if ssl should be enabled
        :param bind_to: ip to bind to for the local socket
        :param to_upstream: if an upstream is used
        :return: established socket or resolved address when dns_only is True
        """
        self.addr = addr
        self.enable_ssl = enable_ssl
        self.username = username.encode('utf-8')
        self.password = password.encode('utf-8')
        self.data = data
        self.bind_to = bind_to
        self.to_upstream = to_upstream
        self.dns_only = dns_only

    def connect(self):
        dest = make_connection(self.addr, self.bind_to, self.to_upstream)
        # SSL enabled
        if dest and self.enable_ssl:
            dest = ssl.wrap_socket(dest)

        if not dest:
            trigger_upstream_check()
            raise Socks5ConnectionFailed()

        # Server needs authentication
        if self.username and self.password:
            # Send auth method (username/password auth)
            dest.sendall(b'\x05\x01\x02')
            ans = dest.recv(BUF_SIZE)
            # Method accepted
            if ans == b'\x05\x02':
                name_length = struct.pack('B', len(self.username))
                pass_length = struct.pack('B', len(self.password))
                # Start auth
                dest.sendall(b'\x01' + name_length + self.username + pass_length + self.password)
                ans = dest.recv(BUF_SIZE)
                # Auth failed
                if ans != b'\x01\x00':
                    if not ans or ans[1] == AUTH_ERR_SERVER:
                        raise Socks5AuthFailed("An error occurred on server")
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
            dest.sendall(b'\x05\x01\x00')
            ans = dest.recv(BUF_SIZE)
            if ans != b'\x05\x00':
                raise Socks5AuthFailed

        if type(self.data) is tuple:
            domain, port = self.data
            port_str = struct.pack('!H', port)
            len_str = struct.pack('B', len(domain))
            if self.dns_only:
                addr_type = b'\x02'
            else:
                addr_type = b'\x03'
            data = b'\x05\x01\x00' + addr_type + len_str + domain + port_str
        else:
            data = self.data

        dest.sendall(data)
        ans = dest.recv(BUF_SIZE)
        if ans.startswith(b'\x05\x00'):
            if ans[3] == b'\x02':
                return socket.inet_ntoa(ans[4:8])
            else:
                return dest
        else:
            raise Socks5ConnectionFailed
