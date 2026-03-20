import warnings
import json
from pathlib import Path

from dotenv import load_dotenv

for env_file in ('.env', '.flaskenv'):
    env = Path() / env_file
    if env.exists():
        load_dotenv(env)

from app import db
from app.models import Poi

from library_database import progressbar_pip_style

num_pois = Poi.query.count()

for idx, p in enumerate(Poi.query.all()):
    progressbar_pip_style(idx, num_pois)
    
    osm_tags = {}
    # Aggiungiamo i campi che poi vorremo togliere come colonne singole, ovvero tutte le colonne su cui non avrà mai senso cercare
    if p.phone:
        osm_tags['phone'] = p.phone
    if p.wikipedia:
        osm_tags['wikipedia'] = p.wikipedia


    # Copiamo i dati che sono salvati in osm_other_tags
    old_osm_tags_string = p.osm_other_tags
    if not old_osm_tags_string:
        continue
    old_osm_tags = old_osm_tags_string.split('\n')
    
    for oot in old_osm_tags:
        osm_key_val = oot.split("=")
        # Teniamo solo quelli che hanno almeno un =
        if len(osm_key_val) > 1:
            osm_key = osm_key_val[0]
            osm_val = ''.join(osm_key_val[1:])
            osm_tags[osm_key] = osm_val
    p.osm_tags = osm_tags

db.session.commit()
