import os
import random
import socket
import logging
import time
import json
import sys
import traceback
from confluent_kafka import avro
from confluent_kafka.avro import AvroProducer


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
logger.info('{} - SKU: {}'.format(HOSTNAME, SKU))
logger.debug('{} - MAX_RATE_PER_SECOND: {}'.format(HOSTNAME, MAX_RATE_PER_SECOND))
logger.debug('{} - MAX_INTERVAL_PER_LOOP: {}'.format(HOSTNAME, MAX_INTERVAL_PER_LOOP))
logger.debug('{} - SLEEP_BUFFER: {}'.format(HOSTNAME, SLEEP_BUFFER))


config = {
    'bootstrap.servers': 'localhost:9092',
    'schema.registry.url': 'http://localhost:8081'
}
try:
    value_schema = avro.loads('{"type": "record", "name": "Value", "fields": [{"name": "name", "type": "string"}]}')
    producer = AvroProducer(config, default_value_schema=value_schema)
except:
    logger.error('EXCEPTION: {}'.format(traceback.format_exc()))
    time.sleep(120)
    sys.exit(1)


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
        producer.produce(topic='test_topic', value={"name": "Alice"})
        producer.flush()
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







