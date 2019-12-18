#!/usr/bin/env python3

# clear; python srv.py 1 224.0.0.1 54330

import sys
import struct
import socket
import logging

import config

# per <https://en.wikipedia.org/wiki/User_Datagram_Protocol>
MAX_UDP_PAYLOAD = 65507

def handleEventMain(notification, continueProcessing, notifications):
    notifications.append(notification)
    print(notification)

    continueProcessing = (notification != "exit")

    return continueProcessing

def main(arg1, arg2):

    notifications = []

    cfg = config.read_config()

    id          = cfg['id']
    serverName  = cfg['name']
    notify = cfg['notify'][0]
    multicastAddress = notify['address']
    multicastPort = notify['port']


    # See <https://pymotw.com/3/socket/multicast.html> for details

    server_address = ('', int(multicastPort))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server_address)

    group = socket.inet_aton(multicastAddress)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"serverName: {serverName}, id: {id} Listening on udp://{multicastAddress}:{multicastPort}")

    continueProcessing = True
    try:
        while continueProcessing:
            data, _ = sock.recvfrom(MAX_UDP_PAYLOAD)
            notification = data.decode()

            continueProcessing = handleEventMain(notification, continueProcessing, notifications)
    except:
        print("Unexpected error:", sys.exc_info()[0])
        sock.close()

def usage(program):
    print(f'Usage: {program} -c srv.1.yaml', file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage(sys.argv[0])

    sys.exit(main(*sys.argv[1:]))