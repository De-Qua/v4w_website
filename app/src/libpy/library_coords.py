from app.src.libpy.mydifflib import get_close_matches_indexes
import numpy as np
import logging
import time

# IMPORT FOR THE DATABASE - db is the database object
from app.models import Neighborhood, Street, Location, Area, Poi
from app import app, db
#Neighborhood.query.all()

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
    found_something, actual_address, address_type = find_address(text)
    if found_something:
        print("we found", actual_address)
        # prendi la coordinata relativa
        coordinates = fetch_coordinates(actual_address, address_type, number, isThereaCivico)
    else:
        coordinates = [-1, -1]

    return coordinates, actual_address


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
def fetch_coordinates(actual_address, address_type, number, isThereaCivico):

    if isThereaCivico:
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
            actual_location = Location.query.filter_by(housenumber=number).join(Pois).filter_by(name=actual_address).join(Neighborhood).first()
    else:
        if address_type == 0:
            print("SESTIERE senza NUMERO")
            # se e sestiere, prendi sestiere + numero
            actual_location = Location.query.join(Street).join(Neighborhood).filter_by(name=actual_address).first()
        elif address_type == 1:
            print("STRADA senza NUMERO")
            # se e strada, prendi strada + numero (+ sestiere?)
            actual_location = Location.query.join(Street).filter_by(name=actual_address).join(Neighborhood).first()
        elif address_type == 2:
            print("POI senza NUMERO")
            # poi!
            actual_location = Location.query.join(Pois).filter_by(name=actual_address).join(Neighborhood).first()

    coords = [actual_location.longitude, actual_location.latitude]
    return coords

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

    neighborhoods = Neighborhood.query.all()
    matching = [hood for hood in neighborhoods if text in (hood.name)]
    if matching:
        return True, matching[0]

    return False, ""

"""
versione super semplice
solo controlla se matcha 1 a 1 un nome di una strada
"""
def is_she_living_in_the_streets(text):

    streets = Street.query.all()
    matching = [street for street in streets if (text in (street.name))] #or text in street.name_alt --> per ora name_alt e null
    if matching:
        return True, matching[0]

    return False, ""

"""
versione super semplice
solo controlla se matcha 1 a 1 un nome di un POI
"""
def is_she_at_the_coffee_place(text):

    POIs = Poi.query.all()
    matching = [pdi for pdi in POIs if text in pdi]
    if matching:
        return True, matching[0]

    return False, ""


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
