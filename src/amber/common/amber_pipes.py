import abc
import logging
import struct
import sys

from amber.common import drivermsg_pb2


__author__ = 'paoolo'

LEN_SIZE = 2
LOGGER_NAME = 'Amber.Pipes'


class MessageHandler(object):
    @abc.abstractmethod
    def handle_data_msg(self, header, message):
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

    def handle_ping_msg(self, header, message):
        if not message.has_syn_num():
            self.__logger.warning('PING message came, but synNum not set, ignoring.')
        else:
            pong_message = drivermsg_pb2.DriverMsg()
            pong_message.type = drivermsg_pb2.DriverMsg.MsgType.PONG
            pong_message.ack_num = message.syn_num

            pong_header = drivermsg_pb2.DriverHdr()
            pong_header.client_ids.append(header.client_ids[0])

            self.__logger.debug('Sending PONG message.')

            self.write_msg_to_pipe(pong_header, pong_message)

    def __write_to_pipe(self, data):
        data = struct.pack('>h', len(data)) + data
        self.__write_exact(data)

    def write_msg_to_pipe(self, header, message):
        header_data = header.SerializeToString()
        self.__write_to_pipe(header_data)

        message_data = message.SerializeToString()
        self.__write_to_pipe(message_data)

    def __read_from_pipe(self, size):
        data = self.__read_exact(size)
        size = struct.unpack('>h', data)
        data = self.__read_exact(size[0])
        return data

    def __read_msg_from_pipe(self):
        header_data = self.__read_from_pipe(LEN_SIZE)
        header = drivermsg_pb2.DriverHdr()
        header.ParseFromString(header_data)

        message_data = self.__read_from_pipe(LEN_SIZE)
        message = drivermsg_pb2.DriverMsg()
        message.ParseFromString(message_data)

        if message.type == drivermsg_pb2.DriverMsg.DATA:
            self.__message_handler.handle_data_msg(header, message)

        elif message.type == drivermsg_pb2.DriverMsg.CLIENT_DIED:
            if len(header.client_ids) != 1:
                self.__logger.warning('CLIENT_DIED message came, but clientID not set, ignoring.')
            else:
                self.__message_handler.handle_client_died_msg(header.client_ids[0])
        else:
            self.__logger.warning('Unsupported message type, ignoring.')

    def __run_process(self):
        while True:
            self.__read_msg_from_pipe()

    def __read_exact(self, size):
        return self.__pipe_in.read(size)

    def __write_exact(self, buf):
        self.__pipe_out.write(buf)