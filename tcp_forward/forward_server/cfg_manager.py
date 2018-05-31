import ConfigParser

class CfgManager(object):

    _inst = None

    def __init__(self):
        self.__cfg_file = ''
        self.__cfg = ConfigParser.ConfigParser()

    @classmethod
    def get_instance(cls):
        if not CfgManager._inst:
            CfgManager._inst = cls()
        return CfgManager._inst

    def register_file(self,cfg_file):
        self.__cfg_file = cfg_file
        self.__cfg.readfp(open(cfg_file, 'rb'))

    def get_cfg(self):
        return self.__cfg