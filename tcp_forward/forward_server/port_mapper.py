import sys
import os
import pyinotify
import ConfigParser

class PortMapper(pyinotify.ProcessEvent):
    class Coninfo(object):
        def __init__(self,ip,port):
            self.ip = ip
            self.port = port

    def __init__(self,map_file_path,call_back):
        # map out port to inner port,like:{1234:Coninfo('192.168.1.5',1234)}
        #self.__port_to_info = {1234:self.Coninfo('192.168.184.128',4321)}
        #self.__port_to_info = {1234:self.Coninfo('127.0.0.1',2222)}
        #self.__port_to_info = {1234:self.Coninfo('127.0.0.1',80),
        #                       1235:self.Coninfo('127.0.0.1',22),
        #                       1236: self.Coninfo('127.0.0.1',4321)}


        # map fileno to out port,like:{4:1234}
        self.__fileno_to_port = {}

        self.__map_file_path = map_file_path
        self.__callback = call_back
        self.__wm = pyinotify.WatchManager()
        self.__notifier = pyinotify.Notifier(self.__wm,self)
        self.__wm.add_watch(os.path.dirname(map_file_path), pyinotify.IN_MODIFY)
        self.__refresh_port_info()
        #self.__wm.watch_transient_file(map_file_path, pyinotify.IN_MODIFY, ProcessTransientFile)

    def __refresh_port_info(self):
        cf = ConfigParser.ConfigParser()
        temp_info = {}
        try:
            cf.readfp(open(self.__map_file_path, 'rb'))
            mappers = cf.items('MAPPER')
            for item in mappers:
                outer_port = int(item[0].lstrip().rstrip())
                inner_info = item[1].lstrip().rstrip().split(':')
                inner_ip = inner_info[0].lstrip().rstrip()
                inner_port = int(inner_info[1].lstrip().rstrip())
                temp_info[outer_port] = self.Coninfo(inner_ip,inner_port)
        except Exception,e:
            print e
            raise e
        self.__port_to_info = temp_info


    def watch_event(self,time_out_ms):
        try:
            self.__notifier.process_events()
            if self.__notifier.check_events(time_out_ms):
                self.__notifier.read_events()
                return True
            else:
                return False
        except Exception,e:
            print 'process_events exception'


    def process_IN_MODIFY(self, event):
        mod_file = os.path.join(event.path, event.name)
        if mod_file == self.__map_file_path:
            print  "Modify file: %s " % os.path.join(event.path, event.name)
            self.__refresh_port_info()
            self.__callback()

    def add_fileno_to_port(self,fileno,port):
        self.__fileno_to_port[fileno] = port

    def del_fileno_to_port(self,fileno):
        if self.__fileno_to_port.has_key(fileno):
            self.__fileno_to_port.pop(fileno)

    def get_outer_ports(self):
        return [port for port in self.__port_to_info]

    def get_inner_info_by_fileno(self,fileno):
        if not self.__fileno_to_port.has_key(fileno):
            return None,None

        out_port = self.__fileno_to_port[fileno]

        if not self.__port_to_info.has_key(out_port):
            return None,None

        return self.__port_to_info[out_port].ip,self.__port_to_info[out_port].port

    def get_inner_info_by_out_port(self,out_port):
        if self.__port_to_info.has_key(out_port):
            return self.__port_to_info[out_port].ip,self.__port_to_info[out_port].port
        else:
            return None,None