import os
import json
import sys
import logging
import struct
import string
import traceback
import time
import socket
import json

import engine
import proxy
import params
import logger

def json_load_conf(conf):
    buffer = ''
    for ln in open(conf):
        ln = ln.strip()
        if ln.startswith('#') or ln.startswith("//") or ln.startswith(';'):
            continue
        else:
            buffer += ln
    return json.loads(buffer)

def make_easy_engine(servant_class, conf = None):
    if not conf:
        if len(sys.argv) == 1:
            print "Usage:", sys.argv[0], "conf"
            sys.exit(1)
        conf = sys.argv[1]

    # config
    if type(conf) == dict:
        setting = conf
    else:
        setting = json_load_conf(conf)

    # debug
    if 'debug' in setting and setting['debug']:
        logger.enable_debug_log()

    # console_log_level
    if 'console_log_level' in setting:
        console_log_level = setting['console_log_level'].lower()
        log_level_conf = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'warn': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL,
        }
        if console_log_level in log_level_conf:
            console_log_level = log_level_conf[console_log_level]
        else:
            console_log_level = logging.WARNING
        logger.set_logger(logger.get_console_logger(console_log_level))

    # endpoint
    endpoint = setting.get('endpoint', None)
    if not endpoint:
        raise engine.EngineError('not endpoint in config')

    service, proto, host, port = proxy.parse_endpoint(endpoint)
    if not service:
        raise engine.EngineError('You must specify the service name.')

    _engine = engine.Engine(setting)

    adapter = engine.Adapter(service, setting)
    _engine.add_adpater(adapter);

    servant = servant_class(setting)
    servant.init(_engine, adapter, setting)

    adapter.add_servant(service, servant)

    return _engine
