from oslo_config import cfg

core_opts = [
    cfg.StrOpt('SERVER_IP',default='127.0.0.1',help='Server IP'),
    cfg.IntOpt('SERVER_PORT',default=1111,help='The port the server is listening on'),
    cfg.StrOpt('LOG_LEVEL',default='INFO',help='log level:CRITICAL ERROR WARNING INFO DEBUG NOTSET'),
    cfg.StrOpt('TAG',default='default',help='the client tag')
]


def register_core_common_config_opts(cfg=cfg.CONF):
    cfg.register_opts(core_opts)