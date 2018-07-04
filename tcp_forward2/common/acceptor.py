import socket

class Acceptor(object):
    def __init__(self,ip,port):
        self.__ip = ip
        self.__port = port
        self.__init()

    def __init(self):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind((self.__ip, self.__port))
        self.__socket.listen(1)
        self.__socket.setblocking(0)

    def get_fileno(self):
        return self.__socket.fileno()

    def get_listen_port(self):
        return self.__port

    def accept(self):
        return self.__socket.accept()

    def close(self):
        self.__socket.close()

class PortMapperAcceptor(Acceptor):
    def __init__(self,ip,port,mapper_ip,mapper_port,mapper_tag):
        super(PortMapperAcceptor,self).__init__(ip,port)
        self.mapper_ip = mapper_ip
        self.mapper_port = mapper_port
        self.mapper_tag = mapper_tag
