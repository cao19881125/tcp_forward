import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '.'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from webob import Request
from oslo_config import cfg
from oslo_service import wsgi
from gevent import pywsgi
import threading
import forward_server


class ShowVersion():
    def __init__(self):
        pass
    def __call__(self,environ,start_response):
        start_response("200 OK",[("Content-type", "text/plain")])
        #print environ
        req = Request(environ)
        print req.method
        print req.POST
        print req.body
        print req.authorization
        
        for key,value in req.params.items():
            print "key=" + str(key) + "  value=" + str(value)
        return ["Paste Deploy LAB: Version = 1.0.0",]
    @classmethod
    def factory(cls,global_conf,**kwargs):
        return ShowVersion()



def main():
    t = threading.Thread(target=forward_server.main)
    t.setDaemon(True)
    t.start()

    loader = wsgi.Loader(cfg.CONF)
    wsgi_app = loader.load_app('forward-server')

    server = pywsgi.WSGIServer(('0.0.0.0',8080),wsgi_app)
    server.serve_forever()


if __name__ == '__main__':
    cfg.CONF(sys.argv[1:])
    sys.exit(main())
