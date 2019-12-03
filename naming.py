#!/usr/bin/env python3

# clear; python naming.py 224.0.0.1 54323

import sys
import struct
import socket
import logging

import proxy
import config

from common import Common

# per <https://en.wikipedia.org/wiki/User_Datagram_Protocol>
MAX_UDP_PAYLOAD = 65507

def preInit():

    configInfo = Common.getTsAdapterInfoFromConfig(Common.EntityNaming)
    ts = proxy.TupleSpaceAdapter(configInfo[2])
    if (Common.isValidTs(ts)):
        try:
            td = [configInfo[0], Common.EventStart, configInfo[1]]
            ts._out(td)

            td = [configInfo[0], Common.EventAdapter, configInfo[2]]
            ts._out(td)
        except:
            logging.error(f'preinit failure')

def replayHandlingInfo():
    return [[Common.EventStart, Common.EventAdapter], lambda msg, ts: handleEventForEachMessage(msg, ts)]

def handleEventForEachMessage(message, ts):

    if ((message[Common.MessageEvent] == Common.EventStart) or (message[Common.MessageEvent] == Common.EventAdapter)):
        ts._out(Common.messageToTuple(message))
        Common.updateServerList(ts, message[Common.MessageEntity])

def handleEventMain(notification, notificationList, messageList, ts, logFilename, isUnique):

    message = Common.deserializeNotification(notification)

    entity = message[Common.MessageEntity]
    event = message[Common.MessageEvent]
    
    if ((event == Common.EventStart) or (event == Common.EventAdapter)):
        Common.logNotificationToFile(logFilename, notification, notificationList, isUnique)
        tupleData = [entity, event, message[Common.MessageData]]
        try:
            ts._out(tupleData)
        except Exception as e:
            logging.error(f'_out Error {e}') 

        Common.updateServerList(ts, entity)
    
    notificationList.append(notification)
    messageList.append(message)

def main(address, port):

    try:
        preInit()
    except Exception as e:
        logging.error(f'preInit failure {e}')

    try:
        logFilename = f'{Common.EntityNaming}{Common.LogExtension}'

        namingTs = Common.getTsFromConfig(Common.EntityNaming, Common.TagAdapter)

        isUnique = True
        lists = Common.processNotificationFromFile(logFilename, isUnique)
        notificationList = lists[Common.NotifyNList]
        messageList = lists[Common.NotifyMList]
        
        eri = replayHandlingInfo()
        entityList = [[Common.EntityNaming, namingTs]]
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
    except:
        print("Unexpected error:", sys.exc_info()[0])
        sock.close()

def usage(program):
    print(f'Usage: {program} ADDRESS PORT', file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage(sys.argv[0])

    sys.exit(main(*sys.argv[1:]))