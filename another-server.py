import sys
import time
import cubi.engine as engine
import cubi.logger as logger
import cubi.params as params
from cubi.engine import Servant;

class AnotherServant(Servant):

    def _init(self, engine, adapter, setting):
        self._simple_server = engine.create_proxy('simple-server@tcp::2014')

    def hello(self, params):
        return self._simple_server.request('hello', dict(params))

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
        for r, req in self._simple_server.request_many(reqs):
            result.append((r, req))
        return {'r' : result}

    @params.assert_integer('age')
    @params.extract_args
    def named_args(self, name, age, gender = 'male'):
        return {'yourname' : name, 'yourage' : age, 'yourgender' : gender}

    def debug(self, params):
        import pdb; pdb.set_trace()
        return params

if __name__ == '__main__':

    logger.enable_debug_log()

    endp = "another-server@tcp::2015"
    setting = {}
    setting['debug'] = True
    setting['endpoint'] = endp
    engine.make_easy_engine('another-server', AnotherServant, setting).serve_forever()
