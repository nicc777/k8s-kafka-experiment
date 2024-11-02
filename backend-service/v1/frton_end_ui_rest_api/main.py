"""
Each time the front-end web page does a REST call to this service, it will
retrieve the latest summary from the DB and send it as JSON to the requesting
client.

INPUT       : REST request from a web client
PROCESSING  : Pull summary data from DB         (1)
OUTPUT      : JSON response back to the requesting client
                                           
+-------------------------------+        +-----+        +-------------------------------+      
| front_end_aggregator_consumer |        |     |        | Back_end_aggregator_producer  |
+-------------------------------+        |  K  |        +-------------------------------+            
                                         |  A  |                                                     
                                         |  F  |                                                     
                                         |  K  |                                                    
            +-----+                      |  A  |         +-------------------------------+
            | DB  |                      |     |         | back_end                      |
            +-----+                      |     |        +-------------------------------+
                ^                        |     |
                |  (1)                   |     |  
                |                        |     |        
#################################        |     |        +-------------------------------+
# front_end_ui_rest_api         #        |     |        | raw_data_generator            |
#################################        +-----+        +-------------------------------+
"""
import os
import socket
import logging
import sys
import traceback
import valkey
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn


# EXAMPLE taken from https://github.com/confluentinc/confluent-kafka-python/blob/master/examples/avro_consumer.py

HOSTNAME = socket.gethostname()
DEBUG = bool(int(os.getenv('DEBUG', '0')))
VALKEY_SERVER_HOST = os.getenv('VALKEY_SERVER_HOST', 'valkey-primary')
VALKEY_SERVER_PORT = int(os.getenv('VALKEY_SERVER_PORT', '6379'))


logger = logging.getLogger(HOSTNAME)
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
logger.debug('{} - VALKEY_SERVER_HOST           : {}'.format(HOSTNAME, VALKEY_SERVER_HOST))
logger.debug('{} - VALKEY_SERVER_PORT           : {}'.format(HOSTNAME, VALKEY_SERVER_PORT))


app = FastAPI()


class ResultData(BaseModel):
    sku: str
    year: int
    month: int
    manufactured_qty: int


class Results(BaseModel):
    version: str = 'v1'
    data: list[ResultData]


def read_keys(client, year: int)->list:
    """
               0        1    2    3
    KEY: 'manufactured:sku:year:month'
    """
    try:
        keys = list()
        index = 'manufactured:*:{}:*'.format(year)
        for key in client.scan_iter(index):
            keys.append(key)
        logger.info('{}- Retrieved {} keys from DB'.format(HOSTNAME, len(keys)))
    except:
        logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))
    return keys


def get_summary_data(client)->Results:
    """
               0        1    2    3
    KEY: 'manufactured:sku:year:month'
    """
    results = Results(data=list())
    try:
        for year in range(2000,2025):
            logger.info('{} - Getting data for year {}'.format(HOSTNAME, year))
            key: bytes
            for key in read_keys(client=client, year=year):
                qty = int(client.get(key))
                decoded_key = key.decode('utf-8')
                logger.debug('{} - decoded_key={}'.format(HOSTNAME, decoded_key))
                key_elements = decoded_key.split(':')
                record = ResultData(
                    sku=key_elements[1],
                    year=int(key_elements[2]),
                    month=int(key_elements[3]),
                    manufactured_qty=qty
                )
                results.data.append(record)
    except:
        logger.error('{} - EXCEPTION: {}'.format(HOSTNAME, traceback.format_exc()))


@app.get("/results")
async def results()->Results:
    return get_summary_data(client=valkey.Valkey(host=VALKEY_SERVER_HOST, port=VALKEY_SERVER_PORT, db=0))


@app.get("/")
async def root():
    return {"message": "ok"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)