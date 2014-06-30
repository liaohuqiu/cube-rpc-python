import sys
import cubi.engine as engine
import cubi.logger as logger
from cubi.engine import Servant;

class SimpleServant(Servant):

    def hello(self, params):
        return dict(params)

if __name__ == '__main__':

    logger.enable_debug_log()

    endp = "@tcp::2014"
    setting = {}
    setting['debug'] = True
    setting['endpoints'] = (endp, )
    engine.make_easy_engine('simple-server', SimpleServant, setting).serve_forever()
