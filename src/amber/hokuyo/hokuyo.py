import logging
import serial
import sys
import os

from amber.common import drivermsg_pb2

from amber.common.amber_pipes import MessageHandler
from amber.hokuyo import hokuyo_pb2
from amber.tools import serial_port, config


__author__ = 'paoolo'

LOGGER_NAME = 'Hokuyo.Controller'

pwd = os.path.dirname(os.path.abspath(__file__))
config.add_config_ini('%s/hokuyo.ini' % pwd)

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
        self.__hokuyo = Hokuyo(self.__port)

        self.__hokuyo.reset()
        self.__hokuyo.set_high_sensitive(True)

        self.__logger = logging.Logger(LOGGER_NAME)
        self.__logger.addHandler(logging.StreamHandler())

        self.__clients = []

    def handle_data_message(self, header, message):
        if message.HasExtension(hokuyo_pb2.laser_on):
            self.__logger.debug('Laser on')
            self.__hokuyo.laser_on()

        elif message.HasExtension(hokuyo_pb2.laser_off):
            self.__logger.debug('Laser off')
            self.__hokuyo.laser_off()

        elif message.HasExtension(hokuyo_pb2.reset):
            self.__logger.debug('Reset')
            self.__hokuyo.reset()

        elif message.HasExtension(hokuyo_pb2.set_motor_speed):
            value = message.Extensions[hokuyo_pb2.motor_speed]
            self.__logger.debug('Set motor speed to %d' % value)
            self.__hokuyo.set_motor_speed(value)

        elif message.HasExtension(hokuyo_pb2.set_high_sensitive):
            value = message.Extensions[hokuyo_pb2.high_sensitive]
            self.__logger.debug('Set high sensitive to %s' % str(value))
            self.__hokuyo.set_high_sensitive(value)

        elif message.HasExtension(hokuyo_pb2.get_version_info):
            self.__logger.debug('Get version info')
            data = self.__hokuyo.get_version_info()
            version = data.split('\n')

            driver_msg = drivermsg_pb2.DriverMsg()
            driver_hdr = drivermsg_pb2.DriverHdr()

            driver_msg.type = drivermsg_pb2.DriverMsg.DATA
            driver_msg.Extensions[hokuyo_pb2.version].response = data
            driver_msg.Extensions[hokuyo_pb2.version].vendor = version[2][5:-2]
            driver_msg.Extensions[hokuyo_pb2.version].product = version[3][5:-2]
            driver_msg.Extensions[hokuyo_pb2.version].firmware = version[4][5:-2]
            driver_msg.Extensions[hokuyo_pb2.version].protocol = version[5][5:-2]
            driver_msg.Extensions[hokuyo_pb2.version].serial = version[6][5:-2]
            driver_msg.ackNum = message.synNum

            driver_hdr.clientIDs.append(header.clientIDs[0])

            self.get_pipes().write_header_and_message_to_pipe(driver_hdr, driver_msg)

        elif message.HasExtension(hokuyo_pb2.get_sensor_state):
            self.__logger.debug('Get sensor state')
            data = self.__hokuyo.get_sensor_state()
            state = data.split('\n')

            driver_msg = drivermsg_pb2.DriverMsg()
            driver_hdr = drivermsg_pb2.DriverHdr()

            driver_msg.type = drivermsg_pb2.DriverMsg.DATA
            driver_msg.Extensions[hokuyo_pb2.state].response = data
            driver_msg.Extensions[hokuyo_pb2.state].model = state[2][5:-2]
            # driver_msg.Extensions[hokuyo_pb2.state].laser = state[3][5:-2]
            driver_msg.Extensions[hokuyo_pb2.state].motor_speed = state[4][5:-2]
            driver_msg.Extensions[hokuyo_pb2.state].measure_mode = state[5][5:-2]
            driver_msg.Extensions[hokuyo_pb2.state].bit_rate = state[6][5:-2]
            driver_msg.Extensions[hokuyo_pb2.state].time = state[7][5:-2]
            driver_msg.Extensions[hokuyo_pb2.state].diagnostic = state[8][5:-2]
            driver_msg.ackNum = message.synNum

            driver_hdr.clientIDs.append(header.clientIDs[0])

            self.get_pipes().write_header_and_message_to_pipe(driver_hdr, driver_msg)

        elif message.HasExtension(hokuyo_pb2.get_sensor_specs):
            self.__logger.debug('Get sensor specs')
            data = self.__hokuyo.get_sensor_specs()
            specs = data.split('\n')

            driver_msg = drivermsg_pb2.DriverMsg()
            driver_hdr = drivermsg_pb2.DriverHdr()

            driver_msg.type = drivermsg_pb2.DriverMsg.DATA
            driver_msg.Extensions[hokuyo_pb2.specs].response = data
            driver_msg.Extensions[hokuyo_pb2.specs].model = specs[2][5:-2]
            driver_msg.Extensions[hokuyo_pb2.specs].distance_minimum = int(specs[3][5:-2])
            driver_msg.Extensions[hokuyo_pb2.specs].distance_maximum = int(specs[4][5:-2])
            driver_msg.Extensions[hokuyo_pb2.specs].area_resolution = int(specs[5][5:-2])
            driver_msg.Extensions[hokuyo_pb2.specs].area_minimum = int(specs[6][5:-2])
            driver_msg.Extensions[hokuyo_pb2.specs].area_maximum = int(specs[7][5:-2])
            driver_msg.Extensions[hokuyo_pb2.specs].area_front = int(specs[8][5:-2])
            driver_msg.Extensions[hokuyo_pb2.specs].motor_speed = int(specs[9][5:-2])
            driver_msg.ackNum = message.synNum

            driver_hdr.clientIDs.append(header.clientIDs[0])

            self.get_pipes().write_header_and_message_to_pipe(driver_hdr, driver_msg)

        elif message.HasExtension(hokuyo_pb2.get_single_scan):
            self.__logger.debug('Get single scan')
            data = self.__hokuyo.get_single_scan(message.Extensions[hokuyo_pb2.start_step],
                                                 message.Extensions[hokuyo_pb2.stop_step],
                                                 message.Extensions[hokuyo_pb2.cluster_count])

            scan = hokuyo_pb2.Scan()
            scan.response = data

            driver_msg = drivermsg_pb2.DriverMsg()
            driver_hdr = drivermsg_pb2.DriverHdr()

            driver_msg.type = drivermsg_pb2.DriverMsg.DATA
            driver_msg.Extensions[hokuyo_pb2.scan] = scan
            driver_msg.ackNum = message.synNum

            driver_hdr.clientIDs.append(header.clientIDs[0])

            self.get_pipes().write_header_and_message_to_pipe(driver_hdr, driver_msg)

    def handle_client_died_message(self, client_id):
        # TODO: handle client died - stop hokuyo laser
        pass


if __name__ == '__main__':
    controller = HokuyoController(sys.stdin, sys.stdout)
    controller()