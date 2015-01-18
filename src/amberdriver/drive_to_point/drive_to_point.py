import threading
import time
import math
import sys

from amberclient.common import amber_client

from amberclient.location import location
from amberclient.roboclaw import roboclaw


__author__ = 'paoolo'


class DriveToPoint(object):
    MAX_SPEED = 300
    X = 0
    Y = 1
    ALFA = 3

    def __init__(self, _robo_width=280.0, _alpha=2.0, _target_radius=75.0):
        self._client_for_roboclaw = amber_client.AmberClient('127.0.0.1', name="roboclaw")
        self._roboclaw_proxy = roboclaw.RoboclawProxy(self._client_for_roboclaw, 0)

        self._client_for_location = amber_client.AmberClient('127.0.0.1', name="location")
        self._location_proxy = location.LocationProxy(self._client_for_location, 0)

        self._next_targets, self._visited_targets, self._current_location = [], [], (0, 0, 0, 0, 0)
        self._targets_and_location_lock = threading.Condition()

        self._is_active = True
        self._is_active_lock = threading.Condition()

        self._driving_thread = threading.Thread(target=self.__driving, name="driving-thread")
        self._driving_thread.start()

        self._time_stamp = time.time()
        self._robo_width = _robo_width
        self._alpha = _alpha

    def set_targets(self, targets):
        try:
            self._targets_and_location_lock.acquire()
            self._next_targets = targets
            self._visited_targets = []
        finally:
            self._targets_and_location_lock.release()

    def get_next_targets_and_location(self):
        try:
            self._targets_and_location_lock.acquire()
            return self._next_targets[:], self._current_location
        finally:
            self._targets_and_location_lock.release()

    def get_next_target_and_location(self):
        try:
            self._targets_and_location_lock.acquire()
            _next_target = self._next_targets[0] if len(self._next_targets) > 0 else (0, 0, 0)
            return _next_target, self._current_location
        finally:
            self._targets_and_location_lock.release()

    def get_visited_targets_and_location(self):
        try:
            self._targets_and_location_lock.acquire()
            return self._visited_targets[:], self._current_location
        finally:
            self._targets_and_location_lock.release()

    def get_visited_target_and_location(self):
        try:
            self._targets_and_location_lock.acquire()
            _visited_target = self._visited_targets[-1] if len(self._visited_targets) > 0 else (0, 0, 0)
            return _visited_target, self._current_location
        finally:
            self._targets_and_location_lock.release()

    def _get_next_target(self):
        try:
            self._targets_and_location_lock.acquire()
            return self._next_targets[0]
        finally:
            self._targets_and_location_lock.release()

    def _add_target_to_visited(self, target):
        try:
            self._targets_and_location_lock.acquire()
            try:
                self._next_targets.pop(0)
            except IndexError as e:
                print e
            self._visited_targets.append(target)
        finally:
            self._targets_and_location_lock.release()

    def __driving(self):
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
            self._is_active_lock.acquire()
            return self._is_active
        finally:
            self._is_active_lock.release()

    def terminate(self):
        try:
            self._is_active_lock.acquire()
            self._is_active = False
            self._client_for_location.terminate()
            self._client_for_roboclaw.terminate()
        finally:
            self._is_active_lock.release()

    def _drive_to(self, target):
        sys.stderr.write('Drive to %s\n' % str(target))

        self._current_location = self._get_current_location(self._location_proxy)

        _target_x, _target_y, _target_radius = target
        while abs(self._current_location[DriveToPoint.X] - _target_x) > _target_radius \
                or abs(self._current_location[DriveToPoint.Y] - _target_y) > _target_radius:
            self._current_location = self._get_current_location(self._location_proxy)

            _current_x = self._current_location[DriveToPoint.X]
            _current_y = self._current_location[DriveToPoint.Y]
            _current_angle = self._current_location[DriveToPoint.ALFA]
            _current_angle = DriveToPoint._normalize_angle(_current_angle)

            _target_angle = math.atan2(_target_y - _current_y, _target_x - _current_x)
            _drive_angle = _target_angle - _current_angle
            _drive_angle = DriveToPoint._normalize_angle(_drive_angle)
            _drive_angle = -_drive_angle  # odbicie lustrzane mapy

            _left = DriveToPoint.MAX_SPEED - self._alpha * _drive_angle / math.pi * DriveToPoint.MAX_SPEED
            _right = DriveToPoint.MAX_SPEED + self._alpha * _drive_angle / math.pi * DriveToPoint.MAX_SPEED

            _left, _right = int(_left), int(_right)

            sys.stderr.write('Drive: %d, %d\tTarget: %d, %d, %f\tLocation: %d, %d, %f\tDrive angle:%f\n' %
                             (_left, _right,
                              _target_x, _target_y, _target_angle,
                              _current_x, _current_y, _current_angle,
                              _drive_angle))

            self._roboclaw_proxy.send_motors_command(_left, _right, _left, _right)

        self._stop()

        sys.stderr.write('Target %s reached\n' % str(target))

    def _stop(self):
        self._roboclaw_proxy.send_motors_command(0, 0, 0, 0)

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
