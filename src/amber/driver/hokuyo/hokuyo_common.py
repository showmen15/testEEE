import logging
import logging.config
import threading
import sys
import traceback

import os
from amber.driver.common import drivermsg_pb2, runtime
from amber.driver.common.amber_pipes import MessageHandler
from amber.driver.hokuyo import hokuyo_pb2
from amber.driver.tools import config


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
    SHORT_COMMAND_LEN = 5
    MD_COMMAND_REPLY_LEN = 20

    LASER_ON = 'BM\n'
    LASER_OFF = 'QT\n'
    RESET = 'RS\n'

    VERSION_INFO = 'VV\n'
    SENSOR_STATE = 'II\n'
    SENSOR_SPECS = 'PP\n'

    CHARS_PER_VALUE = 3.0
    CHARS_PER_LINE = 66.0
    CHARS_PER_BLOCK = 64.0

    START_DEG = 119.885
    STEP_DEG = 0.35208516886930985

    START_STEP = 44
    STOP_STEP = 725

    VERSION_INFO_LINES = 6
    SENSOR_STATE_LINES = 8
    SENSOR_SPECS_LINES = 9

    def __init__(self, port, _disable_assert=False):
        self.__port = port
        self.__disable_assert = _disable_assert

    def __offset(self):
        count = 2
        result = ''
        a = self.__port.read(1)
        b = self.__port.read(1)

        while not ((a == '\n' and b == '\n') or (a == '' and b == '')):
            result += a
            a = b
            b = self.__port.read(1)
            count += 1

        result += a
        result += b

        sys.stderr.write('READ %d EXTRA BYTES: "%s"\n' % (count, str(result)))

    def __execute_command(self, command):
        self.__port.write(command)

        result = self.__port.read(len(command))
        assert self.__disable_assert or result == command

        return result

    def __short_command(self, command, check_response=True):
        result = ''
        # noinspection PyBroadException
        try:
            result += self.__execute_command(command)

            result += self.__port.read(Hokuyo.SHORT_COMMAND_LEN)
            if check_response:
                assert self.__disable_assert or result[-5:-2] == '00P'
            assert self.__disable_assert or result[-2:] == '\n\n'

            return result
        except BaseException as e:
            sys.stderr.write('RESULT: "%s"' % result)
            traceback.print_exc()
            self.__offset()
            raise e

    def __long_command(self, cmd, lines, check_response=True):
        result = ''
        # noinspection PyBroadException
        try:
            result += self.__execute_command(cmd)

            result += self.__port.read(4)
            if check_response:
                assert self.__disable_assert or result[-4:-1] == '00P'
            assert self.__disable_assert or result[-1:] == '\n'

            line = 0
            while line < lines:
                char = self.__port.read_byte()
                if not char is None:
                    char = chr(char)
                    result += char
                    if char == '\n':
                        line += 1
                else:  # char is None
                    line += 1

            assert self.__disable_assert or result[-2:] == '\n\n'

            return result
        except BaseException as e:
            sys.stderr.write('RESULT: "%s"' % result)
            traceback.print_exc()
            self.__offset()
            raise e

    def close(self):
        self.__port.close()

    def laser_on(self):
        return self.__short_command(Hokuyo.LASER_ON, check_response=True)

    def laser_off(self):
        return self.__short_command(Hokuyo.LASER_OFF)

    def reset(self):
        return self.__short_command(Hokuyo.RESET)

    def set_motor_speed(self, motor_speed=99):
        return self.__short_command('CR' + '%02d' % motor_speed + '\n', check_response=False)

    def set_high_sensitive(self, enable=True):
        return self.__short_command('HS' + ('1\n' if enable else '0\n'), check_response=False)

    def get_version_info(self):
        return self.__long_command(Hokuyo.VERSION_INFO, Hokuyo.VERSION_INFO_LINES)

    def get_sensor_state(self):
        return self.__long_command(Hokuyo.SENSOR_STATE, Hokuyo.SENSOR_STATE_LINES)

    def get_sensor_specs(self):
        return self.__long_command(Hokuyo.SENSOR_SPECS, Hokuyo.SENSOR_SPECS_LINES)

    def __get_and_parse_scan(self, result, cluster_count, start_step, stop_step):
        distances = {}

        count = ((stop_step - start_step) * Hokuyo.CHARS_PER_VALUE * Hokuyo.CHARS_PER_LINE)
        count /= (Hokuyo.CHARS_PER_BLOCK * cluster_count)
        count += 1.0 + 4.0  # paoolo(FIXME): why +4.0?
        count = int(count)
        result += self.__port.read(count)

        assert result[-2:] == '\n\n'

        result = result.split('\n')
        result = map(lambda line: line[:-1], result)
        result = ''.join(result)

        i = 0
        start = (-Hokuyo.START_DEG + Hokuyo.STEP_DEG * cluster_count * (start_step - Hokuyo.START_STEP))
        for chunk in chunks(result, 3):
            distances[- ((Hokuyo.STEP_DEG * cluster_count * i) + start)] = decode(chunk)
            i += 1

        return distances

    def get_single_scan(self, start_step=START_STEP, stop_step=STOP_STEP, cluster_count=1):
        # noinspection PyBroadException
        try:
            cmd = 'GD%04d%04d%02d\n' % (start_step, stop_step, cluster_count)
            self.__port.write(cmd)

            result = self.__port.read(len(cmd))
            assert result == cmd

            result += self.__port.read(4)
            assert result[-4:-1] == '00P'
            assert result[-1] == '\n'

            result = self.__port.read(6)
            assert result[-1] == '\n'

            result = ''
            return self.__get_and_parse_scan(result, cluster_count, start_step, stop_step)
        except BaseException as e:
            traceback.print_exc()
            self.__offset()
            raise e

    def get_multiple_scan(self, start_step=START_STEP, stop_step=STOP_STEP, cluster_count=1,
                          scan_interval=0, number_of_scans=0):
        # noinspection PyBroadException
        try:
            cmd = 'MD%04d%04d%02d%01d%02d\n' % (start_step, stop_step, cluster_count, scan_interval, number_of_scans)
            self.__port.write(cmd)

            result = self.__port.read(len(cmd))
            assert result == cmd

            result += self.__port.read(Hokuyo.SHORT_COMMAND_LEN)
            assert result[-2:] == '\n\n'

            index = 0
            while number_of_scans == 0 or index > 0:
                index -= 1

                result = self.__port.read(Hokuyo.MD_COMMAND_REPLY_LEN)
                assert result[:13] == cmd[:13]

                result = self.__port.read(6)
                assert result[-1] == '\n'

                result = ''
                yield self.__get_and_parse_scan(result, cluster_count, start_step, stop_step)
        except BaseException as e:
            traceback.print_exc()
            self.__offset()
            raise e


