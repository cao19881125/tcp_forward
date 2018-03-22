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
import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
logger = logging.getLogger('my_logger')

def log_config(level):
    if not os.path.isdir('/var/log/tcp_forward'):
        os.makedirs('/var/log/tcp_forward')
    logger.setLevel(logging._levelNames[level])
    handler = RotatingFileHandler("/var/log/tcp_forward/forward_client.log", maxBytes=10000000, backupCount=10)
    console = logging.StreamHandler()
    formatter = logging.Formatter(
        '%(asctime)s %(process)d %(levelname)s %(filename)s:%(lineno)s %(funcName)s [-] %(message)s ')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(handler)
    logger.addHandler(console)

def main(cfg_file):
    cfg = ConfigParser.ConfigParser()
    cfg.readfp(open(cfg_file, 'rb'))
    log_config(cfg.get('DEFAULT','LOG_LEVEL'))
    logger.info("Process start!")

    outer_ip = cfg.get('DEFAULT','SERVER_IP')
    outer_port = int(cfg.get('DEFAULT','SERVER_PORT'))
    out_worker = outer_worker.OuterWorker(outer_ip, outer_port)
    recver = epoll_recever.Epoll_receiver()

    logger.info("Outer ip:%s:%d"%(outer_ip, outer_port))

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
                    logger.error("Can't get fileno:%d inner_worker,unregister it"%(fileno))
                    epoll_recever.del_receiver(fileno)



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    #parser.add_argument("server_ip", help="server ip")
    #parser.add_argument("server_port", help="server port")
    parser.add_argument("cfg_file", help="config file")

    args = parser.parse_args()

    sys.exit(main(args.cfg_file))