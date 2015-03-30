import threading
import traceback
import sys
import time

from ambercommon.common import runtime


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

    def __init__(self, port):
        self.__port = port
        self.__port_lock = threading.RLock()

        self.__timestamp, self.__angles, self.__distances = 0, [], []
        self.__scan_lock = threading.RLock()

        self.__motor_speed = 0
        self.__high_sensitive = False

        self.__is_active = True
        self.__scanning_allowed = False
        self.__controller = None

        runtime.add_shutdown_hook(self.terminate)

    def set_controller(self, controller):
        self.__controller = controller

    def __flush(self):
        self.__port_lock.acquire()
        try:
            self.__port.write('QT\nRS\nQT\n')
            result = ''
            flushing = True
            while flushing:
                char = self.__port.read(1)
                flushing = (char != '')
                result += char
            sys.stderr.write('\n===============\nFLUSH SERIAL PORT\n"%s"\n===============\n' % result)
        finally:
            self.__port_lock.release()

    def __set_up(self):
        self.set_motor_speed(self.__motor_speed)
        self.set_high_sensitive(self.__high_sensitive)

    def __offset(self):
        count = 2
        result = ''

        self.__port_lock.acquire()
        try:
            a = self.__port.read(1)
            b = self.__port.read(1)

            while not ((a == '\n' and b == '\n') or (a == '' and b == '')):
                result += a
                a = b
                b = self.__port.read(1)
                count += 1
        finally:
            self.__port_lock.release()

        result += a
        result += b

        sys.stderr.write('READ %d EXTRA BYTES: "%s"\n' % (count, str(result)))

    def __execute_command(self, command):
        self.__port_lock.acquire()
        try:
            self.__port.write(command)
            result = self.__port.read(len(command))
            assert result == command
            return result
        finally:
            self.__port_lock.release()

    def __short_command(self, command, check_response=True):
        result = ''
        self.__port_lock.acquire()
        try:
            try:
                result += self.__execute_command(command)
                result += self.__port.read(Hokuyo.SHORT_COMMAND_LEN)

                if check_response:
                    assert result[-5:-2] == '00P'
                assert result[-2:] == '\n\n'

                return result
            except BaseException:
                sys.stderr.write('RESULT: "%s"\n' % result)
                traceback.print_exc()
                traceback.print_stack()
                self.__offset()
        finally:
            self.__port_lock.release()

    def __long_command(self, cmd, lines, check_response=True):
        result = ''
        self.__port_lock.acquire()
        try:
            try:
                result += self.__execute_command(cmd)

                result += self.__port.read(4)
                if check_response:
                    assert result[-4:-1] == '00P'
                assert result[-1:] == '\n'

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

                assert result[-2:] == '\n\n'

                return result
            except BaseException:
                sys.stderr.write('RESULT: "%s"\n' % result)
                traceback.print_exc()
                traceback.print_stack()
                self.__offset()
        finally:
            self.__port_lock.release()

    def terminate(self):
        self.reset()

        self.__scanning_allowed = False
        self.__is_active = False
        self.__port_lock.acquire()
        try:
            self.__port.close()
        finally:
            self.__port_lock.release()

    def laser_on(self):
        return self.__short_command(Hokuyo.LASER_ON, check_response=True)

    def laser_off(self):
        return self.__short_command(Hokuyo.LASER_OFF)

    def reset(self):
        return self.__short_command(Hokuyo.RESET)

    def set_motor_speed(self, motor_speed=99):
        self.__motor_speed = motor_speed
        return self.__short_command('CR' + '%02d' % motor_speed + '\n', check_response=False)

    def set_high_sensitive(self, high_sensitive=True):
        self.__high_sensitive = high_sensitive
        return self.__short_command('HS' + ('1\n' if high_sensitive else '0\n'), check_response=False)

    def get_version_info(self):
        return self.__long_command(Hokuyo.VERSION_INFO, Hokuyo.VERSION_INFO_LINES)

    def get_sensor_state(self):
        return self.__long_command(Hokuyo.SENSOR_STATE, Hokuyo.SENSOR_STATE_LINES)

    def get_sensor_specs(self):
        return self.__long_command(Hokuyo.SENSOR_SPECS, Hokuyo.SENSOR_SPECS_LINES)

    def __get_and_parse_scan(self, cluster_count, start_step, stop_step):
        distances = {}
        result = ''

        count = ((stop_step - start_step) * Hokuyo.CHARS_PER_VALUE * Hokuyo.CHARS_PER_LINE)
        count /= (Hokuyo.CHARS_PER_BLOCK * cluster_count)
        count += 5.0  # magic number
        count = int(count)

        self.__port_lock.acquire()
        try:
            result += self.__port.read(count)
        finally:
            self.__port_lock.release()

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

    def __get_single_scan(self, start_step=START_STEP, stop_step=STOP_STEP, cluster_count=1):
        self.__port_lock.acquire()
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

            scan = self.__get_and_parse_scan(cluster_count, start_step, stop_step)
            return scan

        except BaseException:
            traceback.print_exc()
            self.__offset()

        finally:
            self.__port_lock.release()

    def __get_multiple_scans(self, start_step=START_STEP, stop_step=STOP_STEP, cluster_count=1,
                             scan_interval=0, number_of_scans=0):
        self.__port_lock.acquire()
        try:
            cmd = 'MD%04d%04d%02d%01d%02d\n' % (start_step, stop_step, cluster_count, scan_interval, number_of_scans)
            self.__port.write(cmd)

            result = self.__port.read(len(cmd))
            assert result == cmd

            result += self.__port.read(Hokuyo.SHORT_COMMAND_LEN)
            assert result[-2:] == '\n\n'

            index = number_of_scans
            while number_of_scans == 0 or index > 0:
                index -= 1

                try:
                    result = self.__port.read(Hokuyo.MD_COMMAND_REPLY_LEN)
                    assert result[:13] == cmd[:13]

                    result = self.__port.read(6)
                    assert result[-1] == '\n'

                    scan = self.__get_and_parse_scan(cluster_count, start_step, stop_step)
                    yield scan

                except AssertionError:
                    sys.stderr.write('Assert error!\n')
                    traceback.print_exc()
                    self.__offset()

        except GeneratorExit:
            sys.stderr.write('Multi scan interrupted!\n')
            self.__offset()

        except BaseException:
            traceback.print_exc()
            self.__offset()

        finally:
            self.__port_lock.release()

    def enable_scanning(self, scanning_allowed):
        self.__scanning_allowed = scanning_allowed

    def __set_scan(self, scan):
        if scan is not None:
            timestamp = int(time.time() * 1000.0)
            angles, distances = Hokuyo.__parse_scan(scan)

            self.__scan_lock.acquire()
            try:
                self.__angles, self.__distances, self.__timestamp = angles, distances, timestamp
            finally:
                self.__scan_lock.release()

    def get_scan(self):
        self.__scan_lock.acquire()
        try:
            if not self.__scanning_allowed:
                scan = self.__get_single_scan()
                self.__set_scan(scan)
            return self.__angles, self.__distances, self.__timestamp
        finally:
            self.__scan_lock.release()

    def scanning_loop(self):
        while self.__is_active:
            if self.__scanning_allowed:
                self.__port_lock.acquire()
                for scan in self.__get_multiple_scans():
                    self.__set_scan(scan)
                    if not self.__scanning_allowed or not self.__is_active:
                        self.__flush()
                        self.__set_up()
                        self.laser_on()
                        self.__port_lock.release()
                        break
            time.sleep(0.1)

    @staticmethod
    def __parse_scan(scan):
        angles = sorted(scan.keys())
        distances = map(scan.get, angles)
        return angles, distances