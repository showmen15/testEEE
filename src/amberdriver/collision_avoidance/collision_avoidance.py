import logging
import logging.config
import random
import threading
import time

import os

from amberdriver.tools import config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/collision_avoidance.ini' % pwd)
config.add_config_ini('%s/collision_avoidance.ini' % pwd)

LOGGER_NAME = 'CollisionAvoidance'


def bound_sleep_interval(value, min_value=0.1, max_value=2.0):
    return value if min_value < value < max_value else max_value if value > max_value else min_value


class CollisionAvoidance(object):
    def __init__(self, roboclaw_proxy, hokuyo_proxy):
        self.__roboclaw_proxy = roboclaw_proxy
        self.__hokuyo_proxy = hokuyo_proxy

        self.__scan = []
        self.__scan_timestamp = 0.0
        self.__scanning_lock = threading.Condition()

        self.__measuring_speed = (0, 0, 0, 0)
        self.__measuring_lock = threading.Condition()

        self.__driving_speed = (0, 0, 0, 0)
        self.__driving_speed_timestamp = 0.0
        self.__driving_lock = threading.Condition()

        self.__is_active = True
        self.__is_active_lock = threading.Condition()

        self.__logger = logging.getLogger(LOGGER_NAME)

    def drive(self, front_left, front_right, rear_left, rear_right):
        try:
            self.__driving_lock.acquire()
            self.__driving_speed = front_left, front_right, rear_left, rear_right
            self.__driving_speed_timestamp = time.time()
        finally:
            self.__driving_lock.release()

    def stop(self):
        self.drive(0, 0, 0, 0)

    def get_scan(self):
        try:
            self.__scanning_lock.acquire()
            return self.__scan
        finally:
            self.__scanning_lock.release()

    def get_speed(self):
        try:
            self.__measuring_lock.acquire()
            return self.__measuring_speed
        finally:
            self.__measuring_lock.release()

    def get_speed_and_scan(self):
        try:
            self.__measuring_lock.acquire()
            speed = self.__measuring_speed
        finally:
            self.__measuring_lock.release()
        try:
            self.__scanning_lock.acquire()
            scan = self.__scan
        finally:
            self.__scanning_lock.release()
        return speed, scan

    def scanning_loop(self):
        sleep_interval = 0.2
        last_scan_timestamp = 0.0

        while self.is_active():
            scan = self.__hokuyo_proxy.get_single_scan()
            if scan.is_available():
                try:
                    self.__scanning_lock.acquire()
                    self.__scan = scan.get_points()
                    current_scan_timestamp = scan.get_timestamp()
                finally:
                    self.__scanning_lock.release()

                scan_interval = current_scan_timestamp - last_scan_timestamp
                last_scan_timestamp = current_scan_timestamp
                if scan_interval < 2.0:
                    sleep_interval += 0.5 * (scan_interval - sleep_interval)
                    sleep_interval = bound_sleep_interval(sleep_interval)

            time.sleep(sleep_interval)

    def measuring_loop(self):
        sleep_interval = 0.15

        while self.is_active():
            current_motors_speed = self.__roboclaw_proxy.get_current_motors_speed()
            if current_motors_speed.is_available():
                try:
                    self.__measuring_lock.acquire()
                    self.__measuring_speed = (current_motors_speed.get_front_left_speed(),
                                              current_motors_speed.get_front_right_speed(),
                                              current_motors_speed.get_rear_left_speed(),
                                              current_motors_speed.get_rear_right_speed())
                finally:
                    self.__measuring_lock.release()
                    sleep_interval_diff = sleep_interval * (random.random() - 0.5)
                    time.sleep(sleep_interval + sleep_interval_diff)

    def driving_loop(self):
        sleep_interval = 0.2
        last_command_timestamp = 0.0

        while self.is_active():
            try:
                self.__driving_lock.acquire()
                self.__roboclaw_proxy.send_motors_command(*self.__driving_speed)
                current_command_timestamp = self.__driving_speed_timestamp
            finally:
                self.__driving_lock.release()

            command_interval = current_command_timestamp - last_command_timestamp
            last_command_timestamp = current_command_timestamp
            if command_interval < 2.0:
                sleep_interval += 0.5 * (command_interval - sleep_interval)
                sleep_interval = bound_sleep_interval(sleep_interval)

            time.sleep(sleep_interval)

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
        finally:
            self.__is_active_lock.release()