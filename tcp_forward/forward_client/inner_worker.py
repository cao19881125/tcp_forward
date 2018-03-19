import select

from enum import Enum

import data_handler
from common import connector


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
        self.__connector.send(msg)

    def close(self):
        self.__connector.close()
        self.__state = self.State.CLOSED

    def has_done(self):
        return self.__state == self.State.DONE

    def handle_event(self, recever,event,outer_connector):
        if self.__state == self.State.CONNECTING:
            self.__connector.refresh_con_state()
            if self.__connector.con_state == connector.CON_STATE.CON_CONNECTED:
                self.__data_handler.inner_connected(self.__id,self.__inner_ip,self.__inner_port,outer_connector)
                self.__state = self.State.WORKING
                recever.change_event(self.__connector.get_fileno(),select.EPOLLIN)
                print 'inner worker:connect succed'
            elif self.__connector.con_state == connector.CON_STATE.CON_FAILED:
                self.__connector.close()
                self.__state = self.State.CLOSED
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


        elif self.__state == self.State.CLOSED:
            #send closed message to outer
            self.__data_handler.inner_closed(self.__id,self.__inner_ip,self.__inner_port,outer_connector)
            recever.del_receiver(self.__connector.get_fileno())
            self.__state = self.State.DONE

    def __handle_working_event(self, event,outer_connector):
        error_happen = False
        if event & select.EPOLLIN:
            recv_msg = self.__connector.recv()
            if len(recv_msg) > 0:
                # trans data
                self.__data_handler.tarns_data(self.__id,self.__inner_ip,self.__inner_port,bytearray(recv_msg),outer_connector)

            else:
                if self.__connector.con_state != connector.CON_STATE.CON_CONNECTED:
                    error_happen = True

        elif event & select.EPOLLHUP:
            error_happen = True

        if error_happen:
            self.__connector.close()
            self.__state = self.State.CLOSED