
from common.data_handler import DataHandler
from common.protocol_handler import ProtocolHandler
from common import forward_data
from common import connector
from common import tools
import logging
logger = logging.getLogger('my_logger')

class OutDataHandler(DataHandler):


    def create_connection(self,forward_id,inner_ip,inner_port,inner_connector):
        _protocol_handler = ProtocolHandler()
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.NEW_CONNECTION, forward_id,
                                             inner_ip, inner_port, '')
        send_package = _protocol_handler.build_data(forw_data)
        if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            send_bytes = inner_connector.send(send_package)
            if send_bytes <= 0:
                logger.error("CreateConnectionData send failed,forward_id:%d inner_ip:%s inner_port:%d" % (forward_id, inner_ip, inner_port))

    def trans_data(self,forward_id,inner_ip,inner_port,data,inner_connector):

        ori = 0
        total_len = len(data)
        while ori < total_len:
            if total_len - ori <= 2**31:
                send_data = data[ori:total_len]
            else:
                send_data = data[ori:ori + 2**31]

            _protocol_handler = ProtocolHandler()
            forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, forward_id,
                                                 inner_ip, inner_port, send_data)
            send_package = _protocol_handler.build_data(forw_data)
            if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
                send_bytes = inner_connector.send(send_package)
                if send_bytes <= 0:
                    logger.error("TransData to inner send failed,forward_id:%d inner_ip:%s inner_port:%d" % (forward_id, inner_ip, inner_port))
                    raise Exception("Send data failed")
                #print 'inner_connector send package'
                #tools.print_hex_buf(send_package)
            ori += 2**31


    def close_connection(self,forward_id,inner_ip,inner_port,inner_connector):
        _protocol_handler = ProtocolHandler()
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.CLOSE_CONNECTION, forward_id,
                                             inner_ip, inner_port, '')
        send_package = _protocol_handler.build_data(forw_data)
        if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            send_bytes = inner_connector.send(send_package)
            if send_bytes <= 0:
                logger.error("CloseConnectionData send failed,forward_id:%d inner_ip:%s inner_port:%d" % (forward_id, inner_ip, inner_port))

class InnerDataHandler(DataHandler):
    def handle_data(self, ring_buffer,worker_manager):
        while True:
            parsed_data = super(InnerDataHandler, self).parse_data(ring_buffer)
            if parsed_data == None:
                return

            if parsed_data.data_type == forward_data.DATA_TYPE.CONNECTION_SUCCESS:
                outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
                if outer_worker != None:
                    outer_worker.connecting_reply(True)
            elif parsed_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
                outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
                if outer_worker != None and outer_worker.is_working():
                    outer_worker.trans_data(parsed_data.data)
            elif parsed_data.data_type == forward_data.DATA_TYPE.CLOSE_CONNECTION:
                outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
                if outer_worker != None:
                    outer_worker.close()
            elif parsed_data.data_type == forward_data.DATA_TYPE.HEART_BEAT:
                logger.debug('Recv heartbeat')