import logging
import threading
import time
import math
import sys

from amberclient.common import amber_client
from amberclient.location import location
from amberclient.roboclaw import roboclaw
import os

from amberdriver.common import runtime
from amberdriver.common.amber_pipes import MessageHandler
from amberdriver.drive_to_point import drive_to_point_pb2


__author__ = 'paoolo'

LOGGER_NAME = 'DriveToPointController'
pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/drive_to_point.ini' % pwd)


class DriveToPoint(object):
    def __init__(self, _robo_width=280.0, _alpha=1.0, _target_radius=75.0):
        self._client = amber_client.AmberClient('127.0.0.1')
        self._roboclaw_proxy = roboclaw.RoboclawProxy(self._client, 0)
        self._location_proxy = location.LocationProxy(self._client, 0)
        self._location_x, self._location_y, self._location_p, self._location_angle, self._location_timestamp = \
            0.0, 0.0, 0.0, 0.0, 0.0

        self._time_stamp = time.time()
        self._robo_width = _robo_width
        self._alpha = _alpha

    def drive_to(self, target):
        self._location_x, self._location_y, self._location_p, self._location_angle, self._location_timestamp = \
            self.__get_current_location(self._location_proxy)
        sys.stderr.write('current location: %f, %f, %f\n' % (self._location_x, self._location_y, self._location_angle))

        _target_x, _target_y, _target_radius = target
        while abs(self._location_x - _target_x) > _target_radius \
                or abs(self._location_y - _target_y) > _target_radius:
            self._location_x, self._location_y, self._location_p, self._location_angle, self._location_timestamp = \
                self.__get_current_location(self._location_proxy)
            sys.stderr.write(
                'current location: %f, %f, %f\n' % (self._location_x, self._location_y, self._location_angle))

            _target_angle = math.atan2(_target_y - self._location_y, _target_x - self._location_x)
            _drive_angle = _target_angle - self._location_angle
            _drive_angle = DriveToPoint._normalize_angle(_drive_angle)

            _left, _right = 300, 300
            _drive_speed = (_left + _right) / 2.0

            _left = _drive_speed - self._alpha * _drive_angle / math.pi * _drive_speed
            _right = _drive_speed + self._alpha * _drive_angle / math.pi * _drive_speed

            _left, _right = int(_left), int(_right)

            self._roboclaw_proxy.send_motors_command(_left, _right, _left, _right)

        self.stop()

    def get_location(self):
        return self._location_x, self._location_y, self._location_p, self._location_angle, self._location_timestamp

    def stop(self):
        self._roboclaw_proxy.send_motors_command(0, 0, 0, 0)

    @staticmethod
    def __get_current_location(_location_proxy):
        _location = _location_proxy.get_location()
        _current_x, _current_y, _current_p, _current_angle, _current_timestamp = _location.get_location()
        _current_x, _current_y = map(lambda value: 1000 * value, (_current_x, _current_y))
        return _current_x, _current_y, _current_p, _current_angle, _current_timestamp

    @staticmethod
    def _normalize_angle(angle):
        if angle < -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    def _get_delta_time(self):
        _time_stamp = time.time()
        _delta_time = _time_stamp - self._time_stamp
        self._time_stamp = _time_stamp
        return _delta_time

    def _calculate_new_relative_location(self, current_speed_left, current_speed_right,
                                         current_x, current_y, current_angle):
        _delta_time = self._get_delta_time()

        if current_speed_right == current_speed_left:
            _x = current_x + current_speed_left * _delta_time * math.cos(current_angle)
            _y = current_y + current_speed_right * _delta_time * math.sin(current_angle)

            _robo_angle = current_angle

        else:
            _a = 0.5 * self._robo_width * (current_speed_right + current_speed_left) / \
                 (current_speed_right - current_speed_left)
            _robo_angle = current_angle + (current_speed_right - current_speed_left) / \
                                          self._robo_width * _delta_time

            _x = current_x + _a * (math.sin(_robo_angle) - math.sin(current_angle))
            _y = current_y - _a * (math.cos(_robo_angle) - math.cos(current_angle))

            _robo_angle = DriveToPoint._normalize_angle(_robo_angle)

        return _x, _y, _robo_angle


