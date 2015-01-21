import logging
import logging.config
import signal

import os


__author__ = 'paoolo'

__pwd = os.path.dirname(os.path.abspath(__file__))

logging.config.fileConfig('%s/runtime.ini' % __pwd)

__logger = logging.getLogger('runtime')

__trap_signals = (signal.SIGINT, signal.SIGTERM)
__funcs = []


# noinspection PyBroadException
def __shutdown_func(*args, **kwargs):
    __logger.warn('trap signal\n')

    for func in __funcs:
        try:
            __logger.warn('run func %s\n' % str(func))
            func()
        except:
            pass


for sig in __trap_signals:
    signal.signal(sig, __shutdown_func)


def add_shutdown_hook(func):
    __funcs.append(func)