from enum import Enum
import select
from common import connector
from common import ring_buffer
import data_handler
import logging
logger = logging.getLogger('my_logger')

class InnerWorker(object):
    class State(Enum):
        NONE = 0
        WORKING = 1
        CLOSED = 2
        DONE = 3


    def __init__(self,worker_id,inner_socket):
        self.__worker_id = worker_id
        self.__state = self.State.NONE
        self.__connector = connector.Connector(inner_socket)
        self.__data_handler = data_handler.InnerDataHandler()
        self.__ring_buffer = ring_buffer.TimeoutRingbuffer(10240 * 10240,5)
        if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
            self.__state = self.State.WORKING

    def get_connector(self):
        return self.__connector

    def has_done(self):
        return self.__state == self.State.DONE

    def get_worker_id(self):
        return self.__worker_id

    def close(self):
        if self.__state == self.State.DONE:
            return
        else:
            self.__connector.close()
            self.__state = self.State.CLOSED
            logger.debug("InnerWorker %d current state:%s change state to CLOSED " % (self.__worker_id,str(self.__state)))

    def get_fileno(self):
        if self.__connector == None:
            return None

        return self.__connector.get_fileno()

    def handle_event(self,event):

        if self.__state == self.State.WORKING:
            self.__handle_working_event(event)

    def do_work(self,worker_manager):
        if self.__state == self.State.CLOSED:
            # close all paired outer worker
            out_workers = worker_manager.get_outer_workers_by_inner_worker_id(self.__worker_id)
            for ow in out_workers:
                ow.close()
            self.__state = self.State.DONE
            logger.debug("InnerWorker %d current state:CLOSED change state to DONE" % (self.__worker_id))
        elif self.__state == self.State.WORKING:
            if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
                logger.debug("InnerWorker %d current state:WORKING change state to CLOSED due connector state error:%s"%(self.__worker_id,str(self.__connector.con_state)) )
                return

        self.__data_handler.handle_data(self.__ring_buffer, worker_manager)
    def __handle_working_event(self, event):
        error_happen = False
        if event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                # handle data
                self.__ring_buffer.put(bytearray(recv_msg))
                #self.__ring_buffer.print_buf()

            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                logger.error("InnerWorker %d current state:WORKING recv data error" % (self.__worker_id))

        elif event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__connector.close()
            self.__state = self.State.CLOSED
            logger.debug("InnerWorker %d current state:WORKING change state to CLOSED" % (self.__worker_id))