import requests
import os
import json
import sys
import time
import logging
from datetime import datetime
logging.basicConfig(
    filename="/home/rafiki/task.log",
    level=logging.DEBUG
)
now = datetime.now()
cur_time = now.strftime("%b %d %Y %H:%M:%S")
logging.info(f"\nUpdate the high tide at: {cur_time}\n")
url_livello = 'https://dati.venezia.it/sites/default/files/dataset/opendata/livello.json'

script_directory = os.path.dirname(os.path.abspath(__file__))
tmp_output_file = os.path.join(script_directory,'high_tide_level_2.json')
output_file = os.path.join(script_directory,'high_tide_level.json')

# get json from comune
resp = requests.get(url=url_livello)
data = resp.json()

data_PSalute = [staz_data for staz_data in data if (staz_data['ID_stazione'] == '01045' or staz_data['ID_stazione'] == '01025')]
print("\nFound {} Maritime Station with High Tide Data:\n {}".format(len(data_PSalute), data_PSalute))
sys.stdout.flush()
logging.info("\nFound {} Maritime Station with High Tide Data:\n {}".format(len(data_PSalute), data_PSalute))

# check if the first object of the array is from Punta della Salute
if data_PSalute:
    data_to_take = data_PSalute[0]
    print(f"High tide data acquired at {data_to_take['data']}")
    logging.info(f"High tide data acquired at {data_to_take['data']}")
    # copiamo su un file temporaneo
    with open(tmp_output_file,'w') as stream:
        json.dump(data_to_take, stream)

    # mettiamo su un file temporaneo e poi rinominiamo
    os.replace(tmp_output_file, output_file)
    logging.info("New data saved")
    print('New data saved')
    sys.stdout.flush()
else:
    print("No PSalute found in json file :(\nLet's skip it for this round")
    sys.stdout.flush()
    logging.info("nothing found")
logging.info("*****\n")
