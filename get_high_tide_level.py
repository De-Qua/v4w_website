import requests
import os
import json
import sys

import logging
logging.basicConfig(
    filename="/home/rafiki/task.log",
    level=logging.DEBUG
)
logging.info("vtasklog")

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
logging.info("found station")

# check if the first object of the array is from Punta della Salute
if data_PSalute:
    data_to_take = data_PSalute[0]

    # copiamo su un file temporaneo
    with open(tmp_output_file,'w') as stream:
        json.dump(data_to_take, stream)

    # mettiamo su un file temporaneo e poi rinominiamo
    os.replace(tmp_output_file, output_file)
    logging.info("new data acquired")
    print('New data acquired')
    sys.stdout.flush()
else:
    print("No PSalute found in json file :(\nLet's skip it for this round")
    sys.stdout.flush()
    logging.info("nothing found")
