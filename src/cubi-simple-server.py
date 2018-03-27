#! /bin/env python
import cubi.utils as utils
from cubi.engine import Servant;

class SimpleServant(Servant):

    def init(self, engine, adapter, setting):
        pass

    # return what client send to server
    def hello(self, params):
        return dict(params)

if __name__ == '__main__':

    utils.make_easy_engine(SimpleServant).serve_forever()
