from oslo_config import cfg
from common import forward_data, protocol_handler
from common import connector
from common.data_handler import DataHandler
import logging
logger = logging.getLogger('my_logger')

class OuterDataHandler(DataHandler):
    def __init__(self):
        self.__one_package_size = 2**31

    def send_preworking_reply(self,outer_connector):
        tag = cfg.CONF.TAG
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.PRE_WORKING, 0, '0.0.0.0', 0, tag)
        protocol_parser = protocol_handler.ProtocolHandler()
        send_package = protocol_parser.build_data(forw_data)
        outer_connector.send(send_package)

    def inner_connect_succed(self, forward_id, inner_ip, inner_port, outer_connector):
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.CONNECTION_SUCCESS, forward_id, inner_ip, inner_port)
        protocol_parser = protocol_handler.ProtocolHandler()
        send_package = protocol_parser.build_data(forw_data)
        outer_connector.send(send_package)

    def close_connection(self,forward_id,inner_ip,inner_port,outer_connector):
        _protocol_handler = protocol_handler.ProtocolHandler()
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.CLOSE_CONNECTION, forward_id,
                                             inner_ip, inner_port, '')
        send_package = _protocol_handler.build_data(forw_data)
        send_bytes = outer_connector.send(send_package)
        if send_bytes <= 0:
            logger.error("CloseConnectionData send failed,forward_id:%d inner_ip:%s inner_port:%d" % (forward_id, inner_ip, inner_port))

    def trans_data(self,forward_id,inner_ip,inner_port,data,outer_connector):
        ori = 0
        total_len = len(data)

        while ori < total_len:
            if total_len - ori <= self.__one_package_size:
                send_data = data[ori:total_len]
            else:
                send_data = data[ori:ori + self.__one_package_size]

            _protocol_handler = protocol_handler.ProtocolHandler()
            forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, forward_id,
                                                 inner_ip, inner_port, send_data)
            send_package = _protocol_handler.build_data(forw_data)
            if outer_connector and outer_connector.con_state == connector.CON_STATE.CON_CONNECTED:
                send_bytes = outer_connector.send(send_package)
                if send_bytes <= 0:
                    logger.error("TransData to inner send failed,forward_id:%d inner_ip:%s inner_port:%d" % (
                    forward_id, inner_ip, inner_port))
                    raise Exception("Send data failed")
                    # print 'inner_connector send package'
                    # tools.print_hex_buf(send_package)
            ori += self.__one_package_size

class InnerDataHandler(DataHandler):
    pass