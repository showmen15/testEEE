import logging.config
import sys
import os
import time

import serial

from amber.hokuyo.hokuyo_common import HokuyoController
from amber.tools import serial_port, config


__author__ = 'paoolo'

LOGGER_NAME = 'AmberPipes'
pwd = os.path.dirname(os.path.abspath(__file__))
config.add_config_ini('%s/hokuyo.ini' % pwd)
logging.config.fileConfig('%s/hokuyo.ini' % pwd)

SERIAL_PORT = config.HOKUYO_SERIAL_PORT
BAUD_RATE = config.HOKUYO_BAUD_RATE
TIMEOUT = 0.1

if __name__ == '__main__':
    logger = logging.getLogger(LOGGER_NAME)

    serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
    port = serial_port.SerialPort(serial)

    while True:
        # noinspection PyBroadException
        try:
            controller = HokuyoController(sys.stdin, sys.stdout, port)
            controller()
        except BaseException as e:
            logger.error('error: %s' % str(e))
            time.sleep(5)