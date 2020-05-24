#%% Imports
import os,sys

from app import app, db

import pandas as pd
from importlib import reload
from app.models import *
import numpy as np
import re
import geopandas as gpd
from descartes import PolygonPatch
import matplotlib.pyplot as plt
import geopy.distance
import shapefile
from fuzzywuzzy import process
#%% Files
# TODO leggere civico.shp invece che txt
folder = os.getcwd()
folder_file = os.path.join(folder,"app","static","files")
# Nomi dei file
name_file_civici = "lista_civici_only.txt"
name_file_civici_denominazioni = "lista_denominazioni_csv.txt"
name_file_civici_coords = "lista_coords_civici_only.txt"
name_file_poi = "POI_venezia_completo.csv"
# path dei file
file_civici = os.path.join(folder_file, name_file_civici)
file_civici_denominazioni = os.path.join(folder_file, name_file_civici_denominazioni)
file_civici_coords = os.path.join(folder_file, name_file_civici_coords)
file_poi = os.path.join(folder_file, name_file_poi)
#%% Load files
# Import with pandas
# civici_address = pd.read_csv(os.path.join(folder_file,file_civici),header=None,names=["civico","empty"])
# civici_address = civici_address.drop("empty",axis=1)
# civici_denominazioni = pd.read_csv(os.path.join(folder_file,file_civici_denominazioni),header=None,names=["denominazione","empty"])
# civici_denominazioni = civici_denominazioni.drop("empty",axis=1)
# civici_coords = pd.read_csv(os.path.join(folder_file,file_civici_coords),header=None,names=["longitude","latitude"])
# civici = pd.concat([civici_address,civici_denominazioni,civici_coords],axis=1)

# Import with numpy
civici_address = np.loadtxt(file_civici, delimiter = ";" , comments=",",dtype='str')
civici_denominazioni = np.loadtxt(file_civici_denominazioni, delimiter = ";" , comments=",",dtype='str')
civici_coords = np.loadtxt(file_civici_coords, delimiter = "," , dtype='float')
poi_csv = np.loadtxt(file_poi,delimiter = "|",dtype='str')
poi_pd = pd.read_csv(file_poi,sep="|",dtype='str')
poi_pd[["lat","lon"]]=poi_pd[["lat","lon"]].apply(pd.to_numeric)
#%%
####### estrarre i poligoni dai sestieri per caricarli nel database
sestieri =  gpd.read_file(os.path.join(folder_file,"Localita","Località.shp"))
sestieri = sestieri.to_crs(epsg=4326)
streets =  gpd.read_file(os.path.join(folder_file,"TP_STR.shp"))
streets = streets.to_crs(epsg=4326)
civici =  gpd.read_file(os.path.join(folder_file,"CIVICO.shp"))
# rimuovo righe senza geometria che danno problemi
empty_civici = civici.loc[pd.isna(civici["geometry"])]
civici = civici.loc[~pd.isna(civici["geometry"])]
civici = civici.to_crs(epsg=4326)
print("*Aggiunti*\nSestieri: {ses}\nStrade: {str}\nCivici: {civ}\n*Rimossi*\nCivici: {civ_rim}".format(
    ses=len(sestieri),
    str=len(streets),
    civ=len(civici),
    civ_rim=len(empty_civici)
    ))

#%%
# # elimina tutto
# Neighborhood.query.delete()
# Street.query.delete()
# Location.query.delete()
# db.session.commit()
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
add_neighb = 0
for s,c in list_sest_cap:
    # controlla geometria
    geom = sestieri[sestieri["A_SCOM_NOM"]==s.title()]["geometry"]
    if geom.empty:
        err_neighb.append((s,c))
        continue
    geom = geom.iloc[0]
    # aggiungi se non è già presente
    neig = Neighborhood.query.filter_by(shape=geom).first()
    if not neig:
        n = Neighborhood(name=s,zipcode=c, shape=geom)
        add_neighb += 1
        db.session.add(n)

db.session.commit()

print("Errori: {err}\nSestieri: {ses}\nNuovi: {new}".format(
    err=len(err_neighb),
    ses=len(Neighborhood.query.all()),
    new=add_neighb
    ))
# Plot dei sestieri
plt.figure()
for n in Neighborhood.query.all():
    plt.plot(*n.shape.exterior.xy)
