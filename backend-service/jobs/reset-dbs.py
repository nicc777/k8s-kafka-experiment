import os
import random
import logging
import json
import sys
import traceback
import copy
import valkey


DEBUG = bool(int(os.getenv('DEBUG', '0')))
VALKEY_DBS_JSON = os.getenv('VALKEY_DBS_JSON', '[]')
BACKEND_DB_NAME = os.getenv('BACKEND_DB_NAME', '')
QTY_SKU_RECORDS = int(os.getenv('QTY_SKU_RECORDS', '3'))


logger = logging.getLogger('reset_db_job')
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


def annual_inflation()->dict:
    inflation = dict()
    for year in range(2000, 2025):
        key = '{}'.format(year)
        inflation[key] = random.randint(5, 10)
    return inflation


def get_db_servers()->list:
    dbs = json.loads(VALKEY_DBS_JSON)
    for db_record in dbs:
        if 'host' in db_record and 'port' in db_record:
            logger.info('CONFIG: DB Server "{}" with port "{}"'.format(db_record['host'], db_record['port']))
        else:
            raise Exception('Invalid Data')
    return dbs


def get_backend_master()->dict:
    for db_record in get_db_servers():
        if db_record['host'] == BACKEND_DB_NAME:
            return copy.deepcopy(db_record)
        

def create_sku_names()->list:
    names = list()
    while len(names) < QTY_SKU_RECORDS:
        names.append(
            'SKU_{}'.format(
                str(random.randint(1,999999)).zfill(6)
            )
        )
    logger.info('Generated Names: {}'.format(names))
    return names


for db_record in get_db_servers():
    try:
        client = valkey.Valkey(host=db_record['host'], port=int(db_record['port']), db=0)
        client.flushall(asynchronous=True)
        logger.info('Database Flushed')
    except:
        logger.error('EXCEPTION: {}'.format(traceback.format_exc()))


backend_record = get_backend_master()
if 'host' in backend_record and 'port' in backend_record:
    client = valkey.Valkey(host=backend_record['host'], port=int(backend_record['port']), db=0)
    client.set('sku_names', json.dumps(create_sku_names(), default=str))
    client.set('inflation', json.dumps(annual_inflation(), default=str))
else:
    raise Exception('Failed to create SKU names')

