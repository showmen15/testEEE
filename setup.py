# coding=utf-8
# !/usr/bin/env python
import sys

try:
    from setuptools import setup
except ImportError:
    sys.stderr.write('using distutils\n')
    from distutils.core import setup

with open('requirements.txt') as f:
    required = f.read().splitlines()

setup(
    name='amber-python-drivers',
    packages=['amberdriver', 'amberdriver.common',
              'amberdriver.dummy', 'amberdriver.hokuyo', 'amberdriver.tools'],
    package_dir={'amber': 'src/amber',
                 'amberdriver': 'src/amberdriver',
                 'amberdriver.common': 'src/amberdriver/common',
                 'amberdriver.dummy': 'src/amberdriver/dummy',
                 'amberdriver.hokuyo': 'src/amberdriver/hokuyo',
                 'amberdriver.tools': 'src/amberdriver/tools'},
    package_data={'': ['src/amberdriver/common/amber.ini',
                       'src/amberdriver/drive_to_point/drive_to_point.ini',
                       'src/amberdriver/dummy/dummy.ini',
                       'src/amberdriver/hokuyo/hokuyo.ini',
                       'src/amberdriver/tools/main.ini']},
    data_files=[
        ('', [
            'src/amberdriver/common/amber.ini',
            'src/amberdriver/drive_to_point/drive_to_point.ini',
            'src/amberdriver/dummy/dummy.ini',
            'src/amberdriver/hokuyo/hokuyo.ini',
            'src/amberdriver/tools/main.ini'
        ]),
    ],
    test_suite="amberdriver.tests",
    install_requires=required,
    version='1.17',
    description='Amber drivers in python',
    author=u'Paweł Suder',
    author_email='pawel@suder.info',
    url='http://project-capo.github.io/',
    download_url='http://github.com/project-capo/amber-python-drivers/',
    keywords=['amber', 'hokuyo', 'panda'],
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
