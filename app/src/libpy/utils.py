import numpy as np
import shapely, shapely.wkt, shapely.geometry
import time
import pdb

# SHOULD THIS BE HERE? Dovrebbe andare nella library_search?
from app import app, db
from sqlalchemy import and_
from app.models import PoiCategoryType, Location, Poi, poi_types, PoiCategory
from shapely.geometry import mapping


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

from app.src.libpy.pyAny_lib import calculate_path_wkt

def find_path_to_closest_riva(G_un, coords_start, rive_list):
    """
    It finds the path to the closest riva with respect to the starting coordinates. coords_start and rive_list are nodes of G_un
    """
    length_paths=[]
    paths=[]
    for riva in rive_list:
        path, length = calculate_path_wkt(G_un, coords_start, riva, flag_ponti=True)
#        print("percorso calcolato per questa riva: ", bool(path) )
        if path:
            length_paths.append(length)
            paths.append(path)

    # qua abbiamo la lista delle strade
    app.logger.debug("quanto sono lunghe le strade? {}".format(length_paths))
    np_lengths = np.asarray(length_paths)
    idx_shortest_path = np.argmin(np_lengths)
    shortest_path = paths[idx_shortest_path]

    # la riva sara l'ultimo nodo della strada
    # closest_riva = shortest_path[-1]
    return shortest_path

import pdb

def add_from_strada_to_porta(path, da, a):
    """
    It adds address linestring to connect doors with streets
    """
    path['shape_list'].insert(0,da['geojson'])
    path['shape_list'].append(a['geojson'])
    return path
