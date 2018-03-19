import sys
import socket,select
import errno


def main():
    inner_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    inner_connection.connect(('192.168.184.1', 1234))

    inner_connection.setblocking(0)
    inner_connection.send('hello')

    epoll = select.epoll()
    epoll.register(inner_connection.fileno(), select.EPOLLIN)


    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == inner_connection.fileno():
                while True:
                    try:
                        recv_mes = inner_connection.recv(2)
                        print recv_mes
                    except socket.error,e:
                        #errno.EAGAIN means recv finished
                        if e.args[0] is not errno.EAGAIN:
                            exit(1)
                        break


if __name__ == '__main__':
    sys.exit(main())