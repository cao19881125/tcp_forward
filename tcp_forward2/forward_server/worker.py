import flow_static
import time

class Worker(object):
    def __init__(self,worker_id,address,connector):
        self._worker_id = worker_id
        self._address = address
        self._connector = connector
        self._recv_flow_static = flow_static.FlowStatic()
        self._send_flow_static = flow_static.FlowStatic()

    def get_worker_id(self):
        return self._worker_id

    def get_address(self):
        return self._address

    def get_worker_static_info(self):
        info = {}
        local_time = time.localtime(self._recv_flow_static.get_init_time())
        info['init_time'] = "%d-%d-%d %d:%d:%d"%(local_time[0],local_time[1],local_time[2],
                                                 local_time[3],local_time[4],local_time[5])

        info['duration_time'] = int(time.time() - self._recv_flow_static.get_init_time())

        info['ip'] = self._address[0]
        info['port'] = self._address[1]


        info['recv_flow_statistics'] = self._recv_flow_static.get_total_flow()
        info['recv_real_time_speed'] = self._recv_flow_static.get_real_speed()
        info['recv_average_speed'] = self._recv_flow_static.get_average_speed()

        info['send_flow_statistics'] = self._send_flow_static.get_total_flow()
        info['send_real_time_speed'] = self._send_flow_static.get_real_speed()
        info['send_average_speed'] = self._send_flow_static.get_average_speed()

        return info