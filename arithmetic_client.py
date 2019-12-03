#!/usr/bin/env python3

# clear; python arithmetic_client.py -c bob.yaml

import proxy
import config

config = config.read_config()

ts_name      = config['name']
adapter_host = config['adapter']['host']
adapter_port = config['adapter']['port']

adapter_uri = f'http://{adapter_host}:{adapter_port}'

ts = proxy.TupleSpaceAdapter(adapter_uri)

tuples = [["*", 2, 2 ], [ "+", 2, 5 ], [ "-", 9, 3 ]]

for t in tuples:
    ts._out(t)
    res = ts._in(["result", None])
    print(f"{res[1]} = {t[1]} {t[0]} {t[2]}")
