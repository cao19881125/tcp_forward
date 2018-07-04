

class InfoCollection(object):

    INSTANCE = None

    @classmethod
    def get_instance(cls):
        if not InfoCollection.INSTANCE:
            InfoCollection.INSTANCE = cls()
        return InfoCollection.INSTANCE

    def set_port_mapper(self,mapper):
        self.__port_mapper = mapper

    def set_worker_manager(self,mamaner):
        self.__worker_manager = mamaner

    def get_port_mapper_str(self):
        ports = self.__port_mapper.get_outer_ports()

        result = {}
        for port in ports:
            ip,port,tag = self.__port_mapper.get_inner_info_by_out_port(port)
            result[port] = {"ip":ip,"port":port,"tag":tag}
        return str(result)

    def create_new_port(self,port,mapper_ip,mapper_port,mapper_tag):
        self.__port_mapper.create_new_port(port,mapper_ip,mapper_port,mapper_tag)

    def delete_port(self,port):
        self.__port_mapper.delete_port(port)

    def get_inner_worker_info(self,worker_id = None):
        return self.__worker_manager.get_inner_worker_info(worker_id)

    def get_outer_worker_info(self,worker_id):
        return self.__worker_manager.get_outer_worker_info(worker_id)

    def close_outer_worker(self,worker_id):
        return self.__worker_manager.close_outer_worker(worker_id)

    def close_inner_worker(self,worker_id):
        return self.__worker_manager.close_inner_worker(worker_id)

    def get_channel_info_by_port(self,port):

        if not port:
            ports = self.__port_mapper.get_outer_ports()
        else:
            ports = [port]

        result = {}
        for p in ports:

            workers = self.__worker_manager.get_workers_by_port(p)

            p_list = []
            for worker in workers:
                info = {}
                info['channel_id'] = worker.get_worker_id()
                address = worker.get_address()
                info['ip'] = address[0]
                info['port'] = address[1]
                info['state'] = worker.get_state_str()
                p_list.append(info)
                result[p] = p_list
        return result


