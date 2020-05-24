from app.src.libpy.mydifflib import get_close_matches_indexes
import numpy as np
import logging
import time

# IMPORT FOR THE DATABASE - db is the database object
from app.models import Neighborhood, Street, Location, Area, Poi
from app import app, db
#Neighborhood.query.all()
from fuzzywuzzy import fuzz, process
"""
da civico, ritorna una coordinata (x,y), che e anche la stringa di accesso a un nodo
"""
def civico2coord(coord_list,civico_name,civico_list, civico_coord):
    coordinate = np.asarray(coord_list)
    # removing one (or more) annoying none values
    #streets_corrected = [street if street else "" for street in streets_list]
    option_number = 3 #rimetto 3 per adesso, poi cambiamo
    matches = get_close_matches_indexes(civico_name.upper(), civico_list, option_number)
    streets_founds = []
    if civico_list[matches[0]] == civico_name.upper():
        which_one = 0
    else:
        for i in range(len(matches)):
            streets_founds.append(civico_list[matches[i]])
            print("Trovato: {}:{}".format(i, streets_founds[i]))
        which_one = int(input("Quale intendi? Scrivi il numero\n"))

    coord = civico_coord[matches[which_one]]
    tmp = np.subtract(np.ones((coordinate.shape)) * coord, coordinate)
    idx = np.argmin(np.sum(tmp * tmp, axis=1))
    return (coordinate[idx][0], coordinate[idx][1])

"""
Cerca nel database
Questo e solo un wrapper che chiama le funzioni, per maggiore leggibilita
"""
def find_address_in_db(input_string):

    print("looking in the db")
    # fetch parameters (puo tornare utile se i parametri saranno modificabili dal browser piu avanti)
    search_parameters = get_parameters()
    # pulisci la stringa col metodo di ale
    clean_string = correct_name(input_string)
    # dividi numero e dicci come e fatta
    text, number, isThereaCivico = dividiEtImpera(clean_string)
    # cerca nel database - qua dentro avviene la magia
    #found_something, actual_address, address_type = find_address(text)
    found_something, actual_address, address_type = fuzzy_exact_search(text)
    # dammi coordinate, del punto o del poligono
    geo_type, coordinates, polygon_shape =  fetch_coordinates(found_something, actual_address, address_type, number, isThereaCivico)

    return geo_type, coordinates, polygon_shape, actual_address


