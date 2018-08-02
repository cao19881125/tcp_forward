from oslo_config import cfg

core_opts = [
    cfg.IntOpt('INNER_PORT',default=1111,help='port which client to connect'),
    cfg.StrOpt('OUTER_PORTS_FILE',default='/etc/tcp-forward/port_mapper.cfg',help='port mapper file'),
    cfg.StrOpt('LOG_LEVEL',default='INFO',help='log level:CRITICAL ERROR WARNING INFO DEBUG NOTSET'),
    cfg.StrOpt('BANDWIDTH',default='100',help='the max network bandwidth,use M as unit'),
    cfg.StrOpt('user_file',default='/etc/tcp-forward/user_file',help='user file'),
]


def register_core_common_config_opts(cfg=cfg.CONF):
    cfg.register_opts(core_opts)