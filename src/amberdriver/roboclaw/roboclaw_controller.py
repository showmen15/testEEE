import logging
import logging.config
import sys
import threading
import traceback
import math
import time

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

SERIAL_PORT = str(config.ROBOCLAW_SERIAL_PORT)
BAUD_RATE = int(config.ROBOCLAW_BAUD_RATE)

REAR_RC_ADDRESS = int(config.ROBOCLAW_REAR_RC_ADDRESS)
FRONT_RC_ADDRESS = int(config.ROBOCLAW_FRONT_RC_ADDRESS)

MOTORS_MAX_QPPS = int(config.ROBOCLAW_MOTORS_MAX_QPPS)
MOTORS_P_CONST = int(config.ROBOCLAW_P_CONST)
MOTORS_I_CONST = int(config.ROBOCLAW_I_CONST)
MOTORS_D_CONST = int(config.ROBOCLAW_D_CONST)

WHEEL_RADIUS = float(config.ROBOCLAW_WHEEL_RADIUS)
PULSES_PER_REVOLUTION = float(config.ROBOCLAW_PULSES_PER_REVOLUTION)

STOP_IDLE_TIMEOUT = float(config.ROBOCLAW_STOP_IDLE_TIMEOUT)
RESET_IDLE_TIMEOUT = float(config.ROBOCLAW_RESET_IDLE_TIMEOUT)

BATTERY_MONITOR_INTERVAL = float(config.ROBOCLAW_BATTERY_MONITOR_INTERVAL)
ERROR_MONITOR_INTERVAL = float(config.ROBOCLAW_ERROR_MONITOR_INTERVAL)
CRITICAL_READ_REPEATS = float(config.ROBOCLAW_CRITICAL_READ_REPEATS)

RESET_DELAY = float(config.ROBOCLAW_RESET_DELAY)
RESET_GPIO_PATH = str(config.ROBOCLAW_RESET_GPIO_PATH)

