import os
import warnings
import json
from shapely.geometry import shape, Polygon, MultiPolygon

from dotenv import load_dotenv

for env_file in ('.env', '.flaskenv'):
    env = os.path.join(os.getcwd(), env_file)
    if os.path.exists(env):
        load_dotenv(env)

from app import db
from app.models import Area

def add_area(name, geojson):
    geom = shape(geojson["features"][0]["geometry"])
    if type(geom) not in [Polygon, MultiPolygon]:
        warnings.warn("La shape deve essere un Polygon o MultiPolygon")
        err = 1
        return
    if type(geom) is Polygon:
        geom = MultiPolygon([geom])
    area = Area(name=name, shape=geom.to_wkt())
    db.session.add(area)
    err = None
    try:
        db.session.commit()
        print(f"Area {name} aggiunta correttamente")
    except:
        db.session.rollback()
        warnings.warn("Errore nel commit")
        err = 1

if __name__ == '__main__':
    print("DEQUA - Add an area!")
    print("Crea un geojson dell'area con https://geojson.io/")
    name = input("Il nome dell'area che vuoi aggiungere? ")
    print("Incolla il geojson e premi Ctrl-D.\n")
    geojson = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        geojson.append(line)
    geojson = '\n'.join(geojson)
    geojson = json.loads(geojson)
    add_area(name, geojson)