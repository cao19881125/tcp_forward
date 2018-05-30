import socket
import errno
from enum import Enum

class CON_STATE(Enum):
    CON_NONE = 0
    CON_CONNECTING = 1
    CON_CONNECTED = 2
    CON_FAILED = 3
    CON_CLOSED = 4


class Connector(object):

    def __init__(self,remote_socket):
        self._socket = remote_socket
        self.refresh_con_state()
        self._fileno = self._socket.fileno()

    def close(self):
        if self.con_state != CON_STATE.CON_CLOSED:
            self._socket.close()
            self.con_state == CON_STATE.CON_CLOSED

    def recv(self):
        if self.con_state != CON_STATE.CON_CONNECTED:
            return ''

        recv_msg = ''
        while True:
            try:
                recv_msg_temp = self._socket.recv(1024 * 1024)
                if len(recv_msg_temp) == 0:
                    # connect closed
                    self.con_state = CON_STATE.CON_CLOSED
                    return ''
                else:
                    recv_msg += recv_msg_temp
            except socket.error,e:
                err = e.args[0]
                if err is errno.EAGAIN:
                    #recv finished
                    return recv_msg
                else:
                    # connect closed
                    self._socket.close()
                    self.con_state = CON_STATE.CON_CLOSED
                    return ''

    def send(self,msg):
        try:
            self._socket.setblocking(1)
            send_bytes = self._socket.send(msg)
            self._socket.setblocking(0)
            return send_bytes
        except Exception,e:
            self._socket.close()
            self.con_state = CON_STATE.CON_CLOSED
            return 0

    def get_fileno(self):
        return self._fileno

    def refresh_con_state(self):
        ret = self._socket.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
        if ret == 0:
            self.con_state = CON_STATE.CON_CONNECTED
        else:
            self.con_state = CON_STATE.CON_FAILED


class ConnectorClient(Connector):
    def __init__(self,remote_ip,remote_port):
        self._remote_ip = remote_ip
        self._remote_port = remote_port
        self.con_state = CON_STATE.CON_NONE

    def connect(self):
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setblocking(0)
        self._fileno = self._socket.fileno()
        try:
            self._socket.connect((self._remote_ip, self._remote_port))
        except socket.error,e:
            if e.errno == errno.EINPROGRESS:
                self.con_state = CON_STATE.CON_CONNECTING
            else:
                self.con_state = CON_STATE.CON_FAILED
        else:
            self.con_state = CON_STATE.CON_CONNECTED

if __name__ == '__main__':
    import select
    epoll = select.epoll()

    con1 = Connector('127.0.0.1',1234)
    con2 = Connector('127.0.0.1',1235)


    con1.connect()
    con2.connect()

    epoll.register(con1.get_fileno(), select.EPOLLIN)
    epoll.register(con2.get_fileno(), select.EPOLLIN)

    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            if fileno == con1.get_fileno():
                if con1.con_state == CON_STATE.CON_CONNECTING:
                    con1.refresh_con_state()
                elif con1.con_state == CON_STATE.CON_CONNECTED:
                    recv_msg = con1.recv()
                    con2.send(recv_msg)
            elif fileno == con2.get_fileno():
                if con2.con_state == CON_STATE.CON_CONNECTING:
                    con2.refresh_con_state()
                elif con2.con_state == CON_STATE.CON_CONNECTED:
                    recv_msg = con2.recv()
                    con1.send(recv_msg)
