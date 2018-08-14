from enum import Enum
from common import connector, epoll_recever, ring_buffer
import logging
import select
from logging.handlers import RotatingFileHandler
import traceback
import data_handler
from common import forward_event
from common import forward_data
import time

logger = logging.getLogger('my_logger')

class OuterWorker(object):
    class State(Enum):
        NONE = 0
        CONNECTING = 1
        WORKING = 2
        DISCONNECTED = 3
    def __init__(self,outer_ip,outer_port,sourth_interface_channel,connector_change_callback):
        self.__state = self.State.NONE
        self.__outer_ip = outer_ip
        self.__outer_port = outer_port
        self.__connector = None
        self.__ring_buffer = ring_buffer.TimeoutRingbuffer(10240 * 10240, 5)
        self.__data_handler = data_handler.OuterDataHandler()
        self.__sourth_interface_channel = sourth_interface_channel
        self.__connector_change_callback = connector_change_callback
        self.__last_heart_beat_time = time.time()

    def __north_interface_event(self, event):
        if self.__state == self.State.CONNECTING:
            self.__connector.refresh_con_state()

            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.WORKING
                self.__connector_change_callback(self.__connector,self.handler_event)
                logger.info("OuterWorker connect success change state to WORKING")

            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                self.__connector.close()
                self.__connector_change_callback(self.__connector,self.handler_event)
                self.__state = self.State.DISCONNECTED
                logger.error("OuterWorker connect failed,change state to DISCONNECTED")
        elif self.__state == self.State.WORKING:
            self.__handle_working_event(event)

    def __handle_working_event(self,event):
        #print '__handle_working_event'
        error_happen = False
        if event.fd_event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                #pass data
                self.__ring_buffer.put(bytearray(recv_msg))
                #self.__ring_buffer.print_buf()
            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                    logger.error("OuterWorker current state:WORKING recv data error")

        elif event.fd_event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__connector.close()
            self.__connector_change_callback(self.__connector,self.handler_event)
            self.__state = self.State.DISCONNECTED
            logger.debug("OuterWorkercurrent state:WORKING change state to DISCONNECTED")

    def __handle_data(self):
        datas = self.__data_handler.get_forward_datas(self.__ring_buffer)
        for data in datas:
            if data.data_type in (forward_data.DATA_TYPE.NEW_CONNECTION,
                                  forward_data.DATA_TYPE.TRANS_DATA):
                trans_event = forward_event.TransDataEvent(data.id,data)
                self.__sourth_interface_channel(trans_event)
            elif data.data_type == forward_data.DATA_TYPE.PRE_WORKING:
                self.__data_handler.send_preworking_reply(self.__connector)
            elif data.data_type == forward_data.DATA_TYPE.CLOSE_CONNECTION:
                close_event = forward_event.CloseConEvent(data.id)
                self.__sourth_interface_channel(close_event)
            elif data.data_type == forward_data.DATA_TYPE.HEART_BEAT:
                logger.debug('OuterWorker recv heartbeat reply')
                self.__last_hear_beat_reply_time = time.time()
    def send_heart_beat(self):
        try:
            self.__data_handler.send_heart_beat(self.__connector)
        except Exception, e:
            logger.error("OuterrWorker current state:WORKING send heartbeat error,change state to DISCONNECTED")
            self.__state = self.State.DISCONNECTED

    def __sourth_interface_transdata_event(self, event):
        if not isinstance(event,forward_event.TransDataEvent):
            return
        f_data = event.forward_data

        if event.forward_data.data_type == forward_data.DATA_TYPE.CONNECTION_SUCCESS:
            self.__data_handler.inner_connect_succed(f_data.id,f_data.inner_ip,f_data.inner_port,self.__connector)
        elif event.forward_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
            self.__data_handler.trans_data(f_data.id,f_data.inner_ip,f_data.inner_port,f_data.data,self.__connector)

    def __sourth_interface_closecon_event(self, event):
        if not isinstance(event,forward_event.CloseConEvent):
            return
        self.__data_handler.close_connection(event.forward_id,'0.0.0.0',0,self.__connector)

    def __scheduler_event(self, event):

        if not isinstance(event,forward_event.SchedulerEvent):
            return


        if self.__state == self.State.NONE:
            #print 'outer_worker:connect to %s %d'%(self.__outer_ip,self.__outer_port)
            self.__connector = connector.ConnectorClient(self.__outer_ip, self.__outer_port)
            self.__connector.connect()

            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
                self.__connector_change_callback(self.__connector,self.handler_event)
                self.__state = self.State.WORKING
            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                #do nothing
                pass
            elif self.__connector.con_state == connector.CON_STATE.CON_CONNECTING:
                self.__connector_change_callback(self.__connector,self.handler_event)
                self.__state = self.State.CONNECTING
        elif self.__state == self.State.WORKING:
            if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.DISCONNECTED
                logger.debug("OuterWorker current state:WORKING change state to DONE due connector state error:%s"%(str(self.__connector.con_state)) )
                return
            else:
                current_time = time.time()
                if current_time - self.__last_heart_beat_time >= 30:
                    self.send_heart_beat()
                    self.__last_heart_beat_time = current_time
                    logger.debug("OuterWorker send hearbeat")
        elif self.__state == self.State.DISCONNECTED:
            close_event = forward_event.CloseConEvent(0)
            self.__sourth_interface_channel(close_event)
            self.__state = self.State.NONE
            logger.debug("OuterWorker current state:DISCONNECTED close all inner_worker,change state to NONE")
        self.__handle_data()

    @forward_event.event_filter
    def handler_event(self, event):
        if event.event_type == forward_event.FDEVENT:
            # socket receive msg
            self.__north_interface_event(event)
        elif event.event_type == forward_event.TRANSDATAEVENT:
            self.__sourth_interface_transdata_event(event)
        elif event.event_type == forward_event.CLOSECONEVENT:
            self.__sourth_interface_closecon_event(event)
        elif event.event_type == forward_event.SCHEDULEREVENT:
            self.__scheduler_event(event)