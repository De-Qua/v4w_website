"""
All the functions related to searching in the database for addresses, words, streets, path, places or whatever else you may look for.
"""
import numpy as np
import logging
import time
import shapely, shapely.wkt, shapely.geometry
import pdb

# IMPORT FOR THE DATABASE - db is the database object
from app.models import Neighborhood, Street, Location, Area, Poi, PoiCategoryType, poi_types, PoiCategory
from app import app, db
from fuzzywuzzy import fuzz, process
import fuzzywuzzy
from shapely.geometry import mapping
from shapely.ops import transform
from sqlalchemy import and_

# IMPORT OUR LIBRARIES
from app.src.libpy import lib_graph, lib_communication, lib_database

def find_POI(N, coordinates, searchPoiCategory="", searchPoiCategoryType="", maxNumOfAttempts=10, searchTimeOut=2):
    """
    Finds at least N Pois of the given type close to the coordinate. Additional parameters control the stop criteria.
    coordinates: (longitude, latitude)
    """
    finished = False
    tooManyAttempt = False
    foundEnough = False
    timeOutReached = False
    app.logger.debug("Looking for at least {} POI of type {} ({}) close to {}".format(N, searchPoiCategory, searchPoiCategoryType, coordinates))
    proximity = np.asarray([0.0001, 0.0001])
    step = np.asarray([0.0005, 0.0005])
    app.logger.debug("Using a simple step strategy, increasing proximity by {} at each step".format(step))
    attCnt = 0
    c_latitude = coordinates[1]
    c_longitude = coordinates[0]
    timeStart = time.time()
    # define query
    query = Poi.query.join(poi_types).join(PoiCategoryType)
    if searchPoiCategoryType:
        app.logger.debug("we use poi category type")
        query = query.filter_by(name=searchPoiCategoryType)
    query = query.join(PoiCategory)
    if searchPoiCategory:
        app.logger.debug("we use poi category")
        query = query.filter_by(name=searchPoiCategory)
    # loop
    while not finished:
        #POI = Poi.query.join(poi_types).join(PoiCategoryType).filter_by(name=searchPoiCategoryType).join(PoiCategory).filter_by(name=searchPoiCategory).join(Location).filter(and_(db.between(Location.longitude,c_longitude-proximity[0],c_longitude+proximity[0]),db.between(Location.latitude,c_latitude-proximity[1],c_latitude+proximity[1]))).all()
        current_query = query.join(Location).filter(and_(db.between(Location.longitude,c_longitude-proximity[0],c_longitude+proximity[0]),db.between(Location.latitude,c_latitude-proximity[1],c_latitude+proximity[1])))
        app.logger.debug('raggio in cui sto cercando: (longitude, latitude)\n {},{},{},{}'.format(c_longitude-proximity[0],c_longitude+proximity[0],c_latitude-proximity[1],c_latitude+proximity[1]))
        #app.logger.debug('query trovata {}'.format(current_query))
        POI = current_query.all()
        app.logger.debug('POI trovati {}'.format(POI))
        if len(POI) < N:
            app.logger.debug("we found only {} POIs, we increase proximity".format(len(POI)))
            proximity += step
        else:
            foundEnough = True
        attCnt += 1
        if attCnt > maxNumOfAttempts:
            app.logger.debug("tried enough ({} times, maximum was set to {}), time to stop..".format(attCnt, maxNumOfAttempts))
            tooManyAttempt = True
        cur_time = time.time() - timeStart
        if (cur_time) > searchTimeOut:
            app.logger.debug("timeout reached ({} passed, timeOut set to {}), time to stop..".format(cur_time, searchTimeOut))
            timeOutReached = True
        finished = foundEnough or tooManyAttempt or timeOutReached


    if len(POI) < 1:
        # bruteforce
        POI = query.join(Location).all()
        foundEnough = True
        app.logger.warning("we could not find close POIs, we just take them all! they are {}. Check out if this should happen!".format(len(POI)))

    #pdb.set_trace()
    if foundEnough:
        coordinates_as_shapely_points = [shapely.geometry.Point(_poi.location.latitude, _poi.location.longitude) for _poi in POI]
        distance_list = [poi_point.distance(shapely.geometry.Point(coordinates)) for poi_point in coordinates_as_shapely_points]
        # ordino la lista basata sulle distanze
        # --> https://stackoverflow.com/questions/6618515/sorting-list-based-on-values-from-another-list
        ordered_POIS = [x for _,x in sorted(zip(distance_list, POI), key=lambda pair: pair[0])]
        bestPOIS = ordered_POIS[:N]
    else:
        bestPOIS = POI

    app.logger.info("Tried {} times, it took {} seconds and we found {} POIs, then we selected the {} best!".format(attCnt, time.time()-timeStart, len(POI), N))
    return bestPOIS, len(bestPOIS)



