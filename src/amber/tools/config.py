import ConfigParser
import sys

__author__ = 'paoolo'


class Config(object):
    def __init__(self, *args):
        self.__config = ConfigParser.ConfigParser()
        self.add_config_ini(*args)

    def __getattr__(self, name):
        # noinspection PyBroadException
        return self.__config.get('default', name)

    def add_config_ini(self, *args):
        map(lambda config_file_path: self.__config.read(config_file_path), args)


sys.modules[__name__] = Config('./main.ini', )


def add_config_ini(*args):
    sys.modules[__name__].add_config_ini(*args)