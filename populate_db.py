#%% Imports
from app import app, db
import os
import pandas as pd
from importlib import reload
from app.models import Neighborhood, Street, Location

import numpy as np
import re
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

#%% Aggiungi sestieri
list_sest_cap = [
   ("CANNAREGIO",30121),
   ("CASTELLO",30122),
   ("DORSODURO",30123),
   ("SAN MARCO",30124),
   ("SAN POLO",30125),
   ("SANTA CROCE",30135),
   ("GIUDECCA",30133)
    ]
for s,c in list_sest_cap:
    # aggiungi se non è già presente
    if not Neighborhood.query.filter_by(name=s,zipcode=c).first():
        n = Neighborhood(name=s,zipcode=c)
        db.session.add(n)
        db.session.commit()
print("Sestieri: {ses}\nStrade: {str}\nCivici: {civ}\nFile: {file}".format(
    ses=len(Neighborhood.query.all()),
    str=len(Street.query.all()),
    civ=len(Location.query.all()),
    file=len(civici_address)
    ))
#%% Aggiungi civici e strade
wrong_entries = []
for add,den,coord in zip(civici_address, civici_denominazioni, civici_coords):
    long,lat = coord
    num_found_add = re.search("\d+(/[A-Z])?",add)
    num_found_den = re.search("\d+(/[A-Z])?",den)
    if not num_found_add or not num_found_den:
        # il civico non ha il numero: passa al successivo
        wrong_entries.append((1,add,den,coord))
        continue
    if num_found_add.group(0) != num_found_den.group(0):
        # civico e denominazione hanno numeri diversi: passa al successivo
        wrong_entries.append((2,add,den,coord))
        continue
    num = num_found_add.group(0)
    sest = add[:-len(num)-1]
    str = den[:-len(num)-1]
    n = Neighborhood.query.filter_by(name=sest).first()
    if not n:
        # il sestiere non esite: passa al successivo
        wrong_entries.append((3,add,den,coord))
        continue
    if not Street.query.filter_by(name=str,neighborhood=n).first():
        # la strada in quel sestiere non esiste: la aggiungo al db
        db.session.add(Street(name=str,neighborhood=n))
    s = Street.query.filter_by(name=str,neighborhood=n).first()
    if not Location.query.filter_by(latitude=lat,longitude=long,street=s,housenumber=num).first():
        # il civico in quella strada non esiste: lo aggiungo al db
        db.session.add(Location(latitude=lat,longitude=long,street=s,housenumber=num))

db.session.commit()
print("Indirizzi non inseriti: {wr}".format(wr=len(wrong_entries)), *wrong_entries, sep="\n")
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
