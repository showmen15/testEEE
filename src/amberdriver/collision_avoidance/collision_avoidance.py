import logging
import logging.config
import threading
import time
import math

from ambercommon.common import runtime
import os

from amberdriver.tools import config
import collision_avoidance_logic as logic


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/collision_avoidance.ini' % pwd)
config.add_config_ini('%s/collision_avoidance.ini' % pwd)

LOGGER_NAME = 'CollisionAvoidance'

ROBO_WIDTH = float(config.ROBO_WIDTH)

MAX_SPEED = float(config.MAX_SPEED)
MAX_ROTATING_SPEED = float(config.MAX_ROTATING_SPEED)
SOFT_LIMIT = float(config.SOFT_LIMIT)
HARD_LIMIT = float(config.HARD_LIMIT)

SCANNER_DIST_OFFSET = float(config.SCANNER_DIST_OFFSET)
ANGLE_RANGE = float(config.ANGLE_RANGE)

DISTANCE_ALPHA = float(config.DISTANCE_ALPHA)
RODEO_SWAP_ALPHA = float(config.RODEO_SWAP_ALPHA)


def bound_sleep_interval(value, min_value=0.2, max_value=2.0):
    return value if min_value < value < max_value else max_value if value > max_value else min_value


class CollisionAvoidance(object):
    def __init__(self, roboclaw_proxy, hokuyo_proxy):
        self.__roboclaw_proxy = roboclaw_proxy
        self.__hokuyo_proxy = hokuyo_proxy

        self.__scan = []
        self.__scan_timestamp = 0.0
        self.__scanning_lock = threading.Condition()

        self.__driving_speed = (0, 0, 0, 0)
        self.__driving_speed_timestamp = 0.0
        self.__driving_lock = threading.Condition()

        self.__is_active = True

        self.__wait_for_data_lock = threading.Condition()

        self.__logger = logging.getLogger(LOGGER_NAME)

        runtime.add_shutdown_hook(self.terminate)

    def set_speed(self, front_left, front_right, rear_left, rear_right):
        try:
            self.__driving_lock.acquire()
            self.__driving_speed = front_left, front_right, rear_left, rear_right
            self.__driving_speed_timestamp = time.time()
            self.__notify()
        finally:
            self.__driving_lock.release()

    def stop(self):
        self.set_speed(0, 0, 0, 0)

    def get_scan(self):
        try:
            self.__scanning_lock.acquire()
            return self.__scan
        finally:
            self.__scanning_lock.release()

    def scanning_loop(self):
        sleep_interval = 0.2
        last_scan_timestamp = 0.0

        while self.__is_active:
            scan = self.__hokuyo_proxy.get_single_scan()
            scan.wait_available(sleep_interval * 1.1)
            if scan.is_available():
                self.__scanning_lock.acquire()
                try:
                    self.__scan = scan.get_points()
                    self.__scan_timestamp = scan.get_timestamp()
                    current_scan_timestamp = scan.get_timestamp()
                    self.__notify()
                finally:
                    self.__scanning_lock.release()

                scan_interval = current_scan_timestamp - last_scan_timestamp
                last_scan_timestamp = current_scan_timestamp
                if scan_interval < 2.0:
                    sleep_interval += 0.5 * (scan_interval - sleep_interval)
                    sleep_interval = bound_sleep_interval(sleep_interval)

            time.sleep(sleep_interval)

    def driving_loop(self):
        wait_timeout = 0.2
        last_scan_timestamp = 0.0
        last_command_timestamp = 0.0
        last_left, last_right = 0.0, 0.0

        while self.__is_active:
            self.__wait(wait_timeout * 1.1)

            try:
                self.__driving_lock.acquire()
                front_left, front_right, rear_left, rear_right = self.__driving_speed
                current_command_timestamp = self.__driving_speed_timestamp
            finally:
                self.__driving_lock.release()

            try:
                self.__scanning_lock.acquire()
                scan = self.__scan
                current_scan_timestamp = self.__scan_timestamp
            finally:
                self.__scanning_lock.release()

            if current_scan_timestamp > last_scan_timestamp or current_command_timestamp > last_command_timestamp:
                left = sum([front_left, rear_left]) / 2.0
                right = sum([front_right, rear_right]) / 2.0

                left, right = CollisionAvoidance.rodeo_swap(left, right, scan)
                left, right = CollisionAvoidance.limit_due_to_reverse_direction(left, right)
                left, right = CollisionAvoidance.limit_due_to_distance(left, right, scan)
                left, right = CollisionAvoidance.low_pass_filter(left, right)
                left, right = CollisionAvoidance.limit_to_max_speed(left, right)

            else:
                left, right = last_left, last_right

            current_timestamp = time.time()
            trust_level = CollisionAvoidance.scan_trust(current_scan_timestamp, current_timestamp) * \
                          CollisionAvoidance.command_trust(current_command_timestamp, current_timestamp)

            left *= trust_level
            right *= trust_level

            left, right = int(left), int(right)

            self.__roboclaw_proxy.send_motors_command(left, right, left, right)
            last_left, last_right = left, right

            command_interval = current_command_timestamp - last_command_timestamp
            last_command_timestamp = current_command_timestamp

            scan_interval = current_scan_timestamp - last_scan_timestamp
            last_scan_timestamp = current_command_timestamp

            min_interval = min(command_interval, scan_interval)
            if min_interval < 2.0:
                wait_timeout += 0.5 * (min_interval - wait_timeout)
                wait_timeout = bound_sleep_interval(wait_timeout)

    def terminate(self):
        self.stop()
        self.__is_active = False

    @staticmethod
    def limit_due_to_distance(left, right, scan):
        if left > 0 or right > 0:
            current_angle = logic.get_angle(left, right, ROBO_WIDTH)
            current_speed = logic.get_speed(left, right)

            if scan is not None:
                min_distance, _ = logic.get_min_distance(scan, current_angle,
                                                         SCANNER_DIST_OFFSET, ANGLE_RANGE)

                if min_distance is not None:
                    soft_limit = logic.get_soft_limit(current_speed, MAX_SPEED,
                                                      SOFT_LIMIT * 1.3, HARD_LIMIT * 1.3, DISTANCE_ALPHA)

                    if HARD_LIMIT * 1.3 < min_distance < soft_limit:
                        max_speed = logic.get_max_speed(min_distance, soft_limit, HARD_LIMIT * 1.3, MAX_SPEED)
                        if current_speed > max_speed:
                            left, right = CollisionAvoidance.__calculate_new_left_right(left, right,
                                                                                        max_speed, current_speed)

                    elif min_distance <= HARD_LIMIT * 1.3:
                        left, right = 0, 0

            else:
                print 'distance: no scan!'
                left, right = 0.0, 0.0

        return left, right

    @staticmethod
    def __calculate_new_left_right(left, right, max_speed, current_speed):
        if current_speed > 0:
            divide = max_speed / current_speed
            return left * divide, right * divide
        else:
            return left, right

    @staticmethod
    def limit_to_max_speed(left, right):
        left = CollisionAvoidance.__limit_to_max_speed(left)
        right = CollisionAvoidance.__limit_to_max_speed(right)

        return left, right

    @staticmethod
    def __limit_to_max_speed(value):
        max_speed = MAX_SPEED
        return max_speed if value > max_speed \
            else -max_speed if value < -max_speed \
            else value

    @staticmethod
    def limit_due_to_reverse_direction(left, right):
        max_speed = MAX_SPEED

        if (left + right) / 2.0 < 0:

            if left < 0 and right < 0:
                left = left if left > -max_speed else -max_speed
                right = right if right > -max_speed else -max_speed

            elif left < 0 < right:
                right = right if right < max_speed else max_speed
                left = -right

            elif left > 0 > right:
                left = left if left < max_speed else max_speed
                right = -left

        return left, right

    @staticmethod
    def rodeo_swap(left, right, scan):
        current_angle = logic.get_angle(left, right, ROBO_WIDTH)
        current_speed = logic.get_speed(left, right)

        min_distance, min_distance_angle = logic.get_min_distance(scan, current_angle,
                                                                  SCANNER_DIST_OFFSET, ANGLE_RANGE)

        if min_distance is not None:
            soft_limit = logic.get_soft_limit(current_speed, MAX_SPEED,
                                              SOFT_LIMIT, HARD_LIMIT, RODEO_SWAP_ALPHA)

            if min_distance < soft_limit:
                if min_distance_angle < current_angle:
                    if left > 0:
                        left = left if left < MAX_ROTATING_SPEED else MAX_ROTATING_SPEED
                        right = -left
                    else:
                        if right > 0:
                            _t = left
                            left = right
                            right = _t

                else:
                    if right > 0:
                        right = right if right < MAX_ROTATING_SPEED else MAX_ROTATING_SPEED
                        left = -right
                    else:
                        if left > 0:
                            _t = right
                            right = left
                            left = _t

            elif min_distance < soft_limit * 0.4:
                left = -left
                right = -right

        return left, right

    @staticmethod
    def low_pass_filter(left, right):
        # TODO implement low pass filter
        return left, right

    @staticmethod
    def scan_trust(scan_timestamp, current_timestamp):
        val = scan_timestamp / 1000.0 - current_timestamp
        return math.pow(4.0 / 3.0, val)

    @staticmethod
    def command_trust(command_timestamp, current_timestamp):
        val = command_timestamp - current_timestamp
        return math.pow(4.0 / 3.0, val)

    def __notify(self):
        self.__wait_for_data_lock.acquire()
        try:
            self.__wait_for_data_lock.notify_all()
        finally:
            self.__wait_for_data_lock.release()

    def __wait(self, wait_timeout):
        self.__wait_for_data_lock.acquire()
        try:
            self.__wait_for_data_lock.wait(wait_timeout)
        finally:
            self.__wait_for_data_lock.release()