#!/usr/bin/env python
import sys
import os
PROJECT_ROOT = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)), '.'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
import argparse
from forward_client.main import main as client_main
from forward_server.main import main as server_main

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='mode',help='running mode')

    server_mode = subparsers.add_parser('server',help='server mode')
    server_mode.add_argument('cfg_file',help='config file path')

    client_mode = subparsers.add_parser('client',help='client mode')
    client_mode.add_argument('cfg_file', help='config file path')
    #client_mode.add_argument('server_ip',help='server ip')
    #client_mode.add_argument('server_port',type=int,help='server port')

    args = parser.parse_args()
    if args.mode == 'server':
        server_main(args.cfg_file)
    elif args.mode == 'client':
        client_main(args.cfg_file)



if __name__=='__main__':
    sys.exit(main())