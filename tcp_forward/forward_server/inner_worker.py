from common import connector
from common import ring_buffer
from common import forward_event
from common import forward_data
import select
import logging
import data_handler
from enum import Enum
import time
import worker
logger = logging.getLogger('my_logger')

class InnerWorker(worker.Worker):
    class State(Enum):
        NONE = 0
        PRE_WORKING = 1
        WORKING = 2
        CLOSED = 3
        DONE = 4
    def __init__(self,worker_id,inner_socket,address,north_interface_channel,connector_change_callback):
        super(InnerWorker,self).__init__(worker_id,address,connector.Connector(inner_socket))
        self.__state = self.State.NONE
        self.__north_interface_channel = north_interface_channel
        self.__data_handler = data_handler.InnerDataHandler()
        self.__ring_buffer = ring_buffer.TimeoutRingbuffer(10240 * 10240, 5)
        self._connector_change_callback = connector_change_callback
        self.__tag = 'NONE'

    def has_done(self):
        return self.__state == self.State.DONE

    def get_tag(self):
        return self.__tag

    def get_worker_static_info(self):
        info = super(InnerWorker,self).get_worker_static_info()
        info['tag'] = self.__tag
        info['state'] = str(self.__state).split('.')[-1]

        return info



    def __sourth_interface_event(self,event):
        if self.__state == self.State.PRE_WORKING:
            self.__recv_data_to_ringbuffer(event)
            tag = self.__data_handler.handle_pre_working_response(self.__ring_buffer)
            if tag:
                self.__tag = str(tag).strip('\0')
                self.__state = self.State.WORKING
                logger.info("InnerWorker %d trans into WORKING state,tag is:%s"%(self._worker_id,tag))
        if self.__state == self.State.WORKING:
            self.__recv_data_to_ringbuffer(event)


    def __recv_data_to_ringbuffer(self,event):
        error_happen = False
        if event.fd_event & select.EPOLLIN:
            recv_msg = self._connector.recv()
            if len(recv_msg) > 0:
                self.__ring_buffer.put(bytearray(recv_msg))
                self._recv_flow_static.add_flow(len(recv_msg))
            else:
                if self._connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                    logger.error("InnerWorker %d current state:WORKING recv data error" % (self._worker_id))
        elif event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self._connector.close()
            self.__state = self.State.CLOSED
            logger.debug("InnerWorker %d current state:WORKING change state to CLOSED" % (self._worker_id))

    def __north_interface_transdata_event(self,event):
        if not isinstance(event,forward_event.TransDataEvent):
            return
        f_data = event.forward_data
        if event.forward_data.data_type == forward_data.DATA_TYPE.NEW_CONNECTION:
            self.__data_handler.create_connection(f_data.id,f_data.inner_ip,
                                                  f_data.inner_port,self._connector)
        elif event.forward_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:

            self.__data_handler.trans_data(f_data.id,f_data.inner_ip,f_data.inner_port,f_data.data,self._connector)
            self._send_flow_static.add_flow(len(f_data.data))

    def __north_interface_closecon_event(self,event):
        if self.__state in (self.State.DONE,self.State.CLOSED):
            return
        if not isinstance(event,forward_event.CloseConEvent):
            return

        if event.forward_id == self._worker_id:
            self._connector.close()
            self.__state = self.State.CLOSED
            logger.debug("InnerWorker %d current state:WORKING change state to CLOSED" % (self._worker_id))
        else:
            self.__data_handler.close_connection(event.forward_id,'0.0.0.0',0,self._connector)

    def __scheduler_event(self,event):
        if self.__state == self.State.NONE:
            self.__data_handler.send_pre_working(self._connector)
            self.__state = self.State.PRE_WORKING
            self.__pre_working_start = time.time()
            logger.debug("InnerWorker %d current state:NONE change state to PRE_WORKING" % (self._worker_id))
        elif self.__state == self.State.PRE_WORKING:
            if (time.time() - self.__pre_working_start) > 5:
                self.__state = self.State.CLOSED
                logger.error("InnerWorker %d stay in PRO_WORKING state over 5 seconds,close it"%(self._worker_id))
        elif self.__state == self.State.CLOSED:
            # close all paired outer worker
            try:
                close_event = forward_event.CloseConEvent(self._worker_id)
                self.__north_interface_channel(close_event)
                self._connector.close()
                self._connector_change_callback(self._connector, self.handler_event)
            except Exception,e:
                logger.error(e.message)
            self.__state = self.State.DONE
            logger.debug("InnerWorker %d current state:CLOSED change state to DONE" % (self._worker_id))
        elif self.__state == self.State.WORKING:
            if self._connector.con_state != connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.CLOSED
                logger.debug("InnerWorker %d current state:WORKING change state to CLOSED due connector state error:%s"%(self._worker_id,str(self._connector.con_state)) )
                return

        self.__handle_data()

    def send_heart_beat_reply(self):
        try:
            self.__data_handler.send_heart_beat_reply(self._connector)
        except Exception, e:
            logger.error("InnerWorker %d current state:WORKING send heartbeat reply error,change state to DISCONNECTED"%(self._worker_id))
            self.__state = self.State.DISCONNECTED

    def __handle_data(self):
        datas = self.__data_handler.get_forward_datas(self.__ring_buffer)
        for data in datas:
            if data.data_type in (forward_data.DATA_TYPE.CONNECTION_SUCCESS,
                                  forward_data.DATA_TYPE.TRANS_DATA):
                trans_event = forward_event.TransDataEvent(data.id,data)
                self.__north_interface_channel(trans_event)
            elif data.data_type == forward_data.DATA_TYPE.CLOSE_CONNECTION:
                close_event = forward_event.CloseConEvent(data.id)
                self.__north_interface_channel(close_event)
            elif data.data_type == forward_data.DATA_TYPE.HEART_BEAT:
                self.send_heart_beat_reply()
                logger.info("InnerWorker %d send heartbeat reply "%(self._worker_id))

    @forward_event.event_filter
    def handler_event(self,event):
        if event.event_type == forward_event.FDEVENT:
            # socket receive msg
            self.__sourth_interface_event(event)
        elif event.event_type == forward_event.TRANSDATAEVENT:
            self.__north_interface_transdata_event(event)
        elif event.event_type == forward_event.CLOSECONEVENT:
            self.__north_interface_closecon_event(event)
        elif event.event_type == forward_event.SCHEDULEREVENT:
            self.__scheduler_event(event)

