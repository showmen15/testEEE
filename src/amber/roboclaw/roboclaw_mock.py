import sys
import os

from amber.roboclaw.roboclaw_common import RoboclawController

from amber.tools import config


__author__ = 'paoolo'

LOGGER_NAME = 'Roboclaw.Controller'

pwd = os.path.dirname(os.path.abspath(__file__))
config.add_config_ini('%s/roboclaw.ini' % pwd)

SERIAL_PORT = config.ROBOCLAW_SERIAL_PORT
BAUD_RATE = config.ROBOCLAW_BAUD_RATE
TIMEOUT = 0.1


class MockPort(object):
    def send_command(self, __rc_address, param):
        pass

    def write_byte(self, val):
        pass

    def get_checksum(self):
        return 0

    def read_slong(self):
        return 0

    def read_byte(self):
        return 0

    def read(self, param):
        return '0' * param

    def read_word(self):
        return 0

    def write_long(self, d):
        pass

    def write_sword(self, val):
        pass

    def write_slong(self, val):
        pass

    def write_word(self, accel):
        pass

    def read_long(self):
        return 0


if __name__ == '__main__':
    port = MockPort()

    controller = RoboclawController(sys.stdin, sys.stdout, port)
    controller()