plt.show()
#%% Aggiungi Strade

err_streets = []
add_streets = 0
for name, name_spe, name_den, pol in streets[['TP_STR_NOM','CVE_TS_SPE','CVE_TS_DEN','geometry']].values:
    if pd.isna(name):
        err_streets.append((0,name,name_spe,name_den,pol))
    sestieri = [n for n in Neighborhood.query.all() if n.shape.distance(pol)==0]
    # se la strada non è contenuta in nessun sestiere passa al successivo
    if len(sestieri)==0:
        continue
    # elif len(sestieri)>1:
    #     # se c'è più di un sestiere aggiungi agli errori e passa al successivo
    #     err_streets.append((1,name,name_spe,name_den,pol))
    #     continue
    if not Street.query.filter_by(shape=pol).first():
        st = Street(name=name,name_spe=name_spe,name_den=name_den,shape=pol)
        db.session.add(st)
        for sestiere in sestieri:
            st.add_neighborhood(sestiere)
        add_streets += 1

db.session.commit()

print("Errori: {err}\nSestieri: {ses}\nStrade: {str}\nNuove: {new}".format(
    err=len(err_streets),
    ses=len(Neighborhood.query.all()),
    str=len(Street.query.all()),
    new=add_streets
    ))
err_streets
#%% Aggiugi civici
# print(civici.columns)
#civici["DENOMINAZI"].unique()
# n = civici.loc[pd.isna(civici["DENOMINAZI"])]
# nn = n.loc[pd.isna(n["DENOMINA_1"])]
# # print(sp)
# # print(sp["CIVICO_SUB"])
# # pol = sp["geometry"].values
# civ = civici.iloc[0:5]
# for num, sub, den, pol in civ[["CIVICO_NUM","CIVICO_SUB","DENOMINAZI","geometry"]].values:
#     num_found_add = re.search("\d+(/[A-Z])?",den)
#     den_num = num_found_add.group(0)
#     den_str = den[:-len(den_num)-1]
#     print(den_str)
# print(pol.centroid)
# lon=pol.centroid.x
# a = "_"
# a.isalpha()

err_civ = []
add_civ = 0

for num, sub, den, den1, pol in civici[["CIVICO_NUM","CIVICO_SUB","DENOMINAZI","DENOMINA_1","geometry"]].values:
    sestieri = [n for n in Neighborhood.query.all() if n.shape.contains(pol)]
    # se il civico non è contenuto in nessun passa al successivo
    if len(sestieri)==0:
        continue
    elif len(sestieri)>1:
        # se c'è più di un sestiere aggiungi agli errori e passa al successivo
        err_civ.append((0,num, sub, den, den1, pol))
        continue
    # principalmente voglio usare DENOMINAZI, nel caso sia vuoto uso DENOMINA_1
    # nel caso siano entrambi vuoti errore e continuo
    if pd.isna(den) and pd.isna(den1):
        err_civ.append((1,num, sub, den, den1, pol))
        continue
    elif not pd.isna(den):
        denom = den
    elif not pd.isna(den1):
        denom = den1
    else:
        # questo non dovrebbe mai succedere
        err_civ.append((2,num, sub, den, den1, pol))
        continue
    # estraggo strada e civico da denominazi
    num_found_denom = re.search("\d+(/[A-Z])?$",denom)
    if not num_found_denom:
        found=False
        # se non ha trovato nulla riprova usando den1 se non è vuota
        if denom==den and not pd.isna(den1):
            num_found_denom = re.search("\d+(/[A-Z])?$",den1)
            if num_found_denom:
                found = True
                denom = den1
        if not found:
            # aggiungi agli errori e passa al successivo
            err_civ.append((3,num, sub, den, den1, pol))
            continue
    den_num = num_found_denom.group(0)
    den_str = denom[:-len(den_num)-1]
    # estraggo numero ed eventuale lettera da CIVICO_NUM e CIVICO_SUB
    housenumber = num
    if sub.isalpha():
        housenumber += '/'+sub.upper()
    # controllo che il numero civico sia uguale a quello trovato prima
    if housenumber != den_num:
        found = False
        # provo a vedere se per caso non è uguale a quello dei den1
        if denom==den and not pd.isna(den1):
            num_found_denom = re.search("\d+(/[A-Z])?$",den1)
            if num_found_denom:
                den1_num = num_found_denom.group(0)
                if housenumber == den1_num:
                    found = True
        if not found:
            # aggiungi agli errori e passa al successivo
            err_civ.append((4,num, sub, den, den1, pol))
            continue
    # cerco tutte le strade che hanno il nome riportato nel civico
    # o il cui nome non sia una sottostringa di quello riportato nel civico
    streets = Street.query.filter(db.or_(
                    Street.name==n,
                    literal(n).contains(Street.name))).all()
    if len(streets)==0:
        # se non c'è una strada
        found = False
        # prova a vedere che non ci sia un typo
        namestr,score=process.extractOne(den_str.strip(),[s.name for s in Street.query.all()])
        if score >= 90:
            streets = [s for s in Street.query.filter_by(name=namestr).all()]
        else:
            #aggiungi agli errori e passa al successivo
            err_civ.append((5,num, sub, den, den1, pol))
            continue
    if len(streets)==1:
        #c'è solo una strada, prendo quella
        street = streets[0]
    else:
        # c'è più di una strada, cerco la più vicina
        # (è un po' rischioso perché non faccio nessun check sulla distanza)
        idx_closest = np.argmin([s.shape.distance(pol) for s in streets])
        street = streets[idx_closest]
    # estraggo latitude e longitudine dal punto rappresentativo
    repr_point = pol.representative_point()
    lat = repr_point.y
    lon = repr_point.x
    # Se la location non esiste già la aggiungo
    if not Location.query.filter_by(latitude=lat,longitude=lon,housenumber=housenumber,street=street).first():
        loc = Location(latitude=lat,longitude=lon,housenumber=housenumber,street=street)
        add_civ += 1
        db.session.add(loc)

