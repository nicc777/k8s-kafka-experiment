"""
Resources:

    ANSI Colors in Output: https://stackoverflow.com/questions/4842424/list-of-ansi-color-escape-sequences
    Tabulate: https://github.com/astanin/python-tabulate
    Requests JSON responses: https://docs.python-requests.org/en/latest/user/quickstart/#json-response-content

"""
import os
import time
import copy
import requests
import json
from tabulate import tabulate


# THe below base URL should be sufficient if the standard instructions are
# followed. Override with an environment variable as required.
END_POINT_BASE_URL = os.getenv('END_POINT_BASE_URL', 'http://demo.example.tld')

# Default year is 2020. To choose any other year between 2000 and 2024, set the
# YEAR environment variable.
YEAR = os.getenv('YEAR', '2020')


def get_sku_names()->list:
    sku_names = list()
    try:
        url = '{}/sku_names'.format(END_POINT_BASE_URL)
        r = requests.get(url)
        data = r.json()
        if 'names' in data:
            for name in data['names']:
                sku_names.append(name)
    except:
        pass
    return sku_names


def get_data_from_query(sku_name: str, year: str)->dict:
    data = dict()
    data['version'] = 'unknown'
    data['total'] = 0
    data['defects'] = 0
    data['cost'] = 0
    try:
        url = '{}/query/{}/{}'.format(END_POINT_BASE_URL, sku_name, year)
        r = requests.get(url)
        returned_data = r.json()
        if 'version' in returned_data:
            data['version'] = returned_data['version']
        total_manufactured = 0
        total_defects = 0
        if 'data' in returned_data:
            for record in returned_data['data']:
                if 'manufactured_qty' in record:
                    total_manufactured += record['manufactured_qty']
                if 'defect_qty' in record:
                    total_defects += record['defect_qty']
            # TODO add logic for v2 and v3 once we know that will look like
        if total_manufactured > 0:
            data['total'] = int(total_manufactured)
        if total_defects > 0:
            data['defects'] = int(total_defects)
    except:
        pass
    return data


def add_row(
    sku_data: dict,
    sku_name: str,
    previous_manufactured_total: int,
    previous_defects_totals: int,
    previous_version: str
)->list:
    ansi_red = '\033[31;1;1m'
    ansi_reset = '\033[0m'
    ansi_yellow = '\033[33;1;1m'
    if 'version' in sku_data:

        final_total = '{}{}{}'.format(ansi_yellow,sku_data['total'],ansi_reset)
        if int(previous_manufactured_total) != int(sku_data['total']):
            final_total = '{}{}{}'.format(ansi_red,sku_data['total'],ansi_reset)

        final_defects = '{}{}{}'.format(ansi_yellow,sku_data['defects'],ansi_reset)
        if int(previous_defects_totals) != int(sku_data['defects']):
            final_defects = '{}{}{}'.format(ansi_red,sku_data['defects'],ansi_reset)
        
        final_version = '{}{}{}'.format(ansi_yellow,sku_data['version'],ansi_reset)
        if previous_version != sku_data['version']:
            final_version = '{}{}{}'.format(ansi_red,sku_data['version'],ansi_reset)

        return (
            [
                '{}'.format(sku_name),          # SKU
                '{}'.format(final_version),     # Version
                '{}'.format(final_total),       # Total Manufactured
                '{}'.format(final_defects),     # Total Defects
                'n/a',                          # Total Costs
            ],
            sku_data['version'],
            int(sku_data['total']),
            int(sku_data['defects']),
        )
    
    return (
        [
            'n/a',
            'n/a',
            'n/a',
            'n/a',
            'n/a',
        ],
        previous_version,
        int(previous_manufactured_total)
    )


previous_manufactured_totals = dict()
previous_defects_totals = dict()
previous_versions = dict()
counter = 0
while True:
    counter += 1
    sku_names = get_sku_names()
    table = list()
    if len(sku_names) > 0:
        for sku_name in sku_names:
            sku_data = get_data_from_query(sku_name=sku_name, year=YEAR)
            if '1' in sku_data['version']:
                row, updated_version, updated_manufactured_total, updated_defects_total = add_row(
                    sku_data=sku_data,
                    sku_name=sku_name,
                    previous_manufactured_total=previous_manufactured_totals[sku_name] if sku_name in previous_manufactured_totals else 0,
                    previous_defects_totals=previous_defects_totals[sku_name] if sku_name in previous_defects_totals else 0,
                    previous_version=previous_versions[sku_name] if 'sku_name' in previous_versions else 'v1'
                )
                table.append(row)
                previous_manufactured_totals[sku_name] = int(updated_manufactured_total)
                previous_defects_totals[sku_name] = int(updated_defects_total)
                previous_versions[sku_name] = updated_version
            else:
                table.append(
                    '{}'.format(sku_name),  # SKU
                    'unknown',              # Version
                    'n/a',                  # Total Manufactured
                    'n/a',                  # Total Defects
                    'n/a',                  # Total Costs
                )

        os.system('cls' if os.name == 'nt' else 'clear')
        print(
            tabulate(
                table, 
                headers=["SKU","API Version","Total Manufactured","Total Defects","Total Costs",],
                # maxcolwidths=[12, 20, 6, 20, 20,]
            )
        )
        
    else:
        os.system('cls' if os.name == 'nt' else 'clear')
        print('No data yet or error connecting...')
    print()
    print('Total requests: {}'.format(counter))

    time.sleep(3)

