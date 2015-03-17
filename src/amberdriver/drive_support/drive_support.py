import threading
import time

from amberclient.common.listener import Listener
from ambercommon.common import runtime


__author__ = 'paoolo'


def bound_sleep_interval(value, min_value=0.2, max_value=2.0):
    return value if min_value < value < max_value else max_value if value > max_value else min_value


class ScanHandler(Listener):
    def __init__(self, driver):
        self.__driver_support = driver

    def handle(self, response):
        self.__driver_support.set_scan(response)


class SensorDataHandler(Listener):
    def __init__(self, driver):
        self.__driver_support = driver

    def handle(self, response):
        self.__driver_support.set_sensor_data(response)


class DriveSupport(object):
    def __init__(self, roboclaw_front, roboclaw_rear, hokuyo_proxy, ninedof_proxy):
        self.__scan, self.__sensor_data = None, None

        self.__roboclaw_front, self.__roboclaw_rear = roboclaw_front, roboclaw_rear
        self.__roboclaw_lock = threading.Lock()

        self.__speeds_timestamp, self.__speeds = 0, (0, 0, 0, 0)
        self.__speeds_lock = threading.Lock()

        self.__measured_speeds_timestamp, self.__measured_speeds = 0, None
        self.__measured_speeds_lock = threading.Lock()

        self.__is_active = True

        self.__hokuyo_proxy, self.__ninedof_proxy = hokuyo_proxy, ninedof_proxy
        self.__hokuyo_listener = ScanHandler(self)
        self.__ninedof_listener = SensorDataHandler(self)

        hokuyo_proxy.subscribe(self.__hokuyo_listener)
        ninedof_proxy.subscribe(self.__ninedof_listener)

        runtime.add_shutdown_hook(self.terminate)

    def terminate(self):
        self.__is_active = False

        self.__hokuyo_proxy.unsubscribe(self.__hokuyo_listener)
        self.__ninedof_proxy.unsubscribe(self.__ninedof_listener)

        self.__roboclaw_lock.acquire()
        try:
            self.stop()
            self.__roboclaw_front.close()
            self.__roboclaw_rear.close()
        finally:
            self.__roboclaw_lock.release()

    def stop(self):
        self.__roboclaw_front.set_mixed_duty(0, 0)
        self.__roboclaw_rear.set_mixed_duty(0, 0)

    def set_scan(self, scan):
        self.__scan = scan

    def set_sensor_data(self, sensor_data):
        self.__sensor_data = sensor_data

    def set_speeds(self, front_left, front_right, rear_left, rear_right):
        self.__speeds_lock.acquire()
        try:
            self.__speeds = (front_left, front_right, rear_left, rear_right)
            self.__speeds_timestamp = time.time()
        finally:
            self.__speeds_lock.release()

    def __get_speeds(self):
        self.__speeds_lock.acquire()
        try:
            return self.__speeds, self.__speeds_timestamp
        finally:
            self.__speeds_lock.release()

    def __set_measure_speeds(self, speeds):
        if speeds is not None:
            self.__measured_speeds_lock.acquire()
            try:
                self.__measured_speeds = speeds
            finally:
                self.__measured_speeds_lock.release()

    def get_measured_speeds(self):
        self.__measured_speeds_lock.acquire()
        try:
            return self.__measured_speeds
        finally:
            self.__measured_speeds_lock.release()

    def measuring_loop(self):
        while self.__is_active:
            self.__roboclaw_lock.acquire()
            try:
                front_left = self.__roboclaw_front.read_m1_speed()
                front_right = self.__roboclaw_front.read_m2_speed()
                rear_left = self.__roboclaw_rear.read_m1_speed()
                rear_right = self.__roboclaw_rear.read_m2_speed()
                self.__set_measure_speeds((front_left, front_right, rear_left, rear_right))
            finally:
                self.__roboclaw_lock.release()
            time.sleep(0.1)

    def avoiding_loop(self):
        while self.__is_active:
            time.sleep(0.1)

    def driving_loop(self):
        sleep_interval = 0.2
        last_speeds_timestamp = 0.0

        while self.__is_active:
            (front_left, front_right, rear_left, rear_right), current_speeds_timestamp = self.__get_speeds()

            if current_speeds_timestamp > last_speeds_timestamp:
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