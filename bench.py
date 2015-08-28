#! /bin/env python

import time
from threading import Thread
from gevent.pool import Pool
import gevent.monkey
gevent.monkey.patch_all()

import cubi.proxy as proxy
import cubi.logger as logger

request_time = 1000
concurrent_num = 256
def basic_test(endpoint, i):

    prx = proxy.Proxy(endpoint)
    data = {'time': time.time()}
    for _ in range(request_time):
        try:
            r = prx.request('hello', data)
        except Exception:
            import traceback
            print traceback.format_exc()
    print i

def stress_test(endp):

    threads = []
    for i in range(concurrent_num):
        t = Thread(target=basic_test, args=(endp, i))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

def start_test(endp):
    print 'start test for ', endp
    basic_test(endp, 0)
    print 'basic test ok'
    t1 = time.time();
    stress_test(endp)
    print concurrent_num * request_time / (time.time() - t1)
    print 'stress test ok'

if __name__ == '__main__':
    # logger.enable_debug_log()
    endp = "simple-server@tcp::2014"
    start_test(endp)
