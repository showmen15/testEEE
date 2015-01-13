import logging
import sys
import threading
import time

from amberclient.common import amber_client
from amberclient.roboclaw import roboclaw
from amberclient.hokuyo import hokuyo
import os

from amberdriver.collision_avoidance import collision_avoidance_pb2
from amberdriver.common import runtime
from amberdriver.common.amber_pipes import MessageHandler


__author__ = 'paoolo'

LOGGER_NAME = 'CollisionAvoidanceController'
pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/collision_avoidance.ini' % pwd)


class CollisionAvoidance(object):
    def __init__(self):
        self._client_for_roboclaw = amber_client.AmberClient('127.0.0.1')
        self._roboclaw_proxy = roboclaw.RoboclawProxy(self._client_for_roboclaw, 0)

        self._client_for_hokuyo = amber_client.AmberClient('127.0.0.1')
        self._hokuyo_proxy = hokuyo.HokuyoProxy(self._client_for_hokuyo, 0)

        self._is_active = True
        self._is_active_lock = threading.Condition()

        self._scan = []
        self._scanning_thread = threading.Thread(target=self.__scanning, name="scanning-thread")
        self._scanning_thread.start()
        self._scanning_lock = threading.Condition()

        self._measuring_speed = (0, 0, 0, 0)
        self._measuring_thread = threading.Thread(target=self.__measuring, name="measuring-thread")
        self._measuring_thread.start()
        self._measuring_lock = threading.Condition()

        self._driving_speed = (0, 0, 0, 0)
        self._driving_thread = threading.Thread(target=self.__driving, name="driving-thread")
        self._driving_thread.start()
        self._driving_lock = threading.Condition()

    def drive(self, front_left, front_right, rear_left, rear_right):
        try:
            self._driving_lock.acquire()
            self._driving_speed = front_left, front_right, rear_left, rear_right
        finally:
            self._driving_lock.release()

    def stop(self):
        self.drive(0, 0, 0, 0)

    def __scanning(self):
        while self.is_active():
            scan = self._hokuyo_proxy.get_single_scan()
            if scan.is_available():
                try:
                    self._scanning_lock.acquire()
                    self._scan = scan.get_points()
                finally:
                    self._scanning_lock.release()
                    time.sleep(0.1)

    def get_scan(self):
        try:
            self._scanning_lock.acquire()
            return self._scan
        finally:
            self._scanning_lock.release()

    def __measuring(self):
        while self.is_active():
            current_motors_speed = self._roboclaw_proxy.get_current_motors_speed()
            if current_motors_speed.is_available():
                try:
                    self._measuring_lock.acquire()
                    self._measuring_speed = (current_motors_speed.get_front_left_speed(),
                                             current_motors_speed.get_front_right_speed(),
                                             current_motors_speed.get_rear_left_speed(),
                                             current_motors_speed.get_rear_right_speed())
                finally:
                    self._measuring_lock.release()
                    time.sleep(0.1)

    def get_speed(self):
        try:
            self._measuring_lock.acquire()
            return self._measuring_speed
        finally:
            self._measuring_lock.release()

    def get_speed_and_scan(self):
        try:
            self._measuring_lock.acquire()
            speed = self._measuring_speed
        finally:
            self._measuring_lock.release()
        try:
            self._scanning_lock.acquire()
            scan = self._scan
        finally:
            self._scanning_lock.release()
        return speed, scan

    def __driving(self):
        while self.is_active():
            try:
                self._driving_lock.acquire()
                self._roboclaw_proxy.send_motors_command(*self._driving_speed)
            finally:
                self._driving_lock.release()
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
        finally:
            self._is_active_lock.release()


class CollisionAvoidanceController(MessageHandler):
    def __init__(self, pipe_in, pipe_out):
        super(CollisionAvoidanceController, self).__init__(pipe_in, pipe_out)
        self.__collision_avoidance = CollisionAvoidance()

        self.__logger = logging.getLogger(LOGGER_NAME)

        runtime.add_shutdown_hook(self.terminate)

    def handle_data_message(self, header, message):
        if message.HasExtension(collision_avoidance_pb2.setSpeed):
            self.__handle_set_speed(header, message)

        elif message.HasExtension(collision_avoidance_pb2.getSpeed):
            self.__handle_get_speed(header, message)

        elif message.HasExtension(collision_avoidance_pb2.getSpeedAndScan):
            self.__handle_get_speed_and_scan(header, message)

        elif message.HasExtension(collision_avoidance_pb2.getScan):
            self.__handle_get_scan(header, message)

        else:
            self.__logger.warning('No request in message')

    def __handle_set_speed(self, header, message):
        self.__logger.debug('Set speed')
        motors_speed = message.Extensions[collision_avoidance_pb2.motorsSpeed]
        self.__collision_avoidance.drive(motors_speed.frontLeftSpeed, motors_speed.frontRightSpeed,
                                         motors_speed.rearLeftSpeed, motors_speed.rearRightSpeed)

    @staticmethod
    def _fill_response_with_speed(speed, response_message):
        front_left, front_right, rear_left, rear_right = speed
        s = response_message.Extensions[collision_avoidance_pb2.motorsSpeed]
        s.frontLeftSpeed = int(front_left)
        s.frontRightSpeed = int(front_right)
        s.rearLeftSpeed = int(rear_left)
        s.rearRightSpeed = int(rear_right)

    @staticmethod
    def _fill_response_with_scan(scan, response_message):
        s = response_message.Extensions[collision_avoidance_pb2.scan]
        angles = map(lambda point: point[0], scan)
        distances = map(lambda point: point[1], scan)
        s.angles.extend(angles)
        s.distances.extend(distances)

    @MessageHandler.handle_and_response
    def __handle_get_speed(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get speed')
        speed = self.__collision_avoidance.get_speed()

        self._fill_response_with_speed(speed, response_message)

        response_message.Extensions[collision_avoidance_pb2.getSpeed] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_speed_and_scan(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get speed and scan')
        speed, scan = self.__collision_avoidance.get_speed_and_scan()

        self._fill_response_with_speed(speed, response_message)
        self._fill_response_with_scan(scan, response_message)

        response_message.Extensions[collision_avoidance_pb2.getSpeedAndScan] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_scan(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get scan')
        scan = self.__collision_avoidance.get_scan()

        self._fill_response_with_scan(scan, response_message)

        response_message.Extensions[collision_avoidance_pb2.getScan] = True

        return response_header, response_message

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action, nothing to do...')

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action, nothing to do...')

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died, nothing to do...' % client_id)

    def terminate(self):
        self.__logger.warning('collision_avoidance: terminate')
        self.__collision_avoidance.terminate()


if __name__ == '__main__':
    controller = CollisionAvoidanceController(sys.stdin, sys.stdout)
    controller()
