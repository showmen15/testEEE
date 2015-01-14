import logging
import logging.config
import threading
import traceback
import time
import sys

import os
import serial

from amberdriver.common import drivermsg_pb2, runtime
from amberdriver.common.amber_pipes import MessageHandler
from amberdriver.hokuyo import hokuyo_pb2
from amberdriver.null.null import NullController
from amberdriver.tools import serial_port, config


__author__ = 'paoolo'

LOGGER_NAME = 'HokuyoController'
pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/hokuyo.ini' % pwd)
config.add_config_ini('%s/hokuyo.ini' % pwd)

HIGH_SENSITIVE = bool(config.HOKUYO_HIGH_SENSITIVE_ENABLE)
SPEED_MOTOR = int(config.HOKUYO_SPEED_MOTOR)
SERIAL_PORT = config.HOKUYO_SERIAL_PORT
BAUD_RATE = config.HOKUYO_BAUD_RATE
TIMEOUT = 0.3


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
        self.__cond = threading.Condition()

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
            self.__cond.acquire()

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

        finally:
            self.__cond.release()

    def get_multiple_scan(self, start_step=START_STEP, stop_step=STOP_STEP, cluster_count=1,
                          scan_interval=0, number_of_scans=0):
        # noinspection PyBroadException
        try:
            self.__cond.acquire()

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

        finally:
            self.__cond.release()


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

        self.__timestamp, self.__angles, self.__distances = None, [], []
        self.__scan_condition = threading.Condition()

        self.__logger = logging.getLogger(LOGGER_NAME)

        self.__subscribers = []
        self.__subscribers_condition = threading.Condition()

        self.__enable_scanning = False
        self.__scanning_thread = None
        self.__scanning_thread_condition = threading.Condition()

        runtime.add_shutdown_hook(self.terminate)

    @MessageHandler.handle_and_response
    def __handle_get_single_scan(self, received_header, received_message, response_header, response_message):
        self.__logger.debug('Get single scan')

        try:
            self.__subscribers_condition.acquire()
            if len(self.__subscribers) == 0:
                angles, distances, timestamp = self.__get_scan_now()
            else:
                angles, distances, timestamp = self.__get_scan()

        finally:
            self.__subscribers_condition.release()

        response_message = self.__fill_scan(response_message, angles, distances, timestamp)

        return response_header, response_message

    def __handle_enable_scanning(self, header, message):
        self.__enable_scanning = message.Extensions[hokuyo_pb2.enable_scanning]
        self.__logger.debug('Enable scanning, set to %s' % ('true' if self.__enable_scanning else 'false'))

        if self.__enable_scanning:
            self.__try_to_start_scanning_thread()

    def handle_data_message(self, header, message):
        if message.HasExtension(hokuyo_pb2.get_single_scan):
            self.__handle_get_single_scan(header, message)

        elif message.HasExtension(hokuyo_pb2.enable_scanning):
            self.__handle_enable_scanning(header, message)

        else:
            self.__logger.warning('No request or unknown request type in message')

    def handle_subscribe_message(self, header, message):
        self.__logger.debug('Subscribe action')

        try:
            self.__subscribers_condition.acquire()

            current_subscribers_count = len(self.__subscribers)
            self.__subscribers.extend(header.clientIDs)
            if current_subscribers_count == 0:
                self.__try_to_start_scanning_thread()

        finally:
            self.__subscribers_condition.release()

    def handle_unsubscribe_message(self, header, message):
        self.__logger.debug('Unsubscribe action')

        map(lambda client_id: self.__remove_subscriber(client_id), header.clientIDs)

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died' % client_id)

        self.__remove_subscriber(client_id)

    def __scanning_run(self):
        try:
            while self.is_alive():
                subscribers = self.__get_subscribers()

                if len(subscribers) == 0 and self.__enable_scanning is False:
                    break

                angles, distances, timestamp = self.__get_scan_now()

                response_header = drivermsg_pb2.DriverHdr()
                response_message = drivermsg_pb2.DriverMsg()

                response_message.type = drivermsg_pb2.DriverMsg.DATA
                response_message.ackNum = 0

                response_header.clientIDs.extend(subscribers)
                response_message = self.__fill_scan(response_message, angles, distances, timestamp)

                self.get_pipes().write_header_and_message_to_pipe(response_header, response_message)

            self.__logger.warning('hokuyo: stop')

        finally:
            self.__remove_scanning_thread()

    def __parse_scan(self, scan):
        angles = sorted(scan.keys())
        distances = map(scan.get, self.__angles)
        return angles, distances

    def __get_scan_now(self):
        scan = self.__hokuyo.get_single_scan()
        timestamp = time.time()
        angles, distances = self.__parse_scan(scan)
        self.__set_scan(angles, distances, timestamp)
        return angles, distances, timestamp

    def __set_scan(self, angles, distances, timestamp):
        try:
            self.__scan_condition.acquire()
            self.__angles, self.__distances, self.__timestamp = angles, distances, timestamp

        finally:
            self.__scan_condition.release()

    def __get_scan(self):
        try:
            self.__scan_condition.acquire()
            return self.__angles, self.__distances, self.__timestamp

        finally:
            self.__scan_condition.release()

    @staticmethod
    def __fill_scan(response_message, angles, distances, timestamp):
        response_message.Extensions[hokuyo_pb2.scan].angles.extend(angles)
        response_message.Extensions[hokuyo_pb2.scan].distances.extend(distances)
        response_message.Extensions[hokuyo_pb2.timestamp] = timestamp
        return response_message

    def __return_current_count_and_add_subscribers(self, client_ids):
        try:
            self.__subscribers_condition.acquire()

            current_count = len(self.__subscribers)
            self.__subscribers.extend(client_ids)

            return current_count

        finally:
            self.__subscribers_condition.release()

    def __get_subscribers(self):
        try:
            self.__subscribers_condition.acquire()
            return list(self.__subscribers)

        finally:
            self.__subscribers_condition.release()

    def __get_subscribers_count(self):
        try:
            self.__subscribers_condition.acquire()
            return len(self.__subscribers)

        finally:
            self.__subscribers_condition.release()

    def __remove_subscriber(self, client_id):
        try:
            self.__subscribers_condition.acquire()
            self.__subscribers.remove(client_id)

        except ValueError:
            self.__logger.warning('Client %d does not registered as subscriber' % client_id)

        finally:
            self.__subscribers_condition.release()

    def __try_to_start_scanning_thread(self):
        try:
            self.__scanning_thread_condition.acquire()

            if self.__scanning_thread is None:
                self.__scanning_thread = threading.Thread(target=self.__scanning_run, name="scanning-thread")
                self.__scanning_thread.start()

        finally:
            self.__scanning_thread_condition.release()

    def __remove_scanning_thread(self):
        try:
            self.__scanning_thread_condition.acquire()
            self.__scanning_thread = None

        finally:
            self.__scanning_thread_condition.release()

    @staticmethod
    def __parse_scan(scan):
        angles = sorted(scan.keys())
        distances = map(scan.get, angles)
        return angles, distances

    def terminate(self):
        self.__logger.warning('hokuyo: terminate')
        self.__hokuyo.close()


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

        controller = HokuyoController(sys.stdin, sys.stdout, _serial_port)
        controller()

    except BaseException as e:
        sys.stderr.write('%s\nRun without Hokuyo.' % str(e))

        controller = NullController(sys.stdin, sys.stdout)
        controller()