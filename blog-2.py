#!/usr/bin/env python3

# clear; python blog-2.py -s alice -a post -p bob -t "mytopic" -m "mymessage"

import uuid
import argparse

import proxy
import config

from common import Common


def commandLine():

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--server', type=str, default='alice')
    parser.add_argument('-a', '--action', type=str, default='read')
    parser.add_argument('-p', '--poster', type=str, default='alice')
    parser.add_argument('-t', '--topic', type=str, default='gtcn')
    parser.add_argument('-m', '--message', type=str, default='emptymessage')

    return parser.parse_args()

def readBlog(server, poster, args, ts):

    ets = Common.getTsFromNaming(server, Common.TagAdapter, ts)
    if (ets is not None):

        td = [poster, args.topic, None]
        dataList = Common.getSortedUnique(ets, td)
        for data in dataList:
            print(f'read blog: {data}')

    # if (ets is not None):

# en = Common.EntityNaming
en = Common.EntityTuplemanager
args = commandLine()
# print(f'a {args.action}, p {args.poster}, t {args.topic}, m {args.message}')
# ts = Common.getTsFromConfig(en, Common.TagAdapter)

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

adapter_host = "localhost"
adapter_port = 8006
servers_adapter_uri = f'http://{adapter_host}:{adapter_port}'
servers_ts = proxy.TupleSpaceAdapter(servers_adapter_uri)
td = servers_ts._rdp(["leader", "leader", None])
server = servers[td[2]]
ts = proxy.TupleSpaceAdapter(server["ts"])

if (args.action == 'read'):
    
    poster = None if (args.poster == 'all') else args.poster   
    readBlog(args.server, poster, args, ts)
    
elif (args.action == 'post'):

    td = [args.poster, args.topic, args.message]
    # Common.playEventsAll(ts, [td], lambda itd, name, ets: ets._out(itd))
    ets = Common.getTsFromNaming(args.poster, Common.TagAdapter, ts)
    ets._out(td)
    print(f'post blog: {td}')
# if (args.action == 'read'):
