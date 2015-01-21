import struct

from amberdriver.tools import serial_port


__author__ = 'paoolo'

import unittest
import mock


class SerialPortTestCase(unittest.TestCase):
    def setUp(self):
        self.mocked_serial_port = mock.Mock()
        self.port = serial_port.SerialPort(self.mocked_serial_port)

    def tearDown(self):
        pass


class CloseTestCase(SerialPortTestCase):
    def runTest(self):
        self.port.close()
        self.mocked_serial_port.close.assert_called_once_with()


class ReadTestCase(SerialPortTestCase):
    def runTest(self):
        size = mock.Mock()
        self.port.read(size)
        self.mocked_serial_port.read.assert_called_once_with(size)


class WriteTestCase(SerialPortTestCase):
    def runTest(self):
        char = mock.Mock()
        self.port.write(char)
        self.mocked_serial_port.write.assert_called_once_with(char)


class SendCommandTestCase(SerialPortTestCase):
    def runTest(self):
        # TODO(paoolo): check how to mock int
        address, command = int(), int()
        calls = [mock.call.write(chr(address)), mock.call.write(chr(address))]
        checksum = self.port.get_checksum()
        self.port.send_command(address, command)
        self.mocked_serial_port.write.assert_has_calls(calls)
        checksum += (address + command)
        assert self.port.get_checksum() == checksum


class ReadByteTestCase(SerialPortTestCase):
    def runTest(self):
        # TODO(paoolo): check how to mock string
        value = str(' ')
        self.mocked_serial_port.read = mock.Mock(return_value=value)
        checksum = self.port.get_checksum()
        result = struct.unpack('>B', value)
        result = result[0]
        assert self.port.read_byte() == result
        self.mocked_serial_port.read.assert_called_once_with(len(value))
        checksum += result
        assert self.port.get_checksum() == checksum
        self.mocked_serial_port.read = mock.Mock(return_value=str())
        assert self.port.read_byte() is None


class ReadSignedByteTestCase(SerialPortTestCase):
    def runTest(self):
        value = str(' ')
        self.mocked_serial_port.read = mock.Mock(return_value=value)
        checksum = self.port.get_checksum()
        result = struct.unpack('>b', value)
        result = result[0]
        assert self.port.read_sbyte() == result
        self.mocked_serial_port.read.assert_called_once_with(len(value))
        checksum += result
        assert self.port.get_checksum() == checksum
        self.mocked_serial_port.read = mock.Mock(return_value=str())
        assert self.port.read_sbyte() is None


class ReadWordTestCase(SerialPortTestCase):
    def runTest(self):
        value = str('  ')
        self.mocked_serial_port.read = mock.Mock(return_value=value)
        checksum = self.port.get_checksum()
        result = struct.unpack('>H', value)
        result = result[0]
        assert self.port.read_word() == result
        self.mocked_serial_port.read.assert_called_once_with(len(value))
        checksum += (result & 0XFF) + ((result >> 8) & 0xFF)
        assert self.port.get_checksum() == checksum
        self.mocked_serial_port.read = mock.Mock(return_value=str())
        assert self.port.read_word() is None


class ReadSignedWordTestCase(SerialPortTestCase):
    def runTest(self):
        value = str('  ')
        self.mocked_serial_port.read = mock.Mock(return_value=value)
        checksum = self.port.get_checksum()
        result = struct.unpack('>h', value)
        result = result[0]
        assert self.port.read_sword() == result
        self.mocked_serial_port.read.assert_called_once_with(len(value))
        # TODO(paoolo): check signed checksum computation
        checksum += (result & 0xFF) + ((result >> 8) & 0xFF)
        assert self.port.get_checksum() == checksum
        self.mocked_serial_port.read = mock.Mock(return_value=str())
        assert self.port.read_sword() is None


class ReadLongTestCase(SerialPortTestCase):
    def runTest(self):
        value = str('    ')
        self.mocked_serial_port.read = mock.Mock(return_value=value)
        checksum = self.port.get_checksum()
        result = struct.unpack('>L', value)
        result = result[0]
        assert self.port.read_long() == result
        self.mocked_serial_port.read.assert_called_once_with(len(value))
        checksum += (result & 0xFF) + ((result >> 8) & 0xFF) + ((result >> 16) & 0xFF) + ((result >> 24) & 0xFF)
        assert self.port.get_checksum() == checksum
        self.mocked_serial_port.read = mock.Mock(return_value=str())
        assert self.port.read_long() is None


