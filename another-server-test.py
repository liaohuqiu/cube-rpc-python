import time
from gevent.pool import Pool
import gevent.monkey
gevent.monkey.patch_all()

import cubi.proxy as proxy
import cubi.logger as logger

def basic_test(endpoint):

    prx = proxy.Proxy(endpoint)

    data = {'time': time.time()}
    r = prx.request('hello', data)
    assert r['time'] - time.time() < 1

    r = prx.request('time', {})
    assert r['time'] - time.time() < 1

    r = prx.request('check', {'i' : 1, 's' : 's', 'l' : [1,2,3]})
    assert r['i'] == 1
    assert r['s'] == 's'
    assert r['l'] == [1,2,3]

    r = prx.request('named_args', {'name' : 'creese', 'age' : 99})
    assert r['yourname'] == 'creese'
    assert r['yourage'] == 99

    r = prx.request('echo', {'a' : 1234})
    assert r['a'] == 1234

    r = prx.request('hello_all', {'msgs' : [{'a': 1234, }, {'b': 1234, }, {'c': 1234, }]})
    print r

def stress_test(endp):
    pool = Pool(128)
    for _ in range(1024):
        pool.spawn(basic_test, endp)

def start_test(endp):
    print 'start test for ', endp
    basic_test(endp)
    print 'basic test ok'
    stress_test(endp)
    print 'stress test ok'

if __name__ == '__main__':
    endp = "another-server@tcp::2015"
    print 'start test for ', endp
    basic_test(endp)
    # start_test(endp)
    # print 'basic test ok'