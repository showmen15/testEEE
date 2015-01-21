from functools import wraps

import abc

from amberdriver.common import drivermsg_pb2
from amberdriver.common.amber_pipes import AmberPipes


__author__ = 'paoolo'


class MessageHandler(object):
    def __init__(self, pipe_in, pipe_out):
        self.__amber_pipes = AmberPipes(self, pipe_in, pipe_out)

    def __call__(self, *args, **kwargs):
        self.__amber_pipes(*args, **kwargs)

    def is_alive(self):
        return self.__amber_pipes.is_alive()

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

    def get_pipes(self):
        return self.__amber_pipes

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