"""
pulisce il nome.
funzione di ale presa da functions.py
"""
def correct_name(name):
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
def fetch_coordinates(found_something, actual_address, address_type, number, isThereaCivico):

    if found_something:
        print("we found", actual_address, type(actual_address))
        # prendi la coordinata relativa

        # controlla i tentativi
        assert(address_type > -1),"tipo di indirizzo negativo! Qualcosa non torna - address_type:" + str(address_type)
        assert(address_type < 3),"tipo di indirizzo troppo grande! Qualcosa non torna! Abbiamo aggiunto un tipo? - address_type:" + str(address_type)
        # SE ABBIAMO UN CIVICO, SCEGLIAMO UN PUNTO!
        if isThereaCivico:
            # geo type = 0 dice che usiamo un punto
            geo_type = 0

            if address_type == 0:
                print("SESTIERE + NUMERO")
                # se e sestiere, prendi sestiere + numero
                actual_location = Location.query.filter_by(housenumber=number).join(Street).join(Neighborhood).filter_by(name=actual_address).first()
            elif address_type == 1:
                print("STRADA + NUMERO")
                # se e strada, prendi strada + numero (+ sestiere?)
                actual_location = Location.query.filter_by(housenumber=number).join(Street).filter_by(name=actual_address).join(Neighborhood).first()
            elif address_type == 2:
                print("POI + NUMERO")
                # poi!
                actual_location = Location.query.filter_by(housenumber=number).join(Poi).filter_by(name=actual_address).join(Neighborhood).first()

            # qualunque cosa abbiamo trovato, actual_location e un punto in questo caso!
            coords = [actual_location.longitude, actual_location.latitude]
            polygon_shape_as_list = None
        else:
            #geo type = 1 dice che usiamo un poligono
            geo_type = 1

            if address_type == 0:
                print("SESTIERE senza NUMERO")
                # se e sestiere, prendi sestiere + numero
                actual_location = Neighborhood.query.filter_by(name=actual_address).first()
            elif address_type == 1:
                print("STRADA senza NUMERO")
                # se e strada, prendi strada + numero (+ sestiere?)
                actual_location = Street.query.filter_by(name=actual_address).first()
            elif address_type == 2:
                print("POI senza NUMERO")
                # poi!
                actual_location = Poi.query.filter_by(name=actual_address).first()

            # prendiamo la shape!
            if actual_location.shape:
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
                            polygon_shape_as_list.append([ys[i], xs[i]])
                elif polygon_shape.geom_type == 'Polygon':
                    # do polygon things.
                    xs, ys = polygon_shape.exterior.coords.xy
                    polygon_shape_as_list = [[ys[i],xs[i]] for i in range(len(xs))]
                else:
                    raise IOError('Shape is not a polygon.')
                # coords va creato in modo che sia subscriptable
                coords = getCentroidSmartly(polygon_shape)
                #print("Polygon shape {}, coordinates {}".format(polygon_shape, coords))
            else:
                coords = [-1, -1]
                geo_type = -1
                polygon_shape_as_list = None

    else:
        coords = [-1, -1]
        geo_type = -1
        polygon_shape_as_list = None

    return geo_type, coords, polygon_shape_as_list

"""
da gestire piu poligoni, piu centroidi, multipoligoni e alieni
"""
def getCentroidSmartly(polygon_shape):

    avg_coordinate = [polygon_shape.centroid.x, polygon_shape.centroid.y]

    # coord_x = 0
    # coord_y = 0
    # number_of_centroids = 0
    # for cur_centroid in polygon_shape.centroid:
    #     coord_x += cur_centroid.x
    #     coord_y += cur_centroid.y
    #     number_of_centroids += 1
    #
    # coord_x /= number_of_centroids
    # coord_y /= number_of_centroids
    # avg_coordinate = [coord_x, coord_y]
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
        found_number = isThereaCivico.group(0)
        # formatta il numero nel format in cui è salvato nel database
        numero_cifra = re.findall(r'\d+',found_number)
        numero_lettera = re.findall(r'[A-z]',found_number)
        if numero_lettera:
            number += '/' + numero_lettera[0]
        else:
            number = numero_cifra[0]
        text = clean_string[:isThereaCivico.start()] + clean_string[isThereaCivico.end():]
        text = text.strip() # elimina spazi che possono essersi creati togliendo il numero
    else:
        text = clean_string
        number = -1

    return text, number, isThereaCivico

"""
La stringa e pulita, ricerca nel DATABASE
 1. cerca nei sestieri
 2. cerca nelle Strade
 3. cerca nei poi
"""
def find_address(text):

    # chi cerca trova
    attempt = 0 # contatore
    found_the_treasure = False
    while not found_the_treasure and attempt < 3:
        # la funzione di ricerca usa attempt come contatore - address_type e anche attempt verra usato uguale
        found_the_treasure, actual_address, address_type = search_and_search_and_search(text, attempt)
        if not found_the_treasure:
            attempt += 1

    # se non abbiamo trovato nulla, pazienza
    if not found_the_treasure:
        return found_the_treasure, "", -1

    # se no, ritorniamo
    # address_type e attempt alla fine, quindi 0: sestiere, 1: strada, 2: poi
    return found_the_treasure, str(actual_address), address_type

