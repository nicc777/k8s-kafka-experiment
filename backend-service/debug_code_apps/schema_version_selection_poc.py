"""
This script produces random data in places it on a message queue

INPUT       : Select a schema to publish/consume a record                   (1)
PROCESSING  : Publish a record and consume it, using the discovered schema  (2)
OUTPUT      : n/a

+---------+       
|         |   (1)  #################################
|  KAFKA  |<-------# schema_version_selection_poc  #
|         |<-------#                               #
|         |   (2)  #################################
+---------+

This POC is intended to work on Schema Version 2
"""
import os
import random
import socket
import logging
import time
import json
import sys
import traceback
import copy
from uuid import uuid4
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient, RegisteredSchema, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer

# EXAMPLE taken from https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_producer.py

HOSTNAME = socket.gethostname()
SKU = 'SKU_{}'.format(
    str(random.randint(1,999999)).zfill(6)
)
DEBUG = True
MAX_COUNTER_VALUE = 4
MAX_RATE_PER_SECOND = 2
MAX_INTERVAL_PER_LOOP = 999999999 / MAX_RATE_PER_SECOND
SLEEP_BUFFER = 10
REPORT_RATE_INTERVAL_TICKS = 60
KAFKA_BOOTSTRAP_SERVER_HOST = 'kafka.confluent.svc.cluster.local'
KAFKA_BOOTSTRAP_SERVER_PORT = '9092'
KAFKA_SCHEMA_SERVER_HOST = 'schemaregistry.confluent.svc.cluster.local'
KAFKA_SCHEMA_SERVER_PORT = '8081'
KAFKA_SCHEMA_SERVER_PROTOCOL = 'http'
KAFKA_TOPIC = 'raw-data-in'
SCHEMA_SUBJECT = 'testrawdata'
SCHEMA_NAMESPACE = 'tld.example'

MONTH_DAYS = [
    00,
    31,     # 1
    28,     # 2
    31,     # 3
    30,     # 4
    31,     # 5
    30,     # 6
    31,     # 7
    31,     # 8
    30,     # 9
    31,     # 10
    30,     # 11
    31,     # 12
]
DEFECTS_MIN = 1
DEFECTS_MAX_SUBTRACTOR = 25


logger = logging.getLogger('raw-data-generator')
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
logger.debug('{} - SCHEMA_SUBJECT               : {}'.format(HOSTNAME, SCHEMA_SUBJECT))
logger.debug('{} - SCHEMA_NAMESPACE             : {}'.format(HOSTNAME, SCHEMA_NAMESPACE))


class RawData:
    def __init__(
        self,
        sku: str,
        manufactured_qty: int,
        defect_qty: int,
        year: int,
        month: int,
        day: int,
        hour: int
    ):
        self.sku = sku
        self.manufactured_qty = manufactured_qty
        self.defect_qty = defect_qty
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour


def raw_data_to_dict(raw_data: RawData, ctx):
    return dict(
        sku=raw_data.sku,
        manufactured_qty=raw_data.manufactured_qty,
        defect_qty=raw_data.defect_qty,
        year=raw_data.year,
        month=raw_data.month,
        day=raw_data.day,
        hour=raw_data.hour
    )


def delivery_report(err, msg):
    if err is not None:
        logger.error('{} - Delivery failed for User record {}: {}'.format(HOSTNAME, msg.key(), err))
        return
    logger.info(
        '{} - User record {} successfully produced to {} [{}] at offset {}'.format(
            HOSTNAME,
            msg.key(),
            msg.topic(),
            msg.partition(),
            msg.offset()
        )
    )


def do_sleep(now_ns: float, counter_timestamp_start: float, counter:int):
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
    return time.time_ns()


def max_defects_possible(base_qty: int)->int:
    return base_qty - DEFECTS_MAX_SUBTRACTOR


def calc_final_defect_qty(qty_widgets_manufactured: int)->int:
    defects_max = max_defects_possible(base_qty=qty_widgets_manufactured)
    defect_percentage = random.randrange(1,100)/100
    defect_qty = int(qty_widgets_manufactured * defect_percentage)
    if defect_qty > defects_max:
        defect_qty = defects_max
    if defect_qty < 1:
        defect_qty = 1
    return defect_qty


