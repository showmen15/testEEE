from amberdriver.common import drivermsg_pb2
from amberdriver.common.message_handler import MessageHandler

__author__ = 'paoolo'

import unittest

import mock


class MessageHandlerTestCase(unittest.TestCase):
    class TestMessageHandler(MessageHandler):
        def handle_subscribe_message(self, header, message):
            pass

        def handle_data_message(self, header, message):
            pass

        def handle_client_died_message(self, client_id):
            pass

        def handle_unsubscribe_message(self, header, message):
            pass

        @MessageHandler.handle_and_response
        def handle_message(self, received_header, received_message, response_header, response_message):
            MessageHandlerTestCase.response_header = response_header
            MessageHandlerTestCase.response_message = response_message
            assert response_message.type == drivermsg_pb2.DriverMsg.DATA
            return response_header, response_message

    def setUp(self):
        self.mocked_stdin, self.mocked_stdout = mock.Mock(), mock.Mock()
        self.message_handler = MessageHandlerTestCase.TestMessageHandler(self.mocked_stdin, self.mocked_stdout)

    def runTest(self):
        header, message = mock.Mock(), mock.Mock()
        amber_pipes = mock.Mock()

        self.message_handler._MessageHandler__amber_pipes = amber_pipes

        message.synNum = int()
        header.clientIDs = list()

        self.message_handler.handle_message(header, message)

        amber_pipes.write_header_and_message_to_pipe.assert_called_once_with(self.response_header,
                                                                             self.response_message)

        amber_pipes.is_alive = mock.Mock(return_value=False)
