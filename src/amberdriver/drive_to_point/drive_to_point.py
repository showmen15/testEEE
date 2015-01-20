import logging
import logging.config
import threading
import time
import math
import sys

import os

from amberdriver.tools import config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/drive_to_point.ini' % pwd)
config.add_config_ini('%s/drive_to_point.ini' % pwd)

LOGGER_NAME = 'DriveToPoint'


def bound_sleep(value):
    return value if 0.2 < value < 2.0 else 2.0 if value > 2.0 else 0.2


class DriveToPoint(object):
    MAX_SPEED = 250
    DRIVING_ALPHA = 3.0  # cut at 60st
    TIMESTAMP_FIELD = 4

    def __init__(self, roboclaw_proxy, location_proxy):
        self.__roboclaw_proxy = roboclaw_proxy
        self.__location_proxy = location_proxy

        self.__next_targets, self.__visited_targets, self.__current_location = [], [], None
        self.__targets_and_location_lock = threading.Condition()

        self.__is_active = True
        self.__is_active_lock = threading.Condition()

        self.__old_left, self.__old_right = 0.0, 0.0
        self.__logger = logging.getLogger(LOGGER_NAME)

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

    def location_loop(self):
        sleep_interval = 0.5

        # FIXME(paoolo): change to wait for first location
        time.sleep(sleep_interval)

        last_location = self.__location_proxy.get_location()
        last_location = last_location.get_location()

        time.sleep(sleep_interval)
        while self.is_active():
            current_location = self.__location_proxy.get_location()
            current_location = current_location.get_location()
            self.__set_current_location(current_location)
            location_interval = current_location[DriveToPoint.TIMESTAMP_FIELD] - \
                                last_location[DriveToPoint.TIMESTAMP_FIELD]
            location_interval /= 1000.0
            last_location = current_location
            if location_interval > 2.0:
                sleep_interval += 0.5 * (location_interval - sleep_interval)
                sleep_interval = bound_sleep(sleep_interval)
            sys.stderr.write('local:sleep %f\n' % sleep_interval)
            time.sleep(sleep_interval)

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

    def __get_current_location(self):
        try:
            self.__targets_and_location_lock.acquire()
            return self.__current_location
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
        self.__logger.info('Drive to %s\n' % str(target))

        sleep_interval = 0.5

        location = self.__get_current_location()
        while location is None:
            time.sleep(sleep_interval)
            location = self.__get_current_location()

        while not DriveToPoint.target_reached(location, target):
            left, right = DriveToPoint.compute_speed(location, target)
            left, right = self.__low_pass(left, right)
            left, right = int(left), int(right)
            self.__roboclaw_proxy.send_motors_command(left, right, left, right)

            sys.stderr.write('drive:sleep %f\n' % sleep_interval)
            time.sleep(sleep_interval)

            old_location = location
            location = self.__get_current_location()

            location_interval = location[DriveToPoint.TIMESTAMP_FIELD] - old_location[DriveToPoint.TIMESTAMP_FIELD]
            location_interval /= 1000.0
            if location_interval > 2.0:
                sleep_interval += 0.5 * (location_interval - sleep_interval)
                sleep_interval = bound_sleep(sleep_interval)

        self.__stop()

        self.__logger.info('Target %s reached\n' % str(target))

    def __low_pass(self, left, right):
        self.__old_left += 0.5 * (left - self.__old_left)
        self.__old_right += 0.5 * (right - self.__old_right)
        return self.__old_left, self.__old_right

    def __stop(self):
        self.__roboclaw_proxy.send_motors_command(0, 0, 0, 0)

    @staticmethod
    def target_reached(location, target):
        target_x, target_y, target_radius = target
        location_x, location_y, _, _, _ = location

        diff_x = location_x - target_x
        diff_y = location_y - target_y

        return math.pow(diff_x, 2) + math.pow(diff_y, 2) < math.pow(target_radius, 2)

    @staticmethod
    def compute_speed(location, target):
        target_x, target_y, target_radius = target

        location_x, location_y, _, location_angle, _ = location
        location_trust = DriveToPoint.location_trust(location)
        location_angle = DriveToPoint.normalize_angle(location_angle)

        target_angle = math.atan2(target_y - location_y, target_x - location_x)
        drive_angle = target_angle - location_angle
        drive_angle = DriveToPoint.normalize_angle(drive_angle)
        drive_angle = -drive_angle  # mirrored map

        if location_trust < 0.3:
            # bad, stop it now
            return 0.0, 0.0

        if abs(drive_angle) < math.pi / 18:  # 10st
            # drive normal
            left, right = DriveToPoint.MAX_SPEED, DriveToPoint.MAX_SPEED

        elif abs(drive_angle) > math.pi / 3:  # 60st
            # rotate in place
            left = DriveToPoint.MAX_SPEED * 2 / (6 * drive_angle / math.pi - 1)
            right = -DriveToPoint.MAX_SPEED * (6 * drive_angle / math.pi - 2)
            if drive_angle < 0:
                left, right = right, left

        else:
            # drive on turn
            left = DriveToPoint.MAX_SPEED - DriveToPoint.compute_change(drive_angle)
            right = DriveToPoint.MAX_SPEED + DriveToPoint.compute_change(drive_angle)

        if location_trust < 0.8:
            # control situation
            left *= location_trust
            right *= location_trust

        return left, right

    @staticmethod
    def location_trust(location):
        _, _, location_probability, _, location_timestamp = location
        location_timestamp /= 1000
        current_timestamp = time.time()
        return location_probability * math.pow(2, location_timestamp - current_timestamp)

    @staticmethod
    def normalize_angle(angle):
        if angle < -math.pi:
            angle += 2 * math.pi
        elif angle > math.pi:
            angle -= 2 * math.pi
        return angle

    @staticmethod
    def compute_change(drive_angle):
        return DriveToPoint.DRIVING_ALPHA * drive_angle / math.pi * DriveToPoint.MAX_SPEED