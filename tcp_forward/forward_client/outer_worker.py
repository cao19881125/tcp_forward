import select
import time
from enum import Enum

from common import connector, epoll_recever, ring_buffer
from data_handler import OuterDataHandler
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger('my_logger')

class OuterWorker(object):
    class State(Enum):
        NONE = 0
        CONNECTING = 1
        WORKING = 2
        DISCONNECTED = 3

    def __init__(self,outer_ip,outer_port):
        self.__state = self.State.NONE
        self.__outer_ip = outer_ip
        self.__outer_port = outer_port
        self.__connector = None
        self.__ring_buffer = ring_buffer.TimeoutRingbuffer(10240 * 10240, 5)
        self.__data_handler = OuterDataHandler()
        self.__last_heart_beat_time = int(time.time())

    def get_fileno(self):
        if self.__connector == None:
            return None

        return self.__connector.get_fileno()

    def get_connector(self):
        return self.__connector

    def send_heart_beat(self):
        try:
            self.__data_handler.send_heart_beat(self.__connector)
        except Exception,e:
            logger.error("OuterrWorker current state:WORKING send heartbeat error,change state to DISCONNECTED" )
            self.__state = self.State.DISCONNECTED

    def handle_event(self,recever,event):


        if self.__state == self.State.CONNECTING:
            self.__connector.refresh_con_state()

            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
                self.__state = self.State.WORKING
                recever.change_event(self.__connector.get_fileno(), select.EPOLLIN)
                logger.info("OuterWorker connect success change state to WORKING")

            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                self.__connector.close()
                self.__state = self.State.DISCONNECTED
                logger.error("OuterWorker connect failed,change state to DISCONNECTED")


        elif self.__state == self.State.WORKING:
            self.__handle_working_event(event)


    def do_work(self,recever,inner_worker_manager):


        if self.__state == self.State.NONE:
            #print 'outer_worker:connect to %s %d'%(self.__outer_ip,self.__outer_port)
            self.__connector = connector.ConnectorClient(self.__outer_ip, self.__outer_port)
            self.__connector.connect()

            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
                recever.add_receiver(self.__connector.get_fileno(), select.EPOLLIN)
                self.__state = self.State.WORKING
            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                #do nothing
                pass
            elif self.__connector.con_state == connector.CON_STATE.CON_CONNECTING:
                recever.add_receiver(self.__connector.get_fileno(), select.EPOLLOUT)
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
            inner_worker_manager.close_all()
            self.__state = self.State.NONE
            logger.debug("OuterWorker current state:DISCONNECTED close all inner_worker,change state to NONE")


        self.__data_handler.handle_data(self.__ring_buffer,inner_worker_manager)

    def __handle_working_event(self,event):
        #print '__handle_working_event'
        error_happen = False
        if event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                #pass data
                self.__ring_buffer.put(bytearray(recv_msg))
                #self.__ring_buffer.print_buf()
            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True
                logger.error("OuterWorker current state:WORKING recv data error")

        elif event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__connector.close()
            self.__state = self.State.DISCONNECTED
            logger.debug("OuterWorkercurrent state:WORKING change state to DISCONNECTED")


if __name__ == '__main__':
    out_worker = OuterWorker('192.168.184.1',1234)
    recver = epoll_recever.Epoll_receiver()

    while True:
        out_worker.do_work(recver,None)
        events = recver.run()
        for fileno, event in events:
            out_worker.handle_event(event)
