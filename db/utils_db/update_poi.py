from pathlib import Path
import json 
from dotenv import load_dotenv

for env_file in ('.env', '.flaskenv'):
    env = Path.cwd() / env_file
    if env.exists():
        load_dotenv(env)

import library_database as lb

current_folder = Path(__file__).parent
static_folder = current_folder.parent / "static"
poi_folder = static_folder / "files" / "poi"


lb.create_query_objects()
files = poi_folder.iterdir()
# os.listdir(poi_folder)
poi_files = [file for file in files if file.name.endswith('.json')]

# pdb.set_trace()

for poi_file in poi_files:
    if poi_file != "water.json":
        full_path_poi_file = poi_folder / poi_file
        with open(full_path_poi_file, 'r') as opj:
            pois = json.load(opj)
        poi_list = pois['elements']
        print("-" * 50)
        print(f"updating from {poi_file}")
        num_new_poi, num_updated_poi, num_errors = lb.update_POI(poi_list, explain=True, err_file=poi_file)
        # breakpoint()