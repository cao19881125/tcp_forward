from enum import Enum
import logging
import time
import select
import traceback
from common import connector
from common import forward_event
from common import forward_data

logger = logging.getLogger('my_logger')

import data_handler
class OuterWorker(object):
    class State(Enum):
        NONE = 0
        CONNECTING_TO_INNER = 1
        WORKING = 2
        CLOSED = 3
        DONE = 4

    def __init__(self,worker_id,inner_ip,inner_port,outer_socket,sourth_interface_channel,connector_change_callback):
        self.__worker_id = worker_id
        self.__inner_ip = inner_ip
        self.__inner_port = inner_port
        self.__state = self.State.NONE
        self.__sourth_interface_channel = sourth_interface_channel
        self.__connector = connector.Connector(outer_socket)
        self.__data_handler = data_handler.OutDataHandler()
        self.__connector_change_callback = connector_change_callback
        self.__connecting_begin_time = 0

    def has_done(self):
        return self.__state == self.State.DONE

    def get_worker_id(self):
        return self.__worker_id

    def __recv_data(self,event):
        error_happen = False
        if event.fd_event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                # trans data
                # print 'recv outer %d msg:'%(self.__worker_id)
                # tools.print_hex_buf(recv_msg)
                try:
                    trans_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA,self.__worker_id,self.__inner_ip,self.__inner_port,recv_msg)
                    trans_data_event = forward_event.TransDataEvent(self.__worker_id,trans_data)

                    self.__sourth_interface_channel(trans_data_event)
                except Exception, e:
                    error_happen = True
                    logger.error("OuterWorker %d current state:WORKING send data error" % (self.__worker_id))
                    logger.debug(traceback.format_exc())
            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                logger.error("OuterWorker %d current state:WORKING recv data error" % (self.__worker_id))

        elif event.fd_event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__connector.close()

            self.__state = self.State.CLOSED
            logger.debug("OuterWorker %d current state:WORKING change state to CLOSED" % (self.__worker_id))


    def __north_interface_event(self, event):
        if self.__state == self.State.WORKING:
            self.__recv_data(event)
        else:
            time.sleep(0.01)

    def __sourth_interface_transdata_event(self,event):
        if not isinstance(event,forward_event.TransDataEvent):
            return

        if self.__state == self.State.CONNECTING_TO_INNER:
            if event.forward_data.data_type == forward_data.DATA_TYPE.CONNECTION_SUCCESS:
                self.__state = self.State.WORKING
                logger.debug(
                    "OuterWorker %d current state:CONNECTING_TO_INNER change state to WORKING" % (self.__worker_id))
        elif self.__state == self.State.WORKING:
            if event.forward_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
                send_bytes = self.__connector.send(event.forward_data.data)
                if send_bytes <= 0:
                    logger.error("OutWorker %d trans bytes <=0 change state to CLOSED", self.__worker_id)
                    self.__state = self.State.CLOSED
        else:
            pass


    def __sourth_interface_closecon_event(self,event):
        if self.__state in (self.State.DONE,self.State.CLOSED):
            return

        self.__connector.close()
        self.__state = self.State.CLOSED
        logger.debug(
            "OuterWorker %d current state:%s change state to CLOSED " % (self.__worker_id, str(self.__state)))

    def __scheduler_event(self, event):
        if self.__state == self.State.NONE:
            self.__data_handler.create_connection(self.__worker_id, self.__inner_ip, self.__inner_port,
                                                  self.__sourth_interface_channel)
            self.__state = self.State.CONNECTING_TO_INNER
            self.__connecting_begin_time = time.time()
            logger.debug("OuterWorker %d current state:NONE create inner connecttion to %s:%d ,change state to CONNECTING_TO_INNER" %
                (self.__worker_id, self.__inner_ip, self.__inner_port))
        elif self.__state == self.State.CONNECTING_TO_INNER:
            if (time.time() - self.__connecting_begin_time) >= 5:
                #connecting can not over 5 seconds
                self.__state = self.State.CLOSED
                logger.error("OuterWorker %d  stay in CONNECTING_TO_INNER state over 5 seconds,change state to CLOSED"%(self.__worker_id))
        elif self.__state == self.State.WORKING:
            if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
                logger.debug("OuterWorker %d current state:WORKING change state to CLOSED due connector state error:%s"%(self.__worker_id,str(self.__connector.con_state)) )
        elif self.__state == self.State.CLOSED:
            # send closed msg to remote
            close_event = forward_event.CloseConEvent(self.__worker_id)
            self.__sourth_interface_channel(close_event)
            self.__connector.close()
            self.__connector_change_callback(self.__connector, self.handler_event)
            self.__state = self.State.DONE
            logger.debug("OuterWorker %d current state:CLOSED change state to DONE" % (self.__worker_id))

    @forward_event.event_filter
    def handler_event(self,event):
        if event.event_type == forward_event.FDEVENT:
            # socket receive msg
            self.__north_interface_event(event)
        elif event.event_type == forward_event.TRANSDATAEVENT:
            self.__sourth_interface_transdata_event(event)
        elif event.event_type == forward_event.CLOSECONEVENT:
            self.__sourth_interface_closecon_event(event)
        elif event.event_type == forward_event.SCHEDULEREVENT:
            self.__scheduler_event(event)