class HokuyoController(MessageHandler):
    def __init__(self, pipe_in, pipe_out, port, _disable_assert=False):
        super(HokuyoController, self).__init__(pipe_in, pipe_out)

        self.__hokuyo = Hokuyo(port, _disable_assert=_disable_assert)

        sys.stderr.write('RESET:\n%s\n' % self.__hokuyo.reset())
        sys.stderr.write('LASER_ON:\n%s\n' % self.__hokuyo.laser_on())
        sys.stderr.write('HIGH_SENSITIVE:\n%s\n' % self.__hokuyo.set_high_sensitive(HIGH_SENSITIVE))
        sys.stderr.write('SPEED_MOTOR:\n%s\n' % self.__hokuyo.set_motor_speed(SPEED_MOTOR))

        sys.stderr.write('SENSOR_SPECS:\n%s\n' % self.__hokuyo.get_sensor_specs())
        sys.stderr.write('SENSOR_STATE:\n%s\n' % self.__hokuyo.get_sensor_state())
        sys.stderr.write('VERSION_INFO:\n%s\n' % self.__hokuyo.get_version_info())

        self.__angles, self.__distances = [], []

        self.__logger = logging.getLogger(LOGGER_NAME)

        self.__subscribers = []

        self.__scan_thread = None
        runtime.add_shutdown_hook(self.terminate)

    @MessageHandler.handle_and_response
    def __handle_get_single_scan(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get single scan')

        if len(self.__subscribers) == 0:
            scan = self.__hokuyo.get_single_scan()
            self.__angles = sorted(scan.keys())
            self.__distances = map(scan.get, self.__angles)

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

        if no_subscribers or self.__scan_thread is None:
            self.__scan_thread = threading.Thread(target=self.__scanning_run)
            self.__scan_thread.start()

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
        while self.is_alive() and len(self.__subscribers) > 0:
            scan = self.__hokuyo.get_single_scan()
            self.__angles = sorted(scan.keys())
            self.__distances = map(scan.get, self.__angles)

            response_header = drivermsg_pb2.DriverHdr()
            response_message = drivermsg_pb2.DriverMsg()

            response_message.type = drivermsg_pb2.DriverMsg.DATA
            response_message.ackNum = 0

            response_header.clientIDs.extend(self.__subscribers)
            response_message = self.__fill_scan(response_message)

            self.get_pipes().write_header_and_message_to_pipe(response_header, response_message)

        self.__logger.warning('hokuyo: stop')

    def __fill_scan(self, response_message):
        response_message.Extensions[hokuyo_pb2.scan].angles.extend(self.__angles)
        response_message.Extensions[hokuyo_pb2.scan].distances.extend(self.__distances)

        return response_message

    def terminate(self):
        self.__logger.warning('hokuyo: terminate')
        self.__hokuyo.close()