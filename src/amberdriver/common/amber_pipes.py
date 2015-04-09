import logging
import logging.config
import struct
import threading
import traceback
import signal

from ambercommon.common import runtime
import os

from amberdriver.common import drivermsg_pb2


__author__ = 'paoolo'

LEN_SIZE = 2

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/amber.ini' % pwd)

LOGGER_NAME = 'AmberPipes'


class AmberException(Exception):
    def __init__(self, message=None, cause=None):
        Exception.__init__(message + u', caused by ' + repr(cause))
        self.cause = cause


class AmberPipes(object):
    def __init__(self, message_handler, pipe_in, pipe_out):
        self.__message_handler = message_handler
        self.__pipe_in, self.__pipe_out = pipe_in, pipe_out
        self.__is_alive = True

        self.__write_lock = threading.Lock()
        self.__logger = logging.getLogger(LOGGER_NAME)

        runtime.add_shutdown_hook(self.terminate)

    def __call__(self, *args, **kwargs):
        self.run()

    def run(self):
        self.__logger.info('Pipes thread started.')
        self.__amber_pipes_loop()

    def is_alive(self):
        return self.__is_alive

    def __amber_pipes_loop(self):
        try:
            while self.__is_alive:
                header, message = self.__read_header_and_message_from_pipe()
                self.__handle_header_and_message(header, message)
        except BaseException:
            self.__logger.fatal('Stop due to error on pipe with mediator')
            self.__is_alive = False
            os.kill(os.getpid(), signal.SIGTERM)

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

    def __read_data_from_pipe(self, container):
        data = self.__read_and_unpack_data_from_pipe(LEN_SIZE)
        container.ParseFromString(data)
        return container

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
        if len(header.clientIDs) < 1:
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
        if not ping_message.HasField('synNum'):
            self.__logger.warning('PING\'s synNum is not set, ignoring.')

        else:
            pong_message = drivermsg_pb2.DriverMsg()
            pong_message.type = drivermsg_pb2.DriverMsg.PONG
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
        self.__logger.debug('Write header and message to pipe:\nHEADER:\n%s\n---\nMESSAGE:\n%s\n---',
                            str(header).strip(), str(message).strip()[:200])

        self.__write_lock.acquire()
        try:
            header_data = header.SerializeToString()
            message_data = message.SerializeToString()

            header_binary_data = struct.pack('!h', len(header_data)) + header_data
            message_binary_data = struct.pack('!h', len(message_data)) + message_data

            self.__write_to_pipe(header_binary_data + message_binary_data)

        except BaseException as e:
            traceback.print_exc(e)
            raise AmberException(cause=e)

        finally:
            self.__write_lock.release()

    def __write_to_pipe(self, binary_string):
        """
        Write string binary to pipe.

        :param binary_string: binary string
        :return: nothing
        """
        self.__pipe_out.write(binary_string)
        self.__pipe_out.flush()

    def terminate(self):
        self.__is_alive = False