

def print_hex_buf(buf):
    current_buf = bytearray(buf)
    print ' '.join(['0x%.2x' % x for x in current_buf])