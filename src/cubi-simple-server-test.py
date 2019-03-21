#! /bin/env python
import time

import cubi.proxy as proxy
import cubi.logger as logger

import gevent.monkey
gevent.monkey.patch_all()

if __name__ == '__main__':

    logger.enable_debug_log()

    endp = "simple-server@tcp::2014"
    print 'start test for ', endp
    prx = proxy.Proxy(endp, True)

    data = {'time': time.time()}
    r = prx.request('hello', data)
    logger.get_logger().debug('result: %s', r)
    print 'result: %s' % r

    data = {'msg': time.time()}
    r = prx.request('echo', data)
    logger.get_logger().debug('result: %s', r)
    print 'result: %s' % r
