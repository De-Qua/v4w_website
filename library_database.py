"""
Module to update and check our database
"""
#%% Imports
import os,sys
# IMPORT FOR THE DATABASE - db is the database object
from app import app, db
from app.models import Neighborhood, Street, Location, Area, Poi
import random
import geopandas as gpd
import pandas as pd
import pyproj
import numpy as np
from distutils.version import StrictVersion
import warnings
import re
from fuzzywuzzy import process
from shapely.geometry import Point
from sqlalchemy import literal
import geopy.distance


global neigh_query, streets_query, location_query

def create_query_objects():
    """
    Skyrocketing our performances with few lines of code (it creates the query objects to be used later).
    """
    global neigh_query, streets_query, location_query
    neigh_query = Neighborhood.query #serve l'all?
    streets_query = Street.query
    location_query = Location.query
    poi_query = Poi.query
    aree_query = Area.query
    # Reset database if there were changes not committed
    db.session.rollback()

def progressbar(current_value,total_value,step=5,text='',progressSymbol='=',remainingSymbol=' ',currentSymbol=''):
    assert (100%step) == 0
    percentage = current_value / total_value * 100
    progress = int(percentage/step)
    remain = int(100/step-progress)
    if len(currentSymbol)>0:
        idx = current_value % len(currentSymbol)
        current = currentSymbol[idx]
    else:
        current = ''

    if percentage < 100:
        print("[{progress}{current}{remain}] {perc:5.1f}% {text}".format(progress=progressSymbol*progress,current=current,remain=remainingSymbol*(remain-len(current)),perc=percentage,text=text),
                                                    end="\r",flush=True)
    else:
        print("[{progress}{remain}] {perc:5.1f}% {text}".format(progress="="*progress,remain=" "*remain,perc=percentage,text=text),
                                                        end="\n",flush=True)


def progressbar_pip_style(current,total,step=5,text=''):
    progressbar(current,total,step=step,text=text,currentSymbol='>')
    # assert (100%step) == 0
    # percentage = current / total * 100
    # progress = int(percentage/step)
    # remain = int(100/step-progress)
    # print("[{progress}{remain}] {perc:5.1f}% {text}".format(progress="="*progress+">",remain=" "*remain,perc=percentage,text=text),
    #                                                 end="\r",flush=True)
    # if percentage == 100:
    #     print("",end="\n",flush=True)

def convert_SHP(shp_file, explain=False):
    """
    If not already, convert the shapefile to WGS 84.
    """

    if StrictVersion(pyproj.__version__) >= StrictVersion("2.2"):
        crs_attr = shp_file.crs.name
    else:
        warnings.warn("PyProj version should be at least 2.2\nSee why here, the crs field changed https://geopandas.readthedocs.io/en/latest/projections.html",
                        category=FutureWarning)
        crs_attr = shp_file.crs['init']

    if not (crs_attr=='WGS 84'):
        if explain:
            print("the shp was in the format {}".format(shp_file.crs))
        shp_file = shp_file.to_crs(epsg=4326)
        if explain:
            print("converted to {}".format(shp_file.crs))

    return shp_file

