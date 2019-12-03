#!/usr/bin/env python3

# clear; python tuplemanager.py 224.0.0.1 54324

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

    configInfo = Common.getTsAdapterInfoFromConfig(Common.EntityTuplemanager)
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
    return [[Common.EventWrite, Common.EventTake, Common.EventStart, Common.EventAdapter], lambda msg, ts: handleEventForEachMessage(msg, ts)]

def handleEventForEachMessage(message, ts):

    if (message[Common.MessageEvent] == Common.EventWrite):
        ts._out(Common.messageToTuple(message))
    elif (message[Common.MessageEvent] == Common.EventTake):
        # ignore return value
        ts._inp(Common.messageToTuple(message))
    elif ((message[Common.MessageEvent] == Common.EventStart) or (message[Common.MessageEvent] == Common.EventAdapter)):
        ts._out(Common.messageToTuple(message))
        Common.updateServerList(ts, message[Common.MessageEntity])

def handleEventMain(notification, ts, procList):

    # procList = [[logFilename1, isUnique1, entityList1, None, None, ignoreEntity1, entityListFunc1], [logFilename2, isUnique2, entityList2, None, None, ignoreEntity2, entityListFunc2]]
    # procList[i][3] = notificationList
    # procList[i][4] = messageList
    message = Common.deserializeNotification(notification)

    entity = message[Common.MessageEntity]
    event = message[Common.MessageEvent]
    td = [entity, event, message[Common.MessageData]]

    if ((event == Common.EventStart) or (event == Common.EventAdapter)):
        if (event == Common.EventStart):
 
            # recovery functionality
            eri = replayHandlingInfo()
            etsList = Common.getEntityTsList(ts)
            for etsi in etsList:
                Common.replayEvents(entity, etsi[1], procList[1][4], eri[0], eri[1], procList[1][5])

            procList[1][3].append(notification)
            procList[1][4].append(message)

        # naming functionality
        Common.logNotificationToFile(procList[0][0], notification, procList[0][3], procList[0][1])

        try:
            ts._out(td)
        except Exception as e:
            logging.error(f'_out Error {e}') 

        Common.updateServerList(ts, entity)        

        procList[0][3].append(notification)
        procList[0][4].append(message)

    elif ((event == Common.EventWrite) or (event == Common.EventTake)):

        # recovery functionality
        # print('recovery functionality for write, take')
        if (message[Common.MessageData] not in [i[Common.MessageData] for i in procList[1][4]]):

            Common.playEventsAll(ts, [message[Common.MessageData]], lambda itd, name, ets: ets._out(itd))
            Common.logNotificationToFile(procList[1][0], notification, procList[1][3], procList[1][1])

            procList[1][3].append(notification)
            procList[1][4].append(message)
    
    else:
        return

def main(address, port):

    try:
        preInit()
    except Exception as e:
        logging.error(f'preInit failure {e}')

    try:

        try:
            namingTs = Common.getTsFromConfig(Common.EntityTuplemanager, Common.TagAdapter)
        except:
            logging.error('naming init error')
            raise Exception('naming init error')

        eri = replayHandlingInfo()

        try:
            logFilename1 = f'{Common.EntityTuplemanager}_{Common.EntityNaming}{Common.LogExtension}'
            isUnique1 = True
            ignoreEntity1 = True
            entityListFunc1 = lambda : [[Common.EntityTuplemanager, namingTs]]
        except Exception as nse:
            logging.error(f'naming set error {nse}')
            raise Exception(f'naming set error {nse}')
        
        try:
            logFilename2 = f'{Common.EntityTuplemanager}_{Common.Recovery}{Common.LogExtension}'
            isUnique2 = False
            ignoreEntity2 = False
            entityListFunc2 = lambda : Common.getEntityTsList(namingTs)
        except Exception as re:
            logging.error(f'recovery error {re}')
            raise Exception(f'recovery error {re}')

        procList = [[logFilename1, isUnique1, None, None, None, ignoreEntity1, entityListFunc1], [logFilename2, isUnique2, None, None, None, ignoreEntity2, entityListFunc2]]

        for i in range(len(procList)):

            logFilename = procList[i][0]
            isUnique = procList[i][1]
            ignoreEntity = procList[i][5]
            entityList = procList[i][6]()

            try:
                lists = Common.processNotificationFromFile(logFilename, isUnique)
                notificationList = lists[Common.NotifyNList]
                messageList = lists[Common.NotifyMList]

                procList[i][3] = notificationList
                procList[i][4] = messageList
                
                Common.replayEventsAll(namingTs, entityList, messageList, eri[0], eri[1], ignoreEntity)
            except Exception as ple:
                logging.error(f'procList[{i}] {ple}')
    
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

            handleEventMain(notification, namingTs, procList)
    except Exception as e:
        print("Unexpected error:", sys.exc_info()[0])
        sock.close()

def usage(program):
    print(f'Usage: {program} ADDRESS PORT', file=sys.stderr)
    sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        usage(sys.argv[0])

    sys.exit(main(*sys.argv[1:]))