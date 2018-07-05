from webob import Request
from webob import Response

class Test(object):

    def __call__(self, environ, start_response):
        start_response("200 OK", [("Content-type", "text/plain")])
        # print environ
        req = Request(environ)
        print req.url
        res = Response()

        res.headers.add('X-Auth-Token','eyJhbGciOiJIUzI1NiIsImV4cCI6MTUzMDY4NzI2OCwiaWF0IjoxNTMwNjg2NjY4fQ.eyJpZCI6MTIzNDU2fQ.rwNSzsQ6oSHQ_RchsGAwiiyomlc6JMp1SeE7YDFL-iM')

        res.body = "Paste Deploy LAB: Version = 1.0.0"

        return res(environ,start_response)

    @classmethod
    def factory(cls, global_conf, **kwargs):
        return cls()