import os
import time
import requests
from tabulate import tabulate


# THe below base URL should be sufficient if the standard instructions are
# followed. Override with an environment variable as required.
END_POINT_BASE_URL = os.getenv('END_POINT_BASE_URL', 'http://127.0.0.1:7098')


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
    try:
        url = '{}/query/{}/{}'.format(END_POINT_BASE_URL, sku_name, year)
        r = requests.get(url)
        returned_data = r.json()
        if 'version' in returned_data:
            data['version'] = returned_data['version']
        total_manufactured = 0
        if 'data' in returned_data:
            for record in returned_data['data']:
                if 'manufactured_qty' in record:
                    total_manufactured += record['manufactured_qty']
        if total_manufactured > 0:
            data['total'] = total_manufactured
    except:
        pass
    return data


previous_manufactured_totals = dict()
previous_versions = dict()
ansi_red = '\033[31;1;1m'
ansi_reset = '\033[0m'
ansi_white = '\033[33;1;1m'
counter = 0
while True:
    counter += 1
    sku_names = get_sku_names()
    table = list()
    if len(sku_names) > 0:
        for sku_name in sku_names:
            sku_data = get_data_from_query(sku_name=sku_name, year=2020)

            final_version = '{}{}{}'.format(
                ansi_white,
                sku_data['version'],
                ansi_reset
            )
            final_total = '{}{}{}'.format(
                ansi_white,
                sku_data['total'],
                ansi_reset
            )

            if sku_name in previous_manufactured_totals:
                if previous_manufactured_totals[sku_name] != sku_data['total']:
                    final_total = '{}{}{}'.format(
                        ansi_red,
                        sku_data['total'],
                        ansi_reset
                    )

            if sku_name in previous_versions:
                if previous_versions[sku_name] != sku_data['version']:
                    final_version = '{}{}{}'.format(
                        ansi_red,
                        sku_data['version'],
                        ansi_reset
                    )

            previous_manufactured_totals[sku_name] = sku_data['total']
            previous_versions[sku_name] = sku_data['version']
            table.append(
                [
                    sku_name,
                    final_version,
                    final_total,
                ]
            )

        os.system('cls' if os.name == 'nt' else 'clear')
        print(tabulate(table, headers=["SKU","API", "2020",]))
        
    else:
        print('No data yet or error connecting...')
    print()
    print('Total requests: {}'.format(counter))

    time.sleep(3)

