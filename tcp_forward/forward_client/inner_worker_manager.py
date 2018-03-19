

class InnerWorkerManager(object):
    def __init__(self):
        self.__inner_map = {}


    def add_worker(self,worker):
        forward_id = worker.get_forward_id()
        self.__inner_map[forward_id] = worker

    def del_worker(self,forward_id):
        self.__inner_map.pop(forward_id)

    def get_worker(self,forward_id):
        if self.__inner_map.has_key(forward_id):
            return self.__inner_map[forward_id]
        else:
            return None

    def all_do(self,recever,outer_connector):
        for key,value in self.__inner_map.items():
            if value.has_done():
                self.__inner_map.pop(key)
                continue
            value.do_work(recever,outer_connector)

    def get_worker_by_fileno(self,fileno):
        for value in self.__inner_map.values():
            if value.get_fileno() == fileno:
                return value

        return None

    def close_all(self):
        for key, value in self.__inner_map.items():
            value.close()