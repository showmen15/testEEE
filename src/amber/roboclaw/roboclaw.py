import serial
import sys

from navi.tools import serial_port


__author__ = 'paoolo'


class Roboclaw(object):
    def __init__(self, port, rc_address=128):
        self.__port = port
        self.__rc_address = rc_address

    def m1_forward(self, val):
        self.__port.send_command(self.__rc_address, 0)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def m1_backward(self, val):
        self.__port.send_command(self.__rc_address, 1)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_min_main_battery(self, val):
        self.__port.send_command(self.__rc_address, 2)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_max_main_battery(self, val):
        self.__port.send_command(self.__rc_address, 3)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def m2_forward(self, val):
        self.__port.send_command(self.__rc_address, 4)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def m2_backward(self, val):
        self.__port.send_command(self.__rc_address, 5)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m1(self, val):
        self.__port.send_command(self.__rc_address, 6)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m2(self, val):
        self.__port.send_command(self.__rc_address, 7)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def forward_mixed(self, val):
        self.__port.send_command(self.__rc_address, 8)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def backward_mixed(self, val):
        self.__port.send_command(self.__rc_address, 9)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def right_mixed(self, val):
        self.__port.send_command(self.__rc_address, 10)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def left_mixed(self, val):
        self.__port.send_command(self.__rc_address, 11)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_mixed(self, val):
        self.__port.send_command(self.__rc_address, 12)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def turn_mixed(self, val):
        self.__port.send_command(self.__rc_address, 13)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_m1_encoder(self):
        self.__port.send_command(self.__rc_address, 16)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def read_m2_encoder(self):
        self.__port.send_command(self.__rc_address, 17)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def read_m1_speed(self):
        self.__port.send_command(self.__rc_address, 18)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def read_m2_speed(self):
        self.__port.send_command(self.__rc_address, 19)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def reset_encoder_cnts(self):
        self.__port.send_command(self.__rc_address, 20)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_version(self):
        self.__port.send_command(self.__rc_address, 21)
        return self.__port.read(32)

    def read_main_battery(self):
        self.__port.send_command(self.__rc_address, 24)
        val = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return val
        return -1

    def read_logic_battery(self):
        self.__port.send_command(self.__rc_address, 25)
        val = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return val
        return -1

    def set_m1_pidq(self, p, i, d, qpps):
        self.__port.send_command(self.__rc_address, 28)
        self.__port.write_long(d)
        self.__port.write_long(p)
        self.__port.write_long(i)
        self.__port.write_long(qpps)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)
        return

    def set_m2_pidq(self, p, i, d, qpps):
        self.__port.send_command(self.__rc_address, 29)
        self.__port.write_long(d)
        self.__port.write_long(p)
        self.__port.write_long(i)
        self.__port.write_long(qpps)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)
        return

    def read_m1_instspeed(self):
        self.__port.send_command(self.__rc_address, 30)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def read_m2_instspeed(self):
        self.__port.send_command(self.__rc_address, 31)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def set_m1_duty(self, val):
        self.__port.send_command(self.__rc_address, 32)
        self.__port.write_sword(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m2_duty(self, val):
        self.__port.send_command(self.__rc_address, 33)
        self.__port.write_sword(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_mixed_duty(self, m1, m2):
        self.__port.send_command(self.__rc_address, 34)
        self.__port.write_sword(m1)
        self.__port.write_sword(m2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m1_speed(self, val):
        self.__port.send_command(self.__rc_address, 35)
        self.__port.write_slong(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m2_speed(self, val):
        self.__port.send_command(self.__rc_address, 36)
        self.__port.write_slong(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_mixed_speed(self, m1, m2):
        self.__port.send_command(self.__rc_address, 37)
        self.__port.write_slong(m1)
        self.__port.write_slong(m2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m1_speed_accel(self, accel, speed):
        self.__port.send_command(self.__rc_address, 38)
        self.__port.write_long(accel)
        self.__port.write_slong(speed)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m2_speed_accel(self, accel, speed):
        self.__port.send_command(self.__rc_address, 39)
        self.__port.write_long(accel)
        self.__port.write_slong(speed)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_mixed_speed_accel(self, accel, speed1, speed2):
        self.__port.send_command(self.__rc_address, 40)
        self.__port.write_long(accel)
        self.__port.write_slong(speed1)
        self.__port.write_slong(speed2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m1_speed_distance(self, speed, distance, buf):
        self.__port.send_command(self.__rc_address, 41)
        self.__port.write_slong(speed)
        self.__port.write_long(distance)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m2_speed_distance(self, speed, distance, buf):
        self.__port.send_command(self.__rc_address, 42)
        self.__port.write_slong(speed)
        self.__port.write_long(distance)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_mixed_speed_distance(self, speed1, distance1, speed2, distance2, buf):
        self.__port.send_command(self.__rc_address, 43)
        self.__port.write_slong(speed1)
        self.__port.write_long(distance1)
        self.__port.write_slong(speed2)
        self.__port.write_long(distance2)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)
        return

    def set_m1_speed_accel_distance(self, accel, speed, distance, buf):
        self.__port.send_command(self.__rc_address, 44)
        self.__port.write_long(accel)
        self.__port.write_slong(speed)
        self.__port.write_long(distance)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m2_speed_accel_distance(self, accel, speed, distance, buf):
        self.__port.send_command(self.__rc_address, 45)
        self.__port.write_long(accel)
        self.__port.write_slong(speed)
        self.__port.write_long(distance)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_mixed_speed_accel_distance(self, accel, speed1, distance1, speed2, distance2, buf):
        self.__port.send_command(self.__rc_address, 46)
        self.__port.write_long(accel)
        self.__port.write_slong(speed1)
        self.__port.write_long(distance1)
        self.__port.write_slong(speed2)
        self.__port.write_long(distance2)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)
        return

    def read_buffer_cnts(self):
        self.__port.send_command(self.__rc_address, 47)
        buffer1 = self.__port.read_byte()
        buffer2 = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return buffer1, buffer2
        return -1, -1

    def read_currents(self):
        self.__port.send_command(self.__rc_address, 49)
        motor1 = self.__port.read_word()
        motor2 = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return motor1, motor2
        return -1, -1

    def set_mixed_speed_i_accel(self, accel1, speed1, accel2, speed2):
        self.__port.send_command(self.__rc_address, 50)
        self.__port.write_long(accel1)
        self.__port.write_slong(speed1)
        self.__port.write_long(accel2)
        self.__port.write_slong(speed2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_mixed_speed_i_accel_distance(self, accel1, speed1, distance1, accel2, speed2, distance2, buf):
        self.__port.send_command(self.__rc_address, 51)
        self.__port.write_long(accel1)
        self.__port.write_slong(speed1)
        self.__port.write_long(distance1)
        self.__port.write_long(accel2)
        self.__port.write_slong(speed2)
        self.__port.write_long(distance2)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m1_duty_accel(self, accel, duty):
        self.__port.send_command(self.__rc_address, 52)
        self.__port.write_sword(duty)
        self.__port.write_word(accel)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m2_duty_accel(self, accel, duty):
        self.__port.send_command(self.__rc_address, 53)
        self.__port.write_sword(duty)
        self.__port.write_word(accel)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_mixed_duty_accel(self, accel1, duty1, accel2, duty2):
        self.__port.send_command(self.__rc_address, 54)
        self.__port.write_sword(duty1)
        self.__port.write_word(accel1)
        self.__port.write_sword(duty2)
        self.__port.write_word(accel2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_m1_pidq(self):
        self.__port.send_command(self.__rc_address, 55)
        p = self.__port.read_long()
        i = self.__port.read_long()
        d = self.__port.read_long()
        qpps = self.__port.read_long()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return p, i, d, qpps
        return -1, -1, -1, -1

    def read_m2_pidq(self):
        self.__port.send_command(self.__rc_address, 56)
        p = self.__port.read_long()
        i = self.__port.read_long()
        d = self.__port.read_long()
        qpps = self.__port.read_long()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return p, i, d, qpps
        return -1, -1, -1, -1

    def read_main_battery_settings(self):
        self.__port.send_command(self.__rc_address, 59)
        _min = self.__port.read_word()
        _max = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return _min, _max
        return -1, -1

    def read_logic_battery_settings(self):
        self.__port.send_command(self.__rc_address, 60)
        _min = self.__port.read_word()
        _max = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return _min, _max
        return -1, -1

    def set_m1_position_constants(self, kp, ki, kd, kimax, deadzone, _min, _max):
        self.__port.send_command(self.__rc_address, 61)
        self.__port.write_long(kd)
        self.__port.write_long(kp)
        self.__port.write_long(ki)
        self.__port.write_long(kimax)
        self.__port.write_long(_min)
        self.__port.write_long(_max)

    def set_m2_position_constants(self, kp, ki, kd, kimax, deadzone, _min, _max):
        self.__port.send_command(self.__rc_address, 62)
        self.__port.write_long(kd)
        self.__port.write_long(kp)
        self.__port.write_long(ki)
        self.__port.write_long(kimax)
        self.__port.write_long(_min)
        self.__port.write_long(_max)

    def read_m1_position_constants(self):
        self.__port.send_command(self.__rc_address, 63)
        p = self.__port.read_long()
        i = self.__port.read_long()
        d = self.__port.read_long()
        imax = self.__port.read_long()
        deadzone = self.__port.read_long()
        _min = self.__port.read_long()
        _max = self.__port.read_long()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return p, i, d, imax, deadzone, _min, _max
        return -1, -1, -1, -1, -1, -1, -1

    def read_m2_position_constants(self):
        self.__port.send_command(self.__rc_address, 64)
        p = self.__port.read_long()
        i = self.__port.read_long()
        d = self.__port.read_long()
        imax = self.__port.read_long()
        deadzone = self.__port.read_long()
        _min = self.__port.read_long()
        _max = self.__port.read_long()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return p, i, d, imax, deadzone, _min, _max
        return -1, -1, -1, -1, -1, -1, -1

    def set_m1_speed_accel_deccel_position(self, accel, speed, deccel, position, buf):
        self.__port.send_command(self.__rc_address, 65)
        self.__port.write_long(accel)
        self.__port.write_long(speed)
        self.__port.write_long(deccel)
        self.__port.write_long(position)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m2_speed_accel_deccel_position(self, accel, speed, deccel, position, buf):
        self.__port.send_command(self.__rc_address, 66)
        self.__port.write_long(accel)
        self.__port.write_long(speed)
        self.__port.write_long(deccel)
        self.__port.write_long(position)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_mixed_speed_accel_deccel_position(self, accel1, speed1, deccel1, position1, accel2, speed2, deccel2,
                                              position2, buf):
        self.__port.send_command(self.__rc_address, 67)
        self.__port.write_long(accel1)
        self.__port.write_long(speed1)
        self.__port.write_long(deccel1)
        self.__port.write_long(position1)
        self.__port.write_long(accel2)
        self.__port.write_long(speed2)
        self.__port.write_long(deccel2)
        self.__port.write_long(position2)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_temperature(self):
        self.__port.send_command(self.__rc_address, 82)
        val = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return val
        return -1

    def read_error_state(self):
        self.__port.send_command(self.__rc_address, 90)
        val = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return val
        return -1


REAR_RC_ADDRESS = 128
FRONT_RC_ADDRESS = 129

MOTORS_MAX_QPPS = 13800
MOTORS_P_CONST = 65536
MOTORS_I_CONST = 32768
MOTORS_D_CONST = 16384

if __name__ == '__main__':
    robo_serial = serial.Serial(port="/dev/ttyO3", baudrate=38400, timeout=0.1)
    robo_port = serial_port.SerialPort(robo_serial)
    robo = Roboclaw(robo_port)
    robo.set_m1_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
    robo.set_m2_pidq(MOTORS_P_CONST, MOTORS_I_CONST, MOTORS_D_CONST, MOTORS_MAX_QPPS)
    if len(sys.argv) == 3:
        robo.set_mixed_speed(int(sys.argv[1]), int(sys.argv[2]))
    else:
        robo.set_mixed_speed(0, 0)