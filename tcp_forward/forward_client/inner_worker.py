import select

from enum import Enum

import data_handler
from common import connector
from common import forward_event
from common import forward_data
import logging
import traceback
import data_handler
logger = logging.getLogger('my_logger')

class InnerWorker(object):
    class State(Enum):
        NONE = 0
        CONNECTING = 1
        WORKING = 2
        CLOSED = 3
        DONE = 4

    def __init__(self,forward_id,inner_ip,inner_port,north_interface_channel,connector_change_callback):
        self.__state = self.State.NONE
        self.__id = forward_id
        self.__inner_ip = inner_ip
        self.__inner_port = inner_port
        self.__connector = None
        self.__data_handler = data_handler.InnerDataHandler()
        self.__north_interface_channel = north_interface_channel
        self.__connector_change_callback = connector_change_callback

    def has_done(self):
        return self.__state == self.State.DONE

    def __sourth_interface_event(self,event):
        if self.__state == self.State.CONNECTING:
            self.__connector.refresh_con_state()
            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
                #self.__data_handler.inner_connected(self.__id, self.__inner_ip, self.__inner_port, outer_connector)
                self.__connecte_success()
                self.__state = self.State.WORKING
                logger.info("InnerWorker %d connect to %s:%d succed,change state to WORKING" % (
                self.__id, self.__inner_ip, self.__inner_port))
            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                self.__connector.close()
                self.__state = self.State.CLOSED
                logger.error("InnerWorker %d connect to %s:%d failed,change state to CLOSED" % (
                self.__id, self.__inner_ip, self.__inner_port))
        elif self.__state == self.State.WORKING:
            self.__handle_working_event(event)



    def __north_interface_transdata_event(self,event):
        if not isinstance(event,forward_event.TransDataEvent):
            return

        if self.__state == self.State.WORKING:
            if event.forward_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
                send_bytes = self.__connector.send(event.forward_data.data)
                if send_bytes <= 0:
                    logger.error("InnerWorker %d trans bytes <=0 change state to CLOSED", self.__id)
                    self.__state = self.State.CLOSED

    def __north_interface_closecon_event(self,event):
        if self.__state in (self.State.DONE,self.State.CLOSED):
            return

        self.__connector.close()
        self.__state = self.State.CLOSED
        logger.debug(
            "InnerWorker %d current state:%s change state to CLOSED " % (self.__id, str(self.__state)))

    def __connecte_success(self):
        connected_data = forward_data.ForwardData(forward_data.DATA_TYPE.CONNECTION_SUCCESS, self.__id,
                                                  self.__inner_ip, self.__inner_port, '')
        connected_event = forward_event.TransDataEvent(self.__id, connected_data)
        self.__north_interface_channel(connected_event)
        self.__connector_change_callback(self.__connector, self.handler_event)

    def __scheduler_event(self, event):

        if not isinstance(event,forward_event.SchedulerEvent):
            return

        if self.__state == self.State.NONE:
            self.__connector = connector.ConnectorClient(self.__inner_ip, self.__inner_port)
            self.__connector.connect()

            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:

                self.__state = self.State.WORKING
                self.__connecte_success()
            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                self.__state = self.State.CLOSED
            elif self.__connector.con_state == connector.CON_STATE.CON_CONNECTING:
                self.__connector_change_callback(self.__connector, self.handler_event)
                self.__state = self.State.CONNECTING
            logger.debug("InnerWorker %d connect to %s:%d current state:%s"%(self.__id,self.__inner_ip,self.__inner_port,str(self.__state)))
        elif self.__state == self.State.WORKING:
            if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
                logger.debug("InnerWorker %d current state:WORKING change state to DONE due connector state error:%s"%(self.__id,str(self.__connector.con_state)) )
        elif self.__state == self.State.CLOSED:
            #send closed message to outer
            #self.__data_handler.inner_closed(self.__id,self.__inner_ip,self.__inner_port,outer_connector)
            close_event = forward_event.CloseConEvent(self.__id)
            self.__north_interface_channel(close_event)
            self.__connector.close()
            self.__connector_change_callback(self.__connector, self.handler_event)
            self.__state = self.State.DONE
            logger.debug("InnerWorker %d current state:CLOSED change state to DONE"%(self.__id))

    def __handle_working_event(self, event):
        error_happen = False
        if event.fd_event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                # trans data
                try:
                    trans_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, self.__id,
                                                          self.__inner_ip, self.__inner_port, bytearray(recv_msg))
                    trans_data_event = forward_event.TransDataEvent(self.__id, trans_data)

                    self.__north_interface_channel(trans_data_event)
                except Exception, e:
                    error_happen = True
                    logger.error("InnerWorker %d current state:WORKING send data error" % (self.__id))
                    logger.debug(traceback.format_exc())

            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                    logger.error("InnerWorker %d current state:WORKING recv data error" % (self.__id))

        elif event.fd_event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__connector.close()
            self.__state = self.State.CLOSED
            logger.debug("InnerWorker %d current state:WORKING change state to CLOSED" % (self.__id))

    @forward_event.event_filter
    def handler_event(self, event):
        if event.event_type == forward_event.FDEVENT:
            # socket receive msg
            self.__sourth_interface_event(event)
        elif event.event_type == forward_event.TRANSDATAEVENT:
            self.__north_interface_transdata_event(event)
        elif event.event_type == forward_event.CLOSECONEVENT:
            self.__north_interface_closecon_event(event)
        elif event.event_type == forward_event.SCHEDULEREVENT:
            self.__scheduler_event(event)