"""
In questa funzione andiamo veramente ad accedere al database:
attempt == 0 --> Sestieri
attempt == 1 --> Strade
attempt == 2 --> POI
attempt < 0 or attempt > 2 --> ERRORE
"""
def search_and_search_and_search(text, attempt):

    # controlla i tentativi
    assert(attempt > -1),"tentativo negativo? - attempt:" + str(attempt)
    assert(attempt < 3),"troppi tentativi! Errore nel ciclo while sopra! - attempt:" + str(attempt)
    # delega
    if attempt == 0:
        found_something, actual_address = bad_neighbourhoods(text)
    if attempt == 1:
        found_something, actual_address = is_she_living_in_the_streets(text)
    if attempt == 2:
        found_something, actual_address = is_she_at_the_coffee_place(text)

    return found_something, actual_address, attempt

"""
versione super semplice
solo controlla se matcha 1 a 1 un nome di un sestiere
"""
def bad_neighbourhoods(text):

    #neighborhoods = Neighborhood.query.all()
    matching=Neighborhood.query.filter(Neighborhood.name.contains(text)).all()
    #matching = [hood for hood in neighborhoods if text in (hood.name)]
    if matching:
        return True, matching[0]
    return False, ""

"""
versione super semplice
solo controlla se matcha 1 a 1 un nome di una strada
"""
def is_she_living_in_the_streets(text):

    matching = Street.query.filter(Street.name.contains(text)).all()
    if matching:
        return True, matching[0]

    return False, ""

"""
versione super semplice
solo controlla se matcha 1 a 1 un nome di un POI
"""
def is_she_at_the_coffee_place(text):

    matching = poi.query.filter(poi.name.contains(text)).all()
    if matching:
        return True, matching[0]

    return False, ""

"""
Sostituisce find_address.
Troviamo la corrispondenza con fuzzy, estraggo l'indice, per poter estrarre il match e la provenienza
"""
def takeSecond(elem):
    return elem[1]
def fuzzy_exact_search(word):
    found,exact_match,exact_type = fuzzy_search(word)
    return found,str(exact_match[0]),int(exact_type[0])

def fuzzy_search(word):
    n_limit = 5
    score_cutoff = 50
    final_matches = []
    matches_neigh = process.extractBests(word,Neighborhood.query.all(),score_cutoff=score_cutoff,limit=n_limit)
    for m,s in matches_neigh:
        final_matches.append((m,s,0))
    if not any([match[1]>98 for match in final_matches]):
        matches_street = process.extractBests(word,Street.query.all(),score_cutoff=score_cutoff,limit=n_limit)
        for m,s in matches_street:
            final_matches.append((m,s,1))
    if not any([match[1]>98 for match in final_matches]):
        matches_poi = process.extractBests(word,Poi.query.all(),score_cutoff=score_cutoff,limit=n_limit)
        for m,s in matches_poi:
            final_matches.append((m,s,2))
    final_matches.sort(key=takeSecond, reverse=True)
    print("match,score,type", final_matches)
    return bool(final_matches), [match[0] for match in final_matches[0:n_limit]], [match[2] for match in final_matches[0:n_limit]]

# finto, per ora non serve a nulla
# teoricamente puo essere utile, ma magari anche no
def get_parameters():

    cutoff = 0.6
    max_result = 5
    return [cutoff, max_result]

