"""
This script read the raw data of the message queue and populate the DB

INPUT       : Read data from message queue  (1)
PROCESSING  : Persist data in DB            (2)
OUTPUT      : n/a
                                           
#################################  (1)   +-----+        +-------------------------------+      
# front_end_aggregator_consumer #------->|     |        | Back_end_aggregator_producer  |
#################################        |  K  |        +-------------------------------+            
                |                        |  A  |                                                     
                | (2)                    |  F  |                                                     
               \/                        |  K  |                                                    
            +-----+                      |  A  |         +-------------------------------+
            | DB  |                      |     |         | back_end                      |
            +-----+                      |     |        +-------------------------------+
                                         |     |
                                         |     |  
                                         |     |        
+-------------------------------+        |     |        +-------------------------------+
| front_end_ui                  |        |     |        | raw_data_generator            |
+-------------------------------+        +-----+        +-------------------------------+
"""
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
import valkey


# EXAMPLE taken from https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_consumer.py

HOSTNAME = socket.gethostname()
GROUP_ID = os.getenv('GROUP_ID', HOSTNAME.replace('_', '-'))
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
KAFKA_TOPIC = os.getenv('KAFKA_TOPIC', 'summary-stats')
SCHEMA_VERSION = int(os.getenv('SCHEMA_VERSION', '1'))
SCHEMA_SUBJECT = os.getenv('SCHEMA_SUBJECT', 'TestSummaryStats')
SCHEMA_NAMESPACE = os.getenv('SCHEMA_NAMESPACE', 'tld.example')
SCHEMA = {
    "namespace": "tld.example",
    "type": "record",
    "name": "testsummarystats",
    "fields": [
        { "name": "sku", "type": "string" },
        { "name": "manufactured_qty", "type": "int" },
        { "name": "year", "type": "int" },
        { "name": "month", "type": "int" }
    ]
}
VALKEY_SERVER_HOST = os.getenv('VALKEY_SERVER_HOST', 'valkey-primary')
VALKEY_SERVER_PORT = int(os.getenv('VALKEY_SERVER_PORT', '6379'))


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
logger.debug('{} - VALKEY_SERVER_HOST           : {}'.format(HOSTNAME, VALKEY_SERVER_HOST))
logger.debug('{} - VALKEY_SERVER_PORT           : {}'.format(HOSTNAME, VALKEY_SERVER_PORT))


VALKEY_WRITE_CLIENT = valkey.Valkey(host=VALKEY_SERVER_HOST, port=VALKEY_SERVER_PORT, db=0)


class SummaryData:
    def __init__(
        self,
        sku: str,
        manufactured_qty: int,
        year: int,
        month: int
    ):
        self.sku = sku
        self.manufactured_qty = manufactured_qty
        self.year = year
        self.month = month


def dict_to_summary_stats(obj, ctx)->SummaryData:
    if obj is None:
        return None
    return SummaryData(
        sku=obj['sku'],
        manufactured_qty=int(obj['manufactured_qty']),
        year=int(obj['year']),
        month=int(obj['month'])
    )


def store_data_in_valkey(summary_data: SummaryData, retries: int=0)->bool:
    global VALKEY_WRITE_CLIENT
    try:
        key = 'manufactured:{}:{}:{}'.format(
            summary_data.sku,
            summary_data.year,
            summary_data.month
        )
        VALKEY_WRITE_CLIENT.incrby(name=key, amount=summary_data.manufactured_qty)
    except:
        logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))
        if retries > 3:
            return False
        sleep_time = 0.5 + (retries*0.5)
        logger.warning('{} - Will retry: sleeping {} seconds'.format(HOSTNAME, sleep_time))
        time.sleep(sleep_time)
        VALKEY_WRITE_CLIENT = None
        time.sleep(0.1)
        VALKEY_WRITE_CLIENT = valkey.Valkey(host=VALKEY_SERVER_HOST, port=VALKEY_SERVER_PORT, db=0)
        new_retry_qty = retries + 1
        store_data_in_valkey(summary_data=summary_data, retries=new_retry_qty)
    return True


def consume_summary_data():
    schema_str = json.dumps(SCHEMA)
    schema_registry_conf = {
        'url': '{}://{}:{}'.format(KAFKA_SCHEMA_SERVER_PROTOCOL, KAFKA_SCHEMA_SERVER_HOST, KAFKA_SCHEMA_SERVER_PORT)
    }
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    avro_deserializer = AvroDeserializer(
        schema_registry_client,
        schema_str,
        dict_to_summary_stats
    )
    consumer_conf = {
        'bootstrap.servers': '{}:{}'.format(KAFKA_BOOTSTRAP_SERVER_HOST, KAFKA_BOOTSTRAP_SERVER_PORT),
        'group.id': GROUP_ID,
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

            raw_data_in: SummaryData
            raw_data_in = avro_deserializer(msg.value(), SerializationContext(msg.topic(), MessageField.VALUE))
            if raw_data_in is not None:
                logger.debug(
                    '{} - SKU: {} {}-{} TOTAL: {}'.format(
                        HOSTNAME,
                        raw_data_in.sku,
                        raw_data_in.year,
                        str(raw_data_in.month,).zfill(2),
                        raw_data_in.manufactured_qty
                    )
                )
                if store_data_in_valkey(summary_data=raw_data_in) is False:
                    # TODO Reject message so that another consumer in our group can try and process it
                    logger.warning('{} - REJECTED Message and putting it back in queue for processing'.format(HOSTNAME))
        except:
            logger.error(
                '{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc())
            )
            break

    consumer.close()


while True:
    consume_summary_data()
    logger.warning('{} - Died due to an exception. Sleeping 3 seconds before trying again...'.format(HOSTNAME))
    time.sleep(3)
