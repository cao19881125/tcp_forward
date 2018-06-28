import sys
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
        return ["Paste Deploy LAB: Version = 1.0.0",]
    @classmethod
    def factory(cls,global_conf,**kwargs):
        print "in ShowVersion.factory", global_conf, kwargs
        return ShowVersion()



def main():
    t = threading.Thread(target=forward_server.main())
    t.start()

    loader = wsgi.Loader(cfg.CONF)
    wsgi_app = loader.load_app('forward-server')

    server = pywsgi.WSGIServer(('0.0.0.0',8080),wsgi_app)
    server.serve_forever()


if __name__ == '__main__':
    cfg.CONF(sys.argv[1:])
    sys.exit(main())