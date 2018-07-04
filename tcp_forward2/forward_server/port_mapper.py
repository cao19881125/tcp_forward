import sys
import os
import pyinotify
import ConfigParser

# PortMapper save the relationship between server's out port and client's inner network's ip:port
# PortMapper parse the mapper file to get these relationships
# PortMapper monitor the mapper file,if the mapper file changed when server process running,PortMapper can received
# a notify event,PortMapper refresh the new relationship immediately

class PortMapper(pyinotify.ProcessEvent):
    class Coninfo(object):
        def __init__(self,ip,port,tag='default'):
            self.ip = ip
            self.port = port
            self.tag = tag
        def __eq__(self, other):
            return self.ip == other.ip and self.port == other.port and self.tag == other.tag

        def __ne__(self, other):
            return not self.__eq__(other)

    def __init__(self,map_file_path):
        # map out port to inner port,like:{1234:Coninfo('192.168.1.5',1234)}
        #self._port_to_info = {1234:self.Coninfo('192.168.184.128',4321)}
        #self._port_to_info = {1234:self.Coninfo('127.0.0.1',2222)}
        #self._port_to_info = {1234:self.Coninfo('127.0.0.1',80),
        #                       1235:self.Coninfo('127.0.0.1',22),
        #                       1236: self.Coninfo('127.0.0.1',4321)}

        self._map_file_path = map_file_path
        self._port_to_info = {}
        self._refresh_port_info()

    def _refresh_port_info(self):
        cf = ConfigParser.ConfigParser()
        temp_info = {}
        try:
            cf.readfp(open(self._map_file_path, 'rb'))
            mappers = cf.items('MAPPER')
            for item in mappers:
                outer_port = int(item[0].lstrip().rstrip())
                inner_info = item[1].lstrip().rstrip().split(':')
                inner_ip = inner_info[0].lstrip().rstrip()
                inner_port = int(inner_info[1].lstrip().rstrip())
                temp_info[outer_port] = self.Coninfo(inner_ip,inner_port)

            tags = cf.items('TAG')
            for item in tags:
                outer_port = int(item[0].lstrip().rstrip())
                tag = item[1].lstrip().rstrip()
                if temp_info.has_key(outer_port):
                    temp_info[outer_port].tag = tag
        except Exception,e:
            print e
            raise e

        new_ports = [port for port in set(temp_info.keys()) - set(self._port_to_info.keys())]
        deld_ports = [port for port in set(self._port_to_info.keys()) - set(temp_info.keys())]
        changed_ports = []

        for port in set(self._port_to_info.keys()) - set(deld_ports):
            if self._port_to_info[port] != temp_info[port]:
                changed_ports.append(port)

        self._port_to_info = temp_info
        return new_ports,deld_ports,changed_ports

    def flush_to_file(self):
        cf = ConfigParser.ConfigParser()
        cf.add_section('MAPPER')
        cf.add_section('TAG')
        try:
            for port,info in self._port_to_info.items():
                cf.set('MAPPER',str(port),"%s:%d"%(info.ip,info.port))
                cf.set('TAG',str(port),info.tag)

            cf.write(open(self._map_file_path,'w'))
        except Exception,e:
            raise e

    def get_outer_ports(self):
        return [port for port in self._port_to_info]

    def get_port_info(self,port):
        if self._port_to_info.has_key(port):
            return self._port_to_info[port]
        else:
            return None

    def get_inner_info_by_out_port(self,out_port):
        if self._port_to_info.has_key(out_port):
            return self._port_to_info[out_port].ip,self._port_to_info[out_port].port,self._port_to_info[out_port].tag
        else:
            return None,None,None

class FileMonitorPortMapper(PortMapper):
    def __init__(self,map_file_path,call_back):
        super(FileMonitorPortMapper,self).__init__(map_file_path)
        self.__callback = call_back
        self.__wm = pyinotify.WatchManager()
        self.__notifier = pyinotify.Notifier(self.__wm,self)
        self.__wm.add_watch(os.path.dirname(map_file_path), pyinotify.IN_MODIFY)

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
            print e.message

    def process_IN_MODIFY(self, event):
        mod_file = os.path.join(event.path, event.name)
        if mod_file == self._map_file_path:
            print  "Modify file: %s " % os.path.join(event.path, event.name)
            new_ports,deld_ports,changed_ports = self._refresh_port_info()

            self.__callback(new_ports, deld_ports, changed_ports)

class InterfaceDriverPortMapper(PortMapper):
    def __init__(self, map_file_path, call_back):
        super(InterfaceDriverPortMapper,self).__init__(map_file_path)
        self.__callback = call_back
        
    def create_new_port(self,port,mapper_ip,mapper_port,mapper_tag):
        if self._port_to_info.has_key(port):
            raise Exception('Create port mapper failed,port:' + str(port) + ' already exists')

        self._port_to_info[port] = self.Coninfo(mapper_ip,mapper_port,mapper_tag)

        self.__callback(new_ports = [port])

        self.flush_to_file()

    def delete_port(self,port):
        if not self._port_to_info.has_key(port):
            raise Exception('Port:' + str(port) + ' not exists')

        self._port_to_info.pop(port)

        self.__callback(deld_ports = [port])

        self.flush_to_file()
