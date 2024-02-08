"""
All the functions related to searching in the database for addresses, words, streets, path, places or whatever else you may look for.
"""
import numpy as np
import logging
import time
import shapely, shapely.wkt, shapely.geometry
import pdb
import ipdb
from geoalchemy2.shape import to_shape

# IMPORT FOR THE DATABASE - db is the database object
from app.models import Neighborhood, Street, Location, Area, Poi, PoiCategoryType, poi_types, PoiCategory, Address
from app import app, db
from fuzzywuzzy import fuzz, process
import fuzzywuzzy
from shapely.geometry import mapping
from shapely.ops import transform
from sqlalchemy import and_, or_
import re
import geopy.distance
import app.site_parameters as site_parameters

# IMPORT OUR LIBRARIES
from app.src.libpy import lib_graph
from app import custom_errors

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

def are_we_sure_of_the_results(match_dict):
    """
    Return true if the dictionary is one unique result or if there is only only one result that is exact.
    """
    if len(match_dict) == 1:
        return True

    exact_results = [match['exact'] for match in match_dict]
    num_of_exact = sum(exact_results)

    if num_of_exact == 1:
        return True
    else:
        return False

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


def find_closest_nodes(dict_list,G_array, MIN_DIST_FOR_THE_CLOSEST_NODE=100):
    """
    Returns list of nodes in G_array closest to coordinate_list (euclidean distance).
    """
    nodes_list=[]
    for d in dict_list:
        coordinate = np.asarray(d.get("coordinate"))
        #time1 = time.time()
        #tmp = np.subtract(np.ones(G_array.shape) * coordinate, G_array)
        #dists = np.sum(np.sqrt(tmp * tmp), axis=1)
        time2 = time.time()
        dists = distance_from_a_list_of_geo_coordinates(coordinate, G_array)
        time3 = time.time()
        app.logger.debug("it took {} to calculate distances".format(time3-time2))
        #dists=d.get("shape").distance(G_array)
        closest_id = np.argmin(dists)
        closest_dist = dists[closest_id]
        app.logger.debug("il tuo nodo è distante {}".format(closest_dist))
        # se la distanza e troppo grande, salutiamo i campagnoli
        if closest_dist>MIN_DIST_FOR_THE_CLOSEST_NODE:
            app.logger.error("Sei troppo distante da Venezia, cosa ci fai là?? (il punto del grafo piu vicino dista {} metri)".format(closest_dist))
            raise custom_errors.UserError("Non abbiamo trovato nulla qua - magari cercavi di andare fuori venezia o forse vorresti andare in barca?")
        nodes_list.append((G_array[closest_id][0], G_array[closest_id][1]))

    return nodes_list#, dists

def distance_from_point_to_point(point1, point2):
    """
    Distance between two points formatted as [lon,lat] or (lon,lat)
    """
    # to be done
    dist2 = distance_from_a_list_of_geo_coordinates(np.asarray(point1),np.asarray([point2]))
    return dist2

def distance_from_a_list_of_geo_coordinates(thePoint, coordinates_list):
    """
    A python implementation from the answer here https://stackoverflow.com/questions/639695/how-to-convert-latitude-or-longitude-to-meters.
    Calculate the distance in meters between 1 geographical point (longitude, latitude) and a list of geographical points (list of tuples) or between 2 geographical points passing through distance_from_point_to_point
    """
    # maybe we need to invert
    lat_index = 1
    lon_index = 0
    # parameters
    earth_radius = 6378.137; # Radius of earth in KM
    deg2rad = np.pi / 180
    # single point
    lat1 = thePoint[lat_index] * deg2rad
    lon1 = thePoint[lon_index] * deg2rad
    # test the whole list again the single point
    lat2 = coordinates_list[:,lat_index] * deg2rad
    lon2 = coordinates_list[:,lon_index] * deg2rad
    dLat = lat2 - lat1
    dLon = lon2 - lon1
    a = np.sin(dLat/2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dLon/2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    d = earth_radius * c
    distances_in_meters = d * 1000

    return distances_in_meters

def haversine_np(lon1, lat1, lon2, lat2):
    """
    Calculate the great circle distance between two points on the earth (specified in decimal degrees).

    All args must be of equal length.
    From https://stackoverflow.com/questions/29545704/fast-haversine-approximation-python-pandas
    """
    lon1, lat1, lon2, lat2 = map(np.radians, [lon1, lat1, lon2, lat2])

    dlon = lon2 - lon1
    dlat = lat2 - lat1

    a = np.sin(dlat/2.0)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2.0)**2

    c = 2 * np.arcsin(np.sqrt(a))
    km = 6367 * c
    return km

