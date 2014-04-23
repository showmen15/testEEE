#!/usr/bin/env python

import logging
import sys

from amber.common.amber_pipes import MessageHandler, AmberPipes


__author__ = 'paoolo'


class Dummy(object):
    pass


class DummyController(MessageHandler):
    def __init__(self, pipe_in, pipe_out):
        self.__amber_pipes = AmberPipes(self, pipe_in, pipe_out)
        self.__logger = logging.Logger('Dummy.Controller')
        self.__logger.addHandler(logging.StreamHandler())

    def handle_data_msg(self, header, message):
        self.__logger.debug('Message came')
        # TODO: fill with checking message

    def handle_client_died_message(self, client_id):
        self.__logger.info('Client %d died' % client_id)

    def __call__(self, *args, **kwargs):
        self.__amber_pipes()


if __name__ == '__main__':
    print('Starting')
    controller = DummyController(sys.stdin, sys.stdout)
    controller()