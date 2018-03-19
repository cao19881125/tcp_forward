import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import inner_worker_manager
import outer_worker
from common import epoll_recever
import inner_worker
import argparse

def main(outer_ip,outer_port):
    out_worker = outer_worker.OuterWorker(outer_ip, outer_port)
    recver = epoll_recever.Epoll_receiver()

    __inner_worker_manager = inner_worker_manager.InnerWorkerManager()

    while True:
        out_worker.do_work(recver,__inner_worker_manager)
        __inner_worker_manager.all_do(recver,out_worker.get_connector())

        events = recver.run()
        for fileno, event in events:
            #print 'get event:' + str(fileno)
            if fileno == out_worker.get_fileno():
                out_worker.handle_event(recver,event)
            else:
                __inner_worker = __inner_worker_manager.get_worker_by_fileno(fileno)
                if __inner_worker != None:
                    __inner_worker.handle_event(recver,event,out_worker.get_connector())
                else:
                    print 'can not get fileno:%d inner_worker,unregister it'%(fileno)
                    epoll_recever.del_receiver(fileno)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("server_ip", help="server ip")
    parser.add_argument("server_port", help="server port")

    args = parser.parse_args()

    sys.exit(main(args.server_ip, int(args.server_port)))