import sys

from amberdriver.common.message_handler import MessageHandler


__author__ = 'paoolo'


class NullController(MessageHandler):
    def handle_unsubscribe_message(self, header, message):
        sys.stderr.write('UNSUBSCRIBE:\n%s\n%s\n' % (str(header), str(message)))

    def handle_subscribe_message(self, header, message):
        sys.stderr.write('SUBSCRIBE:\n%s\n%s\n' % (str(header), str(message)))

    def handle_client_died_message(self, client_id):
        sys.stderr.write('CLIENT_DIED:\n%s\n' % (str(client_id)))

    def handle_data_message(self, header, message):
        sys.stderr.write('DATA:\n%s\n%s\n' % (str(header), str(message)))