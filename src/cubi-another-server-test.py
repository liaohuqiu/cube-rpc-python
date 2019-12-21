#! /bin/env python

import time
import gevent.monkey
from gevent.pool import Pool

gevent.monkey.patch_all()

import cubi.proxy as proxy


def basic_test(endpoint):
    prx = proxy.Proxy(endpoint)

    data = {'time': time.time()}
    r = prx.request('hello', data)
    assert r['time'] - time.time() < 1

    r = prx.request('time', {})
    assert r['time'] - time.time() < 1

    r = prx.request('check', {'i': 1, 's': 's', 'l': [1, 2, 3]})
    assert r['i'] == 1
    assert r['s'] == 's'
    assert r['l'] == [1, 2, 3]

    r = prx.request('named_args', {'name': 'creese', 'age': 99})
    assert r['yourname'] == 'creese'
    assert r['yourage'] == 99

    r = prx.request('echo', {'a': 1234})
    assert r['a'] == 1234

    r = prx.request('hello_all', {'msgs': [{'a': 1234, }, {'b': 1234, }, {'c': 1234, }]})
    print r


def stress_test(endp):
    pool = Pool(128)
    for _ in range(100):
        pool.spawn(basic_test, endp)


def start_test(endp):
    print 'start test for ', endp
    basic_test(endp)
    print 'basic test ok'
    stress_test(endp)
    print 'stress test ok'


if __name__ == '__main__':
    endp = "another-server@127.0.0.1:2019"
    start_test(endp)
