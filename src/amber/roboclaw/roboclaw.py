import serial
import sys
import os

from amber.roboclaw.roboclaw_common import RoboclawController

from amber.tools import serial_port, config


__author__ = 'paoolo'

LOGGER_NAME = 'Roboclaw.Controller'

pwd = os.path.dirname(os.path.abspath(__file__))
config.add_config_ini('%s/roboclaw.ini' % pwd)

SERIAL_PORT = config.ROBOCLAW_SERIAL_PORT
BAUD_RATE = config.ROBOCLAW_BAUD_RATE
TIMEOUT = 0.1

if __name__ == '__main__':
    serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
    port = serial_port.SerialPort(serial)

    controller = RoboclawController(sys.stdin, sys.stdout, port)
    controller()