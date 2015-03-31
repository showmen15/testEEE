import logging
import logging.config
import sys
import threading
import traceback
import math

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

SERIAL_PORT = config.ROBOCLAW_SERIAL_PORT
BAUD_RATE = config.ROBOCLAW_BAUD_RATE

REAR_RC_ADDRESS = int(config.ROBOCLAW_REAR_RC_ADDRESS)
FRONT_RC_ADDRESS = int(config.ROBOCLAW_FRONT_RC_ADDRESS)

MOTORS_MAX_QPPS = int(config.ROBOCLAW_MOTORS_MAX_QPPS)
MOTORS_P_CONST = int(config.ROBOCLAW_P_CONST)
MOTORS_I_CONST = int(config.ROBOCLAW_I_CONST)
MOTORS_D_CONST = int(config.ROBOCLAW_D_CONST)

WHEEL_RADIUS = float(config.ROBOCLAW_WHEEL_RADIUS)
PULSES_PER_REVOLUTION = float(config.ROBOCLAW_PULSES_PER_REVOLUTION)

TIMEOUT = 0.3


class RoboclawController(MessageHandler):
    def __init__(self, pipe_in, pipe_out, driver):
        MessageHandler.__init__(self, pipe_in, pipe_out)
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

        front_left, front_right, rear_left, rear_right = self.__driver.get_measured_speeds()

        current_speed = response_message.Extensions[roboclaw_pb2.currentSpeed]
        current_speed.frontLeftSpeed = int(front_left)
        current_speed.frontRightSpeed = int(front_right)
        current_speed.rearLeftSpeed = int(rear_left)
        current_speed.rearRightSpeed = int(rear_right)

        return response_header, response_message

    def __handle_motors_command(self, _, message):
        self.__logger.debug('Set speed')

        front_left = message.Extensions[roboclaw_pb2.motorsCommand].frontLeftSpeed
        front_right = message.Extensions[roboclaw_pb2.motorsCommand].frontRightSpeed
        rear_left = message.Extensions[roboclaw_pb2.motorsCommand].rearLeftSpeed
        rear_right = message.Extensions[roboclaw_pb2.motorsCommand].rearRightSpeed

        self.__driver.set_speeds(front_left, front_right, rear_left, rear_right)

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action for %s', str(header.clientIDs))

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action for %s', str(header.clientIDs))

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died, stop!', client_id)
        self.__driver.stop()


def to_mmps(val):
    return int(val * WHEEL_RADIUS * math.pi * 2.0 / PULSES_PER_REVOLUTION)


def to_qpps(val):
    rps = val / (WHEEL_RADIUS * math.pi * 2.0)
    return int(rps * PULSES_PER_REVOLUTION)


class RoboclawDriver(object):
    def __init__(self, front, rear):
        self.__front, self.__rear = front, rear
        self.__roboclaw_lock = threading.Lock()

    def get_measured_speeds(self):
        self.__roboclaw_lock.acquire()
        try:
            front_right, _ = self.__front.read_speed_m1()
            front_left, _ = self.__front.read_speed_m2()
            rear_right, _ = self.__rear.read_speed_m1()
            rear_left, _ = self.__rear.read_speed_m2()
        finally:
            self.__roboclaw_lock.release()

        front_left = to_mmps(front_left)
        front_right = to_mmps(front_right)
        rear_left = to_mmps(rear_left)
        rear_right = to_mmps(rear_right)

        return front_left, front_right, rear_left, rear_right

    def set_speeds(self, front_left, front_right, rear_left, rear_right):
        front_left = to_qpps(front_left)
        front_right = to_qpps(front_right)
        rear_left = to_qpps(rear_left)
        rear_right = to_qpps(rear_right)

        self.__roboclaw_lock.acquire()
        try:
            self.__front.drive_mixed_with_signed_speed(front_right, front_left)
            self.__rear.drive_mixed_with_signed_speed(rear_right, rear_left)
        finally:
            self.__roboclaw_lock.release()

    def stop(self):
        self.__roboclaw_lock.acquire()
        try:
            self.__front.drive_mixed_with_signed_speed(0, 0)
            self.__rear.drive_mixed_with_signed_speed(0, 0)
        finally:
            self.__roboclaw_lock.release()


if __name__ == '__main__':
    try:
        _serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
        _serial_port = serial_port.SerialPort(_serial)

        roboclaw_front = Roboclaw(_serial_port, FRONT_RC_ADDRESS)
        roboclaw_rear = Roboclaw(_serial_port, REAR_RC_ADDRESS)

        roboclaw_front.set_pid_constants_m1(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        roboclaw_front.set_pid_constants_m2(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        roboclaw_rear.set_pid_constants_m1(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        roboclaw_rear.set_pid_constants_m2(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)

        roboclaw_front.set_m1_encoder_mode(0)
        roboclaw_front.set_m2_encoder_mode(0)
        roboclaw_rear.set_m1_encoder_mode(0)
        roboclaw_rear.set_m2_encoder_mode(0)

        sys.stderr.write('FIRMWARE VERSION, FRONT:\n%s\n' % str(roboclaw_front.read_firmware_version()))
        sys.stderr.write('FIRMWARE VERSION, REAR:\n%s\n' % str(roboclaw_rear.read_firmware_version()))

        sys.stderr.write('BUFFER LENGTH, FRONT:\n%s\n' % str(roboclaw_front.read_buffer_length()))
        sys.stderr.write('BUFFER LENGTH, REAR:\n%s\n' % str(roboclaw_rear.read_buffer_length()))

        sys.stderr.write('PIDQ SETTINGS, FRONT, M1:\n%s\n' % str(roboclaw_front.read_m1_pidq_settings()))
        sys.stderr.write('PIDQ SETTINGS, FRONT, M2:\n%s\n' % str(roboclaw_front.read_m2_pidq_settings()))
        sys.stderr.write('PIDQ SETTINGS, REAR, M1:\n%s\n' % str(roboclaw_rear.read_m1_pidq_settings()))
        sys.stderr.write('PIDQ SETTINGS, REAR, M2:\n%s\n' % str(roboclaw_rear.read_m2_pidq_settings()))

        sys.stderr.write('ENCODER MODE, FRONT:\n%s\n' % str(roboclaw_front.read_encoder_mode()))
        sys.stderr.write('ENCODER MODE, REAR:\n%s\n' % str(roboclaw_rear.read_encoder_mode()))

        roboclaw_driver = RoboclawDriver(roboclaw_front, roboclaw_rear)
        controller = RoboclawController(sys.stdin, sys.stdout, roboclaw_driver)
        controller.run()

    except BaseException as e:
        sys.stderr.write('Run without Roboclaw.\n')
        traceback.print_exc()

        controller = NullController(sys.stdin, sys.stdout)
        controller.run()