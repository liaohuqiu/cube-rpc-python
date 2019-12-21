#! /bin/env python

import time

import cubi.logger as logger
import cubi.params as params
import cubi.utils as utils
from cubi.engine import Servant


class AnotherServant(Servant):

    def __init__(self, engine):
        Servant.__init__(self, engine)
        self._simple_server_proxy = engine.create_proxy('simple-server@127.0.0.1:2018')

    def hello(self, params):
        return self._simple_server_proxy.request('hello', dict(params))

    def check(self, params):
        i = params.want_integer('i')
        s = params.want_str('s')
        l = params.get_list('l')
        return params

    def echo(self, params):
        return params

    def time(self, params):
        result = {}
        result['time'] = time.time()
        return result

    def error(self, params):
        raise Exception(str(params))

    @params.extract_args
    def hello_all(self, msgs):
        reqs = [['hello', msg] for msg in msgs]
        result = []
        for r, req in self._simple_server_proxy.request_many(reqs):
            result.append((r, req))
        return {'r': result}

    @params.assert_integer('age')
    @params.extract_args
    def named_args(self, name, age, gender='male'):
        return {'yourname': name, 'yourage': age, 'yourgender': gender}

    def debug(self, params):
        import pdb;
        pdb.set_trace()
        return params


if __name__ == '__main__':
    endp = 'another-server@0.0.0.0:2019'
    setting = {}
    setting['debug'] = True
    setting['endpoint'] = endp
    utils.make_easy_engine(AnotherServant, setting).serve_forever()
