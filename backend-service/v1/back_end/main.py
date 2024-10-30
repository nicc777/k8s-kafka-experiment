import os
import random
import socket
import logging
import time
import json
import sys
import traceback
from confluent_kafka import Consumer
from confluent_kafka.serialization import SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient
from confluent_kafka.schema_registry.avro import AvroDeserializer


# EXAMPLE taken from https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_consumer.py

HOSTNAME = socket.gethostname()
SKU = 'SKU_{}'.format(
    str(random.randint(1,999999)).zfill(6)
)
DEBUG = bool(int(os.getenv('DEBUG', '0')))
MAX_COUNTER_VALUE = int(os.getenv('MAX_COUNTER_VALUE', '-1'))
MAX_RATE_PER_SECOND = int(os.getenv('MAX_RATE_PER_SECOND', '2'))
MAX_INTERVAL_PER_LOOP = 999999999 / MAX_RATE_PER_SECOND
SLEEP_BUFFER = 10
REPORT_RATE_INTERVAL_TICKS = int(os.getenv('REPORT_RATE_INTERVAL_TICKS', '60'))
KAFKA_HOST = ''
KAFKA_BOOTSTRAP_SERVER_HOST = os.getenv('KAFKA_BOOTSTRAP_SERVER', 'localhost')
KAFKA_BOOTSTRAP_SERVER_PORT = os.getenv('KAFKA_BOOTSTRAP_PORT', '9092')
KAFKA_SCHEMA_SERVER_HOST = os.getenv('SCHEMA_SERVER_HOST', 'localhost')
KAFKA_SCHEMA_SERVER_PORT = os.getenv('SCHEMA_SERVER_PORT', '8081')
KAFKA_SCHEMA_SERVER_PROTOCOL = os.getenv('SCHEMA_SERVER_PROTOCOL', 'http')
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'raw-data-in')
SCHEMA_VERSION = int(os.getenv('SCHEMA_VERSION', '1'))
SCHEMA_SUBJECT = os.getenv('SCHEMA_SUBJECT', 'TestRawData')
SCHEMA_NAMESPACE = os.getenv('SCHEMA_NAMESPACE', 'tld.example')
SCHEMA = {
    "namespace": "tld.example",
    "type": "record",
    "name": "testrawdata",
    "fields": [
        { "name": "sku", "type": "string" },
        { "name": "manufactured_qty", "type": "int" },
        { "name": "year", "type": "int" },
        { "name": "month", "type": "int" },
        { "name": "day", "type": "int" },
        { "name": "hour", "type": "int" },
    ]
}


logger = logging.getLogger('raw_data_generator')
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
logger.info('{} - SKU                          : {}'.format(HOSTNAME, SKU))
logger.debug('{} - MAX_RATE_PER_SECOND          : {}'.format(HOSTNAME, MAX_RATE_PER_SECOND))
logger.debug('{} - MAX_INTERVAL_PER_LOOP        : {}'.format(HOSTNAME, MAX_INTERVAL_PER_LOOP))
logger.debug('{} - SLEEP_BUFFER                 : {}'.format(HOSTNAME, SLEEP_BUFFER))
logger.debug('{} - KAFKA_BOOTSTRAP_SERVER_HOST  : {}'.format(HOSTNAME, KAFKA_BOOTSTRAP_SERVER_HOST))
logger.debug('{} - KAFKA_BOOTSTRAP_SERVER_PORT  : {}'.format(HOSTNAME, KAFKA_BOOTSTRAP_SERVER_PORT))
logger.debug('{} - KAFKA_SCHEMA_SERVER_PROTOCOL : {}'.format(HOSTNAME, KAFKA_SCHEMA_SERVER_PROTOCOL))
logger.debug('{} - KAFKA_SCHEMA_SERVER_HOST     : {}'.format(HOSTNAME, KAFKA_SCHEMA_SERVER_HOST))
logger.debug('{} - KAFKA_SCHEMA_SERVER_PORT     : {}'.format(HOSTNAME, KAFKA_SCHEMA_SERVER_PORT))
logger.debug('{} - KAFKA_TOPIC                  : {}'.format(HOSTNAME, KAFKA_TOPIC))
logger.debug('{} - SCHEMA_VERSION               : {}'.format(HOSTNAME, SCHEMA_VERSION))
logger.debug('{} - SCHEMA_SUBJECT               : {}'.format(HOSTNAME, SCHEMA_SUBJECT))
logger.debug('{} - SCHEMA_NAMESPACE             : {}'.format(HOSTNAME, SCHEMA_NAMESPACE))


class RawData:
    def __init__(
        self,
        sku: str,
        manufactured_qty: int,
        year: int,
        month: int,
        day: int,
        hour: int
    ):
        self.sku = sku
        self.manufactured_qty = manufactured_qty
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour


def dict_to_raw_data(obj, ctx)->RawData:
    if obj is None:
        return None
    return RawData(
        sku=obj['sku'],
        manufactured_qty=int(obj['manufactured_qty']),
        year=int(obj['year']),
        month=int(obj['month']),
        day=int(obj['day']),
        hour=int(obj['hour'])
    )


def delivery_report(err, msg):
    if err is not None:
        logger.error('{} - Delivery failed for User record {}: {}'.format(HOSTNAME, msg.key(), err))
        return
    logger.error(
        '{} - User record {} successfully produced to {} [{}] at offset {}'.format(
            HOSTNAME,
            msg.key(),
            msg.topic(),
            msg.partition(),
            msg.offset()
        )
    )


def consume_raw_data():
    schema_str = json.dumps(SCHEMA)
    schema_registry_conf = {
        'url': '{}://{}:{}'.format(KAFKA_SCHEMA_SERVER_PROTOCOL, KAFKA_SCHEMA_SERVER_HOST, KAFKA_SCHEMA_SERVER_PORT)
    }
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    avro_deserializer = AvroDeserializer(
        schema_registry_client,
        schema_str,
        dict_to_raw_data
    )
    consumer_conf = {
        'bootstrap.servers': '{}:{}'.format(KAFKA_BOOTSTRAP_SERVER_HOST, KAFKA_BOOTSTRAP_SERVER_PORT),
        'group.id': KAFKA_TOPIC,
        'auto.offset.reset': "earliest"
    }
    consumer = Consumer(consumer_conf)
    consumer.subscribe([KAFKA_TOPIC])

    while True:
        try:
            # SIGINT can't be handled when polling, limit timeout to 1 second.
            msg = consumer.poll(1.0)
            if msg is None:
                continue

            raw_data_in: RawData
            raw_data_in = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
            if raw_data_in is not None:
                logger.debug(
                    '{} - SKU: {} {}-{}-{} Hour {} TOTAL: {}'.format(
                        HOSTNAME,
                        raw_data_in.sku,
                        str(raw_data_in.day).zfill(2),
                        str(raw_data_in.month,).zfill(2),
                        raw_data_in.year,
                        str(raw_data_in.hour,).zfill(2),
                        raw_data_in.manufactured_qty
                    )
                )
        except:
            logger.error(
                '{} - EXCEPTON: {}'.format(HOSTNAME, traceback.format_exc())
            )
            break

    consumer.close()


while True:
    consume_raw_data()
    logger.warning('{} - Died due to an exception. Sleeping 3 seconds before trying again...'.format(HOSTNAME))
    time.sleep(3)
