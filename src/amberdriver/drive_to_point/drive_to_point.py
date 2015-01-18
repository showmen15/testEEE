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

    def driving_loop(self):
        while self.is_active():
            try:
                while self.is_active():
                    target = self.__get_next_target()
                    self.__drive_to(target)
                    self.__add_target_to_visited(target)
            except IndexError:
                self.__stop()
            time.sleep(0.1)

    def is_active(self):
        try:
            self.__is_active_lock.acquire()
            return self.__is_active
        finally:
            self.__is_active_lock.release()

    def __get_next_target(self):
        try:
            self.__targets_and_location_lock.acquire()
            return self.__next_targets[0]
        finally:
            self.__targets_and_location_lock.release()

    def __set_current_location(self, location):
        try:
            self.__targets_and_location_lock.acquire()
            self.__current_location = location
        finally:
            self.__targets_and_location_lock.release()

    def __add_target_to_visited(self, target):
        try:
            self.__targets_and_location_lock.acquire()
            self.__next_targets.remove(target)
            self.__visited_targets.append(target)
        finally:
            self.__targets_and_location_lock.release()

    def terminate(self):
        try:
            self.__is_active_lock.acquire()
            self.__is_active = False
        finally:
            self.__is_active_lock.release()

    def __drive_to(self, target):
        sys.stderr.write('Drive to %s\n' % str(target))

        location = self.__location_proxy.get_location().get_location()
        self.__set_current_location(location)

        while not DriveToPoint.__target_reached(location, target):
            left, right = DriveToPoint.__compute_speed(location, target)
            left, right = int(left), int(right)

            self.__roboclaw_proxy.send_motors_command(left, right, left, right)

            location = self.__location_proxy.get_location().get_location()
            self.__set_current_location(location)

        self.__stop()

        sys.stderr.write('Target %s reached\n' % str(target))

    @staticmethod
    def __target_reached(location, target):
        target_x, target_y, target_radius = target
        location_x, location_y, _, _, _ = location

        diff_x = location_x - target_x
        diff_y = location_y - target_y

        return math.pow(diff_x, 2) + math.pow(diff_y, 2) < math.pow(target_radius, 2)

    @staticmethod
    def __compute_speed(location, target):
        target_x, target_y, target_radius = target

        current_x, current_y, _, current_angle, _ = location
        current_angle = DriveToPoint.__normalize_angle(current_angle)

        target_angle = math.atan2(target_y - current_y, target_x - current_x)
        drive_angle = target_angle - current_angle
        drive_angle = DriveToPoint.__normalize_angle(drive_angle)

        drive_angle = -drive_angle  # mirrored map

        left = DriveToPoint.MAX_SPEED - DriveToPoint.__compute_change(drive_angle)
        right = DriveToPoint.MAX_SPEED + DriveToPoint.__compute_change(drive_angle)

        return left, right

    def __stop(self):
        self.__roboclaw_proxy.send_motors_command(0, 0, 0, 0)

    @staticmethod
    def __normalize_angle(angle):
        if angle < -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    @staticmethod
    def __compute_change(drive_angle):
        return DriveToPoint.DRIVING_ALPHA * drive_angle / math.pi * DriveToPoint.MAX_SPEED
