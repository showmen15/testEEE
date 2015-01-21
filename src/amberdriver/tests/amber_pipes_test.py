import struct

from amberdriver.common import drivermsg_pb2
from amberdriver.common.amber_pipes import AmberPipes, LEN_SIZE


__author__ = 'paoolo'

import unittest
import mock


class AmberPipesTestCase(unittest.TestCase):
    def setUp(self):
        self.mocked_stdin, self.mocked_stdout = mock.Mock(), mock.Mock()
        self.mocked_message_handler = mock.Mock()
        self.amber_pipes = AmberPipes(self.mocked_message_handler, self.mocked_stdin, self.mocked_stdout)


class ReadFromPipeTestCase(AmberPipesTestCase):
    def runTest(self):
        size, result = mock.Mock(), mock.Mock()
        self.mocked_stdin.read = mock.Mock(return_value=result)
        self.assertEqual(self.amber_pipes._AmberPipes__read_from_pipe(size), result)
        self.mocked_stdin.read.assert_called_once_with(size)


class ReadAndUnpackDataFromPipeTestCase(AmberPipesTestCase):
    def runTest(self):
        data = '\x01\x02\x03\x04'

        def pipe_in(size):
            if size is LEN_SIZE:
                return struct.pack('>h', len(data))
            return data

        self.amber_pipes._AmberPipes__read_from_pipe = mock.Mock(side_effect=pipe_in)
        result = self.amber_pipes._AmberPipes__read_and_unpack_data_from_pipe(LEN_SIZE)
        self.assertEqual(result, data)


class ReadDataFromPipeTestCase(AmberPipesTestCase):
    def runTest(self):
        data = mock.Mock()
        container = mock.Mock()
        self.amber_pipes._AmberPipes__read_and_unpack_data_from_pipe = mock.Mock(return_value=data)
        self.amber_pipes._AmberPipes__read_data_from_pipe(container)
        container.ParseFromString.assert_called_once_with(data)


class ReadHeaderAndMessageFromPipe(AmberPipesTestCase):
    def runTest(self):
        def read_data_from_pipe(container):
            return container

        mocked_read_data_from_pipe = mock.Mock(side_effect=read_data_from_pipe)
        self.amber_pipes._AmberPipes__read_data_from_pipe = mocked_read_data_from_pipe

        header, message = self.amber_pipes._AmberPipes__read_header_and_message_from_pipe()
        self.assertIsInstance(header, drivermsg_pb2.DriverHdr)
        self.assertIsInstance(message, drivermsg_pb2.DriverMsg)
        self.assertEqual(mocked_read_data_from_pipe.call_count, 2)


class HandleHeaderAndMessageTestCase(AmberPipesTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()
        self.amber_pipes._AmberPipes__handle_header_and_message(header, message)

        message.type = drivermsg_pb2.DriverMsg.PING
        self.amber_pipes._AmberPipes__handle_ping_message = mock.Mock()
        self.amber_pipes._AmberPipes__handle_header_and_message(header, message)
        self.amber_pipes._AmberPipes__handle_ping_message.assert_called_once_with(header, message)

        message.type = drivermsg_pb2.DriverMsg.CLIENT_DIED
        self.amber_pipes._AmberPipes__handle_client_died_message = mock.Mock()
        self.amber_pipes._AmberPipes__handle_header_and_message(header, message)
        self.amber_pipes._AmberPipes__handle_client_died_message.assert_called_once_with(header, message)

        message.type = drivermsg_pb2.DriverMsg.UNSUBSCRIBE
        self.amber_pipes._AmberPipes__handle_header_and_message(header, message)
        self.mocked_message_handler.handle_unsubscribe_message.assert_called_once_with(header, message)

        message.type = drivermsg_pb2.DriverMsg.SUBSCRIBE
        self.amber_pipes._AmberPipes__handle_header_and_message(header, message)
        self.mocked_message_handler.handle_subscribe_message.assert_called_once_with(header, message)

        message.type = drivermsg_pb2.DriverMsg.DATA
        self.amber_pipes._AmberPipes__handle_header_and_message(header, message)
        self.mocked_message_handler.handle_data_message.assert_called_once_with(header, message)


class HandleClientDiedTestCase(AmberPipesTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        value = mock.Mock()
        header.clientIDs = [value, ]

        self.amber_pipes._AmberPipes__handle_client_died_message(header, message)
        self.mocked_message_handler.handle_client_died_message.assert_called_once_with(value)


class HandlePingMessage(AmberPipesTestCase):
    def runTest(self):
        ping_header, ping_message = mock.Mock(), mock.Mock()

        ping_message.synNum = 0
        value = int()
        ping_header.clientIDs = [value, ]

        def write_header_and_message_to_pipe(pong_header, pong_message):
            self.assertEqual(pong_message.type, drivermsg_pb2.DriverMsg.PONG)
            self.assertEqual(pong_message.ackNum, ping_message.synNum)
            self.assertTrue(value in pong_header.clientIDs)

        self.amber_pipes.write_header_and_message_to_pipe = write_header_and_message_to_pipe

        self.amber_pipes._AmberPipes__handle_ping_message(ping_header, ping_message)


class WriteHeaderAndMessageToPipeTestCase(AmberPipesTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()
        header_data, message_data = str(), str()

        header.SerializeToString = mock.Mock(return_value=header_data)
        message.SerializeToString = mock.Mock(return_value=message_data)

        mocked_write_to_pipe = mock.Mock()
        self.amber_pipes._AmberPipes__write_to_pipe = mocked_write_to_pipe

        self.amber_pipes.write_header_and_message_to_pipe(header, message)

        header.SerializeToString.assert_called_once_with()
        message.SerializeToString.assert_called_once_with()
        mocked_write_to_pipe.assert_called_once_with('\x00\x00\x00\x00')


class WriteToPipeTestCase(AmberPipesTestCase):
    def runTest(self):
        binary_string = mock.Mock()

        self.amber_pipes._AmberPipes__write_to_pipe(binary_string)

        self.mocked_stdout.write.assert_called_once_with(binary_string)
        self.mocked_stdout.flush.assert_called_once_with()