from app.src.libpy.mydifflib import get_close_matches_indexes
import numpy as np
import logging
import time

# IMPORT FOR THE DATABASE - db is the database object
from app.models import Neighborhood, Street, Location, Area, Poi
from app import app, db
#Neighborhood.query.all()
from fuzzywuzzy import fuzz, process

def find_address_in_db(input_string):
    """
    Wrapper functions that looks for an address in the database.
    """
    print("looking in the db")
    # pulisci la stringa col metodo di ale
    clean_string = correct_name(input_string)
    # dividi numero e dicci come e fatta
    text, number, isThereaCivico = dividiEtImpera(clean_string)
    # cerca nel database - qua dentro avviene la magia
    #found_something, actual_address, address_type = find_address(text)
    address_list, score_list, exact = fuzzy_search(text, isThereaCivico)
    print(address_list, score_list)
    result_dict = []
    # dammi coordinate, del punto o del poligono
    if not address_list:
        coords = [-1, -1]
        geo_type = -1
        polygon_shape_as_list = None
    else:
        for i,address in enumerate(address_list):
            print(address)
            geo_type, coordinates, polygon_shape = fetch_coordinates(address, number, isThereaCivico)
            if not geo_type<0:
                nome=str(address)+ " " + str(number)
            else:
                nome=str(address)
            result_dict.append({"nome":nome,
                        "coordinate":coordinates,
                        "shape":polygon_shape,
                        "geotype":geo_type,
                        "score":score_list[i],
                        "exact":exact})
        result_dict=sort_results(result_dict)
        print(result_dict)
    return result_dict


def correct_name(name):
    """
    Clean and correct the input name.
    """
    # prende la stringa in ingresso e fa delle sostituzioni
    # 0. Eliminare spazi iniziali e finali
    name = name.strip()
    # 1. Sostituzione s.->san
    name = name.replace("s.","san ")
    # 2. Rimozione doppi spazi
    name = name.replace("  "," ")
    # Ritorna stringa corretta
    return name.upper()

"""
la parte finale. Siamo sicuri che tutto funziona, solo prendiamo le coordinate
"""
def fetch_coordinates(actual_location, number, isThereaCivico):

    # SE ABBIAMO UN CIVICO, SCEGLIAMO UN PUNTO!
    if isThereaCivico:
#         # geo type = 0 dice che usiamo un punto
        geo_type = 0
        with_num=actual_location.locations.filter_by(housenumber=number).first()
        #if not with_num:
        #    with_num=Location.query.filter_by(housenumber=number).join(Street).filter_by(name=str(actual_location)).first()
        if with_num:
            actual_location=with_num
            coords = [actual_location.longitude, actual_location.latitude]
            polygon_shape_as_list = [coo for coo in actual_location.shape.coords]
        else:
            # in questo caso l'errore per l'utente è lo stesso se - non abbiamo trovato niente, -abbiamo trovato la strada ma l'indirizzo non è dentro - la strada/sestiere non ha una shape (questo caso si può eliminare se il database è consistente)
            coords = [-1, -1]
            geo_type = -2
            polygon_shape_as_list = None
    # SE NON ABBIAMO UN CIVICO, FORSE E' UN POI! in quel caso estraiamo il punto
    elif type(actual_location)==Poi:
        geo_type = 0
        coords = [actual_location.location.longitude,actual_location.location.latitude]
        try:
            polygon_shape_as_list = [coo for coo in actual_location.location.shape.coords]
        except:
            polygon_shape_as_list = None
    # SE NON ABBIAMO UN CIVICO, E' UNA STRADA O UN SESTIERE! in quel caso estraiamo la shape e un punto rappresentativo
    elif actual_location.shape:
        geo_type = 1
        polygon_shape = actual_location.shape
        if polygon_shape.geom_type == 'MultiPolygon':
            # do multipolygon things.
            polygon_shape_as_list = []
            # loop su ogni poligono
            for single_polygon in polygon_shape:
                # poligono
                xs, ys = single_polygon.exterior.coords.xy
                # for loop questa volta per evitare una lista di liste -- vogliamo una lista sola
                for i in range(len(xs)):
                    polygon_shape_as_list.append([xs[i], ys[i]])
        elif polygon_shape.geom_type == 'Polygon':
            # do polygon things.
            xs, ys = polygon_shape.exterior.coords.xy
            polygon_shape_as_list = [[xs[i],ys[i]] for i in range(len(xs))]
        else:
            raise IOError('Shape is not a polygon.')
        # coords va creato in modo che sia subscriptable
        coords = getCentroidSmartly(polygon_shape) # polygon_shape potreebbe esser un multipoligono!
        #print("Polygon shape {}, coordinates {}".format(polygon_shape, coords))
    else:
        # in teoria questo caso non esiste per consistenza del db, lo lasciamo solo temporanemente con un print
        print("ERRORE ASSURDO: l'oggetto trovato non è un indirizzo, non è un poi, e se è una strada o sestiere non ha geometria!", actual_location)
        coords = [-1, -1]
        geo_type = -1
        polygon_shape_as_list = None

