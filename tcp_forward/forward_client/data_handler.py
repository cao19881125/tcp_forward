import inner_worker
from common import forward_data, protocol_handler
from common import connector
from common.data_handler import DataHandler
import logging
logger = logging.getLogger('my_logger')


class OuterDataHandler(DataHandler):
    def handle_data(self,ring_buffer,inner_worker_manager):
        while True:
            parsed_data = super(OuterDataHandler,self).parse_data(ring_buffer)

            if parsed_data == None:
                return

            if parsed_data.data_type == forward_data.DATA_TYPE.NEW_CONNECTION:
                __inner_worker = inner_worker.InnerWorker(parsed_data.id,parsed_data.inner_ip,parsed_data.inner_port)
                inner_worker_manager.add_worker(__inner_worker)
            elif parsed_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
                # get the connector for the data_id
                __inner_worker = inner_worker_manager.get_worker(parsed_data.id)
                if __inner_worker != None and __inner_worker.is_working():
                    __inner_worker.trans_data(parsed_data.data)
            elif parsed_data.data_type == forward_data.DATA_TYPE.CLOSE_CONNECTION:
                __inner_worker = inner_worker_manager.get_worker(parsed_data.id)
                if __inner_worker != None:
                    __inner_worker.close()

    def send_heart_beat(self,outer_connector):
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.HEART_BEAT, 0,'0.0.0.0', 0, '')
        protocol_parser = protocol_handler.ProtocolHandler()
        send_package = protocol_parser.build_data(forw_data)
        if outer_connector and outer_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            send_bytes = outer_connector.send(send_package)
            if send_bytes <= 0:
                logger.error("HeartBeat send failed")
                raise Exception("Send HeartBeat failed")
class InnerDataHandler(DataHandler):
    def tarns_data(self,forward_id,inner_ip,inner_port,data,outer_connector):

        ori = 0
        total_len = len(data)
        while ori < total_len:
            if total_len - ori <= 2**31:
                send_data = data[ori:total_len]
            else:
                send_data = data[ori:ori+2**31]

            forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, forward_id,
                                             inner_ip, inner_port, send_data)

            protocol_parser = protocol_handler.ProtocolHandler()
            send_package = protocol_parser.build_data(forw_data)
            if outer_connector and outer_connector.con_state == connector.CON_STATE.CON_CONNECTED:
                send_bytes = outer_connector.send(send_package)
                if send_bytes <= 0:
                    logger.error("TransData send failed,forward_id:%d inner_ip:%s inner_port:%d"%(forward_id,inner_ip,inner_port))
                    raise Exception("Send data failed")
            ori += 2**31

    def inner_closed(self,forward_id,inner_ip,inner_port,outer_connector):
        close_data = forward_data.ForwardData()
        close_data.id = forward_id
        close_data.data_type = forward_data.DATA_TYPE.CLOSE_CONNECTION
        close_data.inner_ip = inner_ip
        close_data.inner_port = inner_port
        close_data.data = ''

        protocol_parser = protocol_handler.ProtocolHandler()
        send_package = protocol_parser.build_data(close_data)
        if outer_connector and outer_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            send_bytes = outer_connector.send(send_package)
            if send_bytes <= 0:
                logger.error("CloseData send failed,forward_id:%d inner_ip:%s inner_port:%d"%(forward_id,inner_ip,inner_port))

    def inner_connected(self,forward_id,inner_ip,inner_port,outer_connector):
        reply_data = forward_data.ForwardData(forward_data.DATA_TYPE.CONNECTION_SUCCESS, forward_id,
                                             inner_ip, inner_port, '')
        protocol_parser = protocol_handler.ProtocolHandler()
        send_package = protocol_parser.build_data(reply_data)
        if outer_connector and outer_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            send_bytes = outer_connector.send(send_package)
            if send_bytes <= 0:
                logger.error("ConnectedData send failed,forward_id:%d inner_ip:%s inner_port:%d"%(forward_id,inner_ip,inner_port))