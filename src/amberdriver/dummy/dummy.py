import threading

__author__ = 'paoolo'


class Dummy(object):
    """
    Example implementation.
    """

    def __init__(self):
        self.__message = 'Message'
        self.__enable = False

        self.__message_lock = threading.Lock()
        self.__enable_lock = threading.Lock()

    @property
    def message(self):
        self.__message_lock.acquire()
        try:
            return str(self.__message)
        finally:
            self.__message_lock.release()

    @message.setter
    def message(self, value):
        self.__message_lock.acquire()
        try:
            self.__message = value
        finally:
            self.__message_lock.release()

    @property
    def enable(self):
        self.__enable_lock.acquire()
        try:
            return self.__enable
        finally:
            self.__enable_lock.release()

    @enable.setter
    def enable(self, value):
        self.__enable_lock.acquire()
        try:
            self.__enable = value
        finally:
            self.__enable_lock.release()