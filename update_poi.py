import os, sys
import library_database as lb
import pdb
import json 

poi_folder = os.path.expanduser('~') + '/dequa/code/static/files/poi'
pdb.set_trace()

lb.create_query_objects()
files = os.listdir(poi_folder)
poi_files = [file for file in files if file.endswith('.json')]

for poi_file in poi_files:
    full_path_poi_file = os.path.join(poi_folder, poi_file)
    with open(full_path_poi_file, 'r') as opj:
        pois = json.load(opj)
    poi_list = pois['elements']
    print("-" * 50)
    print(f"updating from {poi_file}")
    lb.update_POI(poi_list, explain=True)
