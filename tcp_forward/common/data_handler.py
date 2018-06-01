import forward_data, protocol_handler
import connector
import logging
logger = logging.getLogger('my_logger')


class DataHandler(object):
    def __init__(self):
        pass

    def parse_data(self,ring_buffer):
        #get one complete package

        if ring_buffer.buf_len() <= 0:
            return None


        protocol_parse = protocol_handler.ProtocolHandler()
        package = None
        try:
            protocol_parse.del_wrong_header(ring_buffer)
            package = protocol_parse.get_one_complete_package(ring_buffer)
            ring_buffer.set_clear()
        except protocol_handler.ParseTimeout,e:
            #print 'parse timeout,current buffer:'
            logger.debug(e.message)
            ring_buffer.set_time_out()
            if ring_buffer.over_max_time():
                protocol_parse.pop_header(ring_buffer)
                protocol_parse.del_wrong_header(ring_buffer)
                logger.error('ring buffer over max timeout time,del wrong header')
            return None
        except protocol_handler.ParseError,e:
            print 'parse error'
            protocol_parse.pop_header(ring_buffer)
            return None
        except Exception,e:
            return None


        if package == None:
            print 'package is None'
            return None

        parsed_data = protocol_parse.parse_data(package)

        if parsed_data == None:
            print 'parse package failed'
            return None

        return parsed_data