def update_sestieri(shp, showFig=False, explain=False):
    """
    Updates the neighborhood Table and returns the number of errors, so 0 is the desired output.
    """
    global neigh_query, streets_query, location_query
    sestieri =  gpd.read_file(shp)
    sestieri =  convert_SHP(sestieri,explain)

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
    if explain:
        print("Aggiungo i sestieri.. ne abbiamo {} in totale nel file.".format(len(list_sest_cap)))

    err_neighb = []
    add_neighb = 0
    tot_neighb = 0
    all_neighb = len(list_sest_cap)
    for s,c in list_sest_cap:
        tot_neighb += 1
        progressbar(tot_neighb,all_neighb)
        # controlla geometria
        geom = sestieri[sestieri["A_SCOM_NOM"]==s.title()]["geometry"]
        if geom.empty:
            err_neighb.append((s,c))
            continue
        geom = geom.iloc[0]
        # aggiungi se non è già presente
        neig = neigh_query.filter_by(shape=geom).first()
        if not neig:
            # TODO: possiamo usare la query gia esistente qui?
            n = Neighborhood(name=s,zipcode=c, shape=geom)
            add_neighb += 1
            db.session.add(n)

    if explain:
        print("committo nel database..")
    try:
        db.session.commit()
    except:
        db.session.rollback()
        warnings.warn("Errore nel commit")

    print("Errori: {err}\nSestieri: {ses}\nNuovi: {new}".format(
        err=len(err_neighb),
        ses=len(neigh_query.all()),
        new=add_neighb
        ))
    if showFig:
        # Plot dei sestieri
        plt.figure()
        plt.title("Neighborhood Shapes")
        for n in neigh_query:
            plt.plot(*n.shape.exterior.xy)
        plt.show()

    return err_neighb

def update_streets(shp, showFig=False, explain=False):
    """
    Updates the Streets Table and returns the number of errors, so 0 is the desired output.
    """
    global neigh_query, streets_query, location_query

    streets = gpd.read_file(shp)
    streets = convert_SHP(streets)

    if explain:
        print("Aggiungiamo le strade, ne abbiamo {} in totale nel file.".format(len(streets['TP_STR_NOM'])))
    err_streets = []
    add_streets = 0
    tot_street = 0
    all_streets = len(streets['TP_STR_NOM'])
    step = np.round(all_streets / 15).astype(int)
    for name, name_spe, name_den, pol in streets[['TP_STR_NOM','CVE_TS_SPE','CVE_TS_DEN','geometry']].values:
        tot_street +=1
        progressbar(tot_street,all_streets)
        if not name:
            err_streets.append((0,name,name_spe,name_den,pol))
            continue
        sestieri = [n for n in neigh_query.all() if n.shape.distance(pol)==0]
        # se la strada non è contenuta in nessun sestiere passa al successivo
        if len(sestieri)==0:
            continue
        # elif len(sestieri)>1:
        #     # se c'è più di un sestiere aggiungi agli errori e passa al successivo
        #     err_streets.append((1,name,name_spe,name_den,pol))
        #     continue
        if not streets_query.filter_by(shape=pol).first():
            #if explain:
                #percentage = tot_street / len(streets['TP_STR_NOM']) * 10
                #for j in range(np.round(percentage).astype(int)):
                #    string_to_be_print.concat("=")
                #print(string_to_be_print, end="", flush=True)
                #percentage = np.round(tot_street / all_streets * 100).astype(int)
                #print("{num:03d}: {tot}/ {tot2}: Aggiungo {str}                                            ".format(num=percentage, bar=string_to_be_print, ot=tot_street, tot2=len(streets['TP_STR_NOM']), str=name), end="\r", flush=True)

            st = Street(name=name,name_spe=name_spe,name_den=name_den,shape=pol)
            db.session.add(st)
            for sestiere in sestieri:
                st.add_neighborhood(sestiere)
            add_streets += 1


    if explain:
        print("committo nel database..")
    try:
        db.session.commit()
    except:
        db.session.rollback()
        warnings.warn("Errore nel commit")

    print("Errori: {err}\nSestieri: {ses}\nStrade: {str}\nNuove: {new}".format(
        err=len(err_streets),
        ses=len(neigh_query.all()),
        str=len(streets_query.all()),
        new=add_streets
        ))

    if showFig:
        print("per evitare congestioni, plotto solo 20% delle strade a random. se proprio ci tieni, plottale tutte manualmente.")
        print("for s in streets_query: plt.plot(*s.shape.exterior.xy)")
        print("potrebbe dare un errore nel plot, perche uso gli indici per plottare le shapes, e magari non si fa cosi - scusate")
        # Plot dei sestieri
        plt.figure()
        plt.title("Neighborhood Shapes")

        random_range = 100
        for i in range(len(streets_query)):
            random_choice = random.randint(0,random_range)
            if random_choice > random_range/2:
                plt.plot(s[i].shape.exterior.xy)
        plt.show()

    return err_streets

