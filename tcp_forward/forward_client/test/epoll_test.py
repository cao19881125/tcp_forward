import sys
import socket,select
import errno

def main():
    serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serversocket.bind(('0.0.0.0', 12345))
    serversocket.listen(1)
    serversocket.setblocking(0)

    epoll = select.epoll()
    epoll.register(serversocket.fileno(), select.EPOLLIN)

    inner_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    connections = {}
    requests = {}
    responses = {}

    error_happen = False
    outer_connection = None
    while True:
        events = epoll.poll(1)
        error_happen = False
        for fileno,event in events:
            if fileno == serversocket.fileno():
                connection,address = serversocket.accept()
                print "accept connection:" + str(connection.fileno())
                connection.setblocking(0)
                epoll.register(connection.fileno(),select.EPOLLIN)
                #connections[connection.fileno()] = connection
                outer_connection = connection

                epoll.unregister(fileno)
                #connect to remote


                inner_connection.connect(('192.168.10.2', 22))
                inner_connection.setblocking(0)
                epoll.register(inner_connection.fileno(),select.EPOLLIN)

            elif event & select.EPOLLIN:
                try:

                    if fileno == outer_connection.fileno():
                        recv_mes = outer_connection.recv(1024)
                        inner_connection.send(recv_mes)
                    elif fileno == inner_connection.fileno():
                        recv_mes = inner_connection.recv(1024)
                        outer_connection.send(recv_mes)

                    '''
                    if len(recv_mes) == 0:
                        error_happen = True
                    else:
                        print 'recv '+ str(fileno) + ' message:' + recv_mes
                        if fileno == outer_connection.fileno():
                            inner_connection.send(recv_mes)
                        elif fileno == inner_connection.fileno():
                            outer_connection.send(recv_mes)
                    '''
                except socket.error,e:
                    err = e.args[0]
                    if err is not errno.EAGAIN:
                        error_happen = True

            elif event & select.EPOLLHUP:
                error_happen = True

            #if error_happen:
            #    print 'connection close:' + str(fileno)
            #    epoll.unregister(fileno)
            #    connections[fileno].close()
            #    del connections[fileno]


if __name__ == '__main__':
    sys.exit(main())