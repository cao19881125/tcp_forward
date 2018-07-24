import random
import select
import inner_worker
import outer_worker
from common import forward_event
from common import connector

class WorkerManager(object):
    def __init__(self,epoll_recver):
        self.__mapper = {}
        self.__outer_workers = {}
        self.__inner_workers = {}
        self.__worker_id_to_port = {}
        self.__worker_id_seq = 0
        self.__epoll_recver = epoll_recver

    def generate_worker_id(self):
        self.__worker_id_seq += 1
        return self.__worker_id_seq

    def add_map(self,outer_worker_id,inner_worker_id):
        self.__mapper[outer_worker_id] = inner_worker_id

    def add_outer_worker(self,outer_socket,port,address,inner_ip,inner_port,inner_tag):
        _worker_id = self.generate_worker_id()
        _paired_inner_worker = self.get_inner_worker_by_tag(inner_tag)


        if not _paired_inner_worker :
            raise Exception('get inner worker by tag failed,tag is:' + str(inner_tag))
        _outer_worker = outer_worker.OuterWorker(_worker_id, inner_ip,inner_port, outer_socket,address,
                                                 self.__outer_to_inner_channel(_worker_id,_paired_inner_worker.get_worker_id()),
                                                 self.__connector_changed)

        self.add_map(_worker_id, _paired_inner_worker.get_worker_id())
        self.__outer_workers[_worker_id] = _outer_worker
        self.__worker_id_to_port[_worker_id] = port
        return _outer_worker

    def add_inner_worker(self,inner_socket,address):

        _worker_id = self.generate_worker_id()
        _inner_worker = inner_worker.InnerWorker(_worker_id, inner_socket, address,self.__inner_to_outer_channel(_worker_id),
                                                 self.__connector_changed)

        self.__inner_workers[_worker_id] = _inner_worker
        return _inner_worker

    def get_worker_by_id(self,worker_id):
        if self.__outer_workers.has_key(worker_id):
            return self.__outer_workers[worker_id]
        elif self.__inner_workers.has_key(worker_id):
            return self.__inner_workers[worker_id]
        else:
            return None

    def get_workers_by_port(self,port):
        workers = []
        for worker_id,o_port in self.__worker_id_to_port.items():
            if o_port == port:
                workers.append(self.__outer_workers[worker_id])
        return workers

    def get_inner_worker_by_random(self):
        if len(self.__inner_workers) <= 0:
            return None

        _random_num = int(random.random()*100)%len(self.__inner_workers)
        return [value for value in self.__inner_workers.values()][_random_num]

    def get_inner_worker_by_tag(self,tag):
        if len(self.__inner_workers) <= 0:
            return None
        for item in self.__inner_workers.values():
            if item.get_tag() == tag:
                return item
        return None

    def remove_outer_worker(self,worker_id):
        self.__outer_workers.pop(worker_id)
        if self.__mapper.has_key(worker_id):
            self.__mapper.pop(worker_id)
        self.__worker_id_to_port.pop(worker_id)

    def remove_inner_worker(self,worker_id):
        self.__inner_workers.pop(worker_id)
        for key,value in self.__mapper.items():
            if value == worker_id:
                self.__mapper.pop(key)
    def all_worker_do(self):
        scheduler_event = forward_event.SchedulerEvent()
        for id,worker in self.__inner_workers.items():
            if worker.has_done():
                self.remove_inner_worker(id)
                continue
            worker.handler_event(scheduler_event)

        for id,worker in self.__outer_workers.items():
            if worker.has_done():
                self.remove_outer_worker(id)
                continue
            worker.handler_event(scheduler_event)

    def get_inner_worker_info(self,worker_id = None):
        info = {}
        if worker_id:
            if self.__inner_workers.has_key(worker_id):
                info[worker_id] = self.__inner_workers[worker_id].get_worker_static_info()
        else:
            for id,worker in self.__inner_workers.items():
                info[id] = worker.get_worker_static_info()
        return info

    def get_outer_worker_info(self,worker_id):
        info = {}
        if self.__outer_workers.has_key(worker_id):
            info[worker_id] = self.__outer_workers[worker_id].get_worker_static_info()
        return info

    def close_outer_worker(self,worker_id):
        if not self.__outer_workers.has_key(worker_id):
            raise Exception('can not find this worker:' + str(worker_id))

        close_event = forward_event.CloseConEvent(worker_id)
        self.__outer_workers[worker_id].handler_event(close_event)

    def close_inner_worker(self,worker_id):
        if not self.__inner_workers.has_key(worker_id):
            raise Exception('can not find this worker:' + str(worker_id))
        close_event = forward_event.CloseConEvent(worker_id)
        self.__inner_workers[worker_id].handler_event(close_event)


    def __connector_changed(self,con,event_handler):
        if con.con_state == connector.CON_STATE.CON_CONNECTED:
            self.__epoll_recver.add_receiver(con.get_fileno(), select.EPOLLIN,event_handler)
        elif con.con_state == connector.CON_STATE.CON_CONNECTING:
            self.__epoll_recver.add_receiver(con.get_fileno(), select.EPOLLOUT,event_handler)
        elif con.con_state == connector.CON_STATE.CON_CLOSED:
            self.__epoll_recver.del_receiver(con.get_fileno())

    def __inner_to_outer_channel(self,inner_worker_id):
        def channel(event):
            if event.event_type == forward_event.TRANSDATAEVENT:
                if not self.__mapper.has_key(event.forward_id) or self.__mapper[event.forward_id] != inner_worker_id:
                    return
                if not self.__outer_workers.has_key(event.forward_id):
                    return
                self.__outer_workers[event.forward_id].handler_event(event)
            elif event.event_type == forward_event.CLOSECONEVENT:
                if event.forward_id == inner_worker_id:
                    # innerworker closed,close all associated outerworker
                    for outer_id,inner_id in self.__mapper.items():
                        if inner_id != inner_worker_id:
                            continue
                        if not self.__outer_workers.has_key(outer_id):
                            continue
                        self.__outer_workers[outer_id].handler_event(event)
                else:
                    # just close one outer worker
                    if not self.__outer_workers.has_key(event.forward_id):
                        return
                    self.__outer_workers[event.forward_id].handler_event(event)
        return channel

    def __outer_to_inner_channel(self,outer_worker_id,inner_worker_id):
        def channel(event):
            if self.__inner_workers.has_key(inner_worker_id):
                self.__inner_workers[inner_worker_id].handler_event(event)
        return channel