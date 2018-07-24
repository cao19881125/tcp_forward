import sys
from oslo_config import cfg
from forward_server.main import main as server_main
from forward_client.forward_client import main as client_main


run_type_opt = [
    cfg.StrOpt('run_type',default='server',help='run type is server or client'),
]
cfg.CONF.register_cli_opts(run_type_opt)

def main():


    cfg.CONF(sys.argv[1:])

    print cfg.CONF.run_type
    if cfg.CONF.run_type == 'server':
        #server_main(args.cfg_file)
        server_main()
    elif cfg.CONF.run_type == 'client':
        #client_main(args.cfg_file)
        client_main()
    else:
        print 'run_type error'


if __name__ == '__main__':

    sys.exit(main())