class ReadSignedLongTestCase(SerialPortTestCase):
    def runTest(self):
        value = str('    ')
        self.mocked_serial_port.read = mock.Mock(return_value=value)
        checksum = self.port.get_checksum()
        result = struct.unpack('>l', value)
        result = result[0]
        assert self.port.read_slong() == result
        self.mocked_serial_port.read.assert_called_once_with(len(value))
        checksum += (result & 0xFF) + ((result >> 8) & 0xFF) + ((result >> 16) & 0xFF) + ((result >> 24) & 0xFF)
        assert self.port.get_checksum() == checksum
        self.mocked_serial_port.read = mock.Mock(return_value=str())
        assert self.port.read_slong() is None


class WriteByteTestCase(SerialPortTestCase):
    def runTest(self):
        value = int()
        packed_value = struct.pack('>B', value)
        self.mocked_serial_port.write = mock.Mock(return_value=len(packed_value))
        checksum = self.port.get_checksum()
        assert self.port.write_byte(value) == len(packed_value)
        self.mocked_serial_port.write.assert_called_once_with(packed_value)
        checksum += value & 0xFF
        assert self.port.get_checksum() == checksum


class WriteSignedByteTestCase(SerialPortTestCase):
    def runTest(self):
        value = int()
        packed_value = struct.pack('>b', value)
        self.mocked_serial_port.write = mock.Mock(return_value=len(packed_value))
        checksum = self.port.get_checksum()
        assert self.port.write_sbyte(value) == len(packed_value)
        self.mocked_serial_port.write.assert_called_once_with(packed_value)
        checksum += value & 0xFF
        assert self.port.get_checksum() == checksum


class WriteWordTestCase(SerialPortTestCase):
    def runTest(self):
        value = int()
        packed_value = struct.pack('>H', value)
        self.mocked_serial_port.write = mock.Mock(return_value=len(packed_value))
        checksum = self.port.get_checksum()
        assert self.port.write_word(value) == len(packed_value)
        self.mocked_serial_port.write.assert_called_once_with(packed_value)
        checksum += (value & 0xFF) + ((value >> 8) & 0xFF)
        assert self.port.get_checksum() == checksum


class WriteSignedWordTestCase(SerialPortTestCase):
    def runTest(self):
        value = int()
        packed_value = struct.pack('>h', value)
        self.mocked_serial_port.write = mock.Mock(return_value=len(packed_value))
        checksum = self.port.get_checksum()
        assert self.port.write_sword(value) == len(packed_value)
        self.mocked_serial_port.write.assert_called_once_with(packed_value)
        checksum += (value & 0xFF) + ((value >> 8) & 0xFF)
        assert self.port.get_checksum() == checksum


class WriteLongTestCase(SerialPortTestCase):
    def runTest(self):
        value = int()
        packed_value = struct.pack('>L', value)
        self.mocked_serial_port.write = mock.Mock(return_value=len(packed_value))
        checksum = self.port.get_checksum()
        assert self.port.write_long(value) == len(packed_value)
        self.mocked_serial_port.write.assert_called_once_with(packed_value)
        checksum += (value & 0xFF) + ((value >> 8) & 0xFF) + ((value >> 16) & 0xFF) + ((value >> 24) & 0xFF)
        assert self.port.get_checksum() == checksum


class WriteSignedLongTestCase(SerialPortTestCase):
    def runTest(self):
        value = int()
        packed_value = struct.pack('>l', value)
        self.mocked_serial_port.write = mock.Mock(return_value=len(packed_value))
        checksum = self.port.get_checksum()
        assert self.port.write_slong(value) == len(packed_value)
        self.mocked_serial_port.write.assert_called_once_with(packed_value)
        checksum += (value & 0xFF) + ((value >> 8) & 0xFF) + ((value >> 16) & 0xFF) + ((value >> 24) & 0xFF)
        assert self.port.get_checksum() == checksum

