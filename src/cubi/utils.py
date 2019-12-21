import os
import sys

from cpbox.tool import logger as cplogger
from cpbox.tool import utils

import engine
import params
import logger as cubelog
import proxy


class AppWrap(object):

    def __init__(self, app_name, env, log_level):
        self.app_name = app_name
        self.env = env
        self.log_level = log_level
        self.app_logs_dir = './logs'


def make_easy_engine(servant_class, setting=None):
    if len(sys.argv) == 1 and setting is None:
        print 'Usage: python %s config-file.yml' % sys.argv[0]
        sys.exit(1)

    setting = setting if setting is not None else utils.load_yaml(sys.argv[1])
    print(setting)
    env = setting.get('env', 'dev')
    debug = setting.get('debug', False)
    log_level = setting.get('log_level', 'info')
    if debug:
        log_level = 'debug'
    app = AppWrap('cube-rpc', env, log_level)
    cplogger.make_logger_for_app(app)

    # endpoint
    endpoint = setting.get('endpoint', None)
    if not endpoint:
        raise params.EngineError('not endpoint in config')

    service, host, port = proxy.parse_endpoint(endpoint)
    if not service:
        raise engine.EngineError('You must specify the service name.')

    _engine = engine.Engine(setting)

    adapter = engine.Adapter(service, endpoint)
    _engine.add_adpater(adapter)

    servant = servant_class(_engine)

    adapter.add_servant(service, servant)

    return _engine
