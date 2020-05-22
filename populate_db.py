#%% Imports
import os,sys

from app import app, db

import pandas as pd
from importlib import reload

from app.models import Neighborhood, Street, Location, Area
import numpy as np
import re
import geopandas as gpd

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
nomi_sestieri=sestieri['A_SCOM_NOM'].to_list()

#%%
match_dorsoduro = [i for i,x in enumerate(nomi_sestieri) if 'Dorsoduro'in x]
match_sanpolo = [i for i,x in enumerate(nomi_sestieri) if 'San Polo'in x]
match_san_marco = [i for i,x in enumerate(nomi_sestieri) if 'San Marco'in x]
match_cannaregio = [i for i,x in enumerate(nomi_sestieri) if 'Cannaregio'in x]
match_santacroce  = [i for i,x in enumerate(nomi_sestieri) if 'Santa Croce'in x]
match_castello = [i for i,x in enumerate(nomi_sestieri) if 'Castello'in x]
match_giudecca = [i for i,x in enumerate(nomi_sestieri) if 'Giudecca'in x]
match_murano = [i for i,x in enumerate(nomi_sestieri) if 'Murano'in x]
match_burano = [i for i,x in enumerate(nomi_sestieri) if 'Burano'in x]
match_santelena = [i for i,x in enumerate(nomi_sestieri) if "Sant'Elena"in x]
match_sacca = [i for i,x in enumerate(nomi_sestieri) if "Sacca Fisola"in x]
match_lido = [i for i,x in enumerate(nomi_sestieri) if "Lido"in x]
match_alberoni = [i for i,x in enumerate(nomi_sestieri) if "Alberoni"in x]
match_malamocco = [i for i,x in enumerate(nomi_sestieri) if "Malamocco"in x]
match_tronchetto= [i for i,x in enumerate(nomi_sestieri) if "Tronchetto"in x]
match_sangiorgio= [i for i,x in enumerate(nomi_sestieri) if "San Giorgio"in x]
match_saccabiagio= [i for i,x in enumerate(nomi_sestieri) if "Sacca San Biagio"in x]
#%% Aggiungi sestieri
list_sest_cap = [
   ("CANNAREGIO",30121,match_cannaregio),
   ("CASTELLO",30122,match_castello),
   ("DORSODURO",30123,match_dorsoduro),
   ("SAN MARCO",30124,match_san_marco),
   ("SAN POLO",30125,match_sanpolo),
   ("SANTA CROCE",30135,match_santacroce),
   ("GIUDECCA",30133,match_giudecca),
   ("SACCA SAN BIAGIO",30133,match_saccabiagio),
   ("SAN GIORGIO",30124,match_sangiorgio),
   ("TRONCHETTO",30135,match_tronchetto),
   ("MALAMOCCO",30126,match_malamocco),
   ("ALBERONI",30126,match_alberoni),
   ("LIDO",30126,match_lido),
   ("SACCA FISOLA",30133,match_sacca),
   ("SANT'ELENA",30122,match_santelena),
   ("BURANO",30012,match_burano),
   ("MURANO",30141,match_murano)
   ]
for s,c,idx in list_sest_cap:
    # aggiungi se non è già presente
    neig = Neighborhood.query.filter_by(name=s,zipcode=c).first()
    if not neig:
        n = Neighborhood(name=s,zipcode=c, shape=sestieri["geometry"][idx])
        db.session.add(n)
        db.session.commit()
    elif neig.shape.empty:
        neig.shape=sestieri["geometry"][idx]
        db.session.commit()

print("Sestieri: {ses}\nStrade: {str}\nCivici: {civ}\nFile: {file}".format(
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

for n,poli in zip(nome, TP_geom):
    matches=Street.query.filter_by(name=n).all()
    for m in matches:
        if m.neighborhood.shape.contains(poli.centroid).values[0]:
            m.shape=poli

db.session.commit()

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
