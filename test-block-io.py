#! /bin/env python
import time

import gevent.monkey
gevent.monkey.patch_all(thread=False)
import cubi.proxy as proxy
import cubi.logger as logger

import threading

def test():
    endp = 'placeholderServer@tcp:10.97.240.139:16512'
    print 'start test for ', endp
    prx = proxy.Proxy(endp, True)

    data = {}
    while (True):
        r = prx.request_blocking('r', data)

if __name__ == '__main__':

    # logger.enable_debug_log()

    ts = []
    for i in range(1, 3):
        print(i);
        t = threading.Thread(target=test, args = ())
        t.start()
        ts.append(t)

    for t in ts:
        t.join()

