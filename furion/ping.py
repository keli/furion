import math
import time
import logging
import socket
import select

try:
    import socketserver
except ImportError:
    import SocketServer as socketserver


def ping(addr, count=20, timeout=1):
    """UDP ping client"""
    # print "--- PING %s:%d ---" % addr
    results = []
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    for i in range(count):
        ts = time.time()
        data = 'PING %d %f %s' % (i, ts, '#' * 480)
        data = data.encode('utf-8')
        sock.sendto(data, addr)
        readables, writeables, exceptions = select.select(
            [sock], [], [], timeout)
        # exception
        if exceptions:
            time.sleep(1)
            continue
        # timeout
        if (readables, writeables, exceptions) == ([], [], []):
            continue
        if readables:
            ret = readables[0].recv(512)
            if ret == data:
                time_spent = (time.time() - ts) * 1000
                results.append(time_spent)
                # print '%d bytes from %s:%d, seq=%d time=%.3f ms' % (len(data), addr[0], addr[1], i, time_spent)

    received = len(results)
    missing = count - received
    loss = count - received
    # print "--- %s:%d ping statistics---" % addr
    # print "%d packets transmitted, %d packets received, %.1f%% packet loss" % (count, received, float(loss)*100/count)
    logging.debug("ping %s result: %d transmitted, %d received, %.1f%% loss",
                  addr, count, received, float(loss) * 100 // count)
    if received != 0:
        min_val = min(results)
        max_val = max(results)
        avg = sum(results) // count
        stddev = math.sqrt(sum([(x - avg) ** 2 for x in results]) // received)
        # print "round-trip min/avg/max/stddev = %.3f/%.3f/%.3f/%.3f" % (min_val, avg, max_val, stddev)
        logging.debug("ping %s min/avg/max/stddev = %.3f/%.3f/%.3f/%.3f", addr, min_val, avg, max_val, stddev)
        return missing * 500 + avg
    else:
        return float("inf")


class PingHandler(socketserver.BaseRequestHandler):
    """UDP Ping server handler"""

    def handle(self):
        data = self.request[0].strip()
        sock = self.request[1]
        sock.sendto(data, self.client_address)
        # print data

# Test client
# import threading
# for x in range(10):
# threading.Thread(target = ping, args = (('192.3.21.149', 8888),)).start()
