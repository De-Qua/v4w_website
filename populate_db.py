#%% Imports
import os,sys

from app import app, db

import pandas as pd
from importlib import reload

from app.models import Neighborhood, Street, Location, Area
import numpy as np
import re
import geopandas as gpd

from descartes import PolygonPatch
import matplotlib.pyplot as plt
#%% Files
# TODO leggere civico.shp invece che txt
folder = os.getcwd()
folder_file = os.path.join(folder,"app","static","files")

file_civici = "lista_civici_only.txt"
file_civici_denominazioni = "lista_denominazioni_csv.txt"
file_civici_coords = "lista_coords_civici_only.txt"

#%% Load files
# Import with pandas
# civici_address = pd.read_csv(os.path.join(folder_file,file_civici),header=None,names=["civico","empty"])
# civici_address = civici_address.drop("empty",axis=1)
# civici_denominazioni = pd.read_csv(os.path.join(folder_file,file_civici_denominazioni),header=None,names=["denominazione","empty"])
# civici_denominazioni = civici_denominazioni.drop("empty",axis=1)
# civici_coords = pd.read_csv(os.path.join(folder_file,file_civici_coords),header=None,names=["longitude","latitude"])
# civici = pd.concat([civici_address,civici_denominazioni,civici_coords],axis=1)

# Import with numpy
civici_address = np.loadtxt(os.path.join(folder_file,file_civici), delimiter = ";" , comments=",",dtype='str')
civici_denominazioni = np.loadtxt(os.path.join(folder_file,file_civici_denominazioni), delimiter = ";" , comments=",",dtype='str')
civici_coords = np.loadtxt(os.path.join(folder_file,file_civici_coords), delimiter = "," , dtype='float')
#%%
####### estrarre i poligoni dai sestieri per caricarli nel database
sestieri =  gpd.read_file(os.path.join(folder_file,"Localita","Località.shp"))
sestieri = sestieri.to_crs(epsg=4326)
#nomi_sestieri=sestieri['A_SCOM_NOM'].to_list()
# nomi_sestieri[24]
# if sestieri[sestieri["A_SCOM_NOM"]=="SANT'ELENA".title()]["geometry"].empty:
#     print('ok')
#%%
# elimina tutto
Neighborhood.query.delete()
Street.query.delete()
Location.query.delete()
db.session.commit()
#%% Aggiungi sestieri
list_sest_cap = [
   ("CANNAREGIO",30121),
   ("CASTELLO",30122),
   ("DORSODURO",30123),
   ("SAN MARCO",30124),
   ("SAN POLO",30125),
   ("SANTA CROCE",30135),
   ("GIUDECCA",30133),
   ("SACCA SAN BIAGIO",30133),
   ("ISOLA SAN GIORGIO",30124),
   ("TRONCHETTO",30135),
   ("MALAMOCCO",30126),
   ("ALBERONI",30126),
   ("LIDO",30126),
   ("SACCA FISOLA",30133),
   ("SANT'ELENA",30122),
   ("BURANO",30012),
   ("MURANO",30141)
   ]
err_neighb = []
for s,c in list_sest_cap:
    # aggiungi se non è già presente
    neig = Neighborhood.query.filter_by(name=s,zipcode=c).first()
    geom = sestieri[sestieri["A_SCOM_NOM"]==s.title()]["geometry"]
    if geom.empty:
        err_neighb.append((s,c))
    else:
        geom = geom.iloc[0]
        if not neig:
            n = Neighborhood(name=s,zipcode=c, shape=geom)
            db.session.add(n)
        elif neig.shape.empty:
            neig.shape=geom

db.session.commit()
print("Error: {err}\nSestieri: {ses}\nStrade: {str}\nCivici: {civ}\nFile: {file}".format(
    err=len(err_neighb),
    ses=len(Neighborhood.query.all()),
    str=len(Street.query.all()),
    civ=len(Location.query.all()),
    file=len(civici_address)
    ))