def update_locations(shp, showFig=False, explain=False):
    """
    Updates the Location Table and returns the number of errors, so 0 is the desired output.
    """

    global neigh_query, streets_query, location_query
    civici = gpd.read_file(shp)
    # rimuovo righe senza geometria che danno problemi
    civici = civici.loc[~pd.isna(civici["geometry"])]
    civici = convert_SHP(civici)

    err_civ = []
    add_civ = 0
    tot_civ_added = 0
    tot_civ_in_file = len(civici['CIVICO_NUM'])
    step_civ = np.round(tot_civ_in_file / 100)

    if explain:
        print("Aggiungiamo i civici, ne abbiamo {} in totale nel file.".format(tot_civ_in_file))
    for num, sub, den, den1, pol in civici[["CIVICO_NUM","CIVICO_SUB","DENOMINAZI","DENOMINA_1","geometry"]].values:
        tot_civ_added += 1
        progressbar_pip_style(tot_civ_added,tot_civ_in_file)
        sestieri = [n for n in neigh_query.all() if n.shape.contains(pol)]
        # se il civico non è contenuto in nessun passa al successivo
        if len(sestieri)==0:
            continue
        elif len(sestieri)>1:
            # se c'è più di un sestiere aggiungi agli errori e passa al successivo
            err_civ.append((0,num, sub, den, den1, pol))
            continue
        # principalmente voglio usare DENOMINAZI, nel caso sia vuoto uso DENOMINA_1
        # nel caso siano entrambi vuoti errore e continuo
        if not den and not den1:
            err_civ.append((1,num, sub, den, den1, pol))
            continue
        elif den:
            denom = den
        elif den1:
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
            if denom==den and den1:
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
        streets = streets_query.filter(db.or_(
                        Street.name==den_str.strip(),
                        literal(den_str.strip()).contains(Street.name))).all()
        if len(streets)==0:
            # se non c'è una strada
            found = False
            # prova a vedere che non ci sia un typo
            namestr,score=process.extractOne(den_str.strip(),[s.name for s in Street.query.all()])
            if score >= 90:
                streets = [s for s in streets_query.filter_by(name=namestr).all()]
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
        if not location_query.filter_by(latitude=lat,longitude=lon,housenumber=housenumber,street=street).first():
            loc = Location(latitude=lat,longitude=lon,housenumber=housenumber,street=street,neighborhood=sestieri[0])
            add_civ += 1
            #percentage = (tot_civ_added / tot_civ_in_file) * 100
            #print("{perc:5.1f}% - {tot:5d}/{tot2}".format(perc=percentage, tot=tot_civ_added, tot2=tot_civ_in_file), end="\r", flush=True)

            db.session.add(loc)

    if explain:
        print("committo nel database..")
    try:
        db.session.commit()
    except:
        db.session.rollback()
        warnings.warn("Errore nel commit")

    print("Errori: {err}\nSestieri: {ses}\nStrade: {str}\nCivici: {civ}\nNuovi: {new}".format(
        err=len(err_civ),
        ses=len(neigh_query.all()),
        str=len(streets_query.all()),
        civ=len(location_query.all()),
        new=add_civ
        ))

    # TODO: dividi per tipo d'errore?
    err_type = [[], [], [], [], [], []]
    for err in err_civ:
        err_type[err[0]].append(err)
    if explain:
        print([len(err) for err in err_type])

    if showFig:
        print("per evitare congestioni, plotto solo 5% delle localita a random. se proprio ci tieni, plottale tutte manualmente.")
        print("for l in location_query: plt.plot(l.latitude, l.longitude)")
        print("potrebbe dare un errore nel plot, perche uso gli indici per plottare le coordinate, e magari non si fa cosi - scusate")
        # Plot dei sestieri
        plt.figure()
        plt.title("Neighborhood Shapes")

        random_range = 100
        for i in range(len(location_query)):
            random_choice = random.randint(0,random_range)
            if random_choice > random_range/2:
                plt.plot(location_query[i].latitude, location_query[i].longitude)
        plt.show()

    return err_civ