def retrieve_supported_registered_schema(schema_registry_client: SchemaRegistryClient)->RegisteredSchema:
    matched_registered_schema: RegisteredSchema
    matched_registered_schema = None

    schema_versions = schema_registry_client.get_versions(subject_name=SCHEMA_SUBJECT)  # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#schemaregistryclient
    matched_schema_found = False
    local_schema_sample = RawData(sku='', manufactured_qty=0, defect_qty=0, year=0, month=0, day=0, hour=0)
    local_schema_sample_as_dict = raw_data_to_dict(raw_data=local_schema_sample, ctx=None)
    local_schema_sample_keys = tuple(local_schema_sample_as_dict.keys())
    local_schema_sample_keys_not_matched = list()
    local_schema_sample_keys_matched = list()
    for schema_version in schema_versions:
        registered_schema: RegisteredSchema # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#confluent_kafka.schema_registry.RegisteredSchema
        registered_schema = schema_registry_client.get_version(subject_name=SCHEMA_SUBJECT, version=schema_version)
        logger.debug('Schema String: {}'.format(registered_schema.schema.schema_str))
        schema_as_dict: dict
        schema_as_dict = json.loads(registered_schema.schema.schema_str)
        schema_keys = list()
        for field in schema_as_dict['fields']:
            schema_keys.append(field['name'])
        schema_keys_not_matched = list()
        schema_keys_matched = list()
        for schema_key in schema_keys:
            if schema_key in local_schema_sample_keys:
                schema_keys_matched.append(schema_key)
            else:
                schema_keys_not_matched.append(schema_key)
        for local_schema_key in local_schema_sample_keys:
            if local_schema_key in schema_keys:
                local_schema_sample_keys_matched.append(local_schema_key)
            else:
                local_schema_sample_keys_not_matched.append(local_schema_key)
        if len(schema_keys_not_matched) > 0:
            logger.warning('Rejecting version {} because the following fields are NOT in the local schema: {}'.format(schema_version, schema_keys_not_matched))
        if len(local_schema_sample_keys_not_matched) > 0:
            logger.warning('Rejecting version {} because the following fields are NOT in the retrieved schema: {}'.format(schema_version, local_schema_sample_keys_not_matched))
        if len(schema_keys_not_matched) == 0 and len(local_schema_sample_keys_not_matched) == 0:
            matched_schema_found = True
            matched_registered_schema = copy.deepcopy(registered_schema)
        local_schema_sample_keys_not_matched = list()   # Reset
        local_schema_sample_keys_matched = list()       # Reset
    if matched_schema_found is False:
        raise Exception('Failed to retrieve a matching schema from the schema registry')
    logger.info('Schema Version Selected: {}'.format(matched_registered_schema.version))
    logger.info('Schema String: {}'.format(matched_registered_schema.schema.schema_str))

    return matched_registered_schema


def produce_raw_data():
    schema_registry_conf = {
        'url': '{}://{}:{}'.format(KAFKA_SCHEMA_SERVER_PROTOCOL, KAFKA_SCHEMA_SERVER_HOST, KAFKA_SCHEMA_SERVER_PORT)
    }
    schema_registry_client = SchemaRegistryClient(schema_registry_conf)
    matched_registered_schema = retrieve_supported_registered_schema(schema_registry_client=schema_registry_client)

    avro_serializer = AvroSerializer(
        schema_registry_client,
        matched_registered_schema.schema.schema_str,
        raw_data_to_dict
    )

    string_serializer = StringSerializer('utf_8')
    producer_conf = {
        'bootstrap.servers': '{}:{}'.format(KAFKA_BOOTSTRAP_SERVER_HOST, KAFKA_BOOTSTRAP_SERVER_PORT)
    }
    producer = Producer(producer_conf)

    now_ns = time.time_ns()
    counter = 0
    counter_timestamp_start = time.time_ns()
    produce_more_data = True
    while produce_more_data:
        counter += 1
        producer.poll(0.0)
        try:
            month = random.randint(1, 12)
            manufactured_qty=random.randint(50, 100)
            qty_defects = calc_final_defect_qty(qty_widgets_manufactured=manufactured_qty)
            simulated_raw_data = RawData(
                sku=SKU,
                manufactured_qty=manufactured_qty,
                defect_qty=qty_defects,
                year=random.randint(2000, 2024),
                month=month,
                day=random.randint(1, MONTH_DAYS[month]),
                hour=random.randint(8, 20)
            )
            logger.debug(
                '{} - RAW DATA Generated: {}'.format(
                    HOSTNAME,
                    json.dumps(raw_data_to_dict(raw_data=simulated_raw_data, ctx=None), sort_keys=True)
                )
            )
            producer.produce(
                topic=KAFKA_TOPIC,
                key=string_serializer(str(uuid4())),
                value=avro_serializer(simulated_raw_data, SerializationContext(KAFKA_TOPIC, MessageField.VALUE)),
                on_delivery=delivery_report
            )
            logger.info('{} - Produce {} messages'.format(HOSTNAME, counter))
            producer.flush(30)
        except:
            logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))
            continue
        now_ns = do_sleep(now_ns=now_ns, counter_timestamp_start=counter_timestamp_start, counter=counter)
        if MAX_COUNTER_VALUE > 0:
            if counter > MAX_COUNTER_VALUE:
                produce_more_data = False
                logger.warning('{} - Reached MAX_COUNTER_VALUE of {} - stopping...'.format(HOSTNAME, MAX_COUNTER_VALUE))
                producer.flush()
    

produce_raw_data()


while True:
    logger.info('{} - Contemplating the meaning of life...'.format(HOSTNAME))
    time.sleep(3.0)

