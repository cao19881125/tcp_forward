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
import port_mapper
import conf
import worker_manager
from rest_api import info_collection

logger = logging.getLogger('my_logger')

port_mapper_changed = False


def run():
    recver = epoll_recever.Epoll_receiver()

    inner_port = int(cfg.CONF.INNER_PORT)
    inner_acceptor = acceptor.Acceptor('0.0.0.0', inner_port)
    logger.info('Inner port listen:' + str(inner_port))

    out_acceptors = {}

    # there are many outer acceptor





    def build_outer_acceptors2(new_ports = [],deld_ports = [],changed_ports = []):
        for port in deld_ports+changed_ports:
            recver.del_receiver(out_acceptors[port].get_fileno())
            out_acceptors[port].close()
            out_acceptors.pop(port)
            logger.info("Out port deled:" + str(port))

        for port in new_ports+changed_ports:
            _inner_ip, _inner_port, _inner_tag = _port_mapper.get_inner_info_by_out_port(port)
            _outer_acceptor = acceptor.PortMapperAcceptor('0.0.0.0', port, _inner_ip, _inner_port, _inner_tag)
            recver.add_receiver(_outer_acceptor.get_fileno(), select.EPOLLIN,
                                outer_acceptor_handler_event(_outer_acceptor))
            out_acceptors[port] = _outer_acceptor
            logger.info("Out port listen:" + str(port) + '->' + str((_inner_ip, _inner_port, _inner_tag)))

    def inner_acceptor_handler_event(event):
        _inner_socket, address = inner_acceptor.accept()
        _inner_socket.setblocking(0)
        _inner_worker = _worker_manager.add_inner_worker(_inner_socket,address)

        recver.add_receiver(_inner_socket.fileno(), select.EPOLLIN,_inner_worker.handler_event)
        logger.info('inner worker accept fileno:' + str(_inner_socket.fileno()))

    def outer_acceptor_handler_event(acceptor):
        def handler(event):
            _outer_socket, address = acceptor.accept()
            _outer_socket.setblocking(0)
            try:
                _outer_worker = _worker_manager.add_outer_worker(_outer_socket,acceptor.get_listen_port(),
                                                                 address,acceptor.mapper_ip,acceptor.mapper_port,
                                                                 acceptor.mapper_tag)
                recver.add_receiver(_outer_socket.fileno(), select.EPOLLIN,_outer_worker.handler_event)
                logger.info("Outer socket accept, worker_id:%d fileno:%d to inner port:%s:%d" %
                            (_outer_worker.get_worker_id(), _outer_socket.fileno(), acceptor.mapper_ip, acceptor.mapper_port))
            except Exception,e:
                _outer_socket.close()
                logger.error(e.message)
                logger.debug(traceback.format_exc())
        return handler

    def port_mapper_change_callback(new_ports = [],deld_ports = [],changed_ports = []):
        build_outer_acceptors2(new_ports,deld_ports,changed_ports)

    _worker_manager = worker_manager.WorkerManager(recver)

    #_port_mapper = port_mapper.FileMonitorPortMapper(cfg.CONF.OUTER_PORTS_FILE, build_outer_acceptors2)
    _port_mapper = port_mapper.InterfaceDriverPortMapper(cfg.CONF.OUTER_PORTS_FILE, build_outer_acceptors2)

    recver.add_receiver(inner_acceptor.get_fileno(), select.EPOLLIN, inner_acceptor_handler_event)

    build_outer_acceptors2(new_ports=_port_mapper.get_outer_ports())

    info_collection.InfoCollection.get_instance().set_port_mapper(_port_mapper)
    info_collection.InfoCollection.get_instance().set_worker_manager(_worker_manager)

    while True:
        #_port_mapper.watch_event(0.1)
        _worker_manager.all_worker_do()
        recver.run()

def log_config(level):
    if not os.path.isdir('/var/log/tcp_forward'):
        os.makedirs('/var/log/tcp_forward')
    logger.setLevel(logging._levelNames[level])
    handler = RotatingFileHandler("/var/log/tcp_forward/forward_server.log", maxBytes=10000000, backupCount=10)
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s %(filename)s:%(lineno)s %(funcName)s [-] %(message)s ')
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