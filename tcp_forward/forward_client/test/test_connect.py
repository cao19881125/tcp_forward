import sys
import socket,select
import errno


def main():
    epoll = select.epoll()

    inner_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    inner_connection.setblocking(0)

    try:
        inner_connection.connect(('127.0.0.1', 1235))

    except socket.error,e:
        if e.errno == errno.EINPROGRESS:
            print 'connection in process'
        else:
            print 'connect failed'
    else:
        print 'connect success'


    epoll.register(inner_connection.fileno(), select.EPOLLIN | select.EPOLLOUT)

    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == inner_connection.fileno():
                if event & select.EPOLLOUT:
                    ret = inner_connection.getsockopt(socket.SOL_SOCKET,socket.SO_ERROR)
                    if ret == 0:
                        print 'success'
                        epoll.unregister(fileno)
                        epoll.register(fileno,select.EPOLLIN)
                    else:
                        print 'failed'


if __name__ == '__main__':
    sys.exit(main())


