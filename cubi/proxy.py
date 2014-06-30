#! /bin/env python

import struct
import socket
import time
import sys
import os
import bp
import logger
import traceback

import gevent
from gevent.queue import Queue
from gevent.event import AsyncResult

MESSAGE_MAGIC               = 'CB'
MESSAGE_VER                 = 0x01
MESSAGE_TYPE_WELCOME        = 0x01
MESSAGE_TYPE_CLOSE          = 0x02
MESSAGE_TYPE_QUERY          = 0x03
MESSAGE_TYPE_ANSWER         = 0x04

class Messager:

    @staticmethod
    def data_for_welcome():
        return struct.pack('<2s2B', MESSAGE_MAGIC, MESSAGE_VER, MESSAGE_TYPE_WELCOME)

    @staticmethod
    def data_for_close():
        return struct.pack('<2s2B', MESSAGE_MAGIC, MESSAGE_VER, MESSAGE_TYPE_WELCOME)

    @staticmethod
    def data_for_query(qid, service, method, params):
        s = bp.encode((qid, service, method, params))
        header = struct.pack('<2s2Bi', MESSAGE_MAGIC, MESSAGE_VER, MESSAGE_TYPE_QUERY, len(s))
        return header + str(s)

    @staticmethod
    def data_for_answer(qid, status, data):
        s = bp.encode((qid, status, data))
        header = struct.pack('<2s2Bi', MESSAGE_MAGIC, MESSAGE_VER, MESSAGE_TYPE_ANSWER, len(s))
        return header + str(s)

    @staticmethod
    def receive_data(socket, num):
        data = ''
        while len(data) < num:
            buf = socket.recv(num - len(data))
            if not buf:
                return None
            data += buf
        return data

    @staticmethod
    def receive_msg_type(socket):
        header_str = Messager.receive_data(socket, 4)
        if not header_str:
            return None

        header = struct.unpack('<2s2B', header_str)
        if header[0] != MESSAGE_MAGIC or header[1] != MESSAGE_VER:
            return None
        return header[2]

    @staticmethod
    def receive_msg(socket):
        type = Messager.receive_msg_type(socket)

        if not type:
            return None

        if type == MESSAGE_TYPE_WELCOME:
            return Welcome()
        elif type == MESSAGE_TYPE_CLOSE:
            return Close()

        len_str = Messager.receive_data(socket, 4)
        if not len_str:
            return None
        len = struct.unpack('<i', len_str)
        len = len[0]

        body = Messager.receive_data(socket, len)
        data = bp.decode(body)

        if type == MESSAGE_TYPE_QUERY:
            return Query.from_receive(data)
        elif type == MESSAGE_TYPE_ANSWER:
            return Answer.from_receive(data)
        else:
            return None

    @staticmethod
    def message_from_data(data):
        if len(data) < 4:
            return None

        header = struct.unpack('<2s2Bi', data[:4])
        if header[0] != MESSAGE_MAGIC or header[1] != MESSAGE_VER:
            return None
        type = header[2]

        if type == MESSAGE_TYPE_WELCOME:
            return Welcome()
        elif type == MESSAGE_TYPE_CLOSE:
            return Close()

        len = struct.unpack('<i', data[4:8])
        if len(data) < 8 + size:
            return None
        odata = pkt[8:8+size]

        data = bp.decode(odata)
        if type == MESSAGE_TYPE_QUERY:
            return Query.from_receive(data)
        elif type == MESSAGE_TYPE_ANSWER:
            return Answer.from_receive(data)
        else:
            return None

class Welcome():

    def __repr__(self):
        return 'proxy.Welcome()'

class Close:

    def __repr__(self):
        return 'proxy.Close()'

class Query:
    def __init__(self, qid, service, method, params):
        self.qid = qid
        self.service = service
        self.method = method
        self.params = params

    def get_data(self):
        return Messager.data_for_query(self.qid, self.service, self.method, self.params)

    @staticmethod
    def from_receive(data):
        return Query(data[0], data[1], data[2], data[3])

    def __repr__(self):
        l = (self.qid, self.service, self.method, self.params)
        return 'proxy.Query(' + str(l) + ')'