def read_POI(poi_file_path):
    poi_csv = np.loadtxt(file_poi,delimiter = "|",dtype='str')
    poi_pd = pd.read_csv(file_poi,sep="|",dtype='str')
    poi_pd[["lat","lon"]]=poi_pd[["lat","lon"]].apply(pd.to_numeric)

    return poi_csv, poi_pd

def update_POI(poi_cs, poi_pd):
    """
    Updates the POI Table and returns the number of errors, so 0 is the desired output.
    """
    global neigh_query, streets_query, location_query
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
    new_poi = 0
    new_loc = 0
    tot_val = [0,0,0,0,0,0,0]
    #massima distanza in metri per considerare una location
    max_dist = 50

    for row in poi_pd.values:

        new_l = False
        # sostituisci nan con None per evitare casini
        r = np.where(pd.isna(row), None, row)
        # Estrai le coordinate e trova la location più vicina
        lat, lon = r[2:4]
        closest,dist = closest_location(lat,lon)
        tot_val[0]+=1
        if row in poi_without_add.values:
            closest,dist = closest_location(lat,lon)
            if not closest:
                err_poi.append((0,row))
                continue
            # aggiungi la location usando come strada quella della location più vicina
            l = Location(latitude=lat,longitude=lon)
            new_l = True
        elif row in poi_with_add.values:
            # Cerca la location più vicina che abbia anche un numero civico
            closest,dist = closest_location(lat,lon,housenumber=True)
            if not closest:
                err_poi.append((0,row))
                continue
            # se la location trovata è più distante di max_dist aggiungi agli errori e passa al successivo
            elif dist > max_dist:
                err_poi.append((2,row))
                continue
            l = closest
        else:
            # questo non dovrebbe mai succedere
            err_poi.append((1,row))
            continue
        tot_val[1]+=1
        # crea informazioni di base
        # (non creo già il poi perché visto che ha una relazione con location che fa
        # già parte della db.session, allora lo aggiungerebbe automaticamente alla session)
        location=l
        name = r[poi_pd.columns.get_loc('name')]
        name_alt = r[poi_pd.columns.get_loc('alt_name')]
        opening_hours = r[poi_pd.columns.get_loc('opening_hours')]
        wheelchair = r[poi_pd.columns.get_loc('wheelchair')]
        if r[poi_pd.columns.get_loc('toilets')] == "yes":
            toilets = True
        elif r[poi_pd.columns.get_loc('toilets')] == "no":
            toilets = False
        else:
            toilets = None
        if r[poi_pd.columns.get_loc('toilets:wheelchair')]=="yes":
            toilets_wheelchair = True
        elif r[poi_pd.columns.get_loc('toilets:wheelchair')]=="no":
            toilets_wheelchair = False
        else:
            toilets_wheelchair = None
        wikipedia = r[poi_pd.columns.get_loc('wikipedia')]
        if r[poi_pd.columns.get_loc('atm')]=="yes":
            atm = True
        elif r[poi_pd.columns.get_loc('atm')]=="no":
            atm = False
        else:
            atm = None
        phone = r[poi_pd.columns.get_loc('phone')]
        tot_val[2]+=1
        # controlla che non esista già lo stesso poi
        if Poi.query.filter_by(name = name,
                        name_alt = name_alt,
                        opening_hours = opening_hours,
                        wheelchair = wheelchair,
                        toilets = toilets,
                        toilets_wheelchair = toilets_wheelchair,
                        wikipedia = wikipedia,
                        atm = atm,
                        phone = phone
                        ).join(Location).filter_by(latitude=location.latitude,
                                            longitude=location.longitude).first():
            continue
        tot_val[3]+=1
        # se la location era nuova aggiungo la strada ora
        # lo faccio ora perché prima aggiungendo la strada avrebbe creato la location
        if new_l:
            location.street = closest.street
        # creo il poi
        p = Poi(location=location,
                name = name,
                name_alt = name_alt,
                opening_hours = opening_hours,
                wheelchair = wheelchair,
                toilets = toilets,
                toilets_wheelchair = toilets_wheelchair,
                wikipedia = wikipedia,
                atm = atm,
                phone = phone
                )
        tot_val[4]+=1
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
                    err_poi.append((3,row))
                    continue
                p.add_type(t)
        tot_val[5]+=1
        # aggiungi al database
        new_poi += 1
        if new_l:
            new_loc +=1
        # magia: incredibilmente questo aggiunge anche la location nel caso non esistesse
        db.session.add(p)

    print("Numero di POI: {poi}\nErrori: {err}\nNuovi POI: {new_p}\nNuove Location: {new_l}".format(
            poi=len(Poi.query.all()),
            err=len(err_poi),
            new_p=new_poi,
            new_l=new_loc))

    # db.session.rollback()
    #2907 154 43381
    #db.session.commit()
    err_type = [[],[],[],[]]
    for err in err_poi:
        err_type[err[0]].append(err)
    print([len(err) for err in err_type])

    return len(err_poi)

