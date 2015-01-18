import threading
import time
import math
import sys


__author__ = 'paoolo'


class DriveToPoint(object):
    MAX_SPEED = 300
    ROBO_WIDTH = 280.0
    DRIVING_ALPHA = 2.0
    LOCATION_X_ENUM = 0
    LOCATION_Y_ENUM = 1
    LOCATION_ALPHA_ENUM = 3

    def __init__(self, roboclaw_proxy, location_proxy):
        self.__roboclaw_proxy = roboclaw_proxy
        self.__location_proxy = location_proxy

        self.__next_targets, self.__visited_targets, self.__current_location = [], [], (0, 0, 0, 0, 0)
        self.__targets_and_location_lock = threading.Condition()

        self.__is_active = True
        self.__is_active_lock = threading.Condition()

        self.__time_stamp = time.time()

    def set_targets(self, targets):
        try:
            self.__targets_and_location_lock.acquire()
            self.__next_targets = targets
            self.__visited_targets = []
        finally:
            self.__targets_and_location_lock.release()

    def get_next_targets_and_location(self):
        try:
            self.__targets_and_location_lock.acquire()
            return self.__next_targets[:], self.__current_location
        finally:
            self.__targets_and_location_lock.release()

    def get_next_target_and_location(self):
        try:
            self.__targets_and_location_lock.acquire()
            _next_target = self.__next_targets[0] if len(self.__next_targets) > 0 else (0, 0, 0)
            return _next_target, self.__current_location
        finally:
            self.__targets_and_location_lock.release()

    def get_visited_targets_and_location(self):
        try:
            self.__targets_and_location_lock.acquire()
            return self.__visited_targets[:], self.__current_location
        finally:
            self.__targets_and_location_lock.release()

    def get_visited_target_and_location(self):
        try:
            self.__targets_and_location_lock.acquire()
            _visited_target = self.__visited_targets[-1] if len(self.__visited_targets) > 0 else (0, 0, 0)
            return _visited_target, self.__current_location
        finally:
            self.__targets_and_location_lock.release()

    def _get_next_target(self):
        try:
            self.__targets_and_location_lock.acquire()
            return self.__next_targets[0]
        finally:
            self.__targets_and_location_lock.release()

    def _add_target_to_visited(self, target):
        try:
            self.__targets_and_location_lock.acquire()
            try:
                self.__next_targets.pop(0)
            except IndexError as e:
                print e
            self.__visited_targets.append(target)
        finally:
            self.__targets_and_location_lock.release()

    def driving_loop(self):
        while self.is_active():
            try:
                while self.is_active():
                    target = self._get_next_target()
                    self._drive_to(target)
                    self._add_target_to_visited(target)
            except IndexError:
                self._stop()
            time.sleep(0.1)

    def is_active(self):
        try:
            self.__is_active_lock.acquire()
            return self.__is_active
        finally:
            self.__is_active_lock.release()

    def terminate(self):
        try:
            self.__is_active_lock.acquire()
            self.__is_active = False
            self.__roboclaw_proxy.terminate_proxy()
            self.__location_proxy.terminate_proxy()
        finally:
            self.__is_active_lock.release()

    def _drive_to(self, target):
        sys.stderr.write('Drive to %s\n' % str(target))

        self.__current_location = self._get_current_location(self.__location_proxy)

        _target_x, _target_y, _target_radius = target
        while abs(self.__current_location[DriveToPoint.LOCATION_X_ENUM] - _target_x) > _target_radius \
                or abs(self.__current_location[DriveToPoint.LOCATION_Y_ENUM] - _target_y) > _target_radius:
            self.__current_location = self._get_current_location(self.__location_proxy)

            _current_x = self.__current_location[DriveToPoint.LOCATION_X_ENUM]
            _current_y = self.__current_location[DriveToPoint.LOCATION_Y_ENUM]
            _current_angle = self.__current_location[DriveToPoint.LOCATION_ALPHA_ENUM]
            _current_angle = DriveToPoint._normalize_angle(_current_angle)

            _target_angle = math.atan2(_target_y - _current_y, _target_x - _current_x)
            _drive_angle = _target_angle - _current_angle
            _drive_angle = DriveToPoint._normalize_angle(_drive_angle)
            _drive_angle = -_drive_angle  # odbicie lustrzane mapy

            _left = DriveToPoint.MAX_SPEED - DriveToPoint.DRIVING_ALPHA * _drive_angle / math.pi * DriveToPoint.MAX_SPEED
            _right = DriveToPoint.MAX_SPEED + DriveToPoint.DRIVING_ALPHA * _drive_angle / math.pi * DriveToPoint.MAX_SPEED

            _left, _right = int(_left), int(_right)

            sys.stderr.write('Drive: %d, %d\tTarget: %d, %d, %f\tLocation: %d, %d, %f\tDrive angle:%f\n' %
                             (_left, _right,
                              _target_x, _target_y, _target_angle,
                              _current_x, _current_y, _current_angle,
                              _drive_angle))

            self.__roboclaw_proxy.send_motors_command(_left, _right, _left, _right)

        self._stop()

        sys.stderr.write('Target %s reached\n' % str(target))

    def _stop(self):
        self.__roboclaw_proxy.send_motors_command(0, 0, 0, 0)

    @staticmethod
    def _get_current_location(_location_proxy):
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
        _delta_time = _time_stamp - self.__time_stamp
        self.__time_stamp = _time_stamp
        return _delta_time

    def _calculate_new_relative_location(self, current_speed_left, current_speed_right,
                                         current_x, current_y, current_angle):
        _delta_time = self._get_delta_time()

        if current_speed_right == current_speed_left:
            _x = current_x + current_speed_left * _delta_time * math.cos(current_angle)
            _y = current_y + current_speed_right * _delta_time * math.sin(current_angle)

            _robo_angle = current_angle

        else:
            _a = 0.5 * DriveToPoint.ROBO_WIDTH * (current_speed_right + current_speed_left) / \
                 (current_speed_right - current_speed_left)
            _robo_angle = current_angle + (current_speed_right - current_speed_left) / \
                                          DriveToPoint.ROBO_WIDTH * _delta_time

            _x = current_x + _a * (math.sin(_robo_angle) - math.sin(current_angle))
            _y = current_y - _a * (math.cos(_robo_angle) - math.cos(current_angle))

            _robo_angle = DriveToPoint._normalize_angle(_robo_angle)

        return _x, _y, _robo_angle
