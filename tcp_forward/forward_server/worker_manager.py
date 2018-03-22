import random
import inner_worker
import outer_worker

class WorkerManager(object):
    def __init__(self):
        self.__mapper = {}
        self.__outer_workers = {}
        self.__inner_workers = {}
        self.__worker_id_seq = 0

    def generate_worker_id(self):
        self.__worker_id_seq += 1
        return self.__worker_id_seq

    def add_map(self,outer_worker_id,inner_worker_id):
        self.__mapper[outer_worker_id] = inner_worker_id

    def get_pair_inner_worker(self,outer_worker_id):
        if self.__mapper.has_key(outer_worker_id) and \
                self.__inner_workers.has_key(self.__mapper[outer_worker_id]):
            return self.__inner_workers[self.__mapper[outer_worker_id]]
        else:
            return None

    def add_outer_worker(self,outer_socket,inner_ip,inner_port):
        _worker_id = self.generate_worker_id()
        _paired_inner_worker = self.get_inner_worker_by_random()


        if not _paired_inner_worker :
            raise Exception('')
        _outer_worker = outer_worker.OuterWorker(_worker_id, inner_ip, inner_port, outer_socket)

        self.add_map(_worker_id, _paired_inner_worker.get_worker_id())
        self.__outer_workers[_worker_id] = _outer_worker
        return _outer_worker

    def add_inner_worker(self,inner_socket):

        _worker_id = self.generate_worker_id()
        _inner_worker = inner_worker.InnerWorker(_worker_id, inner_socket)

        self.__inner_workers[_worker_id] = _inner_worker

    def get_worker_by_id(self,worker_id):
        if self.__outer_workers.has_key(worker_id):
            return self.__outer_workers[worker_id]
        elif self.__inner_workers.has_key(worker_id):
            return self.__inner_workers[worker_id]
        else:
            return None

    def get_outer_worker_by_fileno(self,fileno):
        for worker in self.__outer_workers.values():
            if worker.get_fileno() == fileno:
                return worker
        return None

    def get_inner_worker_by_fileno(self,fileno):
        for worker in self.__inner_workers.values():
            if worker.get_fileno() == fileno:
                return worker
        return None

    def get_outer_workers_by_inner_worker_id(self,inner_id):
        result_workers = []
        for key,value in self.__mapper.items():
            if value == inner_id:
                if self.__outer_workers.has_key(key):
                    result_workers.append(self.__outer_workers[key])
        return result_workers

    def get_inner_worker_by_random(self):
        if len(self.__inner_workers) <= 0:
            return None

        _random_num = int(random.random()*100)%len(self.__inner_workers)
        return [value for value in self.__inner_workers.values()][_random_num]

    def remove_outer_worker(self,worker_id):
        self.__outer_workers.pop(worker_id)
        if self.__mapper.has_key(worker_id):
            self.__mapper.pop(worker_id)

    def remove_inner_worker(self,worker_id):
        self.__inner_workers.pop(worker_id)
        for key,value in self.__mapper.items():
            if value == worker_id:
                self.__mapper.pop(key)
    def all_worker_do(self):
        for id,worker in self.__inner_workers.items():
            if worker.has_done():
                self.remove_inner_worker(id)
                continue
            worker.do_work(self)

        for id,worker in self.__outer_workers.items():
            if worker.has_done():
                self.remove_outer_worker(id)
                continue
            _inner_worker = self.get_pair_inner_worker(worker.get_worker_id())
            if _inner_worker == None:
                worker.close()
                self.remove_outer_worker(id)
                continue
            worker.do_work(_inner_worker.get_connector())