#%% Aggiungi civici e strade
wrong_entries = []
err = [0,0,0]
for add,den,coord in zip(civici_address, civici_denominazioni, civici_coords):
    long,lat = coord
    num_found_add = re.search("\d+(/[A-Z])?",add)
    num_found_den = re.search("\d+(/[A-Z])?",den)
    if not num_found_add or not num_found_den:
        # il civico non ha il numero: passa al successivo
        wrong_entries.append((1,add,den,coord))
        err[0] += 1
        continue
    if num_found_add.group(0) != num_found_den.group(0):
        # civico e denominazione hanno numeri diversi: passa al successivo
        wrong_entries.append((2,add,den,coord))
        err[1] += 1
        continue
    num = num_found_add.group(0)
    sest = add[:-len(num)-1]
    str = den[:-len(num)-1]
    n = Neighborhood.query.filter_by(name=sest).first()
    if not n:
        # il sestiere non esite: passa al successivo
        wrong_entries.append((3,add,den,coord))
        err[2] += 1
        continue
    if not Street.query.filter_by(name=str,neighborhood=n).first():
        # la strada in quel sestiere non esiste: la aggiungo al db
        db.session.add(Street(name=str,neighborhood=n))
    s = Street.query.filter_by(name=str,neighborhood=n).first()
    if not Location.query.filter_by(latitude=lat,longitude=long,street=s,housenumber=num).first():
        # il civico in quella strada non esiste: lo aggiungo al db
        db.session.add(Location(latitude=lat,longitude=long,street=s,housenumber=num))

db.session.commit()
print("Sestieri: {ses}\nStrade: {str}\nCivici: {civ}\nFile: {file}".format(
    ses=len(Neighborhood.query.all()),
    str=len(Street.query.all()),
    civ=len(Location.query.all()),
    file=len(civici_address)
    ))
print("Indirizzi non inseriti: {wr}\nNumero mancante: {noNum}\nNumero diverso: {divNum}\nSestiere non esiste: {noSes}".format(wr=len(wrong_entries),noNum=err[0],divNum=err[1],noSes=err[2]), *wrong_entries, sep="\n")
#%%
####### estrarre i poligoni delle strade per caricarli nel database
TP_streets =  gpd.read_file(os.path.join(folder_file,"TP_STR.shp"))
TP_streets = TP_streets.to_crs(epsg=4326)
TP_nome = np.asarray(TP_streets["TP_STR_NOM"])
TP_geom = TP_streets["geometry"]
TP_geom[1].centroid

err_shp = []
for n,poli in zip(TP_nome, TP_geom):
    matches=Street.query.filter_by(name=n).all()
    for m in matches:
        if m.neighborhood.shape.contains(poli.centroid):
            m.shape=poli
        else:
            err_shp.append((m,poli))
db.session.commit()

print("Strade con shape: {con}\nStrade senza shape: {sen}".format(
    con = len(Street.query.filter(Street.shape.isnot(None)).all()),
    sen = len(Street.query.filter_by(shape=None).all())
    ), *Street.query.filter_by(shape=None).all(), sep="\n")
#%%
import shapely
sm = Neighborhood.query.filter_by(name="SAN POLO").first()
shapes = Street.query.filter_by(neighborhood=sm).filter(Street.shape.isnot(None)).all()
n1 = err_shp[0][0]
n1_geom = err_shp[0][1]
y1 = shapes[0]
err_shp[0]

# Plot del sestiere
fig, axs = plt.subplots()
xsm, ysm = sm.shape.exterior.xy
axs.fill(xsm,ysm, alpha=0.5, fc='b', ec='none')
# Plot della strada trovata
if type(y1.shape)==shapely.geometry.polygon.Polygon:
    x_y, y_y = y1.shape.exterior.xy
    axs.fill(x_y, y_y, alpha=1, fc='r', ec='none')
elif type(y1.shape)==shapely.geometry.polygon.MultiPolygon:
    for geom in y1.shape.geoms:
        xg, yg = geom.exterior.xy
        axs.fill(xg, yg, alpha=1, fc='r', ec='none')
# Plot della strada non trovata
if type(n1_geom)==shapely.geometry.polygon.Polygon:
    x_n, y_n = n1_geom.exterior.xy
    axs.fill(x_n, y_n, alpha=1, fc='g', ec='none')
elif type(n1_geom)==shapely.geometry.polygon.MultiPolygon:
    for geom in n1_geom.geoms:
        xg, yg = geom.exterior.xy
        axs.fill(xg, yg, alpha=1, fc='g', ec='none')
x_n
plt.show()



#%% Un po' di print e info
print("Sestieri: {ses}\nStrade: {str}\nCivici: {civ}\nFile: {file}".format(
    ses=len(Neighborhood.query.all()),
    str=len(Street.query.all()),
    civ=len(Location.query.all()),
    file=len(civici_address)
    ))
