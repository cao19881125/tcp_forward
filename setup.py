#!/usr/bin/env python
#-*- coding:utf-8 -*-

from setuptools import setup, find_packages

setup(
    name = "tcp-forward",
    version = "1.0.2",
    keywords = ("tcp-forward"),
    description = "forward data from an established tcp connection",
    license = "MIT",

    url = "https://github.com/cao19881125/tcp_forward.git",
    author = "yuntao.cao",
    author_email = "yuntao.cao@nocsys.com.cn",

    packages = find_packages(),
    include_package_data = True,
    platforms = "any",
    install_requires = ['enum','argparse','ConfigParser','pyinotify'],
    data_files = [('/etc/tcp-forward',['./forward_server.cfg','./forward_client.cfg','./port_mapper.cfg'])],
    scripts=['tools/tcp-forward']
)
