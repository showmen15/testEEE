import logging
import logging.config
import sys
import threading
import traceback

import os
import serial

from amberdriver.common.message_handler import MessageHandler
from amberdriver.hokuyo import hokuyo_pb2
from amberdriver.hokuyo.hokuyo import Hokuyo
from amberdriver.null.null import NullController
from amberdriver.tools import serial_port, config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/hokuyo.ini' % pwd)
config.add_config_ini('%s/hokuyo.ini' % pwd)

LOGGER_NAME = 'HokuyoController'
HIGH_SENSITIVE = config.HOKUYO_HIGH_SENSITIVE_ENABLE == 'True'
SPEED_MOTOR = int(config.HOKUYO_SPEED_MOTOR)
SERIAL_PORT = config.HOKUYO_SERIAL_PORT
BAUD_RATE = config.HOKUYO_BAUD_RATE
TIMEOUT = 0.3


class HokuyoController(MessageHandler):
    def __init__(self, pipe_in, pipe_out, driver):
        MessageHandler.__init__(self, pipe_in, pipe_out)
        self.__hokuyo = driver
        self.__logger = logging.getLogger(LOGGER_NAME)

    def handle_data_message(self, header, message):
        if message.HasExtension(hokuyo_pb2.get_single_scan):
            self.__handle_get_single_scan(header, message)

        else:
            self.__logger.warning('No recognizable request in message')

    @MessageHandler.handle_and_response
    def __handle_get_single_scan(self, _received_header, _received_message, response_header, response_message):
        self.__logger.debug('Get single scan')
        angles, distances, timestamp = self.__hokuyo.get_scan()
        response_message = HokuyoController.__fill_scan(response_message, angles, distances, timestamp)
        return response_header, response_message

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action')
        self.add_subscribers(header.clientIDs)

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action for clients %s', str(header.clientIDs))
        map(self.remove_subscriber, header.clientIDs)

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died', client_id)
        self.remove_subscriber(client_id)

    def fill_subscription_response(self, response_message):
        angles, distances, timestamp = self.__hokuyo.get_scan()
        return HokuyoController.__fill_scan(response_message, angles, distances, timestamp)

    @staticmethod
    def __fill_scan(response_message, angles, distances, timestamp):
        response_message.Extensions[hokuyo_pb2.scan].angles.extend(angles)
        response_message.Extensions[hokuyo_pb2.scan].distances.extend(distances)
        response_message.Extensions[hokuyo_pb2.timestamp] = timestamp
        return response_message


if __name__ == '__main__':
    try:
        _serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
        _serial_port = serial_port.SerialPort(_serial)

        _serial.write('QT\nRS\nQT\n')
        result = ''
        flushing = True
        while flushing:
            char = _serial.read()
            flushing = (char != '')
            result += char
        sys.stderr.write('\n===============\nFLUSH SERIAL PORT\n"%s"\n===============\n' % result)

        hokuyo = Hokuyo(_serial_port)

        sys.stderr.write('RESET:\n%s\n' % hokuyo.reset())
        sys.stderr.write('LASER_ON:\n%s\n' % hokuyo.laser_on())
        sys.stderr.write('HIGH_SENSITIVE:\n%s\n' % hokuyo.set_high_sensitive(HIGH_SENSITIVE))
        sys.stderr.write('SPEED_MOTOR:\n%s\n' % hokuyo.set_motor_speed(SPEED_MOTOR))

        sys.stderr.write('SENSOR_SPECS:\n%s\n' % hokuyo.get_sensor_specs())
        sys.stderr.write('SENSOR_STATE:\n%s\n' % hokuyo.get_sensor_state())
        sys.stderr.write('VERSION_INFO:\n%s\n' % hokuyo.get_version_info())

        scanning_thread = threading.Thread(target=hokuyo.scanning_loop, name='scanning-thread')
        scanning_thread.start()

        controller = HokuyoController(sys.stdin, sys.stdout, hokuyo)
        hokuyo.set_controller(controller)
        controller.run()

    except BaseException as e:
        sys.stderr.write('Run without Hokuyo.\n')
        traceback.print_exc()

        controller = NullController(sys.stdin, sys.stdout)
        controller.run()