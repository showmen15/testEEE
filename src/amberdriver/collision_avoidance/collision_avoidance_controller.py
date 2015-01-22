import logging
import logging.config
import sys
import threading

from amberclient.common.amber_client import AmberClient
from amberclient.hokuyo.hokuyo import HokuyoProxy
from amberclient.roboclaw.roboclaw import RoboclawProxy

import os

from amberdriver.collision_avoidance import collision_avoidance_pb2
from amberdriver.collision_avoidance.collision_avoidance import CollisionAvoidance
from amberdriver.common.message_handler import MessageHandler
from amberdriver.tools import config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/collision_avoidance.ini' % pwd)
config.add_config_ini('%s/collision_avoidance.ini' % pwd)

LOGGER_NAME = 'CollisionAvoidanceController'


class CollisionAvoidanceController(MessageHandler):
    def __init__(self, pipe_in, pipe_out, driver):
        super(CollisionAvoidanceController, self).__init__(pipe_in, pipe_out)
        self.__driver = driver
        self.__logger = logging.getLogger(LOGGER_NAME)

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
        self.__driver.drive(motors_speed.frontLeftSpeed, motors_speed.frontRightSpeed,
                            motors_speed.rearLeftSpeed, motors_speed.rearRightSpeed)

    @staticmethod
    def __fill_response_with_speed(speed, response_message):
        front_left, front_right, rear_left, rear_right = speed
        s = response_message.Extensions[collision_avoidance_pb2.motorsSpeed]
        s.frontLeftSpeed = int(front_left)
        s.frontRightSpeed = int(front_right)
        s.rearLeftSpeed = int(rear_left)
        s.rearRightSpeed = int(rear_right)

    @staticmethod
    def __fill_response_with_scan(scan, response_message):
        s = response_message.Extensions[collision_avoidance_pb2.scan]
        angles = map(lambda point: point[0], scan)
        distances = map(lambda point: point[1], scan)
        s.angles.extend(angles)
        s.distances.extend(distances)

    @MessageHandler.handle_and_response
    def __handle_get_speed(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get speed')
        speed = self.__driver.get_speed()

        self.__fill_response_with_speed(speed, response_message)

        response_message.Extensions[collision_avoidance_pb2.getSpeed] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_speed_and_scan(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get speed and scan')
        speed, scan = self.__driver.get_speed_and_scan()

        self.__fill_response_with_speed(speed, response_message)
        self.__fill_response_with_scan(scan, response_message)

        response_message.Extensions[collision_avoidance_pb2.getSpeedAndScan] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_scan(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get scan')
        scan = self.__driver.get_scan()

        self.__fill_response_with_scan(scan, response_message)

        response_message.Extensions[collision_avoidance_pb2.getScan] = True

        return response_header, response_message

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action, nothing to do...')

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action, nothing to do...')

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died, stop!' % client_id)
        self.__driver.stop()

    def terminate(self):
        self.__logger.warning('collision_avoidance: terminate')
        self.__driver.terminate()


if __name__ == '__main__':
    client_for_roboclaw = AmberClient('127.0.0.1', name='roboclaw')
    client_for_hokuyo = AmberClient('127.0.0.1', name='hokuyo')

    roboclaw_proxy = RoboclawProxy(client_for_roboclaw, 0)
    hokuyo_proxy = HokuyoProxy(client_for_hokuyo, 0)

    collision_avoidance = CollisionAvoidance(roboclaw_proxy, hokuyo_proxy)

    scanning_thread = threading.Thread(target=collision_avoidance.scanning_loop, name="scanning-thread")
    scanning_thread.start()

    measuring_thread = threading.Thread(target=collision_avoidance.measuring_loop, name="measuring-thread")
    measuring_thread.start()

    driving_thread = threading.Thread(target=collision_avoidance.driving_loop, name="driving-thread")
    driving_thread.start()

    controller = CollisionAvoidanceController(sys.stdin, sys.stdout, collision_avoidance)
    controller()