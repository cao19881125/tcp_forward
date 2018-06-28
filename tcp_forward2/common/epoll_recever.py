import socket,select
import errno

EVENT_TYPE = 'EVENT_TYPE'
EVENT_HANDLER = 'EVENT_HANDLER'
class Epoll_receiver(object):



    def __init__(self):
        self.__recv_fds = {}
        self.__epoll = select.epoll()

    def add_receiver(self,fd,events,event_handler):
        self.__recv_fds[fd] = {
            EVENT_TYPE:events,
            EVENT_HANDLER:event_handler
        }
        self.__epoll.register(fd, events)

    def change_event(self,fd,events):
        if self.__recv_fds.has_key(fd):
            self.__epoll.unregister(fd)
            self.__epoll.register(fd,events)
            self.__recv_fds[fd][EVENT_TYPE] = events

    def del_receiver(self,fd):
        if self.__recv_fds.has_key(fd):
            self.__recv_fds.pop(fd)
            self.__epoll.unregister(fd)

    def run(self):
        events = self.__epoll.poll(1)
        for fileno, event in events:
            if not self.__recv_fds.has_key(fileno):
                continue


            self.__recv_fds[fileno][EVENT_HANDLER](event)

