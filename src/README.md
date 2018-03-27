# Install

* Install from pip

```sh
pip install cubi
```

* Install from source

Clone this project or download the source code, then

```sh
python setup.py install
```

# Implement a service

* Code for service: 

    Here is a simple service, this service just return what client send to server.

    [`cubi-simple-server.py`](https://github.com/liaohuqiu/cube-rpc-python/blob/master/cubi-simple-server.py)


    ```python
    import cubi.utils as utils
    from cubi.engine import Servant;

    class SimpleServant(Servant):

        def init(self, engine, adapter, setting):
            pass

        # return what client send to server
        def hello(self, params):
            return dict(params)

    if __name__ == '__main__':
        utils.make_easy_engine(SimpleServant).serve_forever()
    ```

    Then run it: 
    
    ```
    python cubi-simple-server.py cubi-simple-server.conf
    ```

* Code for client:

    [`cubi-simple-server-test.py`](https://github.com/liaohuqiu/cube-rpc-python/blob/master/cubi-simple-server-test.py)

    ```
    import time

    import cubi.proxy as proxy
    import cubi.logger as logger

    import gevent.monkey
    gevent.monkey.patch_all()

    if __name__ == '__main__':

        endp = "simple-server@tcp::2014"
        print 'start test for ', endp
        prx = proxy.Proxy(endp, True)

        data = {'time': time.time()}
        r = prx.request('hello', data)
        print 'result: %s' % r
    ```

    Run it: `python cubi-simple-server-test.py`

### Config file

An example:

```
{
    "endpoint": "simple-server@tcp:0.0.0.0:2014",
    "servant_num": 512,
    "accept_pool_size": 512,
    "debug": false,
    "console_log_level": "debug",
    "client_ips": ["127.0.0.1"],
    "app":  {
    }
}
```

* endpoint

    Format: `service_name@protocal:ip:port`
    Example: `simple-server@tcp:0.0.0.0:2014`

* servant_num

    The default value is 512.

* accept_pool_size

    The default value is 512.

* debug

    If is set and value is `True`, will call `logger.enable_debug_log()` to enable debug log.

    And the `debug` field in `Adapter`, `Engine`, `Proxy`, `Servant` will set to `True`.

* console_log_level

    If has this field, will enable console logger with specified log_level

    ```
    debug
    info
    warning   // default
    error
    critical
    ```

* client_ips

    If is set and not empty, only the ip address in this list can access the service.

* app

    The config for application.

### License

MIT License
