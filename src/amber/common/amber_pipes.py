import abc
import logging
import struct

from amber.common import drivermsg_pb2


__author__ = 'paoolo'

LEN_SIZE = 2
LOGGER_NAME = 'Amber.Pipes'


class MessageHandler(object):
    def __init__(self, pipe_in, pipe_out):
        self.__amber_pipes = AmberPipes(self, pipe_in, pipe_out)

    def __call__(self, *args, **kwargs):
        self.__amber_pipes(*args, **kwargs)

    def get_pipes(self):
        return self.__amber_pipes

    @abc.abstractmethod
    def handle_data_message(self, header, message):
        pass

    @abc.abstractmethod
    def handle_client_died_message(self, client_id):
        pass


class AmberPipes(object):
    def __init__(self, message_handler, pipe_in, pipe_out):
        self.__message_handler = message_handler
        self.__pipe_in, self.__pipe_out = pipe_in, pipe_out

        self.__logger = logging.Logger(LOGGER_NAME)
        self.__logger.addHandler(logging.StreamHandler())

    def __call__(self, *args, **kwargs):
        self.__logger.info('Pipes thread started.')
        self.__run_process()

    def __run_process(self):
        while True:
            self.__read_header_and_message_from_pipe()

    def __read_header_and_message_from_pipe(self):
        """
        Read and parse header and message from pipe.

        :return: nothing
        """
        header_data = self.__read_and_unpack_data_from_pipe(LEN_SIZE)
        header = drivermsg_pb2.DriverHdr()
        header.ParseFromString(header_data)

        message_data = self.__read_and_unpack_data_from_pipe(LEN_SIZE)
        message = drivermsg_pb2.DriverMsg()
        message.ParseFromString(message_data)

        self.__handle_header_and_message(header, message)

    def __read_and_unpack_data_from_pipe(self, size):
        """
        Read and unpack data from pipe.

        :param size: size of length data
        :return: binary string
        """
        data = self.__read_from_pipe(size)
        # FIXME: can generate error, why?
        size = struct.unpack('!H', data)
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

    def __handle_ping_message(self, header, message):
        """
        Handle PING message which came from mediator.

        :param header: object of DriverHdr
        :param message: object of DriverMsg
        :return: nothing
        """
        if message.HasField('synNum'):
            self.__logger.warning('PING\'s synNum not set, ignoring.')

        else:
            pong_message = drivermsg_pb2.DriverMsg()
            pong_message.type = drivermsg_pb2.DriverMsg.MsgType.PONG
            pong_message.ackNum = message.synNum

            pong_header = drivermsg_pb2.DriverHdr()
            pong_header.clientIDs.append(header.client_ids[0])

            self.__logger.debug('Send PONG message')

            self.write_header_and_message_to_pipe(pong_header, pong_message)

    def write_header_and_message_to_pipe(self, header, message):
        """
        Serialize and write header and message to pipe.

        :param header: object of DriverHdr
        :param message: object of DriverMsg
        :return: nothing
        """
        self.__logger.debug('Write header and message to pipe: header="%s", message="%s".' %
                            (str(header).strip(), str(message).strip()))

        header_data = header.SerializeToString()
        self.__pack_and_write_data_to_pipe(header_data)

        message_data = message.SerializeToString()
        self.__pack_and_write_data_to_pipe(message_data)

    def __pack_and_write_data_to_pipe(self, binary_data):
        """
        Pack and write data to pipe.

        :param binary_data: binary data as string
        :return: nothing
        """
        binary_data = struct.pack('!H', len(binary_data)) + binary_data
        self.__write_to_pipe(binary_data)

    def __write_to_pipe(self, binary_string):
        """
        Write string binary to pipe.

        :param binary_string: binary string
        :return: nothing
        """
        self.__pipe_out.write(binary_string)
        self.__pipe_out.flush()