def find_closest_edge(list_of_node_coordinates, graph):
    """
    Return the two nodes that belongs to the closes edge in the graph.
    """
    outcome_list = []
    for node_coordinates in list_of_node_coordinates:
        edges = [edge for edge in graph.edges]
        shapely_canali = [shapely.wkt.loads(graph[cur_edge[0]][cur_edge[1]]['Wkt']) for cur_edge in edges]
        shape_riva = shapely.geometry.Point([node_coordinates[0], node_coordinates[1]])
        distances_riva_canale = [shape_riva.distance(canale) for canale in shapely_canali]
        distanza_piu_corta_index = np.argmin(distances_riva_canale)
        assert (len(distances_riva_canale) == len(edges))
        start_node, end_node = edges[distanza_piu_corta_index]
        start_dist = shape_riva.distance(shapely.geometry.Point([start_node[0], start_node[1]]))
        end_dist = shape_riva.distance(shapely.geometry.Point([end_node[0], end_node[1]]))
        dict_for_a_node = {}
        dict_for_a_node["first_node"] = start_node
        dict_for_a_node["second_node"] = end_node
        dict_for_a_node["first_dist"] = start_dist
        dict_for_a_node["second_dist"] = end_dist
        outcome_list.append(dict_for_a_node)

    app.logger.info("Created list with the {} dictionary of edges!".format(len(outcome_list)))
    app.logger.debug("Full List:\n {}".format(outcome_list))

    return outcome_list


def find_closest_nodes(dict_list,G_array):
    """
    Returns list of nodes in G_array closest to coordinate_list (euclidean distance).
    """
    coord_beg_end=[]
    for d in dict_list:
        if d.get("geotype")==0 and d.get("shape"):
            coord_beg_end.append(d.get("shape")[0])
            #print("node start",d.get("shape")[0])
        else:
            coord_beg_end.append(d.get("coordinate"))
    nodes_list=[]
    for coordinate in coord_beg_end:
        #print(coordinate)
        tmp = np.subtract(np.ones(G_array.shape) * coordinate, G_array)
        # indice del nodo piu vicino
        idx = np.argmin(np.sum(tmp * tmp, axis=1))
        #print("distance to node", tmp[idx]**2)
        #print("node grafo",(G_array[idx][0], G_array[idx][1] ))
        nodes_list.append((G_array[idx][0], G_array[idx][1]))

    return nodes_list


def find_path_to_closest_riva(G_un, coords_start, rive_list):
    """
    It finds the path to the closest riva with respect to the starting coordinates. It prepares the geojson and returns the chosen riva.
    """
    length_paths=[]
    paths=[]
    for riva in rive_list:
        path, length = lib_graph.calculate_path_wkt(G_un, coords_start, riva, flag_ponti=True)
#        print("percorso calcolato per questa riva: ", bool(path) )
        if path:
            length_paths.append(length)
            paths.append(path)

    # qua abbiamo la lista delle strade
    app.logger.debug("quanto sono lunghe le strade? {}".format(length_paths))
    np_lengths = np.asarray(length_paths)
    idx_shortest_path = np.argmin(np_lengths)
    shortest_path = paths[idx_shortest_path]
    chosen_riva = shortest_path[-1]
    app.logger.debug("la piu corta e la strada con indice {} e il punto d'arrivo e' {}".format(idx_shortest_path,chosen_riva))
    app.logger.debug("ora ricalcolo per il dizionario con le info")
    path_info = lib_graph.give_me_the_street(G_un, coords_start, chosen_riva, flag_ponti=True)

    # la riva sara l'ultimo nodo della strada
    # closest_riva = shortest_path[-1]
    return path_info, chosen_riva


def add_from_strada_to_porta(path, da, a):
    """
    It adds address linestring to connect doors with streets.
    """
    path['shape_list'].insert(0,da['geojson'])
    path['shape_list'].append(a['geojson'])
    return path


