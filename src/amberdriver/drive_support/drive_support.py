import logging
import logging.config
import threading
import time
import math

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


def to_mmps(val):
    return int(val * 60.0 * math.pi * 2.0 / 1865.0)


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

    def stop(self):
        self.__roboclaw_lock.acquire()
        try:
            self.__roboclaw_front.drive_mixed_with_signed_duty_cycle(0, 0)
            self.__roboclaw_rear.drive_mixed_with_signed_duty_cycle(0, 0)
        finally:
            self.__roboclaw_lock.release()

    def set_scan(self, scan):
        self.__scan = scan

    def set_speeds(self, front_left, front_right, rear_left, rear_right):
        self.__speeds = Speeds((front_left, front_right, rear_left, rear_right), time.time())

    def get_measured_speeds(self):
        self.__roboclaw_lock.acquire()
        try:
            front_left = to_mmps(self.__roboclaw_front.read_speed_m1()[0])
            front_right = to_mmps(self.__roboclaw_front.read_speed_m2()[0])
            rear_left = to_mmps(self.__roboclaw_rear.read_speed_m1()[0])
            rear_right = to_mmps(self.__roboclaw_rear.read_speed_m2()[0])
            return front_left, front_right, rear_left, rear_right
        finally:
            self.__roboclaw_lock.release()

    def driving_loop(self):
        while self.__is_active:
            speeds_values = DriveSupport.__drive_support(self.__speeds, self.__scan)
            (front_left, front_right, rear_left, rear_right) = speeds_values

            self.__roboclaw_lock.acquire()
            try:
                self.__roboclaw_front.drive_mixed_with_signed_duty_cycle(front_left, front_right)
                self.__roboclaw_rear.drive_mixed_with_signed_duty_cycle(rear_left, rear_right)
            finally:
                self.__roboclaw_lock.release()

            time.sleep(0.1)

    @staticmethod
    def __drive_support(speeds, scan):
        current_speeds_timestamp = speeds.get_timestamp()
        speeds_values = speeds.get_speeds()

        current_scan_timestamp = scan.get_timestamp()
        scan_values = scan.get_scan()

        (front_left, front_right, rear_left, rear_right) = speeds_values

        left = sum([front_left, rear_left]) / 2.0
        right = sum([front_right, rear_right]) / 2.0

        left, right = drive_support_logic.limit_due_to_distance(left, right, scan_values)

        current_timestamp = time.time()
        trust_level = drive_support_logic.scan_trust(current_scan_timestamp, current_timestamp) * \
                      drive_support_logic.command_trust(current_speeds_timestamp, current_timestamp)

        left *= trust_level
        right *= trust_level

        left, right = int(left), int(right)

        return left, right, left, right