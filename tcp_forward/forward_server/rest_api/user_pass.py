import ConfigParser
from oslo_config import cfg


class NoUserException(Exception):
    pass

class PassErrorException(Exception):
    pass

class UserPass(object):
    def __init__(self):
        pass


    def check_pass_word(self,user,password):
        all_users = self.__parse_file()
        if all_users.has_key(user):
            if all_users[user] == password:
                return True
            else:
                raise PassErrorException()
        else:
            raise NoUserException()

    def __parse_file(self):
        cf = ConfigParser.ConfigParser()
        all_users = {}
        try:
            cf.readfp(open(cfg.CONF.user_file,'rb'))
            users = cf.items('USER')
            for item in users:
                user = item[0].lstrip().rstrip()
                passwd = item[1].lstrip().rstrip()
                all_users[user] = passwd

        except Exception,e:
            pass

        return all_users