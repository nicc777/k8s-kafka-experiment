"""
This script will periodically read all data from DB and produce a stream of
summary messages to be send to the front-end stats aggregator 

INPUT       : Read data from Valkey                     (1)
PROCESSING  : Calculate summary statistics
OUTPUT      : Place summary stats on message queue      (2)

                                           
+-------------------------------+        +-----+   (2)  #################################      (1)
| front_end_aggregator_consumer |        |     |<-------# Back_end_aggregator_producer  #------------+
+-------------------------------+        |  K  |        #################################            |
                                         |  A  |                                                     |
                                         |  F  |                                                     |
                                         |  K  |                                                    \/
            +-----+                      |  A  |        +-------------------------------+        +-----+
            | DB  |                      |     |        | back_end                      |        | DB  |
            +-----+                      |     |        +-------------------------------+        +-----+
                                         |     |
                                         |     |  
                                         |     |        
+-------------------------------+        |     |        +-------------------------------+
| front_end_ui_rest_api         |        |     |        | raw_data_generator            |
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
import copy
from uuid import uuid4
from confluent_kafka import Producer
from confluent_kafka.serialization import StringSerializer, SerializationContext, MessageField
from confluent_kafka.schema_registry import SchemaRegistryClient, RegisteredSchema, Schema
from confluent_kafka.schema_registry.avro import AvroSerializer
import valkey

# EXAMPLE taken from https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_producer.py

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
        { "name": "defect_qty", "type": "int" },
        { "name": "sku_manufacturing_cost", "type": "int" },
        { "name": "year", "type": "int" },
        { "name": "month", "type": "int" }
    ]
}
VALKEY_SERVER_HOST = os.getenv('VALKEY_SERVER_HOST', 'valkey-primary')
VALKEY_SERVER_PORT = int(os.getenv('VALKEY_SERVER_PORT', '6379'))


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
logger.debug('{} - SCHEMA_VERSION               : {}'.format(HOSTNAME, SCHEMA_VERSION))
logger.debug('{} - SCHEMA_SUBJECT               : {}'.format(HOSTNAME, SCHEMA_SUBJECT))
logger.debug('{} - SCHEMA_NAMESPACE             : {}'.format(HOSTNAME, SCHEMA_NAMESPACE))
logger.debug('{} - VALKEY_SERVER_HOST           : {}'.format(HOSTNAME, VALKEY_SERVER_HOST))
logger.debug('{} - VALKEY_SERVER_PORT           : {}'.format(HOSTNAME, VALKEY_SERVER_PORT))


class SummaryData:
    def __init__(
        self,
        sku: str,
        manufactured_qty: int,
        defect_qty: int,
        sku_manufacturing_cost: int,
        year: int,
        month: int
    ):
        self.sku = sku
        self.manufactured_qty = manufactured_qty
        self.defect_qty = defect_qty
        self.sku_manufacturing_cost = sku_manufacturing_cost
        self.year = year
        self.month = month


class Records:
    def __init__(self):
        self.manufactured = dict()
        self.defects = dict()
        self.sku_manufacturing_cost = dict()
    def add_record(self, sku: str, year: int, month: int, manufactured_qty: int, defect_qty: int, sku_manufacturing_cost: int):
        index = '{}:{}:{}'.format(sku, year, month)
        if index not in self.manufactured:
            self.manufactured[index] = manufactured_qty
        else:
            self.manufactured[index] = self.manufactured[index] + manufactured_qty
        if index not in self.defects:
            self.defects[index] = defect_qty
        else:
            self.defects[index] = self.defects[index] + defect_qty
        if index not in self.sku_manufacturing_cost:
            self.sku_manufacturing_cost[index] = sku_manufacturing_cost
        else:
            self.sku_manufacturing_cost[index] = self.sku_manufacturing_cost[index] + sku_manufacturing_cost
    def keys(self)->tuple:
        return tuple(self.manufactured.keys())
    def pop(self)->SummaryData:
        keys = self.keys()
        if len(keys) == 0:
            raise Exception('No More Records...')
        index = random.choice(keys)
        manufactured_qty = self.manufactured.pop(index)
        defect_qty = self.defects.pop(index)
        sku_manufacturing_cost = self.sku_manufacturing_cost.pop(index)
        key_items = index.split(':')
        return SummaryData(
            sku=key_items[0],
            year=int(key_items[1]),
            month=int(key_items[2]),
            manufactured_qty=manufactured_qty,
            defect_qty=defect_qty,
            sku_manufacturing_cost=sku_manufacturing_cost
        )


def summary_data_to_dict(raw_data: SummaryData, ctx):
    return dict(
        sku=raw_data.sku,
        manufactured_qty=raw_data.manufactured_qty,
        defect_qty=raw_data.defect_qty,
        sku_manufacturing_cost=raw_data.sku_manufacturing_cost,
        year=raw_data.year,
        month=raw_data.month
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


def read_keys(client, year: int)->list:
    try:
        keys = list()
        index = 'manufactured:*:{}:*'.format(year)
        for key in client.scan_iter(index):
            #logger.debug('{} - Retrieved key (type={})  :  {}'.format(HOSTNAME, type(key), key))
            keys.append(key)
        logger.info('{}- Retrieved {} keys from DB'.format(HOSTNAME, len(keys)))
    except:
        logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))
    return keys


def summarize_data_from_db(client, key: bytes, current_records: Records):
    try:
        manufactured_qty = 0
        defect_qty = 0
        sku_manufacturing_cost = 0
        """
            0       1    2    3    4    5
        '__TYPE__:sku:year:month:day:hour'
        """
        decoded_key = key.decode('utf-8')
        key2_str = decoded_key.replace('manufactured', 'defects')
        key2 = key2_str.encode('utf-8')
        key3_str = decoded_key.replace('manufactured', 'cost')
        key3 = key3_str.encode('utf-8')
        try:
            manufactured_qty = int(client.get(key))
        except:
            logger.warning('{} - FAILED to get Manufactured QTY - Assuming 0'.format(HOSTNAME))
        try:
            defect_qty = int(client.get(key2))
        except:
            logger.warning('{} - FAILED to get Defect QTY - Assuming 0'.format(HOSTNAME))
        try:
            sku_manufacturing_cost = int(client.get(key3))
        except:
            logger.warning('{} - FAILED to get Defect QTY - Assuming 0'.format(HOSTNAME))
        logger.debug('{} - decoded_key={}'.format(HOSTNAME, decoded_key))
        key_elements = decoded_key.split(':')
        current_records.add_record(
            sku=key_elements[1],
            year=int(key_elements[2]),
            month=int(key_elements[3]),
            manufactured_qty=manufactured_qty,
            defect_qty=defect_qty,
            sku_manufacturing_cost=sku_manufacturing_cost
        )
    except:
        logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))


def retrieve_supported_registered_schema(schema_registry_client: SchemaRegistryClient)->RegisteredSchema:
    matched_registered_schema: RegisteredSchema
    matched_registered_schema = None

    schema_versions = schema_registry_client.get_versions(subject_name=SCHEMA_SUBJECT)  # https://docs.confluent.io/platform/current/clients/confluent-kafka-python/html/index.html#schemaregistryclient
    matched_schema_found = False
    local_schema_sample = SummaryData(sku='', defect_qty=0, sku_manufacturing_cost=0, manufactured_qty=0, year=0, month=0)
    local_schema_sample_as_dict = summary_data_to_dict(raw_data=local_schema_sample, ctx=None)
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


def publish_summary(records: Records):
    try:
        schema_registry_conf = {
            'url': '{}://{}:{}'.format(KAFKA_SCHEMA_SERVER_PROTOCOL, KAFKA_SCHEMA_SERVER_HOST, KAFKA_SCHEMA_SERVER_PORT)
        }
        schema_registry_client = SchemaRegistryClient(schema_registry_conf)
        matched_registered_schema = retrieve_supported_registered_schema(schema_registry_client=schema_registry_client)
        avro_serializer = AvroSerializer(
            schema_registry_client,
            matched_registered_schema.schema.schema_str,
            summary_data_to_dict
        )
        string_serializer = StringSerializer('utf_8')
        producer_conf = {
            'bootstrap.servers': '{}:{}'.format(KAFKA_BOOTSTRAP_SERVER_HOST, KAFKA_BOOTSTRAP_SERVER_PORT)
        }
        producer = Producer(producer_conf)

        produce_more_data = True
        while produce_more_data:
            record = records.pop()
            try:
                logger.debug(
                    '{} - RAW DATA Generated: {}'.format(
                        HOSTNAME,
                        json.dumps(summary_data_to_dict(raw_data=record, ctx=None), sort_keys=True)
                    )
                )
                producer.produce(
                    topic=KAFKA_TOPIC,
                    key=string_serializer(str(uuid4())),
                    value=avro_serializer(record, SerializationContext(KAFKA_TOPIC, MessageField.VALUE)),
                    on_delivery=delivery_report
                )
                logger.debug('{} - Sent data:'.format(HOSTNAME, json.dumps(summary_data_to_dict(raw_data=record, ctx=None))))
            except:
                logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))
                continue
            producer.flush(30)
    except:
        logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))


while True:
    logger.info('{} - Entering Main Loop'.format(HOSTNAME))
    records = Records()
    try:
        valkey_client = valkey.Valkey(host=VALKEY_SERVER_HOST, port=VALKEY_SERVER_PORT, db=0)
        for year in range(2000,2025):
            logger.info('{} - Getting data for year {}'.format(HOSTNAME, year))
            for key in read_keys(client=valkey_client, year=year):
                summarize_data_from_db(client=valkey_client, key=key, current_records=records)
        logger.info('{} - Records: {}'.format(HOSTNAME, len(records.manufactured)))
        publish_summary(records=records)
        logger.info('{} - Processing Done - sleeping 3 seconds'.format(HOSTNAME))
        valkey_client = None
    except:
        logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))
    time.sleep(3.0)

