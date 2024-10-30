import os
import random
import socket
import logging
import time
import json
import sys
import traceback
from confluent_kafka.avro import AvroProducer
from confluent_kafka.avro.cached_schema_registry_client import CachedSchemaRegistryClient


HOSTNAME = socket.gethostname()
SKU = 'SKU_{}'.format(
    str(random.randint(1,999999)).zfill(6)
)
DEBUG = bool(int(os.getenv('DEBUG', '0')))
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

KAFKA_SERVER_CONNECTION_CONFIG = {
    'bootstrap.servers': '{}:{}'.format(KAFKA_BOOTSTRAP_SERVER_HOST, KAFKA_BOOTSTRAP_SERVER_PORT),
    'schema.registry.url': '{}://{}:{}'.format(KAFKA_SCHEMA_SERVER_PROTOCOL, KAFKA_SCHEMA_SERVER_HOST, KAFKA_SCHEMA_SERVER_PORT)
}

# Initialize Schema Registry client
schema_registry_client = CachedSchemaRegistryClient(KAFKA_SERVER_CONNECTION_CONFIG['schema.registry.url'])


# Function to load specific schema version
def load_schema(subject_name, version):
    return schema_registry_client.get_version(subject_name, version).schema
                                              

def produce_with_schema(topic, data, schema_subject, schema_version):
    schema = load_schema(schema_subject, schema_version)
    avro_producer = AvroProducer(KAFKA_SERVER_CONNECTION_CONFIG, default_value_schema=schema)

    if schema.validate(data):
        avro_producer.produce(topic=topic, value=data)
        avro_producer.flush()
        print(f"Message with schema version {schema_version} sent successfully!")
    else:
        print(f"Data validation failed for schema version {schema_version}.")


now_ns = time.time_ns()
counter = 0
counter_timestamp_start = time.time_ns()
while True:
    counter += 1
    raw_data = {
        "sku": '{}'.format(SKU),
        "manufactured_qty": 0,
        "year": 2024,
        "month": 1,
        "day": 15,
        "hour": 3
    }
    logger.info('{} - DATA: {}'.format(HOSTNAME, json.dumps(raw_data, default=str)))
    try:
        produce_with_schema(
            KAFKA_TOPIC,
            raw_data,
            '{}.{}-value'.format(
                SCHEMA_NAMESPACE,
                SCHEMA_SUBJECT
            ),
            SCHEMA_VERSION
        )
    except:
        logger.error('EXCEPTION: {}'.format(traceback.format_exc()))
    now_ns_step = time.time_ns()
    time_diff = now_ns_step - now_ns
    sleep_time = 0.0
    if time_diff < MAX_INTERVAL_PER_LOOP:
        sleep_time = (MAX_INTERVAL_PER_LOOP - time_diff) + SLEEP_BUFFER
    if sleep_time > 0.0:
        sleep_time = sleep_time / 1000000000
        time.sleep(sleep_time)
    if counter % REPORT_RATE_INTERVAL_TICKS == 0:
        counter_current_timestamp = time.time_ns()
        counter_time_diff = (counter_current_timestamp - counter_timestamp_start)/1000000000
        current_rate = counter / counter_time_diff
        logger.info(
            '{} - Processed {} data points in {} seconds. Rate: {} per second'.format(
                HOSTNAME,
                counter,
                counter_time_diff,
                current_rate
            )
        )
    now_ns = time.time_ns()







