import sys
import logging

import cubi.engine as engine
import cubi.logger as logger
from cubi.engine import Servant;

class SimpleServant(Servant):

    def _init(self, engine, adapter):
        pass

    def hello(self, params):
        return dict(params)

if __name__ == '__main__':

    # product logger level
    # log = logger.get_console_logger(logging.DEBUG)
    # logger.set_logger(log)

    # deubg logger level
    logger.enable_debug_log()

    endp = "@tcp::2014"
    setting = {}
    setting['debug'] = True
    setting['endpoint'] = endp
    engine.make_easy_engine('simple-server', SimpleServant, setting).serve_forever()
