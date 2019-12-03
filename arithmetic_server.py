#!/usr/bin/env python3

# clear; python arithmetic_server.py -c bob.yaml

import re

import proxy
import config

config = config.read_config()

ts_name      = config['name']
adapter_host = config['adapter']['host']
adapter_port = config['adapter']['port']
adapter_uri = f'http://{adapter_host}:{adapter_port}'

ts = proxy.TupleSpaceAdapter(adapter_uri)

while True:
    ops, a, b = ts._in([re.compile(r'^[-+/*]$'), int, int])

    if ops == '-':
        result = a - b
    elif ops == '+':
        result = a + b
    elif ops == '/':
        result = a // b
    elif ops == '*':
        result = a * b

    print('server calculated - outputting the result')
    ts._out(['result', result])

