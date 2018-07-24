import os
import sys
from oslo_config import cfg

PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import select
import logging
import traceback
from logging.handlers import RotatingFileHandler
from common import epoll_recever
from common import acceptor
import conf
import worker_manager

logger = logging.getLogger('my_logger')

ID = 1
def run():
    recver = epoll_recever.Epoll_receiver()

    outer_ip = cfg.CONF.SERVER_IP
    outer_port = cfg.CONF.SERVER_PORT

    logger.info("Outer ip:%s:%d" % (outer_ip, outer_port))
    global ID
    logger.info(str(ID))
    ID = ID +1

    _worker_manager = worker_manager.WorkerManager(recver)
    _worker_manager.add_outer_worker(outer_ip,outer_port)

    while True:
        _worker_manager.all_do()
        recver.run()


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


def main():
    conf.register_core_common_config_opts(cfg.CONF)

    log_config(cfg.CONF.LOG_LEVEL)

    logger.info("Process start!")
    run()


if __name__ == '__main__':
    cfg.CONF(sys.argv[1:])
    sys.exit(main())