def find_address_in_db(input_string):
    """
    Wrapper functions that looks for an address in the database.
    """
    app.logger.info("looking in the db")
    # fetch parameters (puo tornare utile se i parametri saranno modificabili dal browser piu avanti)
    search_parameters = get_parameters()
    # pulisci la stringa col metodo di ale
    clean_string = correct_name(input_string)
    # dividi numero e dicci come e fatta
    text, number, isThereaCivico = dividiEtImpera(clean_string)
    # cerca nel database - qua dentro avviene la magia
    #found_something, actual_address, address_type = find_address(text)
    address_list, score_list, exact = fuzzy_search(text, isThereaCivico)
    app.logger.debug("Lista {}, scores {}".format(address_list, score_list))
    result_dict = []
    # dammi coordinate, del punto o del poligono
    if not address_list:
        app.logger.warning("Non abbiamo trovato nulla!")
        coords = [-1, -1]
        geo_type = -1
        polygon_shape_as_list = None
    else:
        for i,address in enumerate(address_list):
            geo_type, coordinates, polygon_shape, shape = fetch_coordinates(address, number, isThereaCivico)
            if not geo_type<0:
                nome=str(address)+ " " + str(number)
            else:
                nome=str(address)

            # INCREDIBILE: stampando il geojson non serve invertire le coordinate!
            # inverti x e y nella shape, è più facile farlo ora piuttosto che dopo
            # shape = transform(lambda x,y:(y,x), shape)
            edge_info_dict = {}
            edge_info_dict['street_type'] = 'calle'
            edge_info_dict['bridge'] = 0
            geojson = {
                "type": "Feature",
                "properties": edge_info_dict,
                "geometry": dict(mapping(shape))
            }
            result_dict.append({"nome":nome,
                        "coordinate":coordinates,
                        "shape":polygon_shape,
                        "geotype":geo_type,
                        "score":score_list[i],
                        "exact":exact,
                        "geojson":geojson
                        })


        result_dict=sort_results(result_dict)
        app.logger.debug(result_dict)
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
            shape = actual_location.shape
            polygon_shape_as_list = [coo for coo in actual_location.shape.coords]
        else:
            # in questo caso l'errore per l'utente è lo stesso se - non abbiamo trovato niente, -abbiamo trovato la strada ma l'indirizzo non è dentro - la strada/sestiere non ha una shape (questo caso si può eliminare se il database è consistente)
            coords = [-1, -1]
            geo_type = -2
            polygon_shape_as_list = None
            shape=None
    # SE NON ABBIAMO UN CIVICO, FORSE E' UN POI! in quel caso estraiamo il punto
    elif type(actual_location)==Poi:
        geo_type = 0
        coords = [actual_location.location.longitude,actual_location.location.latitude]
        try:
            polygon_shape_as_list = [coo for coo in actual_location.location.shape.coords]
            shape = actual_location.location.shape
        except:
            polygon_shape_as_list = None
            shape = None
    # SE NON ABBIAMO UN CIVICO, E' UNA STRADA O UN SESTIERE! in quel caso estraiamo la shape e un punto rappresentativo
    elif actual_location.shape:
        shape = actual_location.shape
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
        app.logger.info("ERRORE ASSURDO: l'oggetto trovato non è un indirizzo, non è un poi, e se è una strada o sestiere non ha geometria!", actual_location)
        coords = [-1, -1]
        geo_type = -1
        polygon_shape_as_list = None
        shape = None

    print("print del fetch", geo_type, coords, shape)
    return geo_type, coords, polygon_shape_as_list, shape

"""
da gestire piu poligoni, piu centroidi, multipoligoni e alieni
"""
def getCentroidSmartly(polygon_shape):
    #avg_coordinate = [polygon_shape.centroid.x, polygon_shape.centroid.y]
    avg_coordinate = [polygon_shape.representative_point().x, polygon_shape.representative_point().y]
    app.logger.debug("Centroide: ", avg_coordinate)
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
            number = numero_cifra[0] + '/' + numero_lettera[0]
        else:
            number = numero_cifra[0]
        text = clean_string[:isThereaCivico.start()] + clean_string[isThereaCivico.end():]
        text = text.strip() # elimina spazi che possono essersi creati togliendo il numero
    else:
        text = clean_string
        number = ""

    return text, number, isThereaCivico


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


def takeSecond(elem):
    return elem[1]


def fuzzy_search(word, isThereaCivico,scorer=fuzz.token_sort_ratio,processor=fuzzywuzzy.utils.full_process):
    """
    Search the input string using the fuzzy library, returns the best matches.

    Troviamo la corrispondenza con fuzzy, estraggo l'indice, per poter estrarre il match e la provenienza
    """
    exact = False
    n_limit = 15
    score_cutoff = 50
    final_matches = []
    if isThereaCivico:
        matches_neigh = process.extractBests(word,Neighborhood.query.all(),scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
        for m,s in matches_neigh:
            final_matches.append((m,s,0))
        if not any([match[1]>98 for match in final_matches]):
            matches_street = process.extractBests(word,Street.query.all(),scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
            for m,s in matches_street:
                final_matches.append((m,s))
    else:
        # andrà implementata qui la ricerca nei poi, che fa un check delle corssipondenze con le keyword e fa la query invece di Poi.query.all() filtrando sui types di poi
        matches_street = process.extractBests(word,Street.query.all(),scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
        for m,s in matches_street:
            final_matches.append((m,s))
        if not any([match[1]>98 for match in final_matches]):
            matches_poi = process.extractBests(word,Poi.query.all(),scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
            for m,s in matches_poi:
                final_matches.append((m,s))
        if not any([match[1]>98 for match in final_matches]):
            matches_neigh = process.extractBests(word,Neighborhood.query.all(),scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
            for m,s in matches_neigh:
                final_matches.append((m,s))
    final_matches.sort(key=takeSecond, reverse=True)
    if any([match[1]>98 for match in final_matches]):
        exact=True
        final_matches=[match for match in final_matches if match[1]>98]
    # se i risultati sono esatti non voglio escludere nessuna soluzione!
    if not exact:
        final_matches = final_matches[0:4]

    return [match[0] for match in final_matches], [match[1] for match in final_matches], exact

# finto, per ora non serve a nulla
# teoricamente puo essere utile, ma magari anche no
def get_parameters():

    cutoff = 0.6
    max_result = 5
    return [cutoff, max_result]
