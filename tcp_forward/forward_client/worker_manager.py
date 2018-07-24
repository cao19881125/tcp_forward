import outer_worker
import inner_worker
import select
from common import connector
from common import forward_event
from common import forward_data

class WorkerManager(object):
    def __init__(self,epoll_recver):
        self.__inner_map = {}
        self.__epoll_recver = epoll_recver

    def add_outer_worker(self,outer_ip, outer_port):
        self.__outer_worker = outer_worker.OuterWorker(outer_ip,outer_port,self.__outer_to_inner_channel(),self.__connector_changed)
        return self.__outer_worker

    def add_inner_worker(self,forward_id,inner_ip,inner_port):
        #forward_id = worker.get_forward_id()
        worker = inner_worker.InnerWorker(forward_id,inner_ip,inner_port,self.__inner_to_outer_channel(forward_id),self.__connector_changed)
        self.__inner_map[forward_id] = worker
        return worker

    def del_inner_worker(self,forward_id):
        self.__inner_map.pop(forward_id)

    def get_worker(self,forward_id):
        if self.__inner_map.has_key(forward_id):
            return self.__inner_map[forward_id]
        else:
            return None

    def all_do(self):
        scheduler_event = forward_event.SchedulerEvent()
        self.__outer_worker.handler_event(scheduler_event)
        for key,value in self.__inner_map.items():
            if value.has_done():
                self.__inner_map.pop(key)
                continue
            value.handler_event(scheduler_event)



    def __connector_changed(self,con,event_handler):
        if con.con_state == connector.CON_STATE.CON_CONNECTED:
            self.__epoll_recver.add_receiver(con.get_fileno(), select.EPOLLIN,event_handler)
        elif con.con_state == connector.CON_STATE.CON_CONNECTING:
            self.__epoll_recver.add_receiver(con.get_fileno(), select.EPOLLOUT,event_handler)
        elif con.con_state == connector.CON_STATE.CON_CLOSED:
            self.__epoll_recver.del_receiver(con.get_fileno())

    def close_all(self):
        for key, value in self.__inner_map.items():
            value.close()

    def __outer_to_inner_channel(self):
        def channel(event):
            if event.event_type == forward_event.TRANSDATAEVENT and \
                event.forward_data.data_type == forward_data.DATA_TYPE.NEW_CONNECTION:
                    self.add_inner_worker(event.forward_data.id,event.forward_data.inner_ip,event.forward_data.inner_port)
            elif event.event_type in (forward_event.TRANSDATAEVENT,forward_event.CLOSECONEVENT):
                if self.__inner_map.has_key(event.forward_id):
                    self.__inner_map[event.forward_id].handler_event(event)

        return channel

    def __inner_to_outer_channel(self,forward_id):
        def channel(event):
            if self.__outer_worker:
                self.__outer_worker.handler_event(event)
        return channel