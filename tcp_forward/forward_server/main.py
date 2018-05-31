import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from common import epoll_recever
from common import acceptor
import socket,select
import port_mapper
import worker_manager
import inner_worker
import outer_worker
import argparse
import ConfigParser
import logging
from logging.handlers import RotatingFileHandler
from cfg_manager import CfgManager

port_mapper_changed = False

logger = logging.getLogger('my_logger')


def build_outer_acceptors(out_acceptors,_port_mapper,recver):
    out_ports = _port_mapper.get_outer_ports()
    for port in out_ports:
        _out_acceptor = acceptor.Acceptor('0.0.0.0',port)
        filno = _out_acceptor.get_fileno()
        out_acceptors[filno] = _out_acceptor
        _port_mapper.add_fileno_to_port(filno,port)
        recver.add_receiver(filno,select.EPOLLIN)
        logger.info("Out port listen:" + str(port) + '->' +  str(_port_mapper.get_inner_info_by_out_port(port)))


def port_mapper_change_callback():
    global port_mapper_changed
    port_mapper_changed = True


def run(cfg):
    recver = epoll_recever.Epoll_receiver()

    # just one inner acceptor
    inner_port = int(cfg.get('DEFAULT','INNER_PORT'))
    inner_acceptor = acceptor.Acceptor('0.0.0.0', inner_port)
    recver.add_receiver(inner_acceptor.get_fileno(), select.EPOLLIN)
    logger.info('Inner port listen:' + str(inner_port))

    # there are many outer acceptor
    _port_mapper = port_mapper.PortMapper(cfg.get('DEFAULT','OUTER_PORTS_FILE'), port_mapper_change_callback)

    _worker_manager = worker_manager.WorkerManager()
    out_acceptors = {}
    build_outer_acceptors(out_acceptors, _port_mapper, recver)

    global port_mapper_changed
    while True:
        _port_mapper.watch_event(10)

        if port_mapper_changed:
            for acc_fileno, acc in out_acceptors.items():
                recver.del_receiver(acc_fileno)
                _port_mapper.del_fileno_to_port(acc_fileno)
                acc.close()
            out_acceptors.clear()
            logger.info('Port mapper changed,clear current outport listeners,recreating')
            build_outer_acceptors(out_acceptors, _port_mapper, recver)
            port_mapper_changed = False

        _worker_manager.all_worker_do()
        events = recver.run()

        for fileno, event in events:
            if fileno == inner_acceptor.get_fileno():
                # recv inner connection
                _inner_socket, address = inner_acceptor.accept()
                _inner_socket.setblocking(0)
                _worker_manager.add_inner_worker(_inner_socket)
                recver.add_receiver(_inner_socket.fileno(), select.EPOLLIN)
                logger.info('Inner socket accept')

            elif out_acceptors.has_key(fileno):
                # recv outer connection
                _outer_socket, address = out_acceptors[fileno].accept()
                _outer_socket.setblocking(0)
                _inner_ip, _inner_port = _port_mapper.get_inner_info_by_fileno(fileno)
                if not _inner_ip or not _inner_port:
                    _outer_socket.close()
                    continue
                try:
                    _outer_worker = _worker_manager.add_outer_worker(_outer_socket, _inner_ip, _inner_port)
                    recver.add_receiver(_outer_socket.fileno(), select.EPOLLIN)
                    logger.info("Outer socket accept, worker_id:%d fileno:%d to inner port:%s:%d"%
                                (_outer_worker.get_worker_id(),_outer_socket.fileno(),_inner_ip,_inner_port))
                except Exception, e:
                    _outer_socket.close()
                    continue
            else:
                _inner_worker = _worker_manager.get_inner_worker_by_fileno(fileno)
                if _inner_worker:
                    _inner_worker.handle_event(event)
                    continue

                _out_worker = _worker_manager.get_outer_worker_by_fileno(fileno)
                if _out_worker:
                    _inner_worker = _worker_manager.get_pair_inner_worker(_out_worker.get_worker_id())
                    if _inner_worker == None:
                        logger.error("OuterWorker %d get paired InnerWorker failed,remove"%(_out_worker.get_worker_id()))
                        _out_worker.close()
                        _worker_manager.remove_outer_worker(_out_worker.get_worker_id())
                        continue

                    _out_worker.handle_event(event, _inner_worker.get_connector())
                    continue


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

def main(cfg_file):

    #cfg = ConfigParser.ConfigParser()
    #cfg.readfp(open(cfg_file, 'rb'))
    CfgManager.get_instance().register_file(cfg_file)
    cfg = CfgManager.get_instance().get_cfg()

    log_config(cfg.get('DEFAULT','LOG_LEVEL'))

    logger.info("Process start!")
    run(cfg)


if __name__=='__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("cfg_file", help="config file")

    args = parser.parse_args()

    sys.exit(main(args.cfg_file))