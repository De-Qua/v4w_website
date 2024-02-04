import os, sys
import library_database as lb
import pdb
import json 
from pathlib import Path

current_folder = Path(__file__).parent
static_folder = current_folder.parent / "static"
poi_folder = static_folder / "files" / "poi"


lb.create_query_objects()
files = poi_folder.iterdir()
# os.listdir(poi_folder)
poi_files = [file for file in files if file.name.endswith('.json')]

pdb.set_trace()

for poi_file in poi_files:
    full_path_poi_file = os.path.join(poi_folder, poi_file)
    with open(full_path_poi_file, 'r') as opj:
        pois = json.load(opj)
    poi_list = pois['elements']
    print("-" * 50)
    print(f"updating from {poi_file}")
    lb.update_POI(poi_list, explain=True)
