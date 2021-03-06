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

        else:
            self.__logger.warning('No request in message')

    def __handle_set_speed(self, _, message):
        self.__logger.debug('Set speed')
        motors_speed = message.Extensions[collision_avoidance_pb2.motorsSpeed]
        self.__driver.set_speed(motors_speed.frontLeftSpeed, motors_speed.frontRightSpeed,
                                motors_speed.rearLeftSpeed, motors_speed.rearRightSpeed)

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action, nothing to do...')

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action, nothing to do...')

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died, stop!', client_id)
        self.__driver.stop()


if __name__ == '__main__':
    client_for_roboclaw = AmberClient('127.0.0.1', name='roboclaw')
    client_for_hokuyo = AmberClient('127.0.0.1', name='hokuyo')

    roboclaw_proxy = RoboclawProxy(client_for_roboclaw, 0)
    hokuyo_proxy = HokuyoProxy(client_for_hokuyo, 0)

    collision_avoidance = CollisionAvoidance(roboclaw_proxy, hokuyo_proxy)

    scanning_thread = threading.Thread(target=collision_avoidance.scanning_loop, name="scanning-thread")
    scanning_thread.start()

    driving_thread = threading.Thread(target=collision_avoidance.driving_loop, name="driving-thread")
    driving_thread.start()

    controller = CollisionAvoidanceController(sys.stdin, sys.stdout, collision_avoidance)
    controller()