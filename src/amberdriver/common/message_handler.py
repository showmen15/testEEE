from functools import wraps
import logging
import threading

import logging.config
import time

import abc
import os

from amberdriver.common import drivermsg_pb2
from amberdriver.common.amber_pipes import AmberPipes


__author__ = 'paoolo'

LOGGER_NAME = 'MessageHandler'
pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/amber.ini' % pwd)


class MessageHandler(object):
    def __init__(self, pipe_in, pipe_out):
        self.__amber_pipes = AmberPipes(self, pipe_in, pipe_out)

        self.__subscribers = []
        self.__subscribers_lock = threading.Lock()

        self.__subscription_thread = threading.Thread(target=self.subscription_loop, name="subscription-thread")
        self.__subscription_thread.start()

        self.__logger = logging.getLogger(LOGGER_NAME)

    def __call__(self, *args, **kwargs):
        self.__amber_pipes(*args, **kwargs)

    def is_alive(self):
        return self.__amber_pipes.is_alive()

    def get_pipes(self):
        return self.__amber_pipes

    @abc.abstractmethod
    def handle_data_message(self, header, message):
        pass

    @abc.abstractmethod
    def handle_subscribe_message(self, header, message):
        pass

    @abc.abstractmethod
    def handle_unsubscribe_message(self, header, message):
        pass

    @abc.abstractmethod
    def handle_client_died_message(self, client_id):
        pass

    def fill_subscription_response(self, response_message):
        pass

    def subscription_loop(self):
        while self.is_alive():
            subscribers = self.__get_subscribers_copy()
            if len(subscribers) > 0:
                response_header = drivermsg_pb2.DriverHdr()
                response_message = drivermsg_pb2.DriverMsg()

                response_message.type = drivermsg_pb2.DriverMsg.DATA
                response_message.ackNum = 0

                response_header.clientIDs.extend(subscribers)
                response_message = self.fill_subscription_response(response_message)

                self.get_pipes().write_header_and_message_to_pipe(response_header, response_message)
            else:
                time.sleep(0.1)

    def __get_subscribers_copy(self):
        self.__subscribers_lock.acquire()
        try:
            return list(self.__subscribers)
        finally:
            self.__subscribers_lock.release()

    def add_subscribers(self, client_ids):
        self.__subscribers_lock.acquire()
        try:
            self.__subscribers.extend(client_ids)
        finally:
            self.__subscribers_lock.release()

    def remove_subscriber(self, client_id):
        self.__subscribers_lock.acquire()
        try:
            self.__subscribers.remove(client_id)
        except ValueError:
            self.__logger.warning('Client %d does not registered as subscriber', client_id)
        finally:
            self.__subscribers_lock.release()

    @staticmethod
    def handle_and_response(func):
        @wraps(func)
        def wrapped(inst, received_header, received_message):
            response_header = drivermsg_pb2.DriverHdr()
            response_message = drivermsg_pb2.DriverMsg()

            response_message.type = drivermsg_pb2.DriverMsg.DATA
            response_message.ackNum = received_message.synNum

            response_header.clientIDs.extend(received_header.clientIDs)

            response_header, response_message = func(inst, received_header, received_message,
                                                     response_header, response_message)

            inst.get_pipes().write_header_and_message_to_pipe(response_header, response_message)

        return wrapped