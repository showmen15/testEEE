import logging
import logging.config
import sys
import threading

import os
from amberclient.collision_avoidance.collision_avoidance_proxy import CollisionAvoidanceProxy
from amberclient.common.amber_client import AmberClient
from amberclient.location.location import LocationProxy
from amberclient.roboclaw.roboclaw import RoboclawProxy
from ambercommon.common import runtime

from amberdriver.common.message_handler import MessageHandler
from amberdriver.drive_to_point import drive_to_point_pb2
from amberdriver.drive_to_point.drive_to_point import DriveToPoint
from amberdriver.tools import config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/drive_to_point.ini' % pwd)
config.add_config_ini('%s/drive_to_point.ini' % pwd)

LOGGER_NAME = 'DriveToPointController'


class DriveToPointController(MessageHandler):
    def __init__(self, pipe_in, pipe_out, driver):
        MessageHandler.__init__(self, pipe_in, pipe_out)
        self.__drive_to_point = driver
        self.__logger = logging.getLogger(LOGGER_NAME)

        runtime.add_shutdown_hook(self.terminate)

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
        _next_target, _current_location = self.__drive_to_point.get_next_target_and_location()

        _targets = response_message.Extensions[drive_to_point_pb2.targets]
        _targets.longitudes.extend([_next_target[0]])
        _targets.latitudes.extend([_next_target[1]])
        _targets.radiuses.extend([_next_target[2]])

        _location = response_message.Extensions[drive_to_point_pb2.location]
        _location.x, _location.y, _location.p, _location.alfa, _location.timeStamp = _current_location

        response_message.Extensions[drive_to_point_pb2.getNextTarget] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_next_targets(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get next targets')
        next_targets, _current_location = self.__drive_to_point.get_next_targets_and_location()

        _targets = response_message.Extensions[drive_to_point_pb2.targets]
        _targets.longitudes.extend(map(lambda next_target: next_target[0], next_targets))
        _targets.latitudes.extend(map(lambda next_target: next_target[1], next_targets))
        _targets.radiuses.extend(map(lambda next_target: next_target[2], next_targets))

        _location = response_message.Extensions[drive_to_point_pb2.location]
        _location.x, _location.y, _location.p, _location.alfa, _location.timeStamp = _current_location

        response_message.Extensions[drive_to_point_pb2.getNextTargets] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_visited_target(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get visited target')
        visited_target, _current_location = self.__drive_to_point.get_visited_target_and_location()

        _targets = response_message.Extensions[drive_to_point_pb2.targets]
        _targets.longitudes.extend([visited_target[0]])
        _targets.latitudes.extend([visited_target[1]])
        _targets.radiuses.extend([visited_target[2]])

        _location = response_message.Extensions[drive_to_point_pb2.location]
        _location.x, _location.y, _location.p, _location.alfa, _location.timeStamp = _current_location

        response_message.Extensions[drive_to_point_pb2.getVisitedTarget] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_visited_targets(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get visited targets')
        visited_targets, _current_location = self.__drive_to_point.get_visited_targets_and_location()

        _targets = response_message.Extensions[drive_to_point_pb2.targets]
        _targets.longitudes.extend(map(lambda target: target[0], visited_targets))
        _targets.latitudes.extend(map(lambda target: target[1], visited_targets))
        _targets.radiuses.extend(map(lambda target: target[2], visited_targets))

        _location = response_message.Extensions[drive_to_point_pb2.location]
        _location.x, _location.y, _location.p, _location.alfa, _location.timeStamp = _current_location

        response_message.Extensions[drive_to_point_pb2.getVisitedTargets] = True

        return response_header, response_message

    @MessageHandler.handle_and_response
    def __handle_get_configuration(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get configuration')

        _configuration = response_message.Extensions[drive_to_point_pb2.configuration]
        _configuration.maxSpeed = self.__drive_to_point.MAX_SPEED

        response_message.Extensions[drive_to_point_pb2.getConfiguration] = True

        return response_header, response_message

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action, nothing to do...')

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action, nothing to do...')

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died, stop!', client_id)
        self.__drive_to_point.set_targets([])

    def terminate(self):
        self.__logger.warning('drive_to_point: terminate')
        self.__drive_to_point.terminate()


if __name__ == '__main__':
    client_for_driver = AmberClient('127.0.0.1', name="roboclaw")
    client_for_location = AmberClient('127.0.0.1', name="location")

    if '__COLLISION_AVOIDANCE_ENABLE' in os.environ:
        driver_proxy = CollisionAvoidanceProxy(client_for_driver, 0)
    else:
        driver_proxy = RoboclawProxy(client_for_driver, 0)

    location_proxy = LocationProxy(client_for_location, 0)

    drive_to_point = DriveToPoint(driver_proxy, location_proxy)

    driving_thread = threading.Thread(target=drive_to_point.driving_loop, name="driving-thread")
    driving_thread.start()

    location_thread = threading.Thread(target=drive_to_point.location_loop, name="location-thread")
    location_thread.start()

    controller = DriveToPointController(sys.stdin, sys.stdout, drive_to_point)
    controller()
