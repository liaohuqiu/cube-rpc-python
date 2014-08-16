import struct
import sys
import string
import traceback
import time
import socket
import json
import gevent
from gevent.server import StreamServer
from gevent.pool import Pool
from gevent.queue import Queue, Empty
from gevent.event import AsyncResult
import gevent.monkey
#patch_all() patch_thread() may cause thread exception at the end of app
gevent.monkey.patch_all(thread=False)

import logger
import proxy
import params
from proxy import Query, Answer, Messager
from params import Params

class EngineError(Exception):
    pass

class Adapter(object):

    def __init__(self, name, setting):
        self._name = name

        endpoint = setting.get('endpoint', None)
        if not endpoint:
                raise EngineError('not endpoint in config')

        self.debug = setting.get('debug', False)
        self._endpoint = endpoint
        self._query_queue = Queue()
        self._servants = {}
        self._servers = []
        self._servant_worker_num = setting.get('servant_num', 512)
        self._accept_pool_num = setting.get('accept_pool_size', 512)
        self._running = True
        self._wildcard_servant = None

    def __repr__(self):
        p = {}
        p['endpoint'] = self._endpoint
        p['servants'] = self._servants.keys()
        return str(p)

    def get_name(self):
        return self._name

    # servant is a function with param (service, method, params)
    # special servant handle all service query
    # for somthing like proxy
    def add_wildcard_servant(self, servant):
        if len(self.servant) > 0:
            raise EngineError("normal servant is not empty when add wildcard servant")
        self._wildcard_servant = servant

    def add_servant(self, service, servant):
        if self._wildcard_servant:
            raise EngineError("wildcard servant is set when add normal servant")
        self._servants[service] = servant

    def _make_exception_params(self, query):
        exdict = {}
        exctype, exmsg, tb = sys.exc_info()
        exdict['exception'] = repr(exctype)
        exdict['code'] = 1
        exdict['message'] = repr(exmsg)
        exdict['raiser'] = query.method + "*" + query.service  + self._endpoint
        exdict['detail'] = {}
        exdict['detail']['what'] = repr(traceback.extract_tb(tb))
        return exdict

    def _handle_wildcard_servant(self, query):
        if self.debug and logger.is_debug():
            logger.get_logger().debug('handle_wildcard_servant: %s', query)
        try:
            result = self._wildcard_servant(query.service, query.method, query.params)
            if query.qid:
                query.inbox.put(Answer(query.qid, 0, result))
        except proxy.Error as ex:
            if query.qid:
                query.inbox.put(Answer(ex.qid, ex.status, ex.params))
        except:
            if query.qid:
                query.inbox.put(Answer(query.qid, 1, self._make_exception_params(query)))

    def _handle_normal_servant(self, query):
        if self.debug and logger.is_debug():
            logger.get_logger().debug('handle_normal_servant: %s', query)
        servant = self._servants.get(query.service)
        if not servant:
            #build exception at params
            exdict = {}
            exdict['exception'] = 'ServantNotFound'
            exdict['code'] = 1
            exdict['message'] = "servant %s not found in adapter %s" % (query.service, self._endpoint)
            exdict['raiser'] = self._endpoint
            if query.qid:
                query.inbox.put(Answer(query.qid, 1, exdict))
            else:
                logger.get_logger().warning("%s.%s %s", query.service, query.method, exdict)
            return

        try:
            if query.method[0] == '\0':
                callback = servant._special_callback(query)
            else:
                callback = getattr(servant, query.method)
        except AttributeError as ex:
            logger.get_logger().error("method %s not found", query.method)
            """
            query method not found in servant
            """
            exdict = {}
            exdict['exception'] = 'MethodNotFound'
            exdict['code'] = 1
            exdict['message'] = "servant %s do no have method %s in adapter %s" % (query.service, query.method, self._endpoint)
            exdict['raiser'] = self._endpoint
            if query.qid:
                query.inbox.put(Answer(query.qid, 100, exdict))
            else:
                logger.get_logger().warning("%s.%s %s", query.service, query.method, exdict)
            return

        try:
            result = callback(Params(query.params))
            if query.qid:
                result = dict(result)
                query.inbox.put(Answer(query.qid, 0, result))
        except proxy.Error as ex:
            if query.qid:
                query.inbox.put(Answer(query.qid, ex.status, ex.params))
            else:
                logger.get_logger().warning("%s.%s %d %s", query.service, query.method, ex.status, ex.params)
        except:
            logger.get_logger().error("query %d handle fail", query.qid, exc_info = 1)
            if query.qid:
                query.inbox.put(Answer(query.qid, 1, self._make_exception_params(query)))

    def servant_worker(self):
        while self._running:
            query = self._query_queue.get()
            if not isinstance(query, Query):
                logger.get_logger().error('invalid query %s', query)
                continue
            if not self._wildcard_servant:
                self._handle_normal_servant(query)
            else:
                self._handle_wildcard_servant(query)

    def activate(self):
        for i in range(self._servant_worker_num):
            gevent.spawn(self.servant_worker)

        pool = Pool(self._accept_pool_num)
        endpoint = self._endpoint
        try:
            service, proto, host, port = proxy.parse_endpoint(endpoint)
            if proto != 'tcp':
                raise proxy.Error(1, 'only tcp server supported now')
            server = StreamServer((host, int(port)), self.sokect_handler, spawn=pool)
            if self.debug and logger.is_debug():
                logger.get_logger().debug('adapter start %s', endpoint)
            self._servers.append(server)
            server.start()
        except:
            logger.get_logger().error('start adapter fail %s', endpoint, exc_info = 1)

    def deactivate(self):
        for server in self._servers:
            server.stop()
        self._servers = []
        self._running = False

    def answer_fiber(self, socket, address, inbox):
        for answer in inbox:
            if not isinstance(answer, Answer):
                logger.get_logger().error('invalid answer %s', answer)
                continue

            if self.debug and logger.is_debug():
                logger.get_logger().debug('%s: reply answer: %s', address, answer)
            socket.sendall(answer.get_data())

        if self.debug and logger.is_debug():
            logger.get_logger().debug('%s: answer fiber stop', address)

    def sokect_handler(self, socket, address):
        if self.debug and logger.is_debug():
            logger.get_logger().debug('%s: accept connection', address)

        # send welcome
        socket.sendall(Messager.data_for_welcome())
        conn_inbox = Queue()
        answer_thread = gevent.spawn(self.answer_fiber, socket, address, conn_inbox)
        while self._running:
            try:
                message = Messager.receive_msg(socket)
                if not message:
                    if self.debug and logger.is_debug():
                        logger.get_logger().debug('%s: connection has been closed by client.', address)
                    break;
                if isinstance(message, Answer):
                    logger.get_logger().error('%s: unexpected message received: %s', address, message)
                    continue
                elif isinstance(message, Query):
                    if self.debug and logger.is_debug():
                        logger.get_logger().debug('%s: message received: %s', address, message)
                    message.inbox = conn_inbox
                    self._query_queue.put(message)
            except gevent.socket.error as ex:
                logger.get_logger().error('%s: socket error: %s', address, repr(ex))
                break
            except:
                logger.get_logger().error('%s: exception: %s', address, traceback.format_exc())
                break

        if self.debug and logger.is_debug():
            logger.get_logger().debug('%s: close connection', address)
        socket.close()
        # stop answer thread
        conn_inbox.put(StopIteration)

