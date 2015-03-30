import logging
import logging.config
import time

import os
from amberclient.common.listener import Listener
from ambercommon.common import runtime

from amberdriver.drive_support import drive_support_logic
from amberdriver.tools import config


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
    def __init__(self, roboclaw_driver, hokuyo_proxy):
        self.__scan = None
        self.__speeds = Speeds((0, 0, 0, 0), 0.0)

        self.__roboclaw_driver = roboclaw_driver

        self.__is_active = True

        self.__hokuyo_proxy = hokuyo_proxy
        self.__hokuyo_listener = ScanHandler(self)

        hokuyo_proxy.subscribe(self.__hokuyo_listener)

        self.__logger = logging.getLogger(LOGGER_NAME)

        runtime.add_shutdown_hook(self.terminate)

    def terminate(self):
        self.__is_active = False
        self.__hokuyo_proxy.unsubscribe(self.__hokuyo_listener)

    def stop(self):
        self.__roboclaw_driver.stop()

    def set_scan(self, scan):
        self.__scan = scan

    def set_speeds(self, front_left, front_right, rear_left, rear_right):
        self.__speeds = Speeds((front_left, front_right, rear_left, rear_right), time.time())

    def get_measured_speeds(self):
        return self.__roboclaw_driver.get_measured_speeds()

    def driving_loop(self):
        last_speeds = (0, 0, 0, 0)
        while self.__is_active:
            current_speeds = DriveSupport.__drive_support(self.__speeds, self.__scan)
            (front_left, front_right, rear_left, rear_right) = current_speeds
            self.__roboclaw_driver.set_speeds(front_left, front_right, rear_left, rear_right)
            time.sleep(0.05)

    @staticmethod
    def __drive_support(speeds, scan):
        if scan is None:
            return 0, 0, 0, 0

        current_speeds_timestamp = speeds.get_timestamp()
        speeds_values = speeds.get_speeds()

        current_scan_timestamp = scan.get_timestamp()
        scan_points = scan.get_points()

        (front_left, front_right, rear_left, rear_right) = speeds_values

        front_left, front_right = drive_support_logic.limit_due_to_distance(front_left, front_right, scan_points)
        rear_left, rear_right = drive_support_logic.limit_due_to_distance(rear_left, rear_right, scan_points)

        current_timestamp = time.time()
        trust_level = drive_support_logic.scan_trust(current_scan_timestamp, current_timestamp) * \
                      drive_support_logic.command_trust(current_speeds_timestamp, current_timestamp)

        front_left *= trust_level
        rear_left *= trust_level
        front_right *= trust_level
        rear_right *= trust_level

        return int(front_left), int(front_right), int(rear_left), int(rear_right)