#%% funzione per trovare il poi più vicino a una certa lat/lon
def closest_location(lat,lon,tolerance=0.001,housenumber=None):
    """
    It returns the closest POI with respect to the input coordinates.
    """
    global neigh_query, streets_query, location_query
    closest = []
    distance = np.inf
    if housenumber == True:
        query = Location.query.filter(db.and_(db.between(Location.longitude,lon-tolerance,lon+tolerance),
                db.between(Location.latitude,lat-tolerance,lat+tolerance),
                Location.housenumber != None
                ))
    elif housenumber == False:
        query = Location.query.filter(db.and_(db.between(Location.longitude,lon-tolerance,lon+tolerance),
                db.between(Location.latitude,lat-tolerance,lat+tolerance),
                Location.housenumber == None
                ))
    else:
        query = Location.query.filter(db.and_(db.between(Location.longitude,lon-tolerance,lon+tolerance),
                db.between(Location.latitude,lat-tolerance,lat+tolerance)
                ))
    for loc in query.all():
        dist = geopy.distance.distance((loc.latitude, loc.longitude),(lat,lon)).meters
        if dist < distance:
            distance = dist
            closest = loc
    return closest,distance

def tell_me_something_I_dont_know():
    """
    It will tell you something from our database - Fun facts for shapefile nerds.
    """
    global neigh_query, streets_query, location_query
    #%% Un po' di print e info
    print("Sestieri: {ses}\nStrade: {str}\nCivici: {civ}".format(
        ses=len(neigh_query.all()),
        str=len(streets_query.all()),
        civ=len(location_query.all())
        ))
    # Gli elementi del db vengono printati secondo quanto definito nella classe al metodo __def__
    rnd_n = random.randint(len(neigh_query.all()))
    rnd_s = random.randint(len(streets_query.all()))
    rnd_l = random.randint(len(location_query.all()))
    print("Il {q} quartiere, la {s} strada e la {l} location del database all'indirizzo:\n{ses}\n{str}\n{loc}".format(
        q=rnd_n, s=rnd_s, l=rnd_l,
        ses=neighbourhoods_query.get(rnd_n),
        str=streets_query.get(rnd_s),
        loc=location_query.get(rnd_l),
        ))
    # Si può facilmente accedere agli elementi di un singolo elemento
    rnd_l2 = random.randint(len(location_query.all()))
    l = location_query.get(rnd_l2)
    print("Informazioni sulla una location che oggi ci piace molto:\nStrada: {str}\nCivico: {civ}\nSestiere: {ses}\nCAP: {cap}\nCoordinate: {lat},{lon}".format(
        str=l.street.name,
        civ=l.housenumber,
        ses=l.neighborhood.name,
        cap=l.neighborhood.zipcode,
        lat=l.latitude,
        lon=l.longitude
        ))
    # I risultati si possono filtrare in due modi
    # 1. filter_by: filtra semplicemente gli attributi di una riga (solo gli attributi diretti non quelli derivati)
    # 2. filter: permette filtri più complicati (ma non ho capito bene come si usa)
    print("Tutte le location che hanno il civico 1:",
        *location_query.filter_by(housenumber=1).all(), sep='\n'
        )
    # Le tabelle si possono unire per filtrare i risultati utilizzando gli attributi derivati
    print("Tutte le strade di San Polo:",
        *streets_query.join(Neighborhood).filter_by(name="SAN POLO").all(), sep='\n'
        )
    print("Il numero 1 di San Polo:",
        *location_query.filter_by(housenumber=1).join(Street).join(Neighborhood).filter_by(name="SAN POLO").all(), sep='\n'
        )
    l = location_query.filter_by(housenumber=1).join(Street).join(Neighborhood).filter_by(name="SAN POLO").first()
    print("Tutte i civici vicini al numero 1 di San Polo:",
        *Location.query.filter(db.and_(
                                db.between(Location.longitude,l.longitude-0.0003,l.longitude+0.0003),
                                db.between(Location.latitude,l.latitude-0.0003,l.latitude+0.0003)
                                )).order_by(Location.housenumber).all(), sep="\n"
        )

    print("Tutte le strade che contengono il nome Rialto:",
        *streets_query.filter(Street.name.contains("RIALTO")).all(), sep="\n")
    print("Tutte le strade che contengono il nome Forno:",
        *streets_query.filter(Street.name.contains("CALLE DEL FORNO")).all(), sep="\n")

    print("\nE dal database è tutto. Linea allo studio.\n")