TEMPERATURE_MONITOR_INTERVAL = float(config.ROBOCLAW_TEMPERATURE_MONITOR_INTERVAL)
TEMPERATURE_CRITICAL = float(config.ROBOCLAW_TEMPERATURE_CRITICAL)
TEMPERATURE_DROP = float(config.ROBOCLAW_TEMPERATURE_DROP)

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
        self.__controller = None

        self.__front, self.__rear = front, rear
        self.__roboclaw_lock = threading.Lock()

        self.__timeout_lock = threading.Lock()
        self.__motors_stop_timer_enabled, self.__battery_low = False, False
        self.__reset_time, self.__motors_stop_time = 0.0, 0.0
        self.__logger = logging.getLogger(LOGGER_NAME)
        self.__reset_gpio = open(RESET_GPIO_PATH, mode='w')
        self.__overheated = False

    def set_controller(self, controller):
        self.__controller = controller

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
            self.__front.drive_m1_with_signed_speed(front_right)
            self.__front.drive_m2_with_signed_speed(front_left)
            self.__rear.drive_m1_with_signed_speed(rear_right)
            self.__rear.drive_m2_with_signed_speed(rear_left)
        finally:
            self.__roboclaw_lock.release()

    def stop(self):
        self.__roboclaw_lock.acquire()
        try:
            self.__front.drive_mixed_with_signed_speed(0, 0)
            self.__rear.drive_mixed_with_signed_speed(0, 0)
        finally:
            self.__roboclaw_lock.release()

    def __reset(self):
        self.__reset_gpio.write(str('\0'))
        time.sleep(0.5)
        self.__reset_gpio.write(str('\1'))

    def setup(self):
        self.__front.set_pid_constants_m1(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        self.__front.set_pid_constants_m2(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        self.__rear.set_pid_constants_m1(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
        self.__rear.set_pid_constants_m2(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)

        self.__front.set_m1_encoder_mode(0)
        self.__front.set_m2_encoder_mode(0)
        self.__rear.set_m1_encoder_mode(0)
        self.__rear.set_m2_encoder_mode(0)

    def __reset_and_wait(self):
        if not self.__battery_low:
            self.__logger.info('Reset Roboclaw and wait for %f ms', RESET_DELAY)
            self.__roboclaw_disabled = True
            self.__reset()
            time.sleep(RESET_DELAY / 1000.0)
            self.setup()
            self.__roboclaw_disabled = True

    def timeout_monitor_loop(self):
        self.__reset_timeouts()
        while not self.__battery_low or self.__controller.is_alive():
            act_time = time.time()
            self.__timeout_lock.acquire()
            try:
                do_stop = False
                if self.__motors_stop_timer_enabled and self.__motors_stop_time < act_time:
                    do_stop = True
                    self.__motors_stop_timer_enabled = False

                do_reset = False
                if self.__reset_time < act_time:
                    do_reset = True
                    self.__reset_time = act_time + RESET_IDLE_TIMEOUT / 1000.0
            finally:
                self.__timeout_lock.release()
            if do_stop:
                self.stop()
            if do_reset:
                self.__reset_and_wait()
            time.sleep(0.1)

    def __read_main_battery_voltage_level(self):
        self.__roboclaw_lock.acquire()
        try:
            front_battery_voltage_level = self.__front.read_main_battery_voltage_level()
            rear_battery_voltage_level = self.__rear.read_main_battery_voltage_level()
            return front_battery_voltage_level, rear_battery_voltage_level
        finally:
            self.__roboclaw_lock.release()

    def battery_monitor_loop(self):
        while self.__controller.is_alive():
            time.sleep(BATTERY_MONITOR_INTERVAL / 1000.0)
            if not self.__roboclaw_disabled:
                front_battery_voltage_level, rear_battery_voltage_level = self.__read_main_battery_voltage_level()
                self.__logger.info('Main battery voltage level: front: %f, rear: %f',
                                   front_battery_voltage_level / 10.0, rear_battery_voltage_level / 10.0)

    def __read_error_state(self):
        self.__roboclaw_lock.acquire()
        try:
            front_error_status = self.__front.read_error_state()
            rear_error_status = self.__rear.read_error_state()
            return front_error_status, rear_error_status
        finally:
            self.__roboclaw_lock.release()

    def error_monitor_loop(self):
        while self.__controller.is_alive():
            time.sleep(ERROR_MONITOR_INTERVAL / 1000.0)
            front_error_status, rear_error_status = self.__read_error_state()
            if front_error_status != 0 or rear_error_status != 0:
                front_error_status_tmp = front_error_status
                rear_error_status_tmp = rear_error_status
                same_errors = True
                for _ in range(CRITICAL_READ_REPEATS):
                    front_error_status, rear_error_status = self.__read_error_state()
                    if front_error_status != front_error_status_tmp or rear_error_status != rear_error_status_tmp:
                        same_errors = False
                        break
                if same_errors:
                    if front_error_status != 0:
                        self.__logger.warn('Front error: %f', front_error_status)
                    if rear_error_status != 0:
                        self.__logger.warn('Rear error: %f', rear_error_status)
                    if front_error_status in [0x01, 0x02] or rear_error_status in [0x01, 0x02]:
                        self.__reset_and_wait()
                    elif front_error_status == 0x20 or rear_error_status == 0x20:
                        self.__battery_low = True
                        return

    def __read_temperature(self):
        self.__roboclaw_lock.acquire()
        try:
            front_temp = self.__front.read_temperature() / 10.0
            rear_temp = self.__rear.read_temperature() / 10.0
            return front_temp, rear_temp
        finally:
            self.__roboclaw_lock.release()

    def temperature_monitor_loop(self):
        while not self.__battery_low or self.__controller.is_alive():
            time.sleep(TEMPERATURE_MONITOR_INTERVAL)
            if not self.__roboclaw_disabled:
                front_temp, rear_temp = self.__read_temperature()
                if self.__overheated:
                    if front_temp < TEMPERATURE_DROP and rear_temp < TEMPERATURE_DROP:
                        for _ in range(CRITICAL_READ_REPEATS):
                            front_temp, rear_temp = self.__read_temperature()
                            if front_temp > TEMPERATURE_DROP or rear_temp > TEMPERATURE_DROP:
                                self.__overheated = True
                                break
                        if self.__overheated:
                            self.__reset_and_wait()
                else:
                    if front_temp > TEMPERATURE_CRITICAL or rear_temp > TEMPERATURE_CRITICAL:
                        self.__overheated = True
                        for _ in range(CRITICAL_READ_REPEATS):
                            front_temp, rear_temp = self.__read_temperature()
                            if front_temp < TEMPERATURE_CRITICAL and rear_temp < TEMPERATURE_CRITICAL:
                                self.__overheated = False
                                break
                        if self.__overheated:
                            self.stop()

    def __reset_timeouts(self):
        act_time = time.time()

        self.__timeout_lock.acquire()
        try:
            self.__reset_time = act_time + RESET_IDLE_TIMEOUT / 1000.0
            self.__motors_stop_time = act_time + STOP_IDLE_TIMEOUT / 1000.0
            self.__motors_stop_timer_enabled = True
        finally:
            self.__timeout_lock.release()


if __name__ == '__main__':
    try:
        _serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
        _serial_port = serial_port.SerialPort(_serial)

        roboclaw_front = Roboclaw(_serial_port, FRONT_RC_ADDRESS)
        roboclaw_rear = Roboclaw(_serial_port, REAR_RC_ADDRESS)

        roboclaw_driver = RoboclawDriver(roboclaw_front, roboclaw_rear)
        roboclaw_driver.setup()

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

        controller = RoboclawController(sys.stdin, sys.stdout, roboclaw_driver)
        roboclaw_driver.set_controller(controller)

        timeout_monitor_thread = threading.Thread(target=roboclaw_driver.timeout_monitor_loop)
        battery_monitor_thread = threading.Thread(target=roboclaw_driver.battery_monitor_loop)
        error_monitor_thread = threading.Thread(target=roboclaw_driver.error_monitor_loop)
        temperature_monitor_thread = threading.Thread(target=roboclaw_driver.temperature_monitor_loop)

        timeout_monitor_thread.start()
        battery_monitor_thread.start()
        error_monitor_thread.start()
        temperature_monitor_thread.start()

        controller.run()

    except BaseException as e:
        sys.stderr.write('Run without Roboclaw.\n')
        traceback.print_exc()

        controller = NullController(sys.stdin, sys.stdout)
        controller.run()