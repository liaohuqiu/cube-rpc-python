#! /bin/env python
import time

import gevent.monkey
gevent.monkey.patch_all()
import cubi.proxy as proxy
import cubi.logger as logger

if __name__ == '__main__':

    # logger.enable_debug_log()

    endp = "simple-server@tcp::2014"
    print 'start test for ', endp
    prx = proxy.Proxy(endp, True)

    data = {'time': time.time()}
    r = prx.request('hello', data)
    logger.get_logger().debug('result: %s', r)
