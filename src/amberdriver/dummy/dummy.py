import logging
import logging.config
import sys

import os

from amberdriver.dummy.dummy_controller import DummyController
from amberdriver.null.null import NullController
from amberdriver.tools import config


__author__ = 'paoolo'

pwd = os.path.dirname(os.path.abspath(__file__))
logging.config.fileConfig('%s/dummy.ini' % pwd)
config.add_config_ini('%s/dummy.ini' % pwd)


class Dummy(object):
    """
    Example implementation.
    """

    def __init__(self):
        self.message = 'Message'
        self.enable = False


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

        controller = NullController(sys.stdin, sys.stdout)
        controller()
