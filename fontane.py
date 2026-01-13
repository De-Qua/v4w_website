from app.geotag.models import *

from pathlib import Path

import pandas as pd

import geopandas as gpd

csv_path = Path('..')/'..'/'fontane'

csv_file = '/home/ale/DeQua/fontane/VENICE DRINKING WATER FOUNTAINS- SESTIERE DI SAN MARCO.csv'

df = pd.read_csv(csv_file)

from shapely import wkt

df['WKT'] = df['WKT'].apply(wkt.loads)
gdf = gpd.GeoDataFrame(df, geometry="WKT", crs='epsg:4326')

owner = Geouser.query.filter_by(nickname="VTW").first()
datagroup = Datagroup.query.filter_by(keyname="fontane").first()
layer = Layer.query.filter_by(url="fontane").first()
italiano = Language.query.filter_by(code="IT").first()
stringtype = Datatype.query.filter_by(name="String").first()

descrizione = LayerItemDatagroupParameter.query.filter_by(keyname="description").first()
aperta = LayerItemDatagroupParameter.query.filter_by(keyname="aperta").first()


for idx, row in gdf.iterrows():
    lon,lat = row.WKT.coords[0]
    nome = row.nome
    desc = row.descrizione
    
    fontana = LayerItem(lat=lat, lng=lon, owner=owner, layer=layer, datagroup=datagroup)
    fontana_transl = LayerItemTranslation(name=nome, language=italiano, layer_item=fontana)
    
    if desc.lower() == "aperta":
        # Create new LayerItemDatagroupParameterValue
        fontana_val = LayerItemDatagroupParameterValue(layer_item=fontana, parameter=aperta)
        fontana_val_transl = LayerItemDatagroupParameterValueTranslation(value=True,parametervalue=fontana_val, language=italiano)
    elif desc.lower() == "chiusa" or desc.lower() == "chiuso":
        # Create new LayerItemDatagroupParameterValue
        fontana_val = LayerItemDatagroupParameterValue(layer_item=fontana, parameter=aperta)
        fontana_val_transl = LayerItemDatagroupParameterValueTranslation(value=False,parametervalue=fontana_val, language=italiano)
    else:
        fontana_val = LayerItemDatagroupParameterValue(layer_item=fontana, parameter=descrizione)
        fontana_val_transl = LayerItemDatagroupParameterValueTranslation(value=desc,parametervalue=fontana_val, language=italiano)
    
    db.session.add(fontana)
    db.session.add(fontana_transl)
    db.session.add(fontana_val)
    db.session.add(fontana_val_transl)
    db.session.commit()
    