def degree2meters(lat, long):
    """
    It needs to be done.
    """

    distance_in_meters, coordinates_in_meters = degree2meters_approx(lat, long)

    return distance_in_meters, coordinates_in_meters

def degree2meters_approx(lat, long):
    """
    A temporary solution using an approximation.
    """
    meters_lat = 111.32 * lat
    meters_long = 40075 * np.cos( latitude ) / 360 * long
    distance_in_meters = np.sqrt(np.power(meters_lat, 2), np.power(meters_long, 2))
    return distance_in_meters, [meters_lat, meters_long]

def find_path_to_closest_riva(G_un, coords_start, rive_list,flag_ponti=True):
    """
    It finds the path to the closest riva with respect to the starting coordinates. It prepares the geojson and returns the chosen riva.
    """
    length_paths=[]
    paths=[]
    if not rive_list:
        app.logger.debug("nessuna riva trovata, non posso findare nessuna path")
    for riva in rive_list:
        try:
            path, length = lib_graph.calculate_path_wkt(G_un, coords_start, riva, lib_graph.weight_bridge)
            length_paths.append(length)
            paths.append(path)
            #     print("percorso calcolato per questa riva: ", bool(path) )
        except:
            app.logger.debug("errore nel calculate path")
            continue

    if paths:
        # qua abbiamo la lista delle strade
        app.logger.debug("quanto sono lunghe le strade? {}".format(length_paths))
        np_lengths = np.asarray(length_paths)
        idx_shortest_path = np.argmin(np_lengths)
        shortest_path = paths[idx_shortest_path]
        chosen_riva = shortest_path[-1]
        app.logger.debug("la piu corta e la strada con indice {} e il punto d'arrivo e' {}".format(idx_shortest_path,chosen_riva))
        app.logger.debug("ora ricalcolo per il dizionario con le info")
        path_info = lib_graph.give_me_the_street(G_un, coords_start, chosen_riva, flag_ponti)
    else:
        app.logger.debug("le rive vicine non sono raggiungibili")
        app.logger.debug("probabilmente sei in un punto speciale in cui le rive sono distanti e non c'e nessuna riva raggiungibile a piedi (es. Murano e rive a Venezia)")
        chosen_riva=-1
        path_info={'lunghezza':0,
                   'human_readable_length':0,
                   'time':0,
                   'human_readable_time':0,
                   'n_ponti':0,
                   'shape_list':[]
        }

    # la riva sara l'ultimo nodo della strada
    # closest_riva = shortest_path[-1]
    return path_info, chosen_riva

def give_me_the_dictionary(input_string, coords):
    """
    Wrapper of the wrapper that check if the user input is a coordinate or a string to be searched in the database.
    """
    if coords:
        isACoordinate, coordinate_current_position = check_if_is_already_a_coordinate(coords)
        app.logger.debug("Abbiamo ricevuto la coordianta! Nient'altro da fare a parte fingere di aver cercato!")
        out_dict = create_fake_dict_because_we_already_have_the_coordinates(input_string, coordinate_current_position)
        app.logger.debug("Il dizionario fake è {}".format(dict))
    else:
        isACoordinate, coordinate_current_position = check_if_is_already_a_coordinate(input_string)
        if isACoordinate:
            app.logger.debug("Abbiamo ricevuto la coordinata! Nient'altro da fare a parte fingere di aver cercato!")
            out_dict = create_fake_dict_because_we_already_have_the_coordinates('Coordinate inserite', coordinate_current_position)
            app.logger.debug("Il dizionario fake è {}".format(dict))
        else:
            app.logger.debug("Abbiamo ricevuto una stringa vera, cerchiamo nel dizionario!")
            out_dict = find_address_in_db(input_string)

    return out_dict