class Answer:
    def __init__(self, qid, status, data):
        self.qid = qid
        self.status = status
        self.data = data

    def __repr__(self):
        return 'proxy.Answer(' + str((self.qid, self.status, self.data)) + ')'

    def get_data(self):
        return Messager.data_for_answer(self.qid, self.status, self.data)

    @staticmethod
    def from_receive(data):
        return Answer(data[0], data[1], data[2])

class Error(Exception):
    def __init__(self, qid, status, params):
        self.status = status
        self.params = params
        self.qid = qid

    def __str__(self):
        return 'proxy.Error(' + str(self.params) + ')'

    def __repr__(self):
        return 'proxy.Error(' + str(self.params) + ')'

class Proxy(object):

    def __init__(self, end_point, debug=False, timeout = 6000, welcome=True):
        self.end_point = end_point
        self.debug = debug
        self.welcome = welcome

        self.service, self.protocol, self.host, self.port = parse_endpoint(end_point)

        self.timeout = timeout

        self.socket = None
        self.reset()

    def stop(self):

        self._running = False
        self._connected = False
        self._recv_thread = None
        self._reap_thread = None

        if self.socket:
            self.socket.close()
        self.socket = None

    def reset(self):
        self.last_id = 0
        self.pending = {}
        self._query_list = {}
        self._send_queue = Queue()
        self._send_thread = gevent.spawn(self.send_fiber)
        self._reap_thread = gevent.spawn(self.reap_fiber)
        self._connected = False
        self._running = True

    def next_qid(self):
        self.last_id +=1;
        return self.last_id;

    def connect(self):
        if self.protocol == 'tcp':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        elif self.protocol == 'udp':
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        self.socket.connect((self.host, self.port))
        if self.debug and logger.is_debug():
            ip, port = self.socket.getsockname()
            logger.get_logger().debug('address = %s:%d' % (ip, port))

        if self.welcome:
            type = Messager.receive_msg_type(self.socket)
            if type != MESSAGE_TYPE_WELCOME:
                raise Exception('Imcomplete message')

            if self.debug and logger.is_debug():
                logger.get_logger().debug('S.WELCOME')

    def unitive_send(self, data):
        self.socket.sendall(data)

    def unitive_recvfrom(self, recvlen):
        data = self.socket.recvfrom(recvlen)
        return data

    def send_quest(self, qid, method, params, twoway=True):
        if qid:
            self.pending[qid] = time.time()

        if self.debug and logger.is_debug():
            logger.get_logger().debug('CQ:%d service=%s method=%s params=%s', qid, self.service, method, params)

        self.unitive_send(Messager.data_for_query(qid, self.service, method, params))
        return qid

    def send_answer(self, qid, status, data):
        if self.debug and logger.is_debug():
            logger.get_logger().debug('CA:%d %d %s', qid, status, data)
        self.unitive_send(Messager.data_for_answer(qid, status, data))

    def receive_next_msg(self):
        if self.protocol == 'tcp':
            message = Messager.receive_msg(self.socket)

        elif self.protocol == 'udp':
            pkt, address = self.unitive_recvfrom(65535)
            message = Messager.message_from_data(pkt)

        if self.debug and logger.is_debug():
            if isinstance(message, Query):
                logger.get_logger().debug('SQ:%d method=%s, params=%s', message.qid, message.method, message.params)
            elif isinstance(message, Answer):
                logger.get_logger().debug('SA:%d status=%d, data=%s', message.qid, message.status, message.data)

        if not message:
            raise Exception('Recieved Unknown packet')

        if isinstance(message, Answer):
            qid = message.qid
            if self.pending.get(qid):
                del self.pending[qid]
            status = message.status
            if status:
                raise Error(qid, status, message.data)
        return message;

    def reap_fiber(self):
        while True:
            try:
                now = time.time()
                for qid, ctime in self.pending.items():
                    timediff = (now - ctime) * 1000
                    if timediff > self.timeout:
                        exdict = {}
                        exdict['exception'] = 'QueryTimeoutError'
                        exdict['code'] = 1
                        exdict['message'] = 'query %d recv timeout ctime %d now %d proxy timeout %dms' % (qid, ctime, now, self.timeout)
                        exdict['detail'] = {}
                        if self._query_list.get(qid):
                            msg = Answer(qid, 1, exdict)
                            self._query_list[qid].set(msg)
                            del self._query_list[qid]
                            del self.pending[qid]
            except:
                logger.get_logger().error('proxy %s reap fiber exception %s', self.end_point, traceback.format_exc())

            gevent.sleep(3);

    def send_fiber(self):
        while self._running:
            qid = None
            try:
                qid, method, params = self._send_queue.get()
                if not self._connected:
                    self.connect()
                    self._connected = True
                    self._recv_thread = gevent.spawn(self.recv_fiber)
                self.send_quest(qid, method, params)
            except:
                self.stop()
                self._fail_quests()
                if self._recv_thread:
                    gevent.kill(self._recv_thread)
                    self._recv_thread = None
            finally:
                pass

    def recv_fiber(self):
        while self._running:
            try:
                msg = self.receive_next_msg()
                if msg == None:
                    raise EngineError('Received nothing')
                if isinstance(msg, Query):
                    raise EngineError('Recieved unexpected Query')
                else : #set result
                    if self._query_list.get(msg.qid):
                        self._query_list[msg.qid].set(msg)
                        del self._query_list[msg.qid]
                    else:
                        logger.get_logger().error('proxy %s get unexpected answer %s. qid may be removed for timeout', self.end_point, msg)
            except Error as ex:
                if self._query_list.get(ex.qid):
                    msg = Answer(ex.qid, ex.status, ex.params)
                    self._query_list[ex.qid].set(msg)
                    del self._query_list[ex.qid]
            except:
                self.stop()
                break

        self._fail_quests()

    def _build_except_info(self):
        exdict = {}
        exctype, exmsg, tb = sys.exc_info()
        exdict['exception'] = repr(exctype)
        exdict['code'] = 1
        exdict['message'] = str(exmsg)
        exdict['detail'] = {}
        exdict['detail']['what'] = repr(traceback.extract_tb(tb))
        return exdict

    def _fail_quests(self):
        exinfo = self._build_except_info()
        logger.get_logger().error('proxy %s get error %s, fail current querys', self.end_point, exinfo)
        curr_req_items = self._query_list.items()
        self._query_list = {}
        for qid, result in curr_req_items:
            msg = Answer(qid, 1, exinfo)
            #AsyncResult set should cause context switch
            result.set(msg)

    def emit_query(self, qid, method, params):
        logger.get_logger().debug('emit_query: qid=%d, method=%s, params=%s', qid, method, params)
        self._send_queue.put((qid, method, params))

    def request_many(self, reqs):
        """
        salvo simultaneous query many service and get result
        """
        local_quests = {}
        idx = 0
        while idx < len(reqs):
            req = reqs[idx]
            ar = AsyncResult()
            qid = self.next_qid()
            self.emit_query(qid, *req)
            self._query_list[qid] = ar
            local_quests[qid] = (idx, ar)
            idx += 1

        for qid, it in local_quests.items():
            idx, ar = it
            """
            async result will always get a response even if other query
            reply soon

            """
            msg = ar.get()
            if msg:
                if msg.status:
                    yield Error(qid, msg.status, msg.params), idx
                else:
                    yield msg.data, idx

    def request(self, method, params, twoway = True):
        ar = AsyncResult()
        qid = 0;
        if twoway:
            qid = self.next_qid()
            self._query_list[qid] = ar

        self.emit_query(qid, method, params);

        if twoway:
            msg = ar.get()
            if msg.status:
                raise Error(qid, msg.status, msg.data)
            logger.get_logger().debug('result: qid=%d, result=%s', msg.qid, msg.data)
            return msg.data

def parse_endpoint(endpoint):
    x = endpoint.split('@')
    service = x[0].strip()

    z = x[1].split()
    protocol, host, port = z[0].split(':')

    if protocol == '':
        protocol = 'tcp'

    if len(host.strip()) == 0:
        host = '127.0.0.1'

    port = int(port)
    return service, protocol, host, port
