import logging
import logging.config
import sys
import traceback

import os

from amberdriver.common.message_handler import MessageHandler

from amberdriver.dummy import dummy_pb2
from amberdriver.dummy.dummy import Dummy
from amberdriver.null.null import NullController
from amberdriver.tools import config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/dummy.ini' % pwd)
config.add_config_ini('%s/dummy.ini' % pwd)

LOGGER_NAME = 'DummyController'


class DummyController(MessageHandler):
    """
    Example implementation of driver.
    Need to extends `MessageHandler` from `amber.driver.common.amber_pipes`.
    """

    def __init__(self, pipe_in, pipe_out, driver):
        super(DummyController, self).__init__(pipe_in, pipe_out)
        self.__dummy = driver
        self.__value = 0
        self.__logger = logging.getLogger(LOGGER_NAME)

    def handle_data_message(self, header, message):
        """
        Handling DATA message type. Must be implemented.
        Use extensions and checking if extension exists in message,
        to determine what to do with message.

        :param header:
        :param message:
        :return:
        """
        if message.HasExtension(dummy_pb2.enable):
            self.__handle_set_enable(header, message)

        elif message.HasExtension(dummy_pb2.message):
            self.__handle_set_message(header, message)

        elif message.HasExtension(dummy_pb2.get_status):
            self.__handle_get_status(header, message)

        else:
            self.__logger.warning('No recognizable request in message')

    def __handle_set_enable(self, header, message):
        """
        Example operation, setting enable flag.

        :param header:
        :param message:
        :return:
        """
        value = message.Extensions[dummy_pb2.enable]
        self.__logger.debug('Set enable to %s' % value)
        self.__dummy.enable = value

    def __handle_set_message(self, header, message):
        """
        Example operation, setting message.

        :param header:
        :param message:
        :return:
        """
        value = message.Extensions[dummy_pb2.message]
        self.__logger.debug('Set message to %s' % value)
        self.__dummy.message = value

    @MessageHandler.handle_and_response
    def __handle_get_status(self, received_header, received_message, response_header, response_message):
        """
        Example operation, receive values.

        :param received_header:
        :param received_message:
        :param response_header:
        :param response_message:
        :return:
        """
        self.__logger.debug('Get status')
        DummyController.__fill_status(response_message, self.__dummy.enable, self.__dummy.message)
        return response_header, response_message

    @staticmethod
    def __fill_status(response_message, enable, message):
        response_message.Extensions[dummy_pb2.enable] = enable
        response_message.Extensions[dummy_pb2.message] = message

    def handle_subscribe_message(self, header, message):
        """
        Handle SUBSCRIBE message type. Must be implemented.

        :param header:
        :param message:
        :return:
        """
        self.__logger.debug('Subscribe action')
        self.add_subscribers(header.clientIDs)

    def handle_unsubscribe_message(self, header, message):
        """
        Handle UNSUBSCRIBE message type. Must be implemented.

        :param header:
        :param message:
        :return:
        """
        self.__logger.debug('Unsubscribe action for clients %s', str(header.clientIDs))
        map(self.remove_subscriber, header.clientIDs)

    def handle_client_died_message(self, client_id):
        """
        Handle CLIENT_DIES message type. Must be implemented.

        :param client_id:
        :return:
        """
        self.__logger.info('Client %d died', client_id)
        self.remove_subscriber(client_id)

    def fill_subscription_response(self, response_message):
        self.__value += 1
        return DummyController.__fill_response(response_message, self.__value)

    @staticmethod
    def __fill_response(response_message, value):
        response_message.Extensions[dummy_pb2.message] = 'Response %d' % value
        return response_message


if __name__ == '__main__':
    try:
        # Create dummy.
        dummy = Dummy()
        # Create controller and run it.
        controller = DummyController(sys.stdin, sys.stdout, dummy)
        # It's running in infinite loop.
        controller()

    except BaseException as e:
        sys.stderr.write('Run without Dummy.\n')
        traceback.print_exc()

        controller = NullController(sys.stdin, sys.stdout)
        controller()
