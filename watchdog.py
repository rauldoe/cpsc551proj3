import sys
import struct
import socket
import uuid
import logging
import time

import proxy
import config

from common import Common

servers = [
    {
    "id": 0,
    "host": "224.0.0.1",
    "port": 54324,
    "ts": "http://localhost:8004"
    },
    {
    "id": 1,
    "host": "224.0.0.1",
    "port": 54325,
    "ts": "http://localhost:8005"
    }
]

electionEvent = f"elect elect elect"
adapter_host = "localhost"
adapter_port = 8006
waitPeriod = 5

servers_adapter_uri = f'http://{adapter_host}:{adapter_port}'

servers_ts = proxy.TupleSpaceAdapter(servers_adapter_uri)

def doEmpty(ts, searchPattern):
    isEmpty = False
    while not isEmpty:
        td = ts._inp(searchPattern)
        if (td is None):
            isEmpty = True

def callForElection(servers, electionEvent, ts):

    doEmpty(ts, ["candidate", "candidate", None])

    for server in servers:
        sendMessage(electionEvent, server["host"], server["port"])

def sendMessage(message, ipAddress, port):
    multicast_group = (ipAddress, port)

    # Create the datagram socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Set a timeout so the socket does not block indefinitely when trying
    # to receive data.
    sock.settimeout(0.2)

    # Set the time-to-live for messages to 1 so they do not go past the
    # local network segment.
    ttl = struct.pack('b', 1)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:

        # Send data to the multicast group
        print(f"sending {message}")
        _ = sock.sendto(bytearray(message, encoding ='utf-8'), multicast_group)

        # Look for responses from all recipients
        while True:
            print(f"waiting to receive")
            try:
                data, server = sock.recvfrom(16)
            except socket.timeout:
                print(f"timed out; no more responses")
                break
            else:
                print(f"received {data} from {server}")

    finally:
        print(f"closing socket")
        sock.close()

def checkLeader(ts, servers, waitPeriod):

    isAlive = True

    electionTd = ts._rdp(["candidate", "candidate", None])
    if (electionTd is None):
        td = ts._rdp(["leader", "leader", None])

        if (td is None):
            isAlive = False
        else:
            server = servers[td[2]]
            print(f'checking {td[2]} {server["port"]}')
            doEmpty(ts, ["alive", "alive", None])
            sendMessage("check_leader check_leader check_leader", server["host"], server["port"])
            time.sleep(waitPeriod)
            aliveTd = ts._rdp(["alive", "alive", None])
            isAlive = (aliveTd is not None)
            doEmpty(ts, ["alive", "alive", None])

    return isAlive

isDone = False

while (not isDone):
    time.sleep(waitPeriod)

    try:
        isAlive = checkLeader(servers_ts, servers, waitPeriod)
    except Exception as e1:
        logging.error(f'{e1}')

    try:
        if (not isAlive):
            print("calling Election")
            callForElection(servers, electionEvent, servers_ts)
    except Exception as e2:
        logging.error(f'{e2}')