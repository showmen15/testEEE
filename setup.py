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
    packages=['amber', 'amber.driver.common', 'amber.driver.dummy', 'amber.driver.hokuyo', 'amber.driver.tools'],
    package_dir={'amber': 'src/amber',
                 'amber.driver.common': 'src/amber/client/common',
                 'amber.driver.dummy': 'src/amber/client/dummy',
                 'amber.driver.hokuyo': 'src/amber/client/hokuyo',
                 'amber.driver.tools': 'src/amber/client/tools'},
    package_data={'': ['src/amber/driver/common/amber.ini',
                       'src/amber/driver/drive_to_point/drive_to_point.ini',
                       'src/amber/driver/dummy/dummy.ini',
                       'src/amber/driver/hokuyo/hokuyo.ini',
                       'src/amber/client/tools/main.ini']},
    data_files=[
        ('', [
            'src/amber/driver/common/amber.ini',
            'src/amber/driver/drive_to_point/drive_to_point.ini',
            'src/amber/driver/dummy/dummy.ini',
            'src/amber/driver/hokuyo/hokuyo.ini',
            'src/amber/client/tools/main.ini'
        ]),
    ],
    install_requires=required,
    version='1.13.1',
    description='Amber drivers in python',
    author=u'Paweł Suder',
    author_email='pawel@suder.info',
    url='http://dev.suder.info/',
    download_url='http://github.com/dev-amber/client/amber-python-drivers/',
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
