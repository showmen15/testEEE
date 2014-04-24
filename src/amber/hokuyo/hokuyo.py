import logging
import serial
import sys

from amber.common.amber_pipes import MessageHandler
from amber.tools import serial_port, config


__author__ = 'paoolo'

LOGGER_NAME = 'Hokuyo.Controller'

SERIAL_PORT = config.HOKUYO_SERIAL_PORT
BAUD_RATE = config.HOKUYO_BAUD_RATE
TIMEOUT = 0.1


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
                result += chr(char)
                if char == '\n':
                    line += 1
            else:
                line += 1
        return result

    def __get(self, code, lines):
        self.__write_command(code)
        return self.__get_result(lines)

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
        return self.__get('VV\n', 3)

    def get_sensor_state(self):
        return self.__get('II\n', 10)

    def get_sensor_specs(self):
        return self.__get('PP\n', 11)

    def __get_scan(self, start_step=44, stop_step=725, cluster_count=1, multiple=False):
        distances = {}

        result = self.__get_result(4 if multiple else 3)
        if result[-1] == '\n' and result[-2] != '\n':
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
            yield self.__get_scan(start_step, stop_step, cluster_count)


class HokuyoController(MessageHandler):
    def __init__(self, pipe_in, pipe_out):
        super(HokuyoController, self).__init__(pipe_in, pipe_out)

        self.__serial = serial.Serial(port=SERIAL_PORT, baudrate=BAUD_RATE, timeout=TIMEOUT)
        self.__port = serial_port.SerialPort(self.__serial)
        self.__hokuyo = Hokuyo(self.__serial)

        self.__hokuyo.reset()
        self.__hokuyo.set_high_sensitive(True)

        self.__logger = logging.Logger(LOGGER_NAME)
        self.__logger.addHandler(logging.StreamHandler())

        self.__clients = []

    def handle_data_message(self, header, message):
        # TODO: check client ID, start laser etc.
        self.__hokuyo.laser_on()

    def handle_client_died_message(self, client_id):
        # TODO: handle client died - stop hokuyo laser
        if len(self.__clients) == 0:
            self.__hokuyo.laser_off()


if __name__ == '__main__':
    controller = HokuyoController(sys.stdin, sys.stdout)
    controller()