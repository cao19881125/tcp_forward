#!/usr/bin/env python
import sys
import thread
import socket,select
import errno
import time
import argparse

def send_data(_connector):
    buf_len = 1024*1024
    buf = bytearray(buf_len)
    buf[0] = 0xAA
    buf[buf_len - 1] = 0xAA
    for i in range(10):
        _connector.send(buf)


def recv_data(epoll,_connector):
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == _connector.fileno():
                error_happen = False
                try:
                    recv_mes = _connector.recv(10240)
                    if len(recv_mes) == 0:
                        error_happen = True
                    else:
                        #print ' '.join(['0x%.2x' % x for x in bytearray(recv_mes)])
                        print 'recv ' + str(len(recv_mes)) + ' messages'
                except socket.error, e:
                    err = e.args[0]
                    if err is not errno.EAGAIN:
                        error_happen = True
                if error_happen:
                    print 'connection closed'
                    _connector.close()
                    return 1

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--listen", help="listen", action="store_true")
    parser.add_argument("-p", "--port", type=int, help="port")
    parser.add_argument("-H", "--host", help="remote host")

    args = parser.parse_args()

    _connector = None
    if args.listen:
        if not args.port:
            print 'server mode must give port'
            return 1

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('0.0.0.0', args.port))
        serversocket.listen(1)
        _connector,address = serversocket.accept()
        _connector.setblocking(0)
        print 'accept connection:' + str(_connector.fileno())
    else:
        if not args.host or not args.port:
            print 'client mode must give host and port'
            return 1
        _connector = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        _connector.connect((args.host, args.port))
        print 'connect success'




    epoll = select.epoll()
    epoll.register(_connector.fileno(), select.EPOLLIN)


    if args.listen:
        recv_data(epoll,_connector)
    else:
        send_data(_connector)






if __name__=='__main__':
    sys.exit(main())