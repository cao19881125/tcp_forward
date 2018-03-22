

import logging
import logging.config
from logging.handlers import RotatingFileHandler

logger = logging.getLogger('my_logger')
if __name__ == '__main__':
    #log_fmt = "%(asctime)s - %(levelname)s - %(message)s"
    #logging.basicConfig(format=log_fmt)



    #logger.setLevel(logging.INFO)
    logger.setLevel(logging._levelNames['DEBUG'])
    handler = RotatingFileHandler("my_logger.log", maxBytes=10000000, backupCount=10)
    console = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s %(process)d %(levelname)s %(filename)s:%(lineno)s %(funcName)s [-] %(message)s ')
    handler.setFormatter(formatter)
    console.setFormatter(formatter)
    logger.addHandler(handler)
    #logger.addHandler(console)

    logger.info('hello %d %s'%(10,'123'))