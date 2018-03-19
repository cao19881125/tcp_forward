
from common.data_handler import DataHandler
from common.protocol_handler import ProtocolHandler
from common import forward_data
from common import connector
from common import tools

class OutDataHandler(DataHandler):


    def create_connection(self,forward_id,inner_ip,inner_port,inner_connector):
        _protocol_handler = ProtocolHandler()
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.NEW_CONNECTION, forward_id,
                                             inner_ip, inner_port, '')
        send_package = _protocol_handler.build_data(forw_data)
        if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            inner_connector.send(send_package)

    def trans_data(self,forward_id,inner_ip,inner_port,data,inner_connector):
        _protocol_handler = ProtocolHandler()
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, forward_id,
                                             inner_ip, inner_port, data)
        send_package = _protocol_handler.build_data(forw_data)
        if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            inner_connector.send(send_package)
            #print 'inner_connector send package'
            #tools.print_hex_buf(send_package)


    def close_connection(self,forward_id,inner_ip,inner_port,inner_connector):
        _protocol_handler = ProtocolHandler()
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.CLOSE_CONNECTION, forward_id,
                                             inner_ip, inner_port, '')
        send_package = _protocol_handler.build_data(forw_data)
        if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            inner_connector.send(send_package)

class InnerDataHandler(DataHandler):
    def handle_data(self, ring_buffer,worker_manager):
        parsed_data = super(InnerDataHandler, self).parse_data(ring_buffer)
        if parsed_data == None:
            return

        if parsed_data.data_type == forward_data.DATA_TYPE.CONNECTION_SUCCESS:
            outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
            if outer_worker != None:
                outer_worker.connecting_reply(True)
        elif parsed_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
            outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
            if outer_worker != None:
                outer_worker.trans_data(parsed_data.data)
        elif parsed_data.data_type == forward_data.DATA_TYPE.CLOSE_CONNECTION:
            outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
            if outer_worker != None:
                outer_worker.close()