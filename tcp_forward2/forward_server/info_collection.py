

class InfoCollection(object):

    INSTANCE = None

    @classmethod
    def get_instance(cls):
        if not InfoCollection.INSTANCE:
            InfoCollection.INSTANCE = cls()
        return InfoCollection.INSTANCE

    def set_port_mapper(self,mapper):
        self.__port_mapper = mapper

    def get_port_mapper_str(self):
        ports = self.__port_mapper.get_outer_ports()

        result = {}
        for port in ports:
            ip,port,tag = self.__port_mapper.get_inner_info_by_out_port(port)
            result[port] = {"ip":ip,"port":port,"tag":tag}
        return str(result)