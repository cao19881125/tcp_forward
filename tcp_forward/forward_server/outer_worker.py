from enum import Enum
import select
from common import connector
from common import tools
import data_handler
import logging
import time
logger = logging.getLogger('my_logger')

class OuterWorker(object):
    class State(Enum):
        NONE = 0
        CONNECTING_TO_INNER = 1
        WORKING = 2
        CLOSED = 3
        DONE = 4

    def __init__(self,worker_id,inner_ip,inner_port,outer_socket):
        self.__worker_id = worker_id
        self.__state = self.State.NONE
        self.__inner_ip = inner_ip
        self.__inner_port = inner_port
        self.__connector = connector.Connector(outer_socket)
        self.__data_handler = data_handler.OutDataHandler()
        self.__connecting_begin_time = 0

    def has_done(self):
        return self.__state == self.State.DONE

    def is_working(self):
        return self.__state == self.State.WORKING

    def handle_event(self,event,inner_connection):

        if self.__state == self.State.WORKING:
            self.__handle_working_event(event,inner_connection)

    def get_worker_id(self):
        return self.__worker_id

    def trans_data(self,msg):
        send_bytes = self.__connector.send(msg)
        if send_bytes <= 0:
            logger.error("OutWorker %d trans bytes <=0 change state to CLOSED",self.__worker_id)
            self.__state = self.State.CLOSED

    def close(self):
        if self.__state == self.State.DONE:
            return
        if self.__state == self.State.CONNECTING_TO_INNER:
            self.connecting_reply(False)
        else:
            self.__connector.close()
            self.__state = self.State.CLOSED
            logger.debug("OuterWorker %d current state:%s change state to CLOSED " % (self.__worker_id,str(self.__state)))

    def get_fileno(self):
        if self.__connector == None:
            return None

        return self.__connector.get_fileno()

    def do_work(self,inner_connection):

        if self.__state == self.State.NONE:
            if inner_connection and inner_connection.con_state == connector.CON_STATE.CON_CONNECTED:
                self.__data_handler.create_connection(self.__worker_id,self.__inner_ip,self.__inner_port,inner_connection)
                self.__state = self.State.CONNECTING_TO_INNER
                self.__connecting_begin_time = time.time()
                logger.debug("OuterWorker %d current state:NONE create inner connecttion to %s:%d ,change state to CONNECTING_TO_INNER"%
                             (self.__worker_id,self.__inner_ip,self.__inner_port))
            else:
                self.__connector.close()
                self.__state = self.State.DONE
                logger.debug("OuterWorker %d current state:NONE change state to DONE due inner_connection state error"%(self.__worker_id))
        elif self.__state == self.State.CONNECTING_TO_INNER:
            if (time.time() - self.__connecting_begin_time) >= 5:
                #connecting can not over 5 seconds
                inner_connection.close()
                self.__state = self.State.CLOSED
        elif self.__state == self.State.WORKING:
            if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
                logger.debug("OuterWorker %d current state:WORKING change state to CLOSED due connector state error:%s"%(self.__worker_id,str(self.__connector.con_state)) )

        elif self.__state == self.State.CLOSED:
            # send closed msg to remote
            if inner_connection and inner_connection.con_state == connector.CON_STATE.CON_CONNECTED:
                self.__data_handler.close_connection(self.__worker_id,self.__inner_ip,self.__inner_port,inner_connection)
            self.__connector.close()
            self.__state = self.State.DONE
            logger.debug("OuterWorker %d current state:CLOSED change state to DONE" %(self.__worker_id))

    def connecting_reply(self,connected):
        if self.__state != self.State.CONNECTING_TO_INNER:
            return

        if connected:
            self.__state = self.State.WORKING
            logger.debug("OuterWorker %d current state:CONNECTING_TO_INNER change state to WORKING" % (self.__worker_id))
        else:
            self.__connector.close()
            self.__state = self.State.DONE
            logger.debug("OuterWorker %d current state:CONNECTING_TO_INNER change state to DONE" % (self.__worker_id))

    def __handle_working_event(self, event,inner_connection):
        error_happen = False
        if event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                # trans data
                #print 'recv outer %d msg:'%(self.__worker_id)
                #tools.print_hex_buf(recv_msg)
                try:
                    self.__data_handler.trans_data(self.__worker_id,self.__inner_ip,self.__inner_port,bytearray(recv_msg),inner_connection)
                except Exception,e:
                    error_happen = True
                    logger.error("OuterWorker %d current state:WORKING send data error" % (self.__worker_id))
            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                logger.error("OuterWorker %d current state:WORKING recv data error" % (self.__worker_id))

        elif event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__connector.close()
            self.__state = self.State.CLOSED
            logger.debug("OuterWorker %d current state:WORKING change state to CLOSED" % (self.__worker_id))
