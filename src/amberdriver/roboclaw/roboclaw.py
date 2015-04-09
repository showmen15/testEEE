from ambercommon.common import runtime

__author__ = 'paoolo'


class Roboclaw(object):
    def __init__(self, port, rc_address=128):
        self.__port = port
        self.__rc_address = rc_address

        runtime.add_shutdown_hook(self.terminate)

    def terminate(self):
        self.drive_mixed_with_signed_duty_cycle(0, 0)
        self.close()

    def close(self):
        self.__port.close()

    def drive_forward_m1(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 0)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_backwards_m1(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 1)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_min_main_voltage(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 2)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_max_main_voltage(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 3)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_forward_m2(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 4)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_backwards_m2(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 5)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m1(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 6)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m2(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 7)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_forward(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 8)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_backwards(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 9)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def turn_right(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 10)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def turn_left(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 11)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_forward_or_backwards(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 12)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def turn_left_or_right(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 13)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_quad_encoder_register_m1(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 16)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def read_quad_encoder_register_m2(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 17)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def read_speed_m1(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 18)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def read_speed_m2(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 19)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def reset_quad_encoder_counters(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 20)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_firmware_version(self):
        self.__port.send_command(self.__rc_address, 21)
        return self.__port.read(32)

    def read_main_battery_voltage_level(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 24)
        val = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return val
        return -1

    def read_logic_battery_voltage_level(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 25)
        val = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return val
        return -1

    def set_min_logic_voltage_level(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 26)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_max_logic_voltage_level(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 27)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_pid_constants_m1(self, p, i, d, qpps):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 28)
        self.__port.write_long(d)
        self.__port.write_long(p)
        self.__port.write_long(i)
        self.__port.write_long(qpps)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)
        return

    def set_pid_constants_m2(self, p, i, d, qpps):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 29)
        self.__port.write_long(d)
        self.__port.write_long(p)
        self.__port.write_long(i)
        self.__port.write_long(qpps)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)
        return

    def read_current_speed_m1(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 30)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def read_current_speed_m2(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 31)
        enc = self.__port.read_slong()
        status = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return enc, status
        return -1, -1

    def drive_m1_with_signed_duty_cycle(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 32)
        self.__port.write_sword(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m2_with_signed_duty_cycle(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 33)
        self.__port.write_sword(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_mixed_with_signed_duty_cycle(self, m1, m2):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 34)
        self.__port.write_sword(m1)
        self.__port.write_sword(m2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m1_with_signed_speed(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 35)
        self.__port.write_slong(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m2_with_signed_speed(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 36)
        self.__port.write_slong(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_mixed_with_signed_speed(self, m1, m2):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 37)
        self.__port.write_slong(m1)
        self.__port.write_slong(m2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m1_with_signed_speed_accel(self, accel, speed):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 38)
        self.__port.write_long(accel)
        self.__port.write_slong(speed)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m2_with_signed_speed_accel(self, accel, speed):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 39)
        self.__port.write_long(accel)
        self.__port.write_slong(speed)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_mixed_with_signed_speed_accel(self, accel, speed1, speed2):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 40)
        self.__port.write_long(accel)
        self.__port.write_slong(speed1)
        self.__port.write_slong(speed2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def buffered_m1_drive_with_signed_speed_distance(self, speed, distance, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 41)
        self.__port.write_slong(speed)
        self.__port.write_long(distance)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def buffered_m2_drive_with_signed_speed_distance(self, speed, distance, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 42)
        self.__port.write_slong(speed)
        self.__port.write_long(distance)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def buffered_drive_mixed_with_signed_speed_distance(self, speed1, distance1, speed2, distance2, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 43)
        self.__port.write_slong(speed1)
        self.__port.write_long(distance1)
        self.__port.write_slong(speed2)
        self.__port.write_long(distance2)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def buffered_m1_drive_with_signed_speed_accel_distance(self, accel, speed, distance, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 44)
        self.__port.write_long(accel)
        self.__port.write_slong(speed)
        self.__port.write_long(distance)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def buffered_m2_drive_with_signed_speed_accel_distance(self, accel, speed, distance, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 45)
        self.__port.write_long(accel)
        self.__port.write_slong(speed)
        self.__port.write_long(distance)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_mixed_with_signed_speed_accel_distance(self, accel, speed1, distance1, speed2, distance2, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 46)
        self.__port.write_long(accel)
        self.__port.write_slong(speed1)
        self.__port.write_long(distance1)
        self.__port.write_slong(speed2)
        self.__port.write_long(distance2)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_buffer_length(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 47)
        buffer1 = self.__port.read_byte()
        buffer2 = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return buffer1, buffer2
        return -1, -1

    def read_motor_currents(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 49)
        motor1 = self.__port.read_word()
        motor2 = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return motor1, motor2
        return -1, -1

    def drive_mixed_with_speed_individual_accel(self, accel1, speed1, accel2, speed2):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 50)
        self.__port.write_long(accel1)
        self.__port.write_slong(speed1)
        self.__port.write_long(accel2)
        self.__port.write_slong(speed2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_mixed_with_speed_individual_accel_distance(self,
                                                         accel1, speed1, distance1, accel2, speed2, distance2, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 51)
        self.__port.write_long(accel1)
        self.__port.write_slong(speed1)
        self.__port.write_long(distance1)
        self.__port.write_long(accel2)
        self.__port.write_slong(speed2)
        self.__port.write_long(distance2)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m1_with_signed_duty_accel(self, accel, duty):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 52)
        self.__port.write_sword(duty)
        self.__port.write_word(accel)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m2_with_signed_duty_accel(self, accel, duty):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 53)
        self.__port.write_sword(duty)
        self.__port.write_word(accel)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_mixed_with_signed_duty_accel(self, accel1, duty1, accel2, duty2):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 54)
        self.__port.write_sword(duty1)
        self.__port.write_word(accel1)
        self.__port.write_sword(duty2)
        self.__port.write_word(accel2)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_m1_pidq_settings(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 55)
        p = self.__port.read_long()
        i = self.__port.read_long()
        d = self.__port.read_long()
        qpps = self.__port.read_long()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return p, i, d, qpps
        return -1, -1, -1, -1

    def read_m2_pidq_settings(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 56)
        p = self.__port.read_long()
        i = self.__port.read_long()
        d = self.__port.read_long()
        qpps = self.__port.read_long()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return p, i, d, qpps
        return -1, -1, -1, -1

    def set_main_battery_voltages(self, _min, _max):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 57)
        self.__port.write_word(_min)
        self.__port.write_word(_max)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_logic_battery_voltages(self, _min, _max):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 58)
        self.__port.write_word(_min)
        self.__port.write_word(_max)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def read_main_battery_voltage_settings(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 59)
        _min = self.__port.read_word()
        _max = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return _min, _max
        return -1, -1

    def read_logic_battery_voltage_settings(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 60)
        _min = self.__port.read_word()
        _max = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return _min, _max
        return -1, -1

    def set_m1_position_pid_constants(self, kp, ki, kd, kimax, deadzone, _min, _max):
        self.__port.send_command(self.__rc_address, 61)
        self.__port.write_long(kp)
        self.__port.write_long(ki)
        self.__port.write_long(kd)
        self.__port.write_long(kimax)
        self.__port.write_long(deadzone)
        self.__port.write_long(_min)
        self.__port.write_long(_max)

    def set_m2_position_pid_constants(self, kp, ki, kd, kimax, deadzone, _min, _max):
        self.__port.send_command(self.__rc_address, 62)
        self.__port.write_long(kp)
        self.__port.write_long(ki)
        self.__port.write_long(kd)
        self.__port.write_long(kimax)
        self.__port.write_long(deadzone)
        self.__port.write_long(_min)
        self.__port.write_long(_max)

    def read_m1_position_pid_constants(self):
        self.__port.reset_checksum()
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

    def read_m2_position_pid_constants(self):
        self.__port.reset_checksum()
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

    def drive_m1_with_signed_speed_accel_deccel_position(self, accel, speed, deccel, position, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 65)
        self.__port.write_long(accel)
        self.__port.write_long(speed)
        self.__port.write_long(deccel)
        self.__port.write_long(position)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_m2_with_signed_speed_accel_deccel_position(self, accel, speed, deccel, position, buf):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 66)
        self.__port.write_long(accel)
        self.__port.write_long(speed)
        self.__port.write_long(deccel)
        self.__port.write_long(position)
        self.__port.write_byte(buf)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def drive_mixed_with_signed_speed_accel_deccel_position(self,
                                                            accel1, speed1, deccel1, position1,
                                                            accel2, speed2, deccel2, position2,
                                                            buf):
        self.__port.reset_checksum()
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
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 82)
        val = self.__port.read_word()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return val
        return -1

    def read_error_state(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 90)
        val = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return val
        return -1

    def read_encoder_mode(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 91)
        mode1 = self.__port.read_byte()
        mode2 = self.__port.read_byte()
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return mode1, mode2
        return -1

    def set_m1_encoder_mode(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 92)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def set_m2_encoder_mode(self, val):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 93)
        self.__port.write_byte(val)
        self.__port.write_byte(self.__port.get_checksum() & 0x7F)

    def write_settings_to_eeprom(self):
        self.__port.reset_checksum()
        self.__port.send_command(self.__rc_address, 94)
        crc = self.__port.get_checksum() & 0x7F
        if crc == self.__port.read_byte():
            return crc
        return -1