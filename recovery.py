#!/usr/bin/env python3

# clear; python recovery.py 224.0.0.1 54322

import sys
import struct
import socket
import uuid
import logging

import proxy
import config

from common import Common

# per <https://en.wikipedia.org/wiki/User_Datagram_Protocol>
MAX_UDP_PAYLOAD = 65507

def preInit():
    logging.info('preInit')

def replayHandlingInfo():
    return [[Common.EventWrite, Common.EventTake], lambda msg, ts: handleEventForEachMessage(msg, ts)]

def handleEventForEachMessage(message, ts):

    if (message[Common.MessageEvent] == Common.EventWrite):
        ts._out(Common.messageToTuple(message))
    elif (message[Common.MessageEvent] == Common.EventTake):
        # ignore return value
        ts._inp(Common.messageToTuple(message))

def handleEventMain(notification, notificationList, messageList, ts, logFilename, isUnique):

    message = Common.deserializeNotification(notification)

    entity = message[Common.MessageEntity]
    event = message[Common.MessageEvent]

    if (event == Common.EventStart):
        # Common.logNotificationToFile(logFilename, notification, notificationList, isUnique)

        ets = Common.getTsFromNaming(entity, Common.TagAdapter, ts)
        eri = replayHandlingInfo()

        Common.replayEvents(entity, ets, messageList, eri[0], eri[1])
    elif ((event == Common.EventWrite) or (event == Common.EventTake)):
        Common.logNotificationToFile(logFilename, notification, notificationList, isUnique)
    else:
        return

    notificationList.append(notification)
    messageList.append(message)

def main(address, port):

    try:
        preInit()
    except Exception as e:
        logging.error(f'preInit failure {e}')

    try:
        logFilename = f'{Common.Recovery}{Common.LogExtension}'

        namingTs = Common.getTsFromConfig(Common.EntityNaming, Common.TagAdapter)

        isUnique = True
        lists = Common.processNotificationFromFile(logFilename, isUnique)
        notificationList = lists[Common.NotifyNList]
        messageList = lists[Common.NotifyMList]
        
        eri = replayHandlingInfo()
        entityList = Common.getEntityTsList(namingTs)
        Common.replayEventsAll(namingTs, entityList, messageList, eri[0], eri[1])
    except Exception as e:
        logging.error(f'replayEventsAll failure {e}')

    # See <https://pymotw.com/3/socket/multicast.html> for details

    server_address = ('', int(port))

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(server_address)

    group = socket.inet_aton(address)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

    print(f"Listening on udp://{address}:{port}")

    try:
        while True:
            data, _ = sock.recvfrom(MAX_UDP_PAYLOAD)
            notification = data.decode()

            handleEventMain(notification, notificationList, messageList, namingTs, logFilename, isUnique)
    except Exception as e:
        print("Unexpected error:", sys.exc_info()[0])
        print(f'{e}')
        sock.close()

def usage(program):
    print(f'Usage: {program} ADDRESS PORT', file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage(sys.argv[0])

    sys.exit(main(*sys.argv[1:]))