import logging
import threading
import time
import math
import sys

import os
from amber.driver.common import runtime

from amber.driver.common.amber_pipes import MessageHandler
from amber.driver.drive_to_point import drive_to_point_pb2


__author__ = 'paoolo'

LOGGER_NAME = 'DriveToPointController'
pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/drive_to_point.ini' % pwd)


class DriveToPoint(object):
    def __init__(self, _robo_width=280.0, _alpha=1.0, _target_radius=75.0):
        self._client = amber_client.AmberClient('127.0.0.1')
        self._roboclaw = roboclaw.RoboclawProxy(self._client, 0)

        self._x, self._y, self._robo_angle = 0.0, 0.0, 0.0
        self._target_x, self._target_y = 0.0, 0.0

        self._robo_width = _robo_width

        self._alpha = _alpha
        self._target_radius = _target_radius

        self._time_stamp = time.time()
        self._active = True

    @staticmethod
    def _normalize_angle(angle):
        if angle < -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    @staticmethod
    def _get_speed(left, right):
        return (left + right) / 2.0

    def _compute_new_relative_position(self, speed_left, speed_right, delta_time):
        if speed_right == speed_left:
            _x = self._x + speed_left * delta_time * math.cos(self._robo_angle)
            _y = self._y + speed_right * delta_time * math.sin(self._robo_angle)

            _robo_angle = self._robo_angle

        else:
            _a = 0.5 * self._robo_width * (speed_right + speed_left) / (speed_right - speed_left)
            _robo_angle = self._robo_angle + (speed_right - speed_left) / self._robo_width * delta_time

            _x = self._x + _a * (math.sin(_robo_angle) - math.sin(self._robo_angle))
            _y = self._y - _a * (math.cos(_robo_angle) - math.cos(self._robo_angle))

            _robo_angle = DriveToPoint._normalize_angle(_robo_angle)

        return _x, _y, _robo_angle

    def _get_delta_time(self):
        _time_stamp = time.time()
        _delta_time = _time_stamp - self._time_stamp
        self._time_stamp = _time_stamp
        return _delta_time

    def modify(self, left, right):
        if abs(self._x - self._target_x) < self._target_radius \
                and abs(self._y - self._target_y) < self._target_radius:
            return 0.0, 0.0

        if self._roboclaw is None:
            return left, right

        _speed = self._roboclaw.get_current_motors_speed()
        _speed_left, speed_right = _speed.get_front_left_speed(), _speed.get_front_right_speed()

        if abs(_speed_left - left) > 500.0 or abs(speed_right - right) > 500.0:
            return left, right

        _delta_time = self._get_delta_time()
        self._x, self._y, self._robo_angle = self._compute_new_relative_position(_speed_left, speed_right, _delta_time)

        _target_angle = math.atan2(self._target_y - self._y, self._target_x - self._x)

        _drive_angle = _target_angle - self._robo_angle
        _drive_angle = DriveToPoint._normalize_angle(_drive_angle)

        if not self._active:
            self._active = (abs(_drive_angle) > 2.0 * math.pi / 3.0)
        else:
            self._active = not (abs(_drive_angle) < 0.03490658503988659)

        if not self._active:
            return left, right

        else:
            _drive_speed = DriveToPoint._get_speed(left, right)

            return _drive_speed - self._alpha * _drive_angle / math.pi * _drive_speed, \
                   _drive_speed + self._alpha * _drive_angle / math.pi * _drive_speed


class DriveToPointController(MessageHandler):
    def __init__(self, pipe_in, pipe_out):
        super(DriveToPointController, self).__init__(pipe_in, pipe_out)
        self.__drive_to_point = DriveToPoint()
        self.__targets = None

        self.__logger = logging.getLogger(LOGGER_NAME)

        self.__targeting_thread = None
        runtime.add_shutdown_hook(self.terminate)

    def handle_data_message(self, header, message):
        if message.HasExtension(drive_to_point_pb2.setTargets):
            self.__handle_set_targets(header, message)

        elif message.HasExtension(drive_to_point_pb2.getNextTarget):
            self.__handle_get_next_target(header, message)

        elif message.HasExtension(drive_to_point_pb2.getNextTargets):
            self.__handle_get_next_targets(header, message)

        elif message.HasExtension(drive_to_point_pb2.getVisitedTarget):
            self.__handle_get_visited_target(header, message)

        elif message.HasExtension(drive_to_point_pb2.getVisitedTargets):
            self.__handle_get_visited_targets(header, message)

        else:
            self.__logger.warning('No request in message')

    def __handle_set_targets(self, header, message):
        self.__logger.debug('Set targets')

        if not self.__targeting_thread is None:
            pass

        targets = message.Extensions[drive_to_point_pb2.targets]
        self.__targets = zip(targets.longitudes, targets.latitudes, targets.radiuses)

        self.__targeting_thread = threading.Thread(target=self.__targeting_run)
        self.__targeting_thread.start()

    @MessageHandler.handle_and_response
    def __handle_get_next_target(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get next target')

    @MessageHandler.handle_and_response
    def __handle_get_next_targets(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get next targets')

    @MessageHandler.handle_and_response
    def __handle_get_visited_target(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get visited target')

    @MessageHandler.handle_and_response
    def __handle_get_visited_targets(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get visited targets')

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action, nothing to do...')

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action, nothing to do...')

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died' % client_id)
        self.__targets = None

    def __targeting_run(self):
        if not self.__targets is None:
            targets_iterator = iter(self.__targets)
            try:
                while not self.__targets is None:
                    target = targets_iterator.next()
                    self.__drive_to_point.drive_to(target)
            except StopIteration:
                pass

    def terminate(self):
        self.__logger.warning('drive_to_point: terminate')
        self.__targets = None


if __name__ == '__main__':
    controller = DriveToPointController(sys.stdin, sys.stdout)
    controller()