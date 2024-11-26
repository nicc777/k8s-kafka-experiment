"""
This script produces random data in places it on a message queue

INPUT       : Random data records, with SKU target selected from DB         (1)
PROCESSING  : Build up raw data objects to be pushed onto a message queue
OUTPUT      : Places raw data objects onto the message queue                (2)

                                           
+-------------------------------+        +-----+        +-------------------------------+      
| front_end_aggregator_consumer |        |     |        | Back_end_aggregator_producer  |
+-------------------------------+        |  K  |        +-------------------------------+            
                                         |  A  |                                                     
                                         |  F  |                                                     
                                         |  K  |                                                    
            +-----+                      |  A  |        +-------------------------------+        +-----+
            | DB  |                      |     |        | back_end                      |        | DB  |
            +-----+                      |     |        +-------------------------------+        +-----+
                                         |     |                                                   ^
                                         |     |                                                   |
                                         |     |                                                   |
+-------------------------------+        |     |   (2)  #################################   (1)    |
| front_end_ui_rest_api         |        |     |<-------# raw_data_generator            #----------+
+-------------------------------+        +-----+        #################################
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
        { "name": "defect_qty", "type": "int" },
        { "name": "sku_manufacturing_cost", "type": "int" },
        { "name": "year", "type": "int" },
        { "name": "month", "type": "int" },
        { "name": "day", "type": "int" },
        { "name": "hour", "type": "int" },
    ]
}
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


def calc_cost_with_inflation(base_price: int, target_year: int)->int:
    if target_year == 2000:
        return base_price
    i = 2000
    while i < target_year:
        i += 1
        inflation_number = inflation.get_inflation_for_year(year=i)
        inflation_value_on_base = int(base_price * ( inflation_number/100.0 ))
        if inflation_value_on_base < 1:
            inflation_value_on_base = 1
        base_price += inflation_value_on_base
    return base_price


class AnnualInflation:

    def __init__(self):
        self.inflation = dict()
        self._load_inflation_from_db()

    def _load_inflation_from_db(self):
        try:
            client = valkey.Valkey(host=VALKEY_SERVER_HOST, port=VALKEY_SERVER_PORT, db=0)
            inflation_as_str = client.get('inflation')
            logger.debug('{} - inflation_as_str: {}'.format(HOSTNAME, inflation_as_str))
            self.inflation = json.loads(inflation_as_str)
        except:
            logger.error('EXCEPTION: {}'.format(traceback.format_exc()))

    def get_inflation_for_year(self, year: int)->int:
        key = '{}'.format(year)
        if key in self.inflation:
            return int(self.inflation[key])
        logger.warning('{} - No inflation data for year {} available - returning default of 5%'.format(HOSTNAME, year))
        return 5
    

class SkuManufacturingUnitCosts:

    def __init__(self):
        self.sku_start_manufacturing_costs = dict()
        self.annual_sku_manufacturing_costs = dict()
        self._load_sku_start_manufacturing_costs_from_db()

    def _load_sku_start_manufacturing_costs_from_db(self):
        try:
            client = valkey.Valkey(host=VALKEY_SERVER_HOST, port=VALKEY_SERVER_PORT, db=0)
            sku_start_manufacturing_costs_as_str = client.get('sku_start_manufacturing_costs')
            logger.debug('{} - sku_start_manufacturing_costs_as_str: {}'.format(HOSTNAME, sku_start_manufacturing_costs_as_str))
            self.sku_start_manufacturing_costs = json.loads(sku_start_manufacturing_costs_as_str)
        except:
            logger.error('EXCEPTION: {}'.format(traceback.format_exc()))

    def _calc_annual_sku_manufacturing_costs(self):
        for sku, sku_start_price in self.sku_start_manufacturing_costs.items():
            self.annual_sku_manufacturing_costs[sku] = dict()
            self.annual_sku_manufacturing_costs[sku]['2000'] = sku_start_price
            i = 2000
            while i < 2024:
                i += 1
                year_key = '{}'.format(i)
                self.annual_sku_manufacturing_costs[sku][year_key] = calc_cost_with_inflation(base_price=sku_start_price, target_year=i)
            logger.info('{} - Annual manufacturing costs per SKU: {}'.format(HOSTNAME, json.dumps(self.annual_sku_manufacturing_costs, default=str, indent=4)))

    def get_sku_manufacturing_cost(self, sku: str, year: int)->int:
        year_key = '{}'.format(year)
        if sku in self.annual_sku_manufacturing_costs:
            if year_key in self.annual_sku_manufacturing_costs[sku]:
                return self.annual_sku_manufacturing_costs[sku][year_key]
        return 0


inflation = AnnualInflation()
sku_manufacturing_unit_costs = SkuManufacturingUnitCosts()


class RawData:
    def __init__(
        self,
        sku: str,
        manufactured_qty: int,
        defect_qty: int,
        sku_manufacturing_cost: int,
        year: int,
        month: int,
        day: int,
        hour: int
    ):
        self.sku = sku
        self.manufactured_qty = manufactured_qty
        self.defect_qty = defect_qty
        self.sku_manufacturing_cost = sku_manufacturing_cost
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour


def raw_data_to_dict(raw_data: RawData, ctx):
    return dict(
        sku=raw_data.sku,
        manufactured_qty=raw_data.manufactured_qty,
        defect_qty=raw_data.defect_qty,
        sku_manufacturing_cost=raw_data.sku_manufacturing_cost,
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
    local_schema_sample = RawData(sku='', defect_qty=0, manufactured_qty=0, year=0, month=0, day=0, hour=0)
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


def select_sku()->str:
    try:
        client = valkey.Valkey(host=VALKEY_SERVER_HOST, port=VALKEY_SERVER_PORT, db=0)
        sku_list_as_str = client.get('sku_names')
        logger.debug('{} - sku_list_as_str: {}'.format(HOSTNAME, sku_list_as_str))
        sku_list = json.loads(sku_list_as_str)
        return random.choice(sku_list)
    except:
        logger.error('EXCEPTION: {}'.format(traceback.format_exc()))
    raise Exception('Failed to get SKU list from DB')


def create_data(month: int, manufactured_qty: int, year: int, hour: int)->RawData:
    try:
        sku = select_sku()
        return RawData(
            sku=sku,
            manufactured_qty=manufactured_qty,
            sku_manufacturing_cost=sku_manufacturing_unit_costs.get_sku_manufacturing_cost(sku=sku, year=year) * manufactured_qty,
            defect_qty=calc_final_defect_qty(qty_widgets_manufactured=manufactured_qty),
            year=year,
            month=month,
            day=random.randint(1, MONTH_DAYS[month]),
            hour=hour
        )
    except:
        logger.error('EXCEPTION: {}'.format(traceback.format_exc()))
    return None


def is_data_valid(data: RawData)->bool:
    if data is None:
        return False
    if isinstance(data, RawData):
        return True
    return False


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
            year = random.randint(2000, 2024)
            hour = random.randint(8, 20)
            simulated_raw_data = create_data(month=month, manufactured_qty=manufactured_qty, year=year, hour=hour)
            if is_data_valid(data=simulated_raw_data) is True:
                logger.info(
                    '{} - SKU {} data generated for {}.{}.{}'.format(
                        HOSTNAME,
                        simulated_raw_data.sku,
                        simulated_raw_data.day,
                        simulated_raw_data.month,
                        simulated_raw_data.year
                    )
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

