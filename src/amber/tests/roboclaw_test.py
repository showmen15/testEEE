import os
import logging.config

import serial

from amber.roboclaw.roboclaw_common import Roboclaw

from amber.tools import serial_port, config


__author__ = 'paoolo'

LOGGER_NAME = 'RoboclawController'
pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/roboclaw.ini' % pwd)
config.add_config_ini('%s/roboclaw.ini' % pwd)

SERIAL_PORT = config.ROBOCLAW_SERIAL_PORT
BAUD_RATE = config.ROBOCLAW_BAUD_RATE
TIMEOUT = 0.1

REAR_RC_ADDRESS = int(config.ROBOCLAW_REAR_RC_ADDRESS)
FRONT_RC_ADDRESS = int(config.ROBOCLAW_FRONT_RC_ADDRESS)

MOTORS_MAX_QPPS = int(config.ROBOCLAW_MAX_QPPS)
MOTORS_P_CONST = int(config.ROBOCLAW_P)
MOTORS_I_CONST = int(config.ROBOCLAW_I)
MOTORS_D_CONST = int(config.ROBOCLAW_D)

if __name__ == '__main__':
    serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
    port = serial_port.SerialPort(serial)

    roboclaw_front = Roboclaw(port, FRONT_RC_ADDRESS)
    roboclaw_rear = Roboclaw(port, REAR_RC_ADDRESS)

    roboclaw_front.set_m1_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
    roboclaw_front.set_m2_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
    roboclaw_rear.set_m1_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
    roboclaw_rear.set_m2_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)

    roboclaw_front.drive_m1(10)
    roboclaw_front.drive_m2(10)