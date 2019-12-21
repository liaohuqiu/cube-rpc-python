#! /bin/env python

import time
from threading import Thread
from gevent.pool import Pool
import gevent.monkey
gevent.monkey.patch_all()

import cubi.proxy as proxy
import cubi.logger as logger

request_time = 15
concurrent_num = 1024
def basic_test(endpoint, i):

    prx = proxy.Proxy(endpoint)
    for _ in range(request_time):
        try:
            data = {'msg': time.time()}
            r = prx.request('echo', data)
        except Exception:
            import traceback
            print traceback.format_exc()

def stress_test(endp):

    if True:
        pool = Pool(128)
        for i in range(concurrent_num):
            pool.spawn(basic_test, endp, i)
    else:
        threads = []
        for i in range(concurrent_num):
            t = Thread(target=basic_test, args=(endp, i))
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

def start_test(endp):
    print 'start test for', endp
    basic_test(endp, 0)
    print 'basic test ok'
    t1 = time.time();
    stress_test(endp)
    print concurrent_num * request_time / (time.time() - t1)
    print 'stress test ok'

if __name__ == '__main__':
    # logger.enable_debug_log()
    endp = "echo@tcp::2014"
    # basic_test(endp, 1)
    start_test(endp)
