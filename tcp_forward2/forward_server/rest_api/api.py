import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from oslo_config import cfg
from webob import Request

class RestApiHandler(object):

    def __call__(self, environ,start_response):
        start_response("200 OK", [("Content-type", "text/plain")])
        req = Request(environ)
        if req.method == 'GET':
            return self._get(req)
        elif req.method == 'POST':
            return self._post(req)
        elif req.method == 'PUT':
            return self._put(req)
        elif req.method == 'DELETE':
            return self._delete(req)

    def _get(self,request):
        return []

    def _post(self,request):
        return []

    def _put(self,request):
        return []

    def _delete(self,request):
        return []

    def _get_params(self,request):
        parms = {}
        for key,value in request.params.items():
            if type(key) == unicode:
                key = unicode.encode(key)
            if type(value) == unicode:
                value = unicode.encode(value)
            parms[key] = value
        return parms
class ClientPort(RestApiHandler):

    def _get(self,request):
        result = {"client_port": cfg.CONF.INNER_PORT}
        return [str(result)]

    @classmethod
    def factory(cls,global_conf,**kwargs):
        return cls()