db.session.commit()

print("Errori: {err}\nSestieri: {ses}\nStrade: {str}\nCivici: {civ}\nNuovi: {new}".format(
    err=len(err_civ),
    ses=len(Neighborhood.query.all()),
    str=len(Street.query.all()),
    civ=len(Location.query.all()),
    new=add_civ
    ))

err_type = [[], [], [], [], [], []]
for err in err_civ:
    err_type[err[0]].append(err)
print([len(err) for err in err_type])

#%% Aggiungi civici e strade
# wrong_entries = []
# err = [0,0,0]
# for add,den,coord in zip(civici_address, civici_denominazioni, civici_coords):
#     long,lat = coord
#     num_found_add = re.search("\d+(/[A-Z])?",add)
#     num_found_den = re.search("\d+(/[A-Z])?",den)
#     if not num_found_add or not num_found_den:
#         # il civico non ha il numero: passa al successivo
#         wrong_entries.append((1,add,den,coord))
#         err[0] += 1
#         continue
#     if num_found_add.group(0) != num_found_den.group(0):
#         # civico e denominazione hanno numeri diversi: passa al successivo
#         wrong_entries.append((2,add,den,coord))
#         err[1] += 1
#         continue
#     num = num_found_add.group(0)
#     sest = add[:-len(num)-1]
#     str = den[:-len(num)-1]
#     n = Neighborhood.query.filter_by(name=sest).first()
#     if not n:
#         # il sestiere non esite: passa al successivo
#         wrong_entries.append((3,add,den,coord))
#         err[2] += 1
#         continue
#     if not Street.query.filter_by(name=str,neighborhood=n).first():
#         # la strada in quel sestiere non esiste: la aggiungo al db
#         db.session.add(Street(name=str,neighborhood=n))
#     s = Street.query.filter_by(name=str,neighborhood=n).first()
#     if not Location.query.filter_by(latitude=lat,longitude=long,street=s,housenumber=num).first():
#         # il civico in quella strada non esiste: lo aggiungo al db
#         db.session.add(Location(latitude=lat,longitude=long,street=s,housenumber=num))
#
# db.session.commit()
# print("Sestieri: {ses}\nStrade: {str}\nCivici: {civ}\nFile: {file}".format(
#     ses=len(Neighborhood.query.all()),
#     str=len(Street.query.all()),
#     civ=len(Location.query.all()),
#     file=len(civici_address)
#     ))
# print("Indirizzi non inseriti: {wr}\nNumero mancante: {noNum}\nNumero diverso: {divNum}\nSestiere non esiste: {noSes}".format(wr=len(wrong_entries),noNum=err[0],divNum=err[1],noSes=err[2]), *wrong_entries, sep="\n")
#%%
# ####### estrarre i poligoni delle strade per caricarli nel database
# TP_streets =  gpd.read_file(os.path.join(folder_file,"TP_STR.shp"))
# TP_streets = TP_streets.to_crs(epsg=4326)
# TP_nome = np.asarray(TP_streets["TP_STR_NOM"])
# TP_geom = TP_streets["geometry"]
# TP_geom[1].centroid
#
# err_shp = []
# for n,poli in zip(TP_nome, TP_geom):
#     matches=Street.query.filter_by(name=n).all()
#     for m in matches:
#         if m.neighborhood.shape.contains(poli.centroid):
#             m.shape=poli
#         else:
#             err_shp.append((m,poli))
# db.session.commit()
#
# print("Strade con shape: {con}\nStrade senza shape: {sen}".format(
#     con = len(Street.query.filter(Street.shape.isnot(None)).all()),
#     sen = len(Street.query.filter_by(shape=None).all())
#     ), *Street.query.filter_by(shape=None).all(), sep="\n")

