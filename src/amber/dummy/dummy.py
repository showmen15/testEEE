# !/usr/bin/env python

import logging
import sys

from amber.common import drivermsg_pb2
from amber.common.amber_pipes import MessageHandler
from amber.dummy import dummy_pb2


__author__ = 'paoolo'

LOGGER_NAME = 'Dummy.Controller'


class Dummy(object):
    def __init__(self):
        self.message = 'Message'
        self.enable = False


class DummyController(MessageHandler):
    def __init__(self, pipe_in, pipe_out):
        super(DummyController, self).__init__(pipe_in, pipe_out)
        self.__dummy = Dummy()

        self.__logger = logging.Logger(LOGGER_NAME)
        self.__logger.addHandler(logging.StreamHandler())

    def handle_data_message(self, header, message):
        if message.HasExtension(dummy_pb2.enable):
            self.__handle_set_enable(header, message)

        elif message.HasExtension(dummy_pb2.message):
            self.__handle_set_message(header, message)

        elif message.HasExtension(dummy_pb2.get_status):
            self.__handle_get_status(header, message)

        else:
            self.__logger.warning('No request in message')

    def __handle_set_enable(self, _, message):
        value = message.Extensions[dummy_pb2.enable]
        self.__logger.debug('Set enable to %s' % value)
        self.__dummy.enable = value

    def __handle_set_message(self, _, message):
        value = message.Extensions[dummy_pb2.message]
        self.__logger.debug('Set message to %s' % value)
        self.__dummy.message = value

    def __handle_get_status(self, header, message):
        self.__logger.debug('Get status')

        driver_msg = drivermsg_pb2.DriverMsg()
        driver_hdr = drivermsg_pb2.DriverHdr()

        driver_msg.type = drivermsg_pb2.DriverMsg.DATA
        driver_msg.Extensions[dummy_pb2.enable] = self.__dummy.enable
        driver_msg.Extensions[dummy_pb2.message] = self.__dummy.message
        driver_msg.synNum = message.synNum

        driver_hdr.clientIDs.append(header.clientIDs[0])

        self.__amber_pipes.write_header_and_message_to_pipe(driver_hdr, driver_msg)

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died' % client_id)


if __name__ == '__main__':
    controller = DummyController(sys.stdin, sys.stdout)
    controller()