def create_fake_dict_because_we_already_have_the_coordinates(name, coords):
    """
    Creates a well-formatted dictionary to pass as result also in the case we already have the coordinates as input.
    """
    # una lista con un dizionario
    coordinate_as_shapely_point = shapely.geometry.Point(coords[0], coords[1])
    edge_info_dict = {}
    edge_info_dict['street_type'] = 'calle'
    edge_info_dict['bridge'] = 0
    geojson = {
        "type": "Feature",
        "properties": edge_info_dict,
        "geometry": dict(mapping(coordinate_as_shapely_point))
    }
    fake_result_dict = [{"nome":name,
                "descrizione": "",
                "coordinate":coords,
                "shape":coordinate_as_shapely_point,
                "geotype":0, # marker
                "score":100,
                "exact":True, # is exact
                "geojson":geojson
                }]
    return fake_result_dict

def check_if_is_already_a_coordinate(input_string):
    """
    Function to check if the input string is a couple of coordinates of the type (12.45,45.32)
    """
    are_coordinates = False
    lat = lon = 0
    # regex: cerchiamo cifre.cifre+spazi, spazi+cifre.cifre
    pattern_coordinates = re.compile('\d+.\d+')
    coordinates = pattern_coordinates.findall(input_string)
    if len(coordinates) == 2:
        are_coordinates = True
        lat = float(coordinates[0])
        lon = float(coordinates[1])
        # gestiamo il caso inverso, visto che nessuno sa l'ordine
        if lat < 40:
            tmp = lat
            lat = lon
            lon = tmp

    coordinates = [lon, lat]
    return are_coordinates, coordinates

def suggest_sql(clean_string, max_num=5):
    suggestions = db.session.execute('SELECT * FROM fn_GetSuggest(:p1, :p2)',
                    {'p1':clean_string, 'p2':max_num}).fetchall()

    return [list(s) for s in suggestions]

def suggest_address_from_db(text, number, max_n=5):
    """
    Wrapper functions that looks for address in the database with the input string as substring
    """

    # retrieve locations that match with number and text
    suggestions = Location.query.join(Address).filter(
        Address.housenumber.isnot(None), Address.housenumber.startswith(number)
        ).join(Neighborhood).join(Street).filter(or_(
        Neighborhood.name.startswith(text),
        Street.name.startswith(text))
        ).order_by(
        Neighborhood.name,
        Address.housenumber
        ).limit(max_n).all()

    # Location.query.filter(Address.housenumber.isnot(None)).join(Location.neighborhood).join(Location.street).filter(or_(Neighborhood.name.startswith(text),Street.name.startswith(text))).order_by(Neighborhood.name,Address.housenumber).limit(max_n).all()

    return suggestions


def places_sql(clean_string, max_num=5):
    places = db.session.execute('SELECT * FROM fn_GetPlaces(:p1, :p2)',
                    {'p1': clean_string, 'p2': max_num}).all()

    return [list(s) for s in places]