class DriveToPointController(MessageHandler):
    def __init__(self, pipe_in, pipe_out):
        super(DriveToPointController, self).__init__(pipe_in, pipe_out)
        self.__drive_to_point = DriveToPoint()

        self.__targets, self.__visited_targets = None, []
        self.__targets_lock = threading.Condition()

        self.__targeting_thread = None
        self.__targeting_lock = threading.Condition()

        self.__logger = logging.getLogger(LOGGER_NAME)

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

        try:
            self.__targeting_lock.acquire()
            self.__targets_lock.acquire()

            targets = message.Extensions[drive_to_point_pb2.targets]
            self.__targets = zip(targets.longitudes, targets.latitudes, targets.radiuses)
            self.__logger.info('Set targets to %s' % str(self.__targets))

            if self.__targeting_thread is None:
                self.__targeting_thread = threading.Thread(target=self.__targeting_run)
                self.__targeting_thread.start()
        finally:
            self.__targeting_lock.release()
            self.__targets_lock.release()

    @MessageHandler.handle_and_response
    def __handle_get_next_target(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get next target')

        try:
            self.__targets_lock.acquire()
            next_target = self.__targets[0] if (self.__targets is not None and
                                                len(self.__targets) > 0) else ()
        finally:
            self.__targets_lock.release()

        response_message.Extensions[drive_to_point_pb2.getNextTarget] = True
        t = response_message.Extensions[drive_to_point_pb2.targets]
        t.longitudes.extend([next_target[0]])
        t.latitudes.extend([next_target[1]])
        t.radiuses.extend([next_target[2]])
        l = response_message.Extensions[drive_to_point_pb2.location]
        l.x, l.y, l.p, l.alfa, l.timeStamp = self.__drive_to_point.get_location()

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_next_targets(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get next targets')

        try:
            self.__targets_lock.acquire()
            next_targets = self.__targets[:] if self.__targets is not None else []
        finally:
            self.__targets_lock.release()

        response_message.Extensions[drive_to_point_pb2.getNextTargets] = True
        t = response_message.Extensions[drive_to_point_pb2.targets]
        t.longitudes.extend(map(lambda t: t[0], next_targets))
        t.latitudes.extend(map(lambda t: t[1], next_targets))
        t.radiuses.extend(map(lambda t: t[2], next_targets))
        l = response_message.Extensions[drive_to_point_pb2.location]
        l.x, l.y, l.p, l.alfa, l.timeStamp = self.__drive_to_point.get_location()

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_visited_target(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get visited target')

        try:
            self.__targets_lock.acquire()
            visited_target = self.__visited_targets[-1] if (self.__visited_targets is not None and
                                                            len(self.__visited_targets) > 0) else ()
        finally:
            self.__targets_lock.release()

        response_message.Extensions[drive_to_point_pb2.getVisitedTarget] = True
        t = response_message.Extensions[drive_to_point_pb2.targets]
        t.longitudes.extend([visited_target[0]])
        t.latitudes.extend([visited_target[1]])
        t.radiuses.extend([visited_target[2]])
        l = response_message.Extensions[drive_to_point_pb2.location]
        l.x, l.y, l.p, l.alfa, l.timeStamp = self.__drive_to_point.get_location()

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_visited_targets(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get visited targets')

        try:
            self.__targets_lock.acquire()
            visited_targets = self.__visited_targets[::-1]
        finally:
            self.__targets_lock.release()

        response_message.Extensions[drive_to_point_pb2.getVisitedTargets] = True
        t = response_message.Extensions[drive_to_point_pb2.targets]
        t.longitudes.extend(map(lambda t: t[0], visited_targets))
        t.latitudes.extend(map(lambda t: t[1], visited_targets))
        t.radiuses.extend(map(lambda t: t[2], visited_targets))
        l = response_message.Extensions[drive_to_point_pb2.location]
        l.x, l.y, l.p, l.alfa, l.timeStamp = self.__drive_to_point.get_location()

        return response_header, response_message

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action, nothing to do...')

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action, nothing to do...')

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died' % client_id)

        try:
            self.__targeting_lock.acquire()
            self.__targets_lock.acquire()

            self.__targets, self.__visited_targets = None, []
            self.__targeting_thread = None
        finally:
            self.__targeting_lock.release()
            self.__targets_lock.release()

    def __targeting_run(self):
        try:
            while self.__targets is not None and len(self.__targets) > 0:
                try:
                    self.__targets_lock.acquire()
                    target = self.__targets[0]
                finally:
                    self.__targets_lock.release()

                self.__logger.info('Drive to %s' % str(target))
                self.__drive_to_point.drive_to(target)
                self.__logger.info('Target %s reached' % str(target))

                try:
                    self.__targets_lock.acquire()
                    if self.__targets is not None:
                        self.__targets.pop(0)
                        self.__visited_targets.append(target)
                finally:
                    self.__targets_lock.release()
        finally:
            self.__drive_to_point.stop()

    def terminate(self):
        self.__logger.warning('drive_to_point: terminate')
        self.__targets = None


if __name__ == '__main__':
    controller = DriveToPointController(sys.stdin, sys.stdout)
    controller()