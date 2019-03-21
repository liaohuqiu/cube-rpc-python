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
import logger as cubelog
from cpbox.tool import utils
from cpbox.tool import logger as cplogger

def json_load_conf(conf):
    buffer = ''
    for ln in open(conf):
        ln = ln.strip()
        if ln.startswith('#') or ln.startswith("//") or ln.startswith(';'):
            continue
        else:
            buffer += ln
    return json.loads(buffer)

def make_easy_engine(servant_class):
    if len(sys.argv) == 1:
        print 'Usage: python %s config-file.yml' % sys.argv[0]
        sys.exit(1)

    setting = utils.load_yaml(sys.argv[1])
    debug = setting.get('debug', False)
    log_level = setting.get('log_level', 'info')
    syslog_ng_server = os.environ.get('PUPPY_SYSLOG_NG_SERVER', None)
    if debug:
        log_level = 'debug'
        cubelog.enable_debug_log()
    cplogger.make_logger('cube-rpc', log_level, syslog_ng_server, True)

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