def find_address_in_db(input_string):
    """
    Wrapper functions that looks for an address in the database.
    """
    app.logger.info("looking in the db")
    # fetch parameters (puo tornare utile se i parametri saranno modificabili dal browser piu avanti)
    search_parameters = get_parameters()

    # pulisci la stringa col metodo di ale
    start_time = time.time()
    clean_string = correct_name(input_string)
    app.logger.info(f"Correct name: {time.time()-start_time:.5f}")
    # dividi numero e dicci come e fatta
    start_time = time.time()
    text, number, isThereaCivico = dividiEtImpera(clean_string)
    app.logger.info(f"Dividi et impera: {time.time()-start_time:.5f}")
    # cerca nel database - qua dentro avviene la magia
    #found_something, actual_address, address_type = find_address(text)
    start_time = time.time()
    address_list, score_list, exact = fuzzy_search(text, isThereaCivico)
    app.logger.info(f"Fuzzy: {time.time()-start_time:.5f}")
    app.logger.debug("Lista {}, scores {}".format(address_list, score_list))
    start_time = time.time()
    result_dict = []
    # dammi coordinate, del punto o del poligono
    if not address_list:
        app.logger.warning("Non abbiamo trovato nulla nel database!")
        raise custom_errors.UserError("Non abbiamo trovato nessuna corrispondenza con {} sicuro di aver scritto bene?".format(input_string))
    else:
        for address, score,  in zip(address_list, score_list):
            # geo_type, coordinates, polygon_shape_as_list, polygon_shape = fetch_coordinates(address, number, isThereaCivico)
            # address ritornato da fetch_coordinates e' l'elemento del database di location
            # quindi e' voluto che venga sostituito, in modo che poi nel dizionario abbiamo le infomazioni.
            # ipdb.set_trace()
            geo_type, coordinates, polygon_shape, address = fetch_coordinates(address, number, isThereaCivico)
            if geo_type>=0:
                # neighborhood, street, location, poi, ecc..
                address_type = get_match_type(address)
                nome=str(address) # address sostitutio ha gia il numero, non serve piu aggiungerlo!
                # INCREDIBILE: stampando il geojson non serve invertire le coordinate!
                # inverti x e y nella shape, è più facile farlo ora piuttosto che dopo
                # shape = transform(lambda x,y:(y,x), shape)
                edge_info_dict = {}
                edge_info_dict['street_type'] = 'calle'
                edge_info_dict['bridge'] = 0
                polygon_shapely_geom = polygon_shape
                geojson = {
                    "type": "Feature",
                    "properties": edge_info_dict,
                    "geometry": dict(mapping(polygon_shapely_geom))
                }
                result_dict.append({"nome":nome,
                            #"descrizione":address.get_description(),
                            "coordinate":coordinates,
                            #"shape":polygon_shape_as_list,
                            "shape":polygon_shape,
                            "geotype":geo_type,
                            "score":score,
                            "type":address_type,
                            "exact":exact,
                            "geojson":geojson,
                            ## this is the description of the object found,
                            ## that could be address, street, poi, whatever
                            ## transformed in a json-like dict
                            f"{address_type}":address.get_description(),
                            "info":address.get_description()
                            })
            else:
                app.logger.debug("in this one there was nothing")
                nome=str(address)

        if not result_dict:
            app.logger.debug("L'indirizzo non è presente nel sestiere o nella strada, ti hanno dato l'indirizzo sbagliato?")
            raise custom_errors.UserError("L'indirizzo non è presente nel sestiere o nella strada, ti hanno dato l'indirizzo sbagliato?")
        # once upon a time there was a sort_results! why? nobody knows
        app.logger.debug("__________________________dizionario risultante\n{}".format(result_dict))
        app.logger.info(f"Dictionary: {time.time()-start_time:.5f}")

    return result_dict

def get_match_type(db_obj):
    """
    Returns a string describing the type of the object.
    It matches against the types defined in models.py, otherwise it returns "unknown".
    """
    obj_type = "unknown"
    if type(db_obj) == Location:
        obj_type = "location"
        try:
            if db_obj.address is not None:
                obj_type = "address"
        except:
            app.logger.debug("correct the get_match_type method, please")
    # this most likely does not work
    elif type(db_obj) == Address:
        obj_type = "address"
    elif type(db_obj) == Neighborhood:
        obj_type = "neighborhood"
    elif type(db_obj) == Street:
        obj_type = "street"
    elif type(db_obj) == Poi:
        obj_type = "poi"

    return obj_type

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
    # 3. Sostituzione apostrofo
    name = name.replace("’", "'")
    # Ritorna stringa corretta
    return name.upper()

"""
la parte finale. Siamo sicuri che tutto funziona, solo prendiamo le coordinate
"""
def fetch_coordinates(actual_location, number, isThereaCivico):

    # SE ABBIAMO UN CIVICO, SCEGLIAMO UN PUNTO!
    if isThereaCivico:
