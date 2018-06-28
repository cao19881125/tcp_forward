

class ClientPort(object):
    def __call__(self,environ,start_response):
        start_response("200 OK",[("Content-type", "text/plain")])
        print 'ClientPort be called'
        return ["port=1111",]
    @classmethod
    def factory(cls,global_conf,**kwargs):
        print "in ClientPort.factory", global_conf, kwargs
        return cls()