class Servant(object):

    def __init__(self, setting):
        self.setting = setting
        self.debug = setting.get('debug', False)

    """
    Customized Servant implement this method to initialize
    """
    def _init(self, engine, adapter):
        raise EngineError('You must implement _init(self, engine, adapter')

    def __reflection_service_methods__(self):
        """
        the service methods is the class method whose name does not start with underscore(_)

        """
        methods = []
        for name in dir(self):
            attr = getattr(self,name)
            if name[0] == '_':
                continue
            if callable(attr):
                methods.append(name)
        return methods

    def _special_callback(self, query):
        if query.method == '\0':
            return self._probe
        else:
            raise AttributeError('special method %s not support' % (query.method,))

    def _probe(self, params):
        """
        special probe method for servants internal status
        """
        sta = {}
        sta['methods'] = self.__reflection_service_methods__()
        return sta

class Engine(object):

    def __init__(self, setting):
        self.setting = setting
        self.debug = setting.get('debug', False)
        self._running = True
        self._adapters = {}
        self._proxies = {}
        if self.debug and logger.is_debug():
            logger.get_logger().debug("application setting %s", setting)

    def create_proxy(self, endpoint):
        prx = proxy.Proxy(endpoint, self.debug)
        self._proxies[endpoint] = prx
        return prx

    def add_adpater(self, adapter):
        name = adapter.get_name()
        self._adapters[name] = adapter

    def stop(self):
        for adp in self._adapters:
            self._adapters[adp].deactivate()
        self._running = False

    def serve_forever(self):
        for (name, adapter) in self._adapters.items():
            adapter.activate()

        self.start_time = time.strftime('%Y-%m-%d %H:%M:%S')
        while self._running:
            # periodic log info that engine is running
            p = {}
            p['start_time'] = self.start_time
            p['adapters'] = self._adapters
            logger.get_logger().critical("THROB %s", str(p))
            gevent.sleep(60)

def json_load_conf(conf):
    buffer = ''
    for ln in open(conf):
        ln = ln.strip()
        if ln.startswith('#') or ln.startswith("//") or ln.startswith(';'):
            continue
        else:
            buffer += ln
    return json.loads(buffer)

def make_easy_engine(name, servant_class, conf = None):
    if not conf:
        if len(sys.argv) == 1:
            print "Usage:", sys.argv[0], "conf"
            sys.exit(1)
        conf = sys.argv[1]

    if type(conf) == dict:
        setting = conf
    else:
        setting = json_load_conf(conf)

    engine = Engine(setting)

    adapter = Adapter(name, setting)
    engine.add_adpater(adapter);

    servant = servant_class(setting)
    servant._init(engine, adapter)
    adapter.add_servant(name, servant)

    return engine
