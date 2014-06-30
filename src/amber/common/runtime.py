import sys
from signal import *

__author__ = 'paoolo'

__trap_signals = (SIGINT, SIGTERM)
__funcs = []


def __shutdown_func(*args, **kwargs):
    sys.stderr.write('trap signal\n')
    for func in __funcs:
        func()


for sig in __trap_signals:
    signal(sig, __shutdown_func)


def add_shutdown_hook(func):
    __funcs.append(func)