#    print("print del fetch, geo_type, coords, polygon_shape_as_list)
    return geo_type, coords, polygon_shape_as_list

"""
da gestire piu poligoni, piu centroidi, multipoligoni e alieni
"""
def getCentroidSmartly(polygon_shape):
    #avg_coordinate = [polygon_shape.centroid.x, polygon_shape.centroid.y]
    avg_coordinate = [polygon_shape.representative_point().x, polygon_shape.representative_point().y]
    print("Centroide: ", avg_coordinate)
    return avg_coordinate

"""
parte di una funzione di Ale presa dal codice dentro searchName in functions.py (riga 125 in questo momento).
Divide testo e numero e ritorna se effettivamente c'era un numero
"""
def dividiEtImpera(clean_string):

    # regular expressions
    import re
    # format del civico:
    # 1. inizia con un numero (es. "2054 santa marta")
    # 2. finisce con un numero (es. "san polo 1424")
    # 3. finisce con un numero e una lettera (es. "santa croce 1062b" oppure "1062 b" oppure "1062/b")
    # nb se il numero è seguito da una lettera ed è all'inizio del nome, la lettera viene riconosciuta solo se seguita da uno spazio
    format_civico = re.compile("(^\d+([ |/]?\w )?)|(\d+[ |/]?\w?$)")
    isThereaCivico = format_civico.search(clean_string)
    if isThereaCivico:
        # un po di caos qui
        number = isThereaCivico.group(0)
        # formatta il numero nel format in cui è salvato nel database
        numero_cifra = re.findall(r'\d+',number)
        numero_lettera = re.findall(r'[A-z]',number)
        if numero_lettera:
            number += '/' + numero_lettera[0]
        else:
            number = numero_cifra[0]
        text = clean_string[:isThereaCivico.start()] + clean_string[isThereaCivico.end():]
        text = text.strip() # elimina spazi che possono essersi creati togliendo il numero
    else:
        text = clean_string
        number = ""

    return text, number, isThereaCivico

# qua aggiungere magheggi per ordinare i risultati come vogliamo!
def sort_results(res_list):
    """
    Sorts the results list to give as a first choice, not the best score matching, but something better. For the moment I put as last, the results with a negative geometry.
    """
    new_res_list=[]
    wrong_list=[]
    for res in res_list:
        if res["geotype"]<0:
            wrong_list.append(res)
        else:
            new_res_list.append(res)
    new_res_list=new_res_list+wrong_list
    return new_res_list

"""
Sostituisce find_address.
Troviamo la corrispondenza con fuzzy, estraggo l'indice, per poter estrarre il match e la provenienza
"""
def fuzzy_search(word, isThereaCivico):
    exact = False
    # massimo numero di risultati
    n_limit = 15
    # non ritorna risultati minori di cutoff
    score_cutoff = 50
    # siamo certi! serve per stoppare la ricerca prima per evitare di cercare per nulla
    quasi_cento = 98
    final_matches = []
    # FORSE: facciamo un metodo qua che evita di avere mille righe uguali?
    # se ce un civico, vogliamo guardare prima in Neighborhood e poi in Street
    if isThereaCivico:
        matches_neigh = process.extractBests(word,Neighborhood.query.all(),score_cutoff=score_cutoff,limit=n_limit)
        for m,s in matches_neigh:
            final_matches.append((m,s,0))
        # stoppiamo se abbiamo trovato un match perfetto
        if not any([match[1]>quasi_cento for match in final_matches]):
            matches_street = process.extractBests(word,Street.query.all(),score_cutoff=score_cutoff,limit=n_limit)
            for m,s in matches_street:
                final_matches.append((m,s))
    # se non ce un civico, vogliamo guardare prima nei poi, poi in Street, poi nei Sestieri
    else:
        # andrà implementata qui la ricerca nei poi, che fa un check delle corssipondenze con le keyword e fa la query invece di Poi.query.all() filtrando sui types di poi
        matches_poi = process.extractBests(word,Poi.query.all(),score_cutoff=score_cutoff,limit=n_limit)
        for m,s in matches_poi:
            final_matches.append((m,s))
        if not any([match[1]>quasi_cento for match in final_matches]):
            matches_street = process.extractBests(word,Street.query.all(),score_cutoff=score_cutoff,limit=n_limit)
            for m,s in matches_street:
                final_matches.append((m,s))
        if not any([match[1]>quasi_cento for match in final_matches]):
            matches_neigh = process.extractBests(word,Neighborhood.query.all(),score_cutoff=score_cutoff,limit=n_limit)
            for m,s in matches_neigh:
                final_matches.append((m,s))
    # lambda e usato per definire una funzione che prende il secondo elemento
    final_matches.sort(key=lambda x:x[1], reverse=True)
    if any([match[1]>quasi_cento for match in final_matches]):
        exact=True
        final_matches=[match for match in final_matches if match[1]>quasi_cento]
    # se i risultati sono esatti non voglio escludere nessuna soluzione!
    if not exact:
        final_matches = final_matches[:5]

    return [match[0] for match in final_matches], [match[1] for match in final_matches], exact
