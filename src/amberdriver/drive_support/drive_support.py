import logging
import logging.config
import threading
import time

import os
from amberclient.common.listener import Listener
from ambercommon.common import runtime

from amberdriver.drive_support import drive_support_logic
from amberdriver.tools import config, bound_sleep_interval


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/drive_support.ini' % pwd)
config.add_config_ini('%s/drive_support.ini' % pwd)

LOGGER_NAME = 'DriveSupport'


class ScanHandler(Listener):
    def __init__(self, driver):
        self.__driver_support = driver

    def handle(self, response):
        self.__driver_support.set_scan(response)


class Speeds(object):
    def __init__(self, speeds, timestamp):
        self.__speeds, self.__timestamp = speeds, timestamp

    def get_speeds(self):
        return self.__speeds

    def get_timestamp(self):
        return self.__timestamp


class DriveSupport(object):
    def __init__(self, roboclaw_front, roboclaw_rear, hokuyo_proxy):
        self.__scan = None
        self.__speeds = Speeds((0, 0, 0, 0), 0.0)

        self.__roboclaw_front, self.__roboclaw_rear = roboclaw_front, roboclaw_rear
        self.__roboclaw_lock = threading.RLock()

        self.__is_active = True

        self.__hokuyo_proxy = hokuyo_proxy
        self.__hokuyo_listener = ScanHandler(self)

        hokuyo_proxy.subscribe(self.__hokuyo_listener)

        self.__logger = logging.getLogger(LOGGER_NAME)

        runtime.add_shutdown_hook(self.terminate)

    def terminate(self):
        self.__is_active = False

        self.__hokuyo_proxy.unsubscribe(self.__hokuyo_listener)

        self.__roboclaw_lock.acquire()
        try:
            self.stop()
            self.__roboclaw_front.close()
            self.__roboclaw_rear.close()
        finally:
            self.__roboclaw_lock.release()

    def stop(self):
        self.__roboclaw_lock.acquire()
        try:
            self.__roboclaw_front.set_mixed_duty(0, 0)
            self.__roboclaw_rear.set_mixed_duty(0, 0)
        finally:
            self.__roboclaw_lock.release()

    def set_scan(self, scan):
        self.__scan = scan

    def set_speeds(self, front_left, front_right, rear_left, rear_right):
        self.__speeds = Speeds((front_left, front_right, rear_left, rear_right), time.time())

    def __get_speeds(self):
        return self.__speeds

    def get_measured_speeds(self):
        self.__roboclaw_lock.acquire()
        try:
            front_left = self.__roboclaw_front.read_m1_speed()
            front_right = self.__roboclaw_front.read_m2_speed()
            rear_left = self.__roboclaw_rear.read_m1_speed()
            rear_right = self.__roboclaw_rear.read_m2_speed()
            return front_left, front_right, rear_left, rear_right
        finally:
            self.__roboclaw_lock.release()

    def driving_loop(self):
        sleep_interval = 0.2
        last_speeds_timestamp = 0.0

        while self.__is_active:
            speeds = self.__get_speeds()
            speeds_values = speeds.get_speeds()
            current_speeds_timestamp = speeds.get_timestamp()
            is_any_non_zero = reduce(lambda acc, speed: acc or speed < 0 or speed > 0, speeds_values, False)

            if is_any_non_zero or current_speeds_timestamp > last_speeds_timestamp:
                speeds_values = DriveSupport.__drive_support(speeds, self.__scan, self.__sensor_data)
                (front_left, front_right, rear_left, rear_right) = speeds_values

                self.__roboclaw_lock.acquire()
                try:
                    self.__roboclaw_front.set_mixed_duty(front_left, front_right)
                    self.__roboclaw_rear.set_mixed_duty(rear_left, rear_right)
                finally:
                    self.__roboclaw_lock.release()

                interval = current_speeds_timestamp - last_speeds_timestamp
                last_speeds_timestamp = current_speeds_timestamp
                if interval < 2.0:
                    sleep_interval += 0.5 * (interval - sleep_interval)
                    sleep_interval = bound_sleep_interval(sleep_interval)

            time.sleep(sleep_interval)

    @staticmethod
    def __drive_support(speeds, scan, sensor_data):
        current_speeds_timestamp = speeds.get_timestamp()
        speeds_values = speeds.get_speeds()

        current_scan_timestamp = scan.get_timestamp()
        scan = scan.get_scan()

        (front_left, front_right, rear_left, rear_right) = speeds_values

        left = sum([front_left, rear_left]) / 2.0
        right = sum([front_right, rear_right]) / 2.0

        left, right = drive_support_logic.limit_due_to_distance(left, right, scan)

        current_timestamp = time.time()
        trust_level = drive_support_logic.scan_trust(current_scan_timestamp, current_timestamp) * \
                      drive_support_logic.command_trust(current_speeds_timestamp, current_timestamp)

        left *= trust_level
        right *= trust_level

        left, right = int(left), int(right)

        return left, right, left, right