"""
Cerca la coordinata e la ritorna insieme al suo nome.

Ha 3 parametri obbligatori e uno opzionale.
Se gli viene data la lista di coordinate del grafo, cerca anch il nodo piu vicino
e ritorna quelle coordinate. Altrimenti ritorna il nome e le coordinate esatte
dallo shapefile


@param:
    - civico_name: il nome da trovare tra quelli in civico_list
    - civico_list: lista dei civici DALLO SHAPEFILE
    - civico_coord: le coordinate dei civici relativi alla lista civico_list SHAPEFILE
    - coord_list: lista di coordinate DEI NODI DEL GRAFO (opzionale)

@return:
    - coordinata: tupla (x,y) - relativa alle coordinate del GRAFO
    - nome scelto - relativo alla lista dei civici ottenuta dallo SHAPEFILE
"""
def civico2coord_find_address(civico_name, civico_list, civico_coord, coord_list=None):

    # solo il match migliore!
    option_number = 1 #rimetto 3 per adesso, poi cambiamo
    # trova il nome piu vicino
    matches = get_close_matches_indexes(civico_name.upper(), civico_list, option_number)
    logging.info("c2c: Trovato all'indice {ind}".format(ind=matches))
    # estrae la sua coordinata
    #if not matches:
    #    indice_lista_civico = 0
    #elif matches[0] < 0 or matches[0] > len(civico_coord):
    #    indice_lista_civico = 0
    #else:
    #    indice_lista_civico = matches[0]
    if matches < 0:
        indice_lista_civico = 0
    else:
        indice_lista_civico = matches
    coord = civico_coord[indice_lista_civico]
    # nome del civico/toponimo piu vicino
    name_chosen = civico_list[indice_lista_civico]
    if coord_list==None:
        return (coord[0], coord[1]), name_chosen[:-1]
    else:
        # numpy array delle coordinate
        coordinate = np.asarray(coord_list)
        tmp = np.subtract(np.ones((coordinate.shape)) * coord, coordinate)
        # indice del nodo piu vicino
        idx = np.argmin(np.sum(tmp * tmp, axis=1))
        return (coordinate[idx][0], coordinate[idx][1]), name_chosen[:-1]


"""
AL MOMENTO NON VIENE UTILIZZATO

Cerca la coordinata e ritorna senza nessuna interazione:
Piu in dettaglio,
1 - cerchiamo il civico nella lista,
2 - estraiamo la sua coordinata,
3 - cerchiamo il nodo piu vicino NEL GRAFO
4 - ritorniamo le sue coordinate

@param:
    - coord_list: lista di coordinate DEI NODI DEL GRAFO
    - civico_name: il nome da trovare tra quelli in civico_list
    - civico_list: lista dei civici DALLO SHAPEFILE
    - civico_coord: le coordinate dei civici relativi alla lista civico_list SHAPEFILE

@return:
    - coordinata: tupla (x,y) - relativa alle coordinate del GRAFO
    - nome scelto - relativo alla lista dei civici ottenuta dallo SHAPEFILE
"""
def civico2coord_first_result(coord_list, civico_name, civico_list, civico_coord):

    # numpy array delle coordinate
    coordinate = np.asarray(coord_list)
    # solo il match migliore!
    option_number = 1 #rimetto 3 per adesso, poi cambiamo
    # trova il nome piu vicino
    t1=time.perf_counter()
    matches = get_close_matches_indexes(civico_name.upper(), civico_list, option_number)
    t11 = time.perf_counter() - t1
    logging.info('c2c: ci ho messo {tot} a trovare il match'.format(tot=time.perf_counter() - t1))
    # estrae la sua coordinata
    if not matches:
        indice_lista_civico = 0
    elif matches[0] < 0 or matches[0] > len(civico_coord):
        indice_lista_civico = 0
    else:
        indice_lista_civico = matches[0]
    coord = civico_coord[indice_lista_civico]
    # nome del civico/toponimo piu vicino
    name_chosen = civico_list[indice_lista_civico]
    # cerca il nodo piu vicino
    t2 = time.perf_counter()
    tmp = np.subtract(np.ones((coordinate.shape)) * coord, coordinate)
    t21 = time.perf_counter() - t2
    logging.info('c2c: ci ho messo {tot} a trovare il risultato piu vicino'.format(tot=time.perf_counter() - t2))
    t3 = time.perf_counter()
    # indice del nodo piu vicino
    idx = np.argmin(np.sum(tmp * tmp, axis=1))
    t31 = time.perf_counter() - t3
    logging.info('c2c: ci ho messo {tot} trovare l indice'.format(tot=time.perf_counter() - t3))

    return (coordinate[idx][0], coordinate[idx][1]), name_chosen[:-1], (t11, t21, t31)
