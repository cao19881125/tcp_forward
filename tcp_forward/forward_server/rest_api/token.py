
from api import RestApiHandler
import token_verify

from webob.headers import ResponseHeaders
class Token(RestApiHandler):



    def _post(self,request,response):
        #str to dict
        body = eval(request.body)
        if not body.has_key('user') or \
            not body.has_key('password'):
            response.status = '400 Bad Request'
            response.body = 'Please enter user and password'
            return


        user = body['user']
        password = body['password']

        if self.__verify_user(user,password):
            token = token_verify.get_token({'user':user})
            response.headers.add('X-Auth-Token',token)

            response.body = str({})
        else:
            response.status = '401 Unauthorized'
            response.body = 'authentication failed'

    def __verify_user(self,user,password):
        return user == 'cyt' and password == '123456'


    @classmethod
    def factory(cls, global_conf, **kwargs):
        return cls()

