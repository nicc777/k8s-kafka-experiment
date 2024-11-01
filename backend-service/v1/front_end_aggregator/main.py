import os
import random
import socket
import logging
import time
import json
import sys
import traceback
import valkey


HOSTNAME = socket.gethostname()
DEBUG = bool(int(os.getenv('DEBUG', '0')))
VALKEY_WRITER_SERVER_HOST = os.getenv('VALKEY_WRITER_SERVER_HOST', 'valkey-primary')
VALKEY_WRITER_SERVER_PORT = int(os.getenv('VALKEY_WRITER_SERVER_PORT', '6379'))
VALKEY_READER_SERVER_HOST = os.getenv('VALKEY_READER_SERVER_HOST', 'valkey-replicas')
VALKEY_READER_SERVER_PORT = int(os.getenv('VALKEY_READER_SERVER_PORT', '6379'))


logger = logging.getLogger(GROUP_ID)
logger.setLevel(logging.INFO)
if DEBUG is True:
    logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
if DEBUG is True:
    ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)
logger.debug('{} - VALKEY_WRITER_SERVER_HOST    : {}'.format(HOSTNAME, VALKEY_WRITER_SERVER_HOST))
logger.debug('{} - VALKEY_WRITER_SERVER_PORT    : {}'.format(HOSTNAME, VALKEY_WRITER_SERVER_PORT))
logger.debug('{} - VALKEY_READER_SERVER_HOST    : {}'.format(HOSTNAME, VALKEY_READER_SERVER_HOST))
logger.debug('{} - VALKEY_READER_SERVER_PORT    : {}'.format(HOSTNAME, VALKEY_READER_SERVER_PORT))


def get_connection_connection(writer_connection: bool=False)->valkey.Valkey:
    if writer_connection is True:
        return valkey.Valkey(host=VALKEY_WRITER_SERVER_HOST, port=VALKEY_WRITER_SERVER_PORT, db=0)
    return valkey.Valkey(host=VALKEY_READER_SERVER_HOST, port=VALKEY_READER_SERVER_PORT, db=0)


def get_keys()->list:
    keys = list()
    client = get_connection_connection()
    
    keys = client.scan()

    return keys

