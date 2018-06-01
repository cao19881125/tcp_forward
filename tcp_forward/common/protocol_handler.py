import socket
from binascii import hexlify
from pprint import pprint

from common import forward_data

'''
'''

class ParseTimeout(Exception):
    def __init__(self, package_len, buf_len):
        self.package_len = package_len
        self.buf_len = buf_len

    @property
    def message(self):
        return "Parse time out,package len:%d buf_len:%d"%(self.package_len,self.buf_len)

class ParseError(Exception):
    pass

class ProtocolHandler(object):


    def __init__(self):
        pass

    def print_buf(self,buf_array):
        print ' '.join(['0x%.2x'% x for x in buf_array ])
    def ip_to_bytearray(self,ip):
        packed_ip_addr = socket.inet_aton(ip)
        hexStr = hexlify(packed_ip_addr)
        result_array = bytearray(4)
        result_array[0] = int(hexStr[0:2],16)
        result_array[1] = int(hexStr[2:4],16)
        result_array[2] = int(hexStr[4:6],16)
        result_array[3] = int(hexStr[6:8],16)

        return result_array

    def bytearray_to_ip(self,ip_array):

        array2ip = lambda x:'.'.join([ str(x[i]) for i in range(4) ])

        return array2ip(ip_array)



    def build_data(self,data):
        trans_type = data.data_type
        trans_id = data.id
        inner_ip = data.inner_ip
        inner_port = data.inner_port
        msg = data.data

        msg_len = len(msg)
        buf_len = 19+msg_len

        result_buf = bytearray(buf_len)

        result_buf[0] = 0xAB
        result_buf[1] = 0xBA

        result_buf[2] = trans_type

        result_buf[3] = trans_id%0x100
        result_buf[4] = trans_id/0x100%0x100
        result_buf[5] = trans_id/0x10000%0x100
        result_buf[6] = trans_id/0x1000000

        ip_array = self.ip_to_bytearray(inner_ip)
        result_buf[7] = ip_array[0]
        result_buf[8] = ip_array[1]
        result_buf[9] = ip_array[2]
        result_buf[10] = ip_array[3]

        result_buf[11] = inner_port%0x100
        result_buf[12] = inner_port/0x100

        result_buf[13] = msg_len%0x100
        result_buf[14] = msg_len/0x100%0x100
        result_buf[15] = msg_len/0x10000%0x100
        result_buf[16] = msg_len/0x1000000

        #for i in range(msg_len):
        #    result_buf[17 + i] = msg[i]
        result_buf[17:17 + msg_len] = msg

        result_buf[buf_len - 1] = 0x16

        return result_buf

    def parse_data(self,array_buf):
        if array_buf[0] != 0xAB or array_buf[1] != 0xBA:
            return None

        result_data = forward_data.ForwardData()
        result_data.data_type = array_buf[2]
        result_data.id = array_buf[3] + array_buf[4]*0x100 + array_buf[5]*0x10000 + array_buf[6]*0x1000000


        result_data.inner_ip = self.bytearray_to_ip(array_buf[7:11])

        result_data.inner_port = array_buf[11] + array_buf[12]*0x100

        data_len = array_buf[13] + array_buf[14]*0x100 + array_buf[15]*0x10000 + array_buf[16]*0x1000000
        if data_len > 0:
            result_data.data = array_buf[17:17+data_len]

        return result_data

    def del_wrong_header(self,ring_buffer):
        i = 0;
        while True:
            if i >= ring_buffer.buf_len():
                ring_buffer.get(ring_buffer.buf_len())
                break
            if ring_buffer.look(i) != 0xAB:
                i += 1
                continue
            else:
                if ring_buffer.buf_len() < 2:
                    ring_buffer.get(ring_buffer.buf_len())
                    break
                if ring_buffer.look(i+1) != 0xBA:
                    i += 2
                    continue
                ring_buffer.get(i)
                break

    def pop_header(self,ring_buffer):
        ring_buffer.get(2)

    def get_one_complete_package(self,ring_buffer):


        if ring_buffer.buf_len() < 19:
            raise ParseTimeout(19,ring_buffer.buf_len())

        if ring_buffer.look(0) != 0xAB or ring_buffer.look(1) != 0xBA:
            raise ParseError()

        data_len = ring_buffer.look(13) + ring_buffer.look(14)*0x100 + ring_buffer.look(15)*0x10000 + ring_buffer.look(16)*0x1000000

        package_len = 19 + data_len

        if ring_buffer.buf_len() < package_len:
            raise ParseTimeout(package_len, ring_buffer.buf_len())

        if ring_buffer.look(package_len - 1) != 0x16:
            raise ParseError()

        package = ring_buffer.get(package_len)

        return package




if __name__=='__main__':
    p = ProtocolHandler()

    data = 'abcdefg'

    test_buf = p.build_data(12, forward_data.DATA_TYPE.TRANS_DATA, '192.168.1.1', 1234, data)
    p.print_buf(test_buf)
    pprint(vars(test_buf))
    pars_result = p.parse_data(test_buf)
    pprint(vars(test_buf))


    #p.print_buf(p.build_data(13,forward_data.DATA_TYPE.CLOSE_CONNECTION,'127.0.0.1',4321,''))