# Gli elementi del db vengono printati secondo quanto definito nella classe al metodo __def__
print("Il primo quartiere, strada e location del database:\n{ses}\n{str}\n{loc}".format(
    ses=Neighborhood.query.get(1),
    str=Street.query.get(1),
    loc=Location.query.get(1)
    ))
# Si può facilmente accedere agli elementi di un singolo elemento
l = Location.query.get(1)
print("Informazioni sulla prima location:\nStrada: {str}\nCivico: {civ}\nSestiere: {ses}\nCAP: {cap}\nCoordinate: {lat},{lon}".format(
    str=l.street.name,
    civ=l.housenumber,
    ses=l.street.neighborhood.name,
    cap=l.street.neighborhood.zipcode,
    lat=l.latitude,
    lon=l.longitude
    ))
# I risultati si possono filtrare in due modi
# 1. filter_by: filtra semplicemente gli attributi di una riga (solo gli attributi diretti non quelli derivati)
# 2. filter: permette filtri più complicati (ma non ho capito bene come si usa)
print("Tutte le location che hanno il civico 1:",
    *Location.query.filter_by(housenumber=1).all(), sep='\n'
    )
# Le tabelle si possono unire per filtrare i risultati utilizzando gli attributi derivati
print("Tutte le strade di San Polo:",
    *Street.query.join(Neighborhood).filter_by(name="SAN POLO").all(), sep='\n'
    )
print("Il numero 1 di San Polo:",
    *Location.query.filter_by(housenumber=1).join(Street).join(Neighborhood).filter_by(name="SAN POLO").all(), sep='\n'
    )
l = Location.query.filter_by(housenumber=1).join(Street).join(Neighborhood).filter_by(name="SAN POLO").first()
print("Tutte i civici vicini al numero 1 di San Polo:",
    *Location.query.filter(db.and_(
                            db.between(Location.longitude,l.longitude-0.0003,l.longitude+0.0003),
                            db.between(Location.latitude,l.latitude-0.0003,l.latitude+0.0003)
                            )).order_by(Location.housenumber).all(), sep="\n"
    )

print("Tutte le strade che contengono il nome Rialto:",
    *Street.query.filter(Street.name.contains("RIALTO")).all(), sep="\n")
print("Tutte le strade che contengono il nome Forno:",
    *Street.query.filter(Street.name.contains("CALLE DEL FORNO")).all(), sep="\n")
r = Street.query.filter(Street.name.contains("RIALTO")).all()
a = r[2].locations.all()
wrong = r[4].locations.first()
[wrong.latitude, wrong.longitude]

#%%### Poi
poi_path = os.path.join(folder,"app","static","files","lista_poi.txt")
path_poi_types = os.path.join(folder,"app","static","files","poi_types.csv")
poi_types = np.loadtxt(path_poi_types,delimiter = ",",dtype='str',skiprows=1)
pois = np.loadtxt(poi_path,delimiter = "|",dtype='str',skiprows=1)

"""
TAGS
name
amenity
shop
wheelchair
cuisine
toilets::wheelchair
tourism
alt_name
building
opening_hours
wikipedia
atm
outdoor_seating
diet::vegetarian
phone
denomination
sport
"""
#%% Get poi_types
import geopy.distance
file_poi_types = os.path.join(folder,"app","static","files","poi_types.csv")
poi_types = np.loadtxt(file_poi_types,delimiter = ",",dtype='str',skiprows=1)
zucca = [45.4408383, 12.3285187]
closest = []
distance = 100000

for loc in Location.query.filter(db.and_(db.between(Location.longitude,zucca[1]-0.0003,zucca[1]+0.0003),
        db.between(Location.latitude,zucca[0]-0.0003,zucca[0]+0.0003)
        )).all():
    dist = geopy.distance.distance((loc.latitude, loc.longitude),(zucca[0],zucca[1])).meters
    if dist < distance:
        distance = dist
        closest = loc
print("{} , {}".format(distance,closest))
loc_zucca = Location.query.filter_by(housenumber=1762).join(Street).join(Neighborhood).filter_by(name="SANTA CROCE").first()
print("{}".format(geopy.distance.distance((closest.latitude, closest.longitude),(loc_zucca.latitude,loc_zucca.longitude)).meters))
