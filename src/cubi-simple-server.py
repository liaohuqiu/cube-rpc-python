#! /bin/env python

import cubi.params as params
import cubi.utils as utils
from cubi.engine import Servant


class SimpleServant(Servant):

    @params.extract_args
    def echo(self, msg):
        return {'msg': msg}

    # return what client send to server
    def hello(self, params):
        return dict(params)


if __name__ == '__main__':
    endp = 'simple-server@0.0.0.0:2018'
    setting = {}
    setting['debug'] = True
    setting['endpoint'] = endp
    utils.make_easy_engine(SimpleServant, setting).serve_forever()
