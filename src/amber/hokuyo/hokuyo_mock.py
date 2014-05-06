import sys

from amber.hokuyo.hokuyo_common import HokuyoController


__author__ = 'paoolo'

LOGGER_NAME = 'Hokuyo.Controller'


class MockPort(object):
    def write(self, command):
        pass

    def read_byte(self):
        return ord('\n')

    def read(self, param):
        return '0' * param


if __name__ == '__main__':
    port = MockPort()

    controller = HokuyoController(sys.stdin, sys.stdout, port)
    controller()