#%%
# import shapely
# sm = Neighborhood.query.filter_by(name="SAN POLO").first()
# shapes = Street.query.filter_by(neighborhood=sm).filter(Street.shape.isnot(None)).all()
# n1 = err_shp[0][0]
# n1_geom = err_shp[0][1]
# y1 = shapes[0]
# err_shp[0]
#
# # Plot del sestiere
# fig, axs = plt.subplots()
# xsm, ysm = sm.shape.exterior.xy
# axs.fill(xsm,ysm, alpha=0.5, fc='b', ec='none')
# # Plot della strada trovata
# if type(y1.shape)==shapely.geometry.polygon.Polygon:
#     x_y, y_y = y1.shape.exterior.xy
#     axs.fill(x_y, y_y, alpha=1, fc='r', ec='none')
# elif type(y1.shape)==shapely.geometry.polygon.MultiPolygon:
#     for geom in y1.shape.geoms:
#         xg, yg = geom.exterior.xy
#         axs.fill(xg, yg, alpha=1, fc='r', ec='none')
# # Plot della strada non trovata
# if type(n1_geom)==shapely.geometry.polygon.Polygon:
#     x_n, y_n = n1_geom.exterior.xy
#     axs.fill(x_n, y_n, alpha=1, fc='g', ec='none')
# elif type(n1_geom)==shapely.geometry.polygon.MultiPolygon:
#     for geom in n1_geom.geoms:
#         xg, yg = geom.exterior.xy
#         axs.fill(xg, yg, alpha=1, fc='g', ec='none')
# x_n
# plt.show()
#


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
"""
TAGS
name
amenity
shop
wheelchair
cuisine
toilets:wheelchair
tourism
alt_name
building
opening_hours
wikipedia
atm
outdoor_seating
diet:vegetarian
phone
denomination
sport
"""

list_category = [
    "amenity",
    "shop",
    "cuisine",
    "tourism",
    "building",
    "sport"
    ]
#%%
# crea le category e i type (se non esistono già)
for c in list_category:
    if not PoiCategory.query.filter_by(name=c).first():
        db.session.add(PoiCategory(name=c))
    cat = PoiCategory.query.filter_by(name=c).first()
    for types in poi_pd[c].unique():
        if pd.isna(types):
            continue
        all_types = types.split(";")
        for t in all_types:
            if not PoiCategoryType.query.filter_by(name=t.strip(),category=cat).first():
                db.session.add(PoiCategoryType(name=t.strip(),category=cat))
db.session.commit()
print("Numero di Category: {cat}\nNumero totale di Type: {typ}".format(
    cat=len(PoiCategory.query.all()),
    typ=len(PoiCategoryType.query.all())
    ))
print("Tutti i tipi",*PoiCategoryType.query.all(),sep="\n")

#%% funzione per trovare il poi più vicino a una certa lat/lon
def closest_location(lat,lon,tolerance=0.001):
    closest = []
    distance = np.inf
    for loc in Location.query.filter(db.and_(db.between(Location.longitude,lon-tolerance,lon+tolerance),
            db.between(Location.latitude,lat-tolerance,lat+tolerance)
            )).all():
        dist = geopy.distance.distance((loc.latitude, loc.longitude),(lat,lon)).meters
        if dist < distance:
            distance = dist
            closest = loc
    return closest,distance
