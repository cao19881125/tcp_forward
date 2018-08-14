from webob import Request
from webob import Response
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from itsdangerous import SignatureExpired
from itsdangerous import BadSignature

ENCRYPT_KEY = 'TCP-FORWARD'


def get_token(data):
    # expires_in is token timeout seconds
    s = Serializer(ENCRYPT_KEY, expires_in=3600)


    return s.dumps(data)


def verify_auth_token(token):
    s = Serializer(ENCRYPT_KEY)
    try:
        data = s.loads(token)
    except SignatureExpired:
        return None  # valid token, but expired
    except BadSignature:
        return None  # invalid token

    return data

def token_verify(func):
    def verity(*args,**kwargs):
        environ = args[1]
        start_response = args[2]

        req = Request(environ)


        if req.url.split('/')[-1] == 'token':
            return func(*args,**kwargs)


        token = req.cookies.get('X-Auth-Token') or req.headers.get('X-Auth-Token')

        def unauthorized_reply(environ,start_response):
            res = Response()
            res.status = '401 Unauthorized'
            res.body = 'Unauthorized'
            res.headers.add('Www-Authenticate ', '/'.join(x for x in (req.url.split('/')[:-1] + ['token'])))
            return res(environ, start_response)

        if not token:
            return unauthorized_reply(environ,start_response)

        data = verify_auth_token(token)

        if not data:
            return unauthorized_reply(environ,start_response)

        return func(*args,**kwargs)

    return verity