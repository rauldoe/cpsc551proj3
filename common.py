import logging
import uuid

import config
import proxy

class Common:
    MessageEntity = 'entity'
    MessageEvent = 'event'
    MessageData = 'data'

    EventStart = 'start'
    EventWrite = 'write'
    EventTake = 'take'
    EventRead = 'read'
    EventAdapter = 'adapter'

    ServerMessage = 'message'
    ServerInstance = 'instance'
    ServerName = 'name'

    NotifyNList = 'notificationlist'
    NotifyMList = 'messagelist'

    ServerList = 'server_list'
    TagAdapter = 'adapter'
    TagUri = 'uri'
    TagName = 'name'

    EntityNaming = 'naming'
    EntityTuplemanager = 'tuplemanager'

    Recovery = 'recovery'

    LogExtension = '.out.txt'

    @staticmethod
    def splitNotification(data):
    
        sp = []
        idx0 = data.index(' ')
        sp.append(data[0:idx0])
        idx1 = data.index(' ', idx0+1)
        sp.append(data[idx0+1:idx1])
        sp.append(data[idx1+1:])

        return sp

    @staticmethod
    def deserializeNotification(data):

        dList = Common.splitNotification(data)

        # print(f'data: {data} len: {len(dList)}')
        event = dList[1]
        data = dList[2] if (event == Common.EventStart) or (event == Common.EventAdapter) else eval(dList[2])

        return {Common.MessageEntity : dList[0], Common.MessageEvent : event,  Common.MessageData : data }

    @staticmethod
    def logNotificationToFile(filename, data, notificationList, isUnique):

        if not (isUnique and (data in notificationList)):
            with open(filename, 'a+') as f:
                f.write(f'{data}\n')

    @staticmethod
    def logNotificationListToFile(filename, notificationList):
        with open(filename, 'w+') as f:
            f.writelines([f'{i}\n' for i in notificationList])

    @staticmethod
    def loadNotificationFromFile(filename, isUnique):

        notificationList = []
        messageList = []

        open(filename, 'a+').close()
        with open(filename, 'r') as f: 
            notificationList = list(filter(lambda i: i != '', [line.rstrip() for line in f]))

        if isUnique:
            notificationList = list(set(notificationList))

        messageList = list(map(lambda i: Common.deserializeNotification(i), notificationList))

        return { Common.NotifyNList : notificationList, Common.NotifyMList : messageList }

    @staticmethod 
    def processNotificationFromFile(filename, isUnique):

        lists = Common.loadNotificationFromFile(filename, isUnique)
        if isUnique:
            Common.logNotificationListToFile(filename, lists[Common.NotifyNList])
        
        return lists

    @staticmethod
    def getServerList(ts):
        return Common.processServerList(ts, lambda  its: its._rdp([Common.ServerList, None]))

    @staticmethod
    def popServerList(ts):
        return Common.processServerList(ts, lambda  its: its._inp([Common.ServerList, None]), True)
    
    @staticmethod
    def popServerListAll(ts):
        
        data = Common.popServerList(ts)
        serverList = data

        while (data is not None):
            data = Common.popServerList(ts)

        return serverList

    @staticmethod
    def processServerList(ts, procFunc, doReturnNull = False):

        serverList = []
        td = None

        try:
            td = procFunc(ts)
            # td = ts._inp([Common.ServerList, None])
        except:
            logging.error("Error in processServerList")

        if ((td is None) and doReturnNull):
            serverList = None
        else:
            serverList = td[1]
        
        return serverList

    @staticmethod
    def updateServerList(ts, entity):
        
        serverList = Common.popServerListAll(ts)
        serverList = [] if (serverList is None) else serverList

        if (entity not in serverList):

            if (len(serverList) <= 0):
                serverList = [entity]
            else:
                s = set(serverList)
                s.add(entity)
                serverList = list(s)
       
        # if (entity not in serverList):

        td = [Common.ServerList, serverList]
        
        try:
            ts._out(td)
        except:
            logging.error("Error in _out for updateServerList")     

    @staticmethod
    def getTsAdapterInfoFromConfig(entity):


        configFilename = f'{entity}.yaml'
        configObj = config.read_config_filename(configFilename)
        host = configObj[Common.TagAdapter]['host']
        port = configObj[Common.TagAdapter]['port']

        name = configObj[Common.TagName]
        tsUri = configObj[Common.TagUri]
        adapterUri = f'http://{host}:{port}'

        return (name, tsUri, adapterUri)

    @staticmethod
    def getTsFromConfig(entity, serverType):

        info = Common.getTsAdapterInfoFromConfig(entity)
        ts = proxy.TupleSpaceAdapter(info[2])

        return ts

    @staticmethod
    def getTsFromNaming(entity, serverType, namingTs):
        
        ts = None

        try:
            td = namingTs._rdp([entity, serverType, None])
            if (td is not None):
                uri = td[2]
                ts = proxy.TupleSpaceAdapter(uri)
        except:
            logging.error("Error in _rdp for getTsFromNaming")

        return ts

    @staticmethod
    def isValidTs(ts):

        isValid = False

        if (ts is None):
            return isValid

        try:
            id = str(uuid.uuid4())
            td = ts._rdp([id])

            if (td is None):
                ts._out([id])
                td = ts._inp([id])

            isValid = (td is not None)
        except Exception as e:
            logging.error(f'isValidTs failure {e}')
            isValid = False

        return isValid

    @staticmethod
    def getEntityTsList(ts):

        entityList = []
        serverList = Common.getServerList(ts)

        for server in serverList:
            ets = Common.getTsFromNaming(server, Common.TagAdapter, ts)
            if Common.isValidTs(ets):
                entityList.append([server, ets])
        
        return entityList

    @staticmethod
    def messageToTuple(message):

        evtList = [Common.EventWrite, Common.EventTake]

        if (message[Common.MessageEvent] in evtList):
            return message[Common.MessageData]
        else:
            return [message[Common.MessageEntity], message[Common.MessageEvent], message[Common.MessageData]]

    @staticmethod
    def replayEvents(entity, entityTs, messageList, eventList, handleEventFunc, ignoreEntity):

        if ignoreEntity:
            replayList = list(filter(lambda i: (i[Common.MessageEvent] in eventList), messageList))
        else:
            replayList = list(filter(lambda i: ((i['entity'] == entity) and (i[Common.MessageEvent] in eventList)), messageList))

        for replay in replayList:
            try:
                handleEventFunc(replay, entityTs)
            except Exception as e:
                logging.error(f'Replay Error {e}')            

    @staticmethod
    def replayEventsAll(ts, entityList, messageList, eventList, handleEventFunc, ignoreEntity):

        try:
            for i in range(len(entityList)):
                entity = entityList[i][0]
                entityTs = entityList[i][1]
                Common.replayEvents(entity, entityTs, messageList, eventList, handleEventFunc, ignoreEntity)

        except:
            logging.error("Error in replayEventsAll")
    
    @staticmethod
    def playEventsAll(ts, tdList, handleEventFunc):

        entityList = Common.getEntityTsList(ts)
        for entityObj in entityList:
            for td in tdList:
                try:
                    handleEventFunc(td, entityObj[0], entityObj[1])
                except Exception as e:
                    logging.error(f'playEventsAll, {entityObj[0]} {td} {e}')

    @staticmethod
    def getSortedUnique(ts, td):
        s = ts._rd_all(td)
        uniqueList = [list(i) for i in set(tuple(j) for j in s)]
        uniqueList.sort()
        return uniqueList