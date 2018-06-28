import sys
from oslo_config import cfg


run_type_opt = [
    cfg.StrOpt('run_type',default='server',help='run type is server or client'),
]
cfg.CONF.register_cli_opts(run_type_opt)

def main(args):


    cfg.CONF(args=args)

    print cfg.CONF.run_type
    if cfg.CONF.run_type == 'server':
        #server_main(args.cfg_file)
        pass
    elif cfg.CONF.run_type == 'client':
        #client_main(args.cfg_file)
        pass
    else:
        print 'run_type error'


if __name__ == '__main__':

    sys.exit(main(sys.argv[1:]))