def check_db():
    """
    A test on the status of the database, to check if everything is ok or fields are empty.
    """
    global neigh_query, streets_query, location_query
    testPassed = True
    print("checking db: ", db)
    #%%
    # CHECK DELLE SHAPES
    #%%
    # CHECK SESTIERI
    print("CHECK SESTIERI")
    print("..generale:")
    hoods = Neighborhood.query.all()
    full_hoods = [hood for hood in hoods if hood.name and hood.shape and hood.zipcode]
    print("{} sestieri:\n{} con tutti i parametri\n{} con parametri mancanti".format(len(hoods), len(full_hoods), len(hoods)-len(full_hoods)))

    print("..nomi:")
    name_hoods = [hood for hood in hoods if hood.name]
    print("{} sestieri:\n{} con nome\n{} senza nome".format(len(hoods), len(name_hoods), len(hoods)-len(name_hoods)))

    print("..shapes:")
    hoods_with_empty_shapes = [hood for hood in hoods if not hood.shape]
    hoods_with_shapes = [hood for hood in hoods if hood.shape]
    hoods_with_polygon = [hood for hood in hoods_with_shapes if hood.shape.geom_type == "Polygon"]
    if len(sys.argv) > 1 and sys.argv[1] == "v":
        print("{} sestieri vuoti: \n{}".format(len(hoods_with_empty_shapes), hoods_with_empty_shapes))
        print("{} sestieri con poligoni: \n{}".format(len(hoods_with_polygon), hoods_with_polygon))
    else:
        print("{} sestieri:\n{} con poligoni\n{} vuoti".format(len(hoods), len(hoods_with_polygon), len(hoods_with_empty_shapes)))
    if len(full_hoods) == len(hoods) and len(hoods_with_empty_shapes) == 0:
        print("TEST - SESTIERI - SUPERATO")
        passedPart1 = True
    else:
        print("TEST - SESTIERI - FALLITO")
        passedPart1 = False
    testPassed = testPassed and passedPart1
    print("-------------")
    #%%
    # CHECK STRADE
    print("STRADE")
    print("..generale:")
    streets_list = Street.query.all()
    full_streets = [street for street in streets_list if street.name and street.shape]
    print("{} strade:\n{} con tutti i parametri\n{} con parametri mancanti".format(len(streets_list), len(full_streets), len(streets_list)-len(full_streets)))

    print("..nomi:")
    name_streets = [street for street in streets_list if street.name]
    print("{} strade:\n{} con il nome\n{} senza nome".format(len(streets_list), len(name_streets), len(streets_list)-len(name_streets)))

    print("..nomi alternativi (opzionale):")
    name_streets = [street for street in streets_list if street.name_alt]
    print("{} strade:\n{} con nome alternativo\n{} senza nome alternativo".format(len(streets_list), len(name_streets), len(streets_list)-len(name_streets)))

    print("..shapes:")
    streets_with_empty_shapes = [street for street in streets_list if not street.shape]
    streets_with_shapes = [street for street in streets_list if street.shape]
    streets_with_polygon = [street for street in streets_with_shapes if street.shape.geom_type == "Polygon"]
    other_streets = [street for street in streets_with_shapes if street.shape and not street.shape.geom_type == "Polygon"]
    if len(sys.argv) > 1 and sys.argv[1] == "v":
        print("{} strade vuote su {}: \n{}".format(len(streets_with_empty_shapes), len(streets_list), streets_with_empty_shapes))
        print("{} strade con poligoni su {}: \n{}".format(len(streets_with_polygon), len(streets_list), streets_with_polygon))
        print("{} strade con altre cose su {}: \n{}".format(len(other_streets), len(streets_list), other_streets))
        print("{}".format([street.shape.geom_type for street in other_streets]))
    else:
        print("{} strade:\n{} con poligoni,\n{} con altre cose (multipoligoni),\n{} vuote".format(len(streets_list), len(streets_with_polygon), len(other_streets), len(streets_with_empty_shapes)))
    if len(streets_list) == len(full_streets) and  len(hoods_with_empty_shapes) == 0:
        print("TEST - STRADE - SUPERATO")
        passedPart2 = True
    else:
        print("TEST - STRADE - FALLITO")
        passedPart2 = False
    testPassed = testPassed and passedPart2
    print("-------------")

    #%%
    # CHECK POI
    print("POI")
    print("..generale:")
    poi_list = Poi.query.all()
    full_pois = [pdi for pdi in poi_list if pdi.location_id]
    print("{} strade:\n{} con la location\n{} senza location".format(len(poi_list), len(full_pois), len(poi_list)-len(full_pois)))

    print("..nomi:")
    name_pois = [pdi for pdi in poi_list if pdi.name]
    print("{} strade:\n{} con il nome\n{} senza nome".format(len(poi_list), len(name_pois), len(poi_list)-len(name_pois)))

    if len(poi_list) == len(full_pois):
        print("TEST - POI - SUPERATO")
        passedPart3 = True
    else:
        print("TEST - POI - FALLITO")
        passedPart3 = False
    testPassed = testPassed and passedPart3
    print("-------------")
    #pois_with_empty_shapes = [cur_poi for cur_poi in poi_list if not cur_poi.shape]
    #pois_with_shapes = [cur_poi for cur_poi in poi_list if cur_poi.shape]
    #pois_with_polygon = [cur_poi for cur_poi in pois_with_shapes if cur_poi.shape.geom_type == "Polygon"]
    #print("{} strade vuote su {}: \n{}".format(len(pois_with_empty_shapes), len(streets_list), pois_with_empty_shapes))
    #print("{} strade con poligoni su {}: \n{}".format(len(pois_with_polygon), len(streets_list), pois_with_polygon))
    #other_pois = [cur_poi for cur_poi in pois_with_shapes if cur_poi.shape and not cur_poi.shape.geom_type == "Polygon"]
    #print("{} strade con altre cose su {}: \n{}".format(len(other_pois), len(streets_list), other_pois))

    if testPassed:
        print("*****************\n* TEST SUPERATO *\n*****************\n")
    else:
        print("*****************\n* TEST  FALLITO *\n*****************\n")
