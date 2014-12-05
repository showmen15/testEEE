import sys

from amber.driver.null.null import NullController

import os
import serial
from amber.driver.hokuyo.hokuyo_common import HokuyoController
from amber.driver.tools import serial_port, config


__author__ = 'paoolo'

LOGGER_NAME = 'AmberPipes'
pwd = os.path.dirname(os.path.abspath(__file__))
config.add_config_ini('%s/hokuyo.ini' % pwd)

SERIAL_PORT = config.HOKUYO_SERIAL_PORT
BAUD_RATE = config.HOKUYO_BAUD_RATE
TIMEOUT = 0.3

if __name__ == '__main__':
    try:
        _serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
        _serial_port = serial_port.SerialPort(_serial)

        _serial.write('QT\nRS\nQT\n')
        result = ''
        flushing = True
        while flushing:
            char = _serial.read()
            flushing = (char != '')
            result += char
        sys.stderr.write('\n===============\nFLUSH SERIAL PORT\n"%s"\n===============\n' % result)

        controller = HokuyoController(sys.stdin, sys.stdout, _serial_port)
        controller()

    except BaseException as e:
        sys.stderr.write('%s\nRun without Hokuyo.' % str(e))

        controller = NullController(sys.stdin, sys.stdout)
        controller()