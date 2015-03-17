import logging
import logging.config
import sys
import threading

import os
from amberclient.collision_avoidance.collision_avoidance_proxy import CollisionAvoidanceProxy
from amberclient.common.amber_client import AmberClient
from amberclient.location.location import LocationProxy
from amberclient.roboclaw.roboclaw import RoboclawProxy

from amberdriver.common.message_handler import MessageHandler
from amberdriver.drive_to_point import drive_to_point_pb2
from amberdriver.drive_to_point.drive_to_point import DriveToPoint
from amberdriver.tools import config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/drive_to_point.ini' % pwd)
config.add_config_ini('%s/drive_to_point.ini' % pwd)

LOGGER_NAME = 'DriveToPointController'
USE_COLLISION_AVOIDANCE = config.DRIVE_TO_POINT_USE_COLLISION_AVOIDANCE == 'True'


class DriveToPointController(MessageHandler):
    def __init__(self, pipe_in, pipe_out, driver):
        MessageHandler.__init__(self, pipe_in, pipe_out)
        self.__drive_to_point = driver
        self.__logger = logging.getLogger(LOGGER_NAME)

    def handle_data_message(self, header, message):
        if message.HasExtension(drive_to_point_pb2.setTargets):
            self.__handle_set_targets(header, message)

        elif message.HasExtension(drive_to_point_pb2.getNextTarget):
            self.__handle_get_next_target(header, message)

        elif message.HasExtension(drive_to_point_pb2.getNextTargets):
            self.__handle_get_next_targets(header, message)

        elif message.HasExtension(drive_to_point_pb2.getVisitedTarget):
            self.__handle_get_visited_target(header, message)

        elif message.HasExtension(drive_to_point_pb2.getVisitedTargets):
            self.__handle_get_visited_targets(header, message)

        elif message.HasExtension(drive_to_point_pb2.getConfiguration):
            self.__handle_get_configuration(header, message)

        else:
            self.__logger.warning('No request in message')

    def __handle_set_targets(self, header, message):
        self.__logger.debug('Set targets')
        targets = message.Extensions[drive_to_point_pb2.targets]
        targets = zip(targets.longitudes, targets.latitudes, targets.radiuses)
        self.__drive_to_point.set_targets(targets)

    @MessageHandler.handle_and_response
    def __handle_get_next_target(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get next target')
        next_target, current_location = self.__drive_to_point.get_next_target_and_location()

        targets = response_message.Extensions[drive_to_point_pb2.targets]
        targets.longitudes.extend([next_target[0]])
        targets.latitudes.extend([next_target[1]])
        targets.radiuses.extend([next_target[2]])

        location = response_message.Extensions[drive_to_point_pb2.location]
        location.x, location.y, location.p, location.alfa, location.timeStamp = current_location

        response_message.Extensions[drive_to_point_pb2.getNextTarget] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_next_targets(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get next targets')
        next_targets, current_location = self.__drive_to_point.get_next_targets_and_location()

        targets = response_message.Extensions[drive_to_point_pb2.targets]
        targets.longitudes.extend(map(lambda next_target: next_target[0], next_targets))
        targets.latitudes.extend(map(lambda next_target: next_target[1], next_targets))
        targets.radiuses.extend(map(lambda next_target: next_target[2], next_targets))

        location = response_message.Extensions[drive_to_point_pb2.location]
        location.x, location.y, location.p, location.alfa, location.timeStamp = current_location

        response_message.Extensions[drive_to_point_pb2.getNextTargets] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_visited_target(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get visited target')
        visited_target, current_location = self.__drive_to_point.get_visited_target_and_location()

        targets = response_message.Extensions[drive_to_point_pb2.targets]
        targets.longitudes.extend([visited_target[0]])
        targets.latitudes.extend([visited_target[1]])
        targets.radiuses.extend([visited_target[2]])

        location = response_message.Extensions[drive_to_point_pb2.location]
        location.x, location.y, location.p, location.alfa, location.timeStamp = current_location

        response_message.Extensions[drive_to_point_pb2.getVisitedTarget] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_visited_targets(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get visited targets')
        visited_targets, current_location = self.__drive_to_point.get_visited_targets_and_location()

        targets = response_message.Extensions[drive_to_point_pb2.targets]
        targets.longitudes.extend(map(lambda target: target[0], visited_targets))
        targets.latitudes.extend(map(lambda target: target[1], visited_targets))
        targets.radiuses.extend(map(lambda target: target[2], visited_targets))

        location = response_message.Extensions[drive_to_point_pb2.location]
        location.x, location.y, location.p, location.alfa, location.timeStamp = current_location

        response_message.Extensions[drive_to_point_pb2.getVisitedTargets] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_configuration(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get configuration')

        configuration = response_message.Extensions[drive_to_point_pb2.configuration]
        configuration.maxSpeed = self.__drive_to_point.MAX_SPEED

        response_message.Extensions[drive_to_point_pb2.getConfiguration] = True

        return response_header, response_message

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action, nothing to do...')

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action, nothing to do...')

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died, stop!', client_id)
        self.__drive_to_point.set_targets([])


if __name__ == '__main__':
    client_for_location = AmberClient('127.0.0.1', name='location')
    client_for_driver = AmberClient('127.0.0.1', name='driver')

    location_proxy = LocationProxy(client_for_location, 0)
    if USE_COLLISION_AVOIDANCE:
        driver_proxy = CollisionAvoidanceProxy(client_for_driver, 0)
    else:
        driver_proxy = RoboclawProxy(client_for_driver, 0)

    drive_to_point = DriveToPoint(driver_proxy, location_proxy)

    driving_thread = threading.Thread(target=drive_to_point.driving_loop, name='driving-thread')
    driving_thread.start()

    location_thread = threading.Thread(target=drive_to_point.location_loop, name='location-thread')
    location_thread.start()

    controller = DriveToPointController(sys.stdin, sys.stdout, drive_to_point)
    controller()