#       # geo type = 0 dice che usiamo un punto
        geo_type = 0
        with_num=actual_location.locations.join(Location.address, aliased=True).filter_by(housenumber=number).first()
        if not with_num:
            # controlliamo che non ci siano altri indirizzi che semplicemente contengano il numero (ad esempio per San Polo 1421 vogliamo San Polo 1421/A)
            with_num = actual_location.locations.join(Location.address, aliased=True).filter(Address.housenumber.contains(number)).all()
            with_num = with_num[0] if len(with_num) == 1 else None

        # pdb.set_trace()
        if with_num:
        # if len(with_num) == 1:
            actual_location=with_num
            coords = [actual_location.longitude, actual_location.latitude]
            # to shape is needed to convert from wkb to shapely
            polygon_shape = to_shape(actual_location.shape)
        # elif len(with_num) > 1:
        #     # TODO: ritorna tutte le possibilità
        #
        else:
            # non abbiamo trovato niente, -abbiamo trovato la strada ma l'indirizzo non è dentro
            app.logger.debug("L'indirizzo non è presente nel sestiere o nella strada. civico {} e location {}".format(number, actual_location))
            geo_type = -2
            coords = [-1, -1]
            polygon_shape = None
            # l'eccezione viene lanciata dal sort results successivo
            #raise Exception("L'indirizzo non è presente nel sestiere o nella strada, ti hanno dato l'indirizzo sbagliato?")
    # SE NON ABBIAMO UN CIVICO, FORSE E' UN POI! in quel caso estraiamo il punto
    elif type(actual_location)==Poi:
        geo_type = 0
        coords = [actual_location.location.longitude,actual_location.location.latitude]
        # to shape is needed to convert from wkb to shapely
        polygon_shape = to_shape(actual_location.location.shape)
    # SE NON ABBIAMO UN CIVICO, E' UNA STRADA O UN SESTIERE! in quel caso estraiamo la shape e un punto rappresentativo
    elif actual_location.shape is not None:
        geo_type = 1
        # to shape is needed to convert from wkb to shapely
        polygon_shape = to_shape(actual_location.shape)
        # if polygon_shape.geom_type == 'MultiPolygon':
        #     # do multipolygon things.
        #     polygon_shape_as_list = []
        #     # loop su ogni poligono
        #     for single_polygon in polygon_shape:
        #         # poligono
        #         xs, ys = single_polygon.exterior.coords.xy
        #         # for loop questa volta per evitare una lista di liste -- vogliamo una lista sola
        #         for i in range(len(xs)):
        #             polygon_shape_as_list.append([xs[i], ys[i]])
        # elif polygon_shape.geom_type == 'Polygon':
        #     # do polygon things.
        #     xs, ys = polygon_shape.exterior.coords.xy
        # else:
        #     raise IOError('Shape is not a polygon.')
        # coords va creato in modo che sia subscriptable
        coords = getCentroidSmartly(polygon_shape) # polygon_shape potreebbe esser un multipoligono!
        #print("Polygon shape {}, coordinates {}".format(polygon_shape, coords))
    else:
        # in teoria questo caso non esiste per consistenza del db, lo lasciamo solo temporanemente con un print
        app.logger.info("ERRORE ASSURDO: l'oggetto trovato non è un indirizzo, non è un poi, e se è una strada o sestiere non ha geometria!", actual_location)
        coords = [-1, -1]
        geo_type = -1
        #polygon_shape_as_list = None
        polygon_shape = None

    app.logger.debug("print del fetch", geo_type, coords, polygon_shape)
    # coords e' solo le coordinate di actual location che e' l'elemento del DATABASE
    # ora ci serve actual_location per le info, descrizione e ID
    # coords non ci serve piu mi sa perche si puo sempre ricavare da actual_location
    # TODO: BETA
    return geo_type, coords, polygon_shape, actual_location

"""
da gestire piu poligoni, piu centroidi, multipoligoni e alieni
"""
def getCentroidSmartly(polygon_shape):
    #avg_coordinate = [polygon_shape.centroid.x, polygon_shape.centroid.y]
    avg_coordinate = [polygon_shape.representative_point().x, polygon_shape.representative_point().y]
    app.logger.debug("Centroide: ".format(avg_coordinate))
    return avg_coordinate

"""
parte di una funzione di Ale presa dal codice dentro searchName in functions.py (riga 125 in questo momento).
Divide testo e numero e ritorna se effettivamente c'era un numero
"""
def dividiEtImpera(clean_string):


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
        # Piccolo trucco per barare con santa marta: sostituisci con Dorsoduro
        # TODO: CAMBIARE CON QUALCOSA DI PIÙ SOLIDO
        if text.lower() == "santa marta":
            text = text.lower().replace("santa marta", "dorsoduro")
        elif text.lower() == "santamarta":
            text = text.lower().replace("santamarta", "dorsoduro")
    else:
        text = clean_string
        number = ""

    return text, number, isThereaCivico


def sort_results(res_list):
    """
    Sorts the results list to give as a first choice, not the best score matching, but something better. For the moment I put as last, the results with a negative geometry.
    """
    new_res_list=[]
    for res in res_list:
        if res["geotype"]>=0:
            new_res_list.append(res)
    if not new_res_list:
        app.logger.debug("L'indirizzo non è presente nel sestiere o nella strada. civico {} e location {}".format(number, actual_location))
        raise custom_errors.UserError("L'indirizzo non è presente nel sestiere o nella strada, ti hanno dato l'indirizzo sbagliato?")
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


def fuzzy_search(word, isThereaCivico,scorer=fuzz.token_sort_ratio,processor=fuzzywuzzy.utils.full_process,threshold=98, n_limit=15, score_cutoff=50):
    """
    Search the input string using the fuzzy library, returns the best matches.

    Troviamo la corrispondenza con fuzzy, estraggo l'indice, per poter estrarre il match e la provenienza
    """
    #raise custom_errors.DeveloperError("fasullissimo")
    exact = False

    final_matches = []
    if isThereaCivico:
        matches_neigh = process.extractBests(word,Neighborhood.query.all(),scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
        for m,s in matches_neigh:
            final_matches.append((m,s))
        if not any([score>=threshold for match,score in final_matches]):
            matches_street = process.extractBests(word,Street.query.all(),scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
            for m,s in matches_street:
                final_matches.append((m,s))
    else:
        # andrà implementata qui la ricerca nei poi, che fa un check delle corssipondenze con le keyword e fa la query invece di Poi.query.all() filtrando sui types di poi
        dict_final_matches = {}
        tables_where_to_look = [Neighborhood, Street, Poi] #[Street, Poi, Neighborhood]
        for table in tables_where_to_look:
            matches_table = process.extractBests(word, table.query.all(),scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
            for m,s in matches_table:
                #final_matches.append((m,s))
                dict_final_matches[m] = s
            #if any([score>=threshold for match,score in final_matches]):
            if any([score>=threshold for score in dict_final_matches.values()]):
                break
            # search in alternative names
            dict_alt_names = create_dict_alternative_names(table)
            if dict_alt_names:
                matches_table = process.extractBests(word, dict_alt_names, scorer=scorer,processor=processor,score_cutoff=score_cutoff,limit=n_limit)
                for match_string,s,m in matches_table:
                    #final_matches.append((m,s))
                    if (m not in dict_final_matches.keys()) or dict_final_matches[m] < s:
                        dict_final_matches[m] = s
                #if any([score>=threshold for match,score in final_matches]):
                if any([score>=threshold for score in dict_final_matches.values()]):
                    break
        final_matches = [(m,s) for m,s in dict_final_matches.items()]
    final_matches.sort(key=takeSecond, reverse=True)
    if any([score>=threshold for match,score in final_matches]):
        exact=True
        final_matches=[(match,score) for match,score in final_matches if score>=threshold]
    # se i risultati sono esatti non voglio escludere nessuna soluzione!
    if not exact:
        final_matches = final_matches[0:n_limit]

    return [match for match,score in final_matches], [score for match,score in final_matches], exact

def create_dict_alternative_names(table_where_to_search):

    if table_where_to_search in site_parameters.tables_with_alt_name:
        list_alt_name = [(s, s.name_alt) for s in table_where_to_search.query.filter(table_where_to_search.name_alt.isnot(None)).all()]
        dict_alt_name = dict(list_alt_name)
    else:
        dict_alt_name = {}

    return dict_alt_name
# finto, per ora non serve a nulla
# teoricamente puo essere utile, ma magari anche no
def get_parameters():

    cutoff = 0.6
    max_result = 5
    return [cutoff, max_result]
