

class DATA_TYPE(object):
    NEW_CONNECTION = 0x00
    CONNECTION_SUCCESS = 0x01
    TRANS_DATA = 0x10
    CLOSE_CONNECTION = 0x20
    HEART_BEAT = 0x30


class ForwardData(object):
    def __init__(self,data_type=0,forward_id=0,inner_ip='',inner_port=0,data=None):
        self.data_type = data_type
        self.id = forward_id
        self.inner_ip = inner_ip
        self.inner_port = inner_port
        self.data = data