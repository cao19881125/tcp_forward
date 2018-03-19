from pprint import pprint

class RingBuffer(object):
    def __init__(self,buffer_size):
        self.__buffer_size = buffer_size
        self.__buffer = bytearray(buffer_size)
        self.__read_ptr = 0
        self.__write_ptr = 0
        self.__data_len = 0

    def print_buf(self):
        current_buf = self.look(0,self.__data_len)
        print ' '.join(['0x%.2x' % x for x in current_buf])

    def buf_len(self):
        return self.__data_len

    def put(self,buf):
        buf_len = len(buf)
        if buf_len > self.__buffer_size - self.__data_len:
            raise Exception('input size:' + str(buf_len) + ' > writable size:' + str(self.__buffer_size - self.__data_len))
        if self.__buffer_size - self.__write_ptr >= buf_len:
            # write direct
            self.__buffer[self.__write_ptr:self.__write_ptr+buf_len] = buf
            self.__write_ptr += buf_len

        else:
            # front len
            front_len = self.__buffer_size - self.__write_ptr
            behind_len = buf_len - front_len
            self.__buffer[self.__write_ptr:self.__write_ptr+front_len] = buf[0:front_len]
            self.__buffer[0:behind_len] = buf[front_len:]
            self.__write_ptr = behind_len

        if self.__write_ptr >= self.__buffer_size:
            self.__write_ptr = 0
        self.__data_len += buf_len

    '''
        return and pop out the get_size len buf
    '''
    def get(self,get_size):
        if get_size > self.__data_len:
            raise Exception('get_size:' + str(get_size) + ' > data_len:' + str(self.__data_len))

        result_array = bytearray(get_size)
        if get_size <= self.__buffer_size - self.__read_ptr:
            result_array = self.__buffer[self.__read_ptr:self.__read_ptr + get_size]
            self.__read_ptr += get_size
        else:
            front_len = self.__buffer_size - self.__read_ptr
            behind_len = get_size - front_len
            result_array[0:front_len] = self.__buffer[self.__read_ptr:]
            result_array[front_len:] = self.__buffer[0:behind_len]
            self.__read_ptr = behind_len

        if self.__read_ptr >= self.__buffer_size:
            self.__read_ptr = 0

        self.__data_len -= get_size
        return result_array


    def look(self,from_location,look_size = 1):
        if look_size <= 0 or look_size > self.__data_len:
            return None
        elif look_size == 1:
            if self.__read_ptr + from_location >= self.__buffer_size:
                return self.__buffer[self.__read_ptr + from_location - self.__buffer_size ]
            else:
                return self.__buffer[self.__read_ptr + from_location]
        else:
            result_array = bytearray(look_size)
            if self.__read_ptr + from_location >= self.__buffer_size:
                return self.__buffer[self.__read_ptr + from_location - self.__buffer_size:self.__read_ptr + from_location - self.__buffer_size + look_size]
            else:
                if self.__read_ptr + from_location + look_size < self.__buffer_size:
                   return self.__buffer[self.__read_ptr + from_location:self.__read_ptr + from_location + look_size]
                else:
                    front_len = self.__buffer_size - self.__read_ptr - from_location
                    behind_len = look_size - front_len
                    result_array[0:front_len] = self.__buffer[self.__read_ptr:]
                    result_array[front_len:] = self.__buffer[0:behind_len]
                    return result_array

if __name__=='__main__':
    test_buffer = RingBuffer(10)
    buf1 = bytearray('1'*5)
    buf2 = bytearray('2'*7)

    test_buffer.put(buf1)
    test_buffer.print_buf()
    pprint(vars(test_buffer))

    get_buf1 = test_buffer.get(3)
    test_buffer.print_buf()
    pprint(vars(test_buffer))

    test_buffer.put(buf2)
    test_buffer.print_buf()
    pprint(vars(test_buffer))

    look1 = test_buffer.look(0,8)
    print look1
    look2 = test_buffer.look(2)
    print look2

    get_buf2 = test_buffer.get(8)
    test_buffer.print_buf()
    pprint(vars(test_buffer))

