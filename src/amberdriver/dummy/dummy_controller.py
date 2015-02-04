import threading
import time
import logging
import logging.config
import sys

import os

from amberdriver.common import drivermsg_pb2
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

        self.__subscribers = []
        self.__subscribers_lock = threading.Lock()

        self.__subscribe_thread = None

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
            self.__logger.warning('No request in message')

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

        response_message.Extensions[dummy_pb2.enable] = self.__dummy.enable
        response_message.Extensions[dummy_pb2.message] = self.__dummy.message

        return response_header, response_message

    def handle_subscribe_message(self, header, message):
        """
        Handle SUBSCRIBE message type. Must be implemented.

        :param header:
        :param message:
        :return:
        """
        self.__logger.debug('Subscribe action')

        self.__subscribers_lock.acquire()
        try:
            no_subscribers = (len(self.__subscribers) == 0)
            self.__subscribers.extend(header.clientIDs)
        finally:
            self.__subscribers_lock.release()

        if no_subscribers or self.__subscribe_thread is None:
            self.__subscribe_thread = threading.Thread(target=self.__run, name="subscribe-thread")
            self.__subscribe_thread.start()

    def handle_unsubscribe_message(self, header, message):
        """
        Handle UNSUBSCRIBE message type. Must be implemented.

        :param header:
        :param message:
        :return:
        """
        self.__logger.debug('Unsubscribe action')
        map(self.__remove_subscriber, header.clientIDs)

    def handle_client_died_message(self, client_id):
        """
        Handle CLIENT_DIES message type. Must be implemented.

        :param client_id:
        :return:
        """
        self.__logger.info('Client %d died', client_id)
        self.__remove_subscriber(client_id)

    def __remove_subscriber(self, client_id):
        self.__subscribers_lock.acquire()
        try:
            self.__subscribers.remove(client_id)
        except ValueError:
            self.__logger.warning('Client %d does not registered as subscriber', client_id)
            # FIXME: silent pass?
        finally:
            self.__subscribers_lock.release()

    def __run(self):
        """
        Implementation of function used to service subscribed clients.

        :return:
        """
        are_subscribes = True
        while self.is_alive() and are_subscribes:
            response_header = drivermsg_pb2.DriverHdr()
            response_message = drivermsg_pb2.DriverMsg()

            self.__subscribers_lock.acquire()
            try:
                are_subscribes = len(self.__subscribers) > 0
                if are_subscribes:
                    response_header.clientIDs.extend(self.__subscribers)
            finally:
                self.__subscribers_lock.release()

            if are_subscribes:
                response_message.type = drivermsg_pb2.DriverMsg.DATA
                response_message.ackNum = 0
                response_message.Extensions[dummy_pb2.message] = 'Response %d' % self.__value
                self.__value += 1
                self.get_pipes().write_header_and_message_to_pipe(response_header, response_message)

            time.sleep(0.01)


if __name__ == '__main__':
    try:
        # Create dummy.
        dummy = Dummy()
        # Create controller and run it.
        controller = DummyController(sys.stdin, sys.stdout, dummy)
        # It's running in infinite loop.
        controller()

    except BaseException as e:
        sys.stderr.write('%s\nRun without Dummy.' % str(e))
        # FIXME: silent pass?

        controller = NullController(sys.stdin, sys.stdout)
        controller()
