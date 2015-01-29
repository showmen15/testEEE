import ConfigParser
import sys

__author__ = 'paoolo'


class Config(object):
    def __init__(self, *args):
        self.__config = ConfigParser.ConfigParser()
        self.add_config_ini(*args)

    def __getattr__(self, name):
        return self.__config.get('default', name)

    def add_config_ini(self, *args):
        map(self.__config.read, args)


sys.modules[__name__] = Config('./main.ini', )


def add_config_ini(*args):
    sys.modules[__name__].add_config_ini(*args)