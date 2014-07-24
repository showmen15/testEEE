from functools import wraps
import logging
import logging.config
import struct
import threading

import abc
import os
from amber.common import drivermsg_pb2, runtime


__author__ = 'paoolo'

LEN_SIZE = 2

LOGGER_NAME = 'AmberPipes'
pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/amber.ini' % pwd)


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


class AmberPipes(object):
    def __init__(self, message_handler, pipe_in, pipe_out):
        self.__message_handler = message_handler
        self.__pipe_in, self.__pipe_out = pipe_in, pipe_out
        self.__alive = True

        runtime.add_shutdown_hook(self.terminate)

        self.__write_lock = threading.Lock()
        self.__logger = logging.getLogger(LOGGER_NAME)

    def __call__(self, *args, **kwargs):
        self.__logger.info('Pipes thread started.')
        self.__run_process()

    def is_alive(self):
        return self.__alive

    def terminate(self):
        self.__logger.warning('amber_pipes: terminate')

        self.__alive = False

    def __run_process(self):
        try:
            while self.__alive:
                header, message = self.__read_header_and_message_from_pipe()
                threading.Thread(target=self.__handle_header_and_message, args=(header, message)).start()
        except struct.error:
            self.__alive = False

        self.__logger.warning('amber_pipes: stop')

    def __read_data_from_pipe(self, container):
        data = self.__read_and_unpack_data_from_pipe(LEN_SIZE)
        container.ParseFromString(data)
        return container

    def __read_header_and_message_from_pipe(self):
        """
        Read and parse header and message from pipe.

        :return: header and message
        """
        header = drivermsg_pb2.DriverHdr()
        message = drivermsg_pb2.DriverMsg()

        header = self.__read_data_from_pipe(header)
        message = self.__read_data_from_pipe(message)

        return header, message

    def __read_and_unpack_data_from_pipe(self, size):
        """
        Read and unpack data from pipe.

        :param size: size of length data
        :return: binary string
        """
        data = self.__read_from_pipe(size)
        # FIXME: can generate error, why?
        size = struct.unpack('!h', data)
        data = self.__read_from_pipe(size[0])
        return data

    def __read_from_pipe(self, size):
        """
        Read binary string from pipe.

        :param size: size of read string
        :return: binary string
        """
        return self.__pipe_in.read(size)

    def __handle_header_and_message(self, header, message):
        """
        Handle any message. Not serviced message are PONG and DRIVER_DIED.

        :param header: object of DriverHdr
        :param message: object of DriverMsg
        :return: nothing
        """
        if message.type == drivermsg_pb2.DriverMsg.DATA:
            self.__logger.debug('Received DATA message')
            self.__message_handler.handle_data_message(header, message)

        elif message.type == drivermsg_pb2.DriverMsg.SUBSCRIBE:
            self.__logger.debug('Received SUBSCRIBE message')
            self.__message_handler.handle_subscribe_message(header, message)

        elif message.type == drivermsg_pb2.DriverMsg.UNSUBSCRIBE:
            self.__logger.debug('Received UNSUBSCRIBE message')
            self.__message_handler.handle_unsubscribe_message(header, message)

        elif message.type == drivermsg_pb2.DriverMsg.CLIENT_DIED:
            self.__logger.debug('Received CLIENT_DIED message')
            self.__handle_client_died_message(header, message)

        elif message.type == drivermsg_pb2.DriverMsg.PING:
            self.__logger.debug('Received PING message')
            self.__handle_ping_message(header, message)

        else:
            self.__logger.warning('Received unknown type message, ignoring.')

    def __handle_client_died_message(self, header, _):
        """
        Handle CLIENT_DIED message which came from mediator.
        Handling message delegated to message handler.

        :param header: object of DriverHdr
        :return: nothing
        """
        if len(header.clientIDs) != 1:
            self.__logger.warning('CLIENT_DIED\'s clientID not set, ignoring.')

        else:
            self.__message_handler.handle_client_died_message(header.clientIDs[0])

    def __handle_ping_message(self, ping_header, ping_message):
        """
        Handle PING message which came from mediator.

        :param ping_header: object of DriverHdr
        :param ping_message: object of DriverMsg
        :return: nothing
        """
        if ping_message.HasField('synNum'):
            self.__logger.warning('PING\'s synNum not set, ignoring.')

        else:
            pong_message = drivermsg_pb2.DriverMsg()
            pong_message.type = drivermsg_pb2.DriverMsg.MsgType.PONG
            pong_message.ackNum = ping_message.synNum

            pong_header = drivermsg_pb2.DriverHdr()
            pong_header.clientIDs.extend(ping_header.clientIDs)

            self.__logger.debug('Send PONG message')

            self.write_header_and_message_to_pipe(pong_header, pong_message)

    def write_header_and_message_to_pipe(self, header, message):
        """
        Serialize and write header and message to pipe.

        :param header: object of DriverHdr
        :param message: object of DriverMsg
        :return: nothing
        """
        self.__logger.debug('Write header and message to pipe:\nHEADER:\n%s\n---\nMESSAGE:\n%s\n---' %
                            (str(header).strip(), str(message).strip()))

        self.__write_lock.acquire()

        header_data = header.SerializeToString()
        self.__pack_and_write_data_to_pipe(header_data)

        message_data = message.SerializeToString()
        self.__pack_and_write_data_to_pipe(message_data)

        self.__write_lock.release()

    def __pack_and_write_data_to_pipe(self, binary_data):
        """
        Pack and write data to pipe.

        :param binary_data: binary data as string
        :return: nothing
        """
        binary_data = struct.pack('!h', len(binary_data)) + binary_data
        self.__write_to_pipe(binary_data)

    def __write_to_pipe(self, binary_string):
        """
        Write string binary to pipe.

        :param binary_string: binary string
        :return: nothing
        """
        self.__pipe_out.write(binary_string)
        self.__pipe_out.flush()