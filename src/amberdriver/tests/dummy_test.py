from amberdriver.dummy import dummy_pb2
from amberdriver.dummy.dummy_controller import DummyController

__author__ = 'paoolo'

import unittest
import mock


class DummyControllerTestCase(unittest.TestCase):
    def setUp(self):
        self.mocked_stdin, self.mocked_stdout = mock.Mock(), mock.Mock()
        self.mocked_amber_pipes = mock.Mock()
        self.mocked_amber_pipes.is_alive = mock.Mock(return_value=True)
        self.mocked_dummy = mock.Mock()

        self.controller = DummyController(self.mocked_stdin, self.mocked_stdout, self.mocked_dummy)
        self.controller._MessageHandler__amber_pipes = self.mocked_amber_pipes

    def tearDown(self):
        self.mocked_amber_pipes.is_alive = mock.Mock(return_value=False)


class HandleDataMessageTestCase(DummyControllerTestCase):
    def setUp(self):
        super(HandleDataMessageTestCase, self).setUp()


class HandleNoRequestTestCase(HandleDataMessageTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        message.HasExtension = mock.Mock(return_value=False)
        calls = [mock.call(dummy_pb2.enable),
                 mock.call(dummy_pb2.message),
                 mock.call(dummy_pb2.get_status)]
        self.controller.handle_data_message(header, message)
        message.HasExtension.assert_has_calls(calls)


class HandleSetEnableTestCase(HandleDataMessageTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        def has_set_enable(arg):
            return arg is dummy_pb2.enable

        message.HasExtension = mock.Mock(side_effect=has_set_enable)

        value = object()

        message.Extensions = {dummy_pb2.enable: value}

        calls = [mock.call(dummy_pb2.enable)]
        self.controller.handle_data_message(header, message)
        message.HasExtension.assert_has_calls(calls)

        self.assertEqual(self.mocked_dummy.enable, value)


class HandleSetMessageTestCase(HandleDataMessageTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        def has_set_message(arg):
            return arg is dummy_pb2.message

        message.HasExtension = mock.Mock(side_effect=has_set_message)

        value = object()

        message.Extensions = {dummy_pb2.message: value}

        calls = [mock.call(dummy_pb2.enable),
                 mock.call(dummy_pb2.message)]
        self.controller.handle_data_message(header, message)
        message.HasExtension.assert_has_calls(calls)

        self.assertEqual(self.mocked_dummy.message, value)


class HandleGetStatusTestCase(HandleDataMessageTestCase):
    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        message.synNum = int()
        header.clientIDs = list()

        self.mocked_dummy.enable = True
        self.mocked_dummy.message = str()

        def has_get_status(arg):
            return arg is dummy_pb2.get_status

        message.HasExtension = mock.Mock(side_effect=has_get_status)

        value = mock.Mock()

        message.Extensions = mock.Mock()
        message.Extensions.__getitem__ = lambda *args, **kw: value

        calls = [mock.call(dummy_pb2.enable),
                 mock.call(dummy_pb2.message),
                 mock.call(dummy_pb2.get_status)]
        self.controller.handle_data_message(header, message)
        message.HasExtension.assert_has_calls(calls)


class HandleSubscribeTestCase(DummyControllerTestCase):
    def setUp(self):
        super(HandleSubscribeTestCase, self).setUp()

    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        header.clientIDs = list()

        self.controller.handle_subscribe_message(header, message)
        # TODO(paoolo): validate if subscribers are extend and thread was started


class HandleUnsubscribeTestCase(DummyControllerTestCase):
    def setUp(self):
        super(HandleUnsubscribeTestCase, self).setUp()

    def runTest(self):
        header, message = mock.Mock(), mock.Mock()

        header.clientIDs = list()

        self.controller.handle_unsubscribe_message(header, message)
        # TODO(paoolo): validate if subscriber was removed from list


class HandleClientDiedTestCase(DummyControllerTestCase):
    def setUp(self):
        super(HandleClientDiedTestCase, self).setUp()

    def runTest(self):
        client_id = int()

        self.controller.handle_client_died_message(client_id)
        # TODO(paoolo): validate if client was removed from list