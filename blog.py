#!/usr/bin/env python3

# clear; python blog.py -s alice -a post -p bob -t "mytopic" -m "mymessage"

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
        try:
            dataList = Common.getSortedUnique(ets, td)
            for data in dataList:
                print(f'read blog: {data}')
        except:
            print('read error')

    # if (ets is not None):

en = Common.EntityNaming
# en = Common.EntityTuplemanager
args = commandLine()
# print(f'a {args.action}, p {args.poster}, t {args.topic}, m {args.message}')
ts = Common.getTsFromConfig(en, Common.TagAdapter)

if (args.action == 'read'):
    
    poster = None if (args.poster == 'all') else args.poster   
    readBlog(args.server, poster, args, ts)
    
elif (args.action == 'post'):

    td = [args.poster, args.topic, args.message]
    Common.playEventsAll(ts, [td], lambda itd, name, ets: ets._out(itd))
    print(f'post blog: {td}')
# if (args.action == 'read'):
