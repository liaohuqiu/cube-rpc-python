#! /bin/env python
import time

import gevent.monkey
gevent.monkey.patch_all(thread=False)
import cubi.proxy as proxy
import cubi.logger as logger

if __name__ == '__main__':

    logger.enable_debug_log()

    endp = 'placeholderServer@tcp::16512'
    print 'start test for ', endp
    prx = proxy.Proxy(endp, True)

    data = {'time': "xxx"}
    r = prx.request_blocking('r', data)
    print(r)

    prx.start();
    r = prx.request('r', data)
    print(r)
