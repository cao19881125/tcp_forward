#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = "tcp-forward",
    version = "1.0.4",
    keywords = ("tcp-forward"),
    description = "forward data from an established tcp connection",
    license = "MIT",

    url = "https://github.com/cao19881125/tcp_forward.git",
    author = "yuntao.cao",
    author_email = "yuntao.cao@nocsys.com.cn",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = ['enum','argparse','ConfigParser','pyinotify','oslo_config','oslo_service','webob','gevent','itsdangerous'],
    data_files = [('/etc/tcp-forward',['./etc/forward_server.cfg','./etc/forward_client.cfg','./etc/port_mapper.cfg','./etc/api-paste.ini','./etc/user_file'])],
    scripts=['tools/tcp-forward']
)
