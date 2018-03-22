import socket,select
import errno


class Epoll_receiver(object):
    def __init__(self):
        self.__recv_fds = {}
        self.__epoll = select.epoll()

    def add_receiver(self,fd,events):
        self.__recv_fds[fd] = events
        self.__epoll.register(fd, events)

    def change_event(self,fd,events):
        if self.__recv_fds.has_key(fd):
            self.__epoll.unregister(fd)
            self.__epoll.register(fd,events)

    def del_receiver(self,fd):
        if self.__recv_fds.has_key(fd):
            self.__recv_fds.pop(fd)
            self.__epoll.unregister(fd)

    def run(self):
        return self.__epoll.poll(1)