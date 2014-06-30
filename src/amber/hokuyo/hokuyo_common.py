import logging
import logging.config
import threading
import time

import os

from amber.common import drivermsg_pb2, runtime
from amber.common.amber_pipes import MessageHandler
from amber.hokuyo import hokuyo_pb2
from amber.tools import config


__author__ = 'paoolo'

LOGGER_NAME = 'HokuyoController'
pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/hokuyo.ini' % pwd)
config.add_config_ini('%s/hokuyo.ini' % pwd)

HIGH_SENSITIVE = bool(config.HOKUYO_HIGH_SENSITIVE_ENABLE)
SPEED_MOTOR = int(config.HOKUYO_SPEED_MOTOR)


def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i + n]


def decode(val):
    bin_str = '0b'
    for char in val:
        val = ord(char) - 0x30
        bin_str += '%06d' % int(bin(val)[2:])
    return int(bin_str, 2)


class Hokuyo(object):
    def __init__(self, port):
        self.__port = port

    def __write_command(self, command):
        self.__port.write(command)

    def __get_result(self, lines=1):
        line = 0
        result = ''
        while line < lines:
            char = self.__port.read_byte()
            if not char is None:
                char = chr(char)
                result += char
                if char == '\n':
                    line += 1
            else:
                line += 1
        return result

    def __get(self, code, lines):
        self.__write_command(code)
        return self.__get_result(lines)

    def close(self):
        self.__port.close()

    def laser_on(self):
        self.__port.write('BM\n')
        return self.__port.read(9)

    def laser_off(self):
        self.__port.write('QT\n')
        return self.__port.read(9)

    def reset(self):
        self.__port.write('RS\n')
        return self.__port.read(9)

    def set_motor_speed(self, motor_speed=99):
        self.__port.write('CR' + '%02d' % motor_speed + '\n')
        return self.__port.read(11)

    def set_high_sensitive(self, enable=True):
        self.__port.write('HS' + ('1\n' if enable else '0\n'))
        return self.__port.read(10)

    def get_version_info(self):
        return self.__get('VV\n', 8)

    def get_sensor_state(self):
        return self.__get('II\n', 10)

    def get_sensor_specs(self):
        return self.__get('PP\n', 11)

    def __get_scan(self, start_step=44, stop_step=725, cluster_count=1, multiple=False):
        distances = {}

        result = self.__get_result(4 if multiple else 3)

        count = ((stop_step - start_step) * 3 * 67) / (64 * cluster_count)
        result += self.__port.read(count)

        result = result.split('\n')
        result = map(lambda line: line[:-1], result[3:-2])
        result = ''.join(result)

        i = 0
        start = (-119.885 + 0.35208516886930985 * cluster_count * (start_step - 44))
        for chunk in chunks(result, 3):
            distances[- ((0.35208516886930985 * cluster_count * i) + start)] = decode(chunk)
            i += 1

        return distances

    def get_single_scan(self, start_step=44, stop_step=725, cluster_count=1):

        self.__port.write('GD%04d%04d%02d\n' % (start_step, stop_step, cluster_count))

        return self.__get_scan(start_step, stop_step, cluster_count)

    def get_multiple_scan(self, start_step=44, stop_step=725, cluster_count=1,
                          scan_interval=0, number_of_scans=0):

        self.__port.write('MD%04d%04d%02d%01d%02d\n' %
                          (start_step, stop_step, cluster_count, scan_interval, number_of_scans))

        index = 0
        while number_of_scans == 0 or index > 0:
            index -= 1
            yield self.__get_scan(start_step, stop_step, cluster_count, True)


class HokuyoController(MessageHandler):
    def __init__(self, pipe_in, pipe_out, port):
        super(HokuyoController, self).__init__(pipe_in, pipe_out)
        self.__hokuyo = Hokuyo(port)

        self.__hokuyo.reset()
        self.__hokuyo.laser_on()
        self.__hokuyo.set_high_sensitive(HIGH_SENSITIVE)
        self.__hokuyo.set_motor_speed(SPEED_MOTOR)

        self.__alive, self.__angles, self.__distances = True, [], []

        self.__scan_thread = threading.Thread(target=self.__scanning_run)
        runtime.add_shutdown_hook(self.terminate)
        self.__scan_thread.start()

        self.__logger = logging.getLogger(LOGGER_NAME)

        self.__subscribers = []
        self.__subscribe_thread = None

    @MessageHandler.handle_and_response
    def __handle_get_single_scan(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get single scan')

        response_message = self.__fill_scan(response_message)

        return response_header, response_message

    def handle_data_message(self, header, message):
        if message.HasExtension(hokuyo_pb2.get_single_scan):
            self.__handle_get_single_scan(header, message)

        else:
            self.__logger.warning('No request or unknown request type in message')

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action')

        no_subscribers = (len(self.__subscribers) == 0)
        self.__subscribers.extend(header.clientIDs)

        if no_subscribers or self.__subscribe_thread is None:
            self.__subscribe_thread = threading.Thread(target=self.__subscription_run)
            self.__subscribe_thread.start()

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action')

        map(lambda client_id: self.__remove_subscriber(client_id), header.clientIDs)

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died' % client_id)

        self.__remove_subscriber(client_id)

    def __remove_subscriber(self, client_id):
        try:
            self.__subscribers.remove(client_id)
        except ValueError:
            self.__logger.warning('Client %d does not registered as subscriber' % client_id)

    def __scanning_run(self):
        while self.__alive:
            scan = self.__hokuyo.get_single_scan()
            self.__angles = sorted(scan.keys())
            self.__distances = map(scan.get, self.__angles)

    def __subscription_run(self):
        try:
            while self.__alive and len(self.__subscribers) > 0:
                response_header = drivermsg_pb2.DriverHdr()
                response_message = drivermsg_pb2.DriverMsg()

                response_message.type = drivermsg_pb2.DriverMsg.DATA
                response_message.ackNum = 0

                response_header.clientIDs.extend(self.__subscribers)
                response_message = self.__fill_scan(response_message)

                self.get_pipes().write_header_and_message_to_pipe(response_header, response_message)

                # It must be less than 0.1s
                time.sleep(0.095)
        except IOError:
            self.__alive = False

    def __fill_scan(self, response_message):
        response_message.Extensions[hokuyo_pb2.scan].angles.extend(self.__angles)
        response_message.Extensions[hokuyo_pb2.scan].distances.extend(self.__distances)

        return response_message

    def terminate(self):
        self.__alive = False
        self.__hokuyo.close()