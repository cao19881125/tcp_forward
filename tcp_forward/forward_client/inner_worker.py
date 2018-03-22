import select

from enum import Enum

import data_handler
from common import connector
import logging
logger = logging.getLogger('my_logger')

class InnerWorker(object):
    class State(Enum):
        NONE = 0
        CONNECTING = 1
        WORKING = 2
        CLOSED = 3
        DONE = 4

    def __init__(self,forward_id,inner_ip,inner_port):
        self.__state = self.State.NONE
        self.__id = forward_id
        self.__inner_ip = inner_ip
        self.__inner_port = inner_port
        self.__connector = None
        self.__data_handler = data_handler.InnerDataHandler()

    def get_fileno(self):
        if self.__connector == None:
            return None

        return self.__connector.get_fileno()

    def get_forward_id(self):
        return self.__id

    def trans_data(self,msg):
        send_bytes = self.__connector.send(msg)
        if send_bytes <= 0:
            logger.error("InnerWorker %d trans bytes <=0 change state to CLOSED",self.__id)
            self.__state = self.State.CLOSED

    def close(self):
        if self.__state == self.State.DONE:
            return
        self.__connector.close()
        self.__state = self.State.CLOSED

    def has_done(self):
        return self.__state == self.State.DONE

    def is_working(self):
        return self.__state == self.State.WORKING

    def handle_event(self, recever,event,outer_connector):
        if self.__state == self.State.CONNECTING:
            self.__connector.refresh_con_state()
            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
                self.__data_handler.inner_connected(self.__id,self.__inner_ip,self.__inner_port,outer_connector)
                self.__state = self.State.WORKING
                recever.change_event(self.__connector.get_fileno(),select.EPOLLIN)
                logger.info("InnerWorker %d connect to %s:%d succed,change state to WORKING"%(self.__id,self.__inner_ip,self.__inner_port))
            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                self.__connector.close()
                self.__state = self.State.CLOSED
                logger.error("InnerWorker %d connect to %s:%d failed,change state to CLOSED"%(self.__id, self.__inner_ip, self.__inner_port))
        elif self.__state == self.State.WORKING:
            self.__handle_working_event(event,outer_connector)

    def do_work(self, recever,outer_connector):
        if self.__state == self.State.NONE:
            self.__connector = connector.ConnectorClient(self.__inner_ip, self.__inner_port)
            self.__connector.connect()

            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
                recever.add_receiver(self.__connector.get_fileno(), select.EPOLLIN)
                self.__state = self.State.WORKING
            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                self.__state = self.State.CLOSED
            elif self.__connector.con_state == connector.CON_STATE.CON_CONNECTING:
                recever.add_receiver(self.__connector.get_fileno(), select.EPOLLOUT)
                self.__state = self.State.CONNECTING
            logger.debug("InnerWorker %d connect to %s:%d current state:%s"%(self.__id,self.__inner_ip,self.__inner_port,str(self.__state)))
        elif self.__state == self.State.WORKING:
            if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
                logger.debug("InnerWorker %d current state:WORKING change state to DONE due connector state error:%s"%(self.__id,str(self.__connector.con_state)) )

        elif self.__state == self.State.CLOSED:
            #send closed message to outer
            self.__data_handler.inner_closed(self.__id,self.__inner_ip,self.__inner_port,outer_connector)
            recever.del_receiver(self.__connector.get_fileno())
            self.__state = self.State.DONE
            logger.debug("InnerWorker %d current state:CLOSED change state to DONE"%(self.__id))

    def __handle_working_event(self, event,outer_connector):
        error_happen = False
        if event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                # trans data
                try:
                    self.__data_handler.tarns_data(self.__id, self.__inner_ip, self.__inner_port,
                                               bytearray(recv_msg), outer_connector)
                except Exception,e:
                    error_happen = True
                    logger.error("InnerWorker %d current state:WORKING send data error" % (self.__id))

            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                logger.error("InnerWorker %d current state:WORKING recv data error" % (self.__id))

        elif event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__connector.close()
            self.__state = self.State.CLOSED
            logger.debug("InnerWorker %d current state:WORKING change state to CLOSED" % (self.__id))