#%% Get poi_types
# Lista di tipi di poi che non avranno una corrispondenza con un numero civico(ad esempio chiese o fontanelle)
types_without_address={
    "amenity":["drinking_water",
            "place_of_worship",
            "bus_station",
            "ferry_terminal"],
    "building":["church",
                "kiosk",
                "column"]
}
# crea un dataframe con solo i poi che non avranno un indirizzo
poi_without_add = pd.DataFrame()
for key in types_without_address.keys():
    for val in types_without_address[key]:
        p = poi_pd.loc[poi_pd[key]==val]
        poi_without_add = pd.concat([poi_without_add,p])
# malvagità per creare un dataframe differenza tra tutti - quelli che non avranno indirizzo
poi_with_add = poi_pd[~poi_pd.apply(tuple,1).isin(poi_without_add.apply(tuple,1))]

# loop per aggiungere tutti i poi
err_poi = []
#massima distanza in metri per considerare una location
max_dist = 50

for row in poi_pd.values:
    # sostituisci nan con None per evitare casini
    r = np.where(pd.isna(row), None, row)
    # Trova la location esistente più vicina alle coordinate
    lat, lon = r[2:4]
    closest,dist = closest_poi(lat,lon)
    # se non c'è nessuna location vicina
    if not closest:
        err_poi.append((0,row))
        continue

    if dist > max_dist:
        err_poi.append((1,row))
        continue
    # Controlla se il poi deve essere aggiunto con o senza indirizzo
    if row in poi_without_add.values:
        # non deve essere aggiunto con indirizzo
        # crea una nuova location (barbatrucco: usa la strada del poi più vicino)

        l = Location(latitude=lat,longitude=lon,street=closest.street)
    elif row in poi_with_add.values:
        # considera come location quella trovata
        l = closest
    else:
        err_poi.append((2,row))
        continue
    # controlla che non esista già un poi nella medesima location
    if Poi.query.filter_by(location=l).count()>0:
        continue
    # crea poi con informazioni di base
    p = Poi(location=l)
    p.name = r[poi_pd.columns.get_loc('name')]
    p.name_alt = r[poi_pd.columns.get_loc('alt_name')]
    p.opening_hours = r[poi_pd.columns.get_loc('opening_hours')]
    p.wheelchair = r[poi_pd.columns.get_loc('wheelchair')]
    if r[poi_pd.columns.get_loc('toilets')] == "yes":
        p.toilets = True
    elif r[poi_pd.columns.get_loc('toilets')] == "no":
        p.toilets = False
    if r[poi_pd.columns.get_loc('toilets:wheelchair')]=="yes":
        p.toilets_wheelchair = True
    elif r[poi_pd.columns.get_loc('toilets:wheelchair')]=="no":
        p.toilets_wheelchair = False
    p.wikipedia = r[poi_pd.columns.get_loc('wikipedia')]
    if r[poi_pd.columns.get_loc('atm')]=="yes":
        p.atm = True
    elif r[poi_pd.columns.get_loc('atm')]=="no":
        p.atm = False
    p.phone = r[poi_pd.columns.get_loc('phone')]
    # aggiungi le informazioni sulle categorie dalla tabella type
    for cat in list_category:
        cat_type = r[poi_pd.columns.get_loc(cat)]
        # se il valore è None vai al prossimo
        if cat_type == None:
            continue
        # dividi con i punti e virgola per aggiungere tutti i tipi
        all_types = cat_type.split(";")
        for typ in all_types:
            t = PoiCategoryType.query.filter_by(name=typ.strip()).first()
            if not t:
                err_poi.append((2,row))
                continue
            p.add_type(t)
    # aggiungi al database
    # magia: incredibilmente questo aggiunge anche la location nel caso non esistesse
    db.session.add(p)
print("Numero di POI: {poi}\nErrori: {err}".format(poi=len(Poi.query.all()),err=len(err_poi)))

db.session.commit()
#%%
lat,lon=err_poi[0][1][2:4]
closest_poi(lat,lon,tolerance=0.01)
