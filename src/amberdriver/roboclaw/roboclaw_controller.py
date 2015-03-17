import logging
import logging.config
import sys
import traceback

import serial
import os

from amberdriver.common.message_handler import MessageHandler
from amberdriver.null.null import NullController
from amberdriver.roboclaw import roboclaw_pb2
from amberdriver.roboclaw.roboclaw import Roboclaw
from amberdriver.tools import serial_port, config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/roboclaw.ini' % pwd)
config.add_config_ini('%s/roboclaw.ini' % pwd)

LOGGER_NAME = 'RoboclawController'

MOTORS_MAX_QPPS = int(config.ROBOCLAW_MAX_QPPS)
MOTORS_P_CONST = int(config.ROBOCLAW_P)
MOTORS_I_CONST = int(config.ROBOCLAW_I)
MOTORS_D_CONST = int(config.ROBOCLAW_D)

REAR_RC_ADDRESS = int(config.ROBOCLAW_REAR_RC_ADDRESS)
FRONT_RC_ADDRESS = int(config.ROBOCLAW_FRONT_RC_ADDRESS)

SERIAL_PORT = config.ROBOCLAW_SERIAL_PORT
BAUD_RATE = config.ROBOCLAW_BAUD_RATE
TIMEOUT = 0.3


class RoboclawController(MessageHandler):
    def __init__(self, pipe_in, pipe_out, driver):
        super(RoboclawController, self).__init__(pipe_in, pipe_out)
        self.__driver = driver
        self.__logger = logging.getLogger(LOGGER_NAME)

    def handle_data_message(self, header, message):
        if message.HasExtension(roboclaw_pb2.currentSpeedRequest):
            self.__handle_current_speed_request(header, message)

        elif message.HasExtension(roboclaw_pb2.motorsCommand):
            self.__handle_motors_command(header, message)

        else:
            self.__logger.warning('No request in message')

    @MessageHandler.handle_and_response
    def __handle_current_speed_request(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get current speed')

        (front_left, front_right, rear_left, rear_right), _ = self.__driver.get_measured_speeds()

        current_speed = response_message.Extensions[roboclaw_pb2.currentSpeed]
        current_speed.frontLeftSpeed = int(front_left[0])
        current_speed.frontRightSpeed = int(front_right[0])
        current_speed.rearLeftSpeed = int(rear_left[0])
        current_speed.rearRightSpeed = int(rear_right[0])

        return response_header, response_message

    def __handle_motors_command(self, _, message):
        self.__logger.debug('Set speed')

        front_left = message.Extensions[roboclaw_pb2.motorsCommand].frontLeftSpeed
        front_right = message.Extensions[roboclaw_pb2.motorsCommand].frontRightSpeed
        rear_left = message.Extensions[roboclaw_pb2.motorsCommand].rearLeftSpeed
        rear_right = message.Extensions[roboclaw_pb2.motorsCommand].rearRightSpeed

        self.__driver.set_speeds(front_left, front_right, rear_left, rear_right)

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action for %s' % str(header.clientIDs))

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action for %s' % str(header.clientIDs))

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died, stop!', client_id)
        self.__driver.stop()


class RoboclawDriver(object):
    def __init__(self, front, rear):
        self.__front, self.__rear = front, rear

    def get_measured_speeds(self):
        front_left = self.__front.read_m1_speed()
        front_right = self.__front.read_m2_speed()
        rear_left = self.__rear.read_m1_speed()
        rear_right = self.__rear.read_m2_speed()
        return front_left, front_right, rear_left, rear_right

    def set_speeds(self, front_left, front_right, rear_left, rear_right):
        self.__front.set_mixed_duty(front_left, front_right)
        self.__rear.set_mixed_duty(rear_left, rear_right)

    def stop(self):
        self.__front.set_mixed_duty(0, 0)
        self.__rear.set_mixed_duty(0, 0)


if __name__ == '__main__':
    try:
        _serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
        _serial_port = serial_port.SerialPort(_serial)

        roboclaw_front = Roboclaw(_serial_port, FRONT_RC_ADDRESS)
        roboclaw_rear = Roboclaw(_serial_port, REAR_RC_ADDRESS)

        roboclaw_front.set_m1_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        roboclaw_front.set_m2_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        roboclaw_rear.set_m1_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        roboclaw_rear.set_m2_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)

        roboclaw_driver = RoboclawDriver(roboclaw_front, roboclaw_rear)
        controller = RoboclawController(sys.stdin, sys.stdout, roboclaw_driver)
        controller()

    except BaseException as e:
        sys.stderr.write('Run without Roboclaw.\n')
        traceback.print_exc()

        controller = NullController(sys.stdin, sys.stdout)
        controller()