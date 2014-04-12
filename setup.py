# coding=utf-8
# !/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='amber-python-drivers',
    packages=['amber', 'amber.common', 'amber.dummy', 'amber.hokuyo', 'amber.roboclaw', 'amber.tests', 'amber.tools'],
    package_dir={'amber': 'src/amber',
                 'amber.common': 'src/amber/common',
                 'amber.dummy': 'src/amber/dummy',
                 'amber.hokuyo': 'src/amber/hokuyo',
                 'amber.roboclaw': 'src/amber/roboclaw',
                 'amber.tests': 'src/amber/tests',
                 'amber.tools': 'src/amber/tools'},
    install_requires=required,
    version='1.0',
    description='Amber drivers in python',
    author=u'Paweł Suder',
    author_email='pawel@suder.info',
    url='http://dev.suder.info/',
    download_url='http://github.com/dev-amber/amber-python-drivers/',
    keywords=['amber', 'hokuyo', 'roboclaw', 'panda'],
    classifiers=[
        'Programming Language :: Python',
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: Other/Proprietary License',
        'Operating System :: OS Independent',
    ],
    long_description='''\
'''
)
