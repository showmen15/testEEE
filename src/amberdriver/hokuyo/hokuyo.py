import threading
import traceback
import sys


__author__ = 'paoolo'


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
                if char is not None:
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
