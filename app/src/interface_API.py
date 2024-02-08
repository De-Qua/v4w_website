"""
Interfaccia intesa come punto di controllo tra le API e i metodi interni.
Qui controlliamo che i parametri in ingresso dalle API siano settati nel modo corretto, se no ritorniamo indietro un avviso.
Avere una struttura fissa e ben definita penso sia utile se poi le API sono usate da esterni.
"""
# non importiamo lib_graph // questa libreria deve usare solo graph_tool
# se no ha poco senso avere il nuovo file, era per aiutare nel cambio
import re
import os
import json
import time
import ipdb
import pdb
import datetime as dt
from random import choice
import string


# FLASK APP
from app import app, db
from flask import current_app
# CODICI DI ERRORE
from app.src.api.constants import (
    DEFAULT_LANGUAGE_CODE,
    ALL_GOOD,
    UNKNOWN_EXCEPTION, MISSING_PARAMETER, NOT_FOUND, RETURNED_EXCEPTION,
    UNCLEAR_SEARCH, NO_PATH_FOUND,
    WORK_IN_PROGRESS
)
# PARAMETERS (like the graph)
import app.site_parameters as site_params
# dequa graph library
from dequa_graph import topology as dqg_topo
from dequa_graph import formatting as dqg_form
from dequa_graph import weights as dqg_weight
from dequa_graph import errors as dqg_err
# lib search
from app.src.libpy import lib_search as ls
# communication for formatting
#from app.src.libpy.libcommunication import format_path_data
# errors
from app.src.api import errors

from app.models import ShortURL, ShortURLCounter



def check_format_coordinates(*args):
    """Check if input strings are coordinates in the format "longitude,latitude".
    The function automatically inverts the coordinates if the latitude is greater
    than the longitude (and therefore they don't belong to Venice). If one of
    the input is not in the correct format it will raise a CoordinatesError.

    :param *str or *list(str): Input strings in the format "12.339041,45.434268".
    :return: For each input returns a list with the coordinates in the correct format

    """
    all_coordinates = []
    for list_coords in args:
        if type(list_coords) is not list:
            list_coords = [list_coords]
        correct_coordinates = []
        for coord in list_coords:
            # match all the float numbers
            pattern_coordinates = re.compile('(\d+\.\d+)\s?,\s?(\d+\.\d+)')
            match_coords = pattern_coordinates.match(coord)
            try:
                lon = float(match_coords.group(1))
                lat = float(match_coords.group(2))
            except IndexError:
                raise errors.CoordinatesNumberError
            except AttributeError:
                raise errors.CoordinatesFormatError(coord)
            coordinates = [lon, lat]
            # gestiamo il caso inverso, visto che nessuno sa l'ordine
            if lat < lon:
                coordinates.reverse()
            correct_coordinates.append(coordinates)

        if len(correct_coordinates) == 1:
            all_coordinates.append(correct_coordinates[0])
        else:
            all_coordinates.append(correct_coordinates)

    if len(all_coordinates) == 1:
        return all_coordinates[0]
    else:
        return all_coordinates


def find_shortest_path_from_coordinates(start, end, mode='walk', start_time=None, **params):
    """
    Search for the shortest path from coordinates A to B.
    If A or B are not coordinates, gives back a warning and does not calculate anything.
    It returns a dict with 'code' (0 = good, anything else, did not work)
    and 'data' (the shortest path or None).
    """
    # The check for the coordinates format should be done by the api
    # start_coord = params['start_coord']
    # end_coord = params['end_coord']
    #
    # # check that they actually are coordinates
    # if not start_coord or not end_coord:
    #     return {'code':INPUT_SHOULD_BE_COORDINATES, 'data':None}

    # check how the street should be calculated
    if start_time is None:
        start_time = dt.datetime.now()

    if mode == 'walk':
        fn_shortest_path = gt_shortest_path_walk_wrapper
        fn_info_path = format_path_walk_data
    elif mode == 'boat':
        fn_shortest_path = gt_shortest_path_boat_wrapper
        fn_info_path = format_path_boat_data
    else:
        raise errors.WorkInProgressError("There are only two modes: walk and boat")
        # return {'code': MISSING_PARAMETER, 'data': None}

    # get the edges and nodes
    # try:
    v_list, e_list, t_list = fn_shortest_path(start, end, start_time=start_time, **params)
    # and format for js
    path_dict = fn_info_path(v_list, e_list, t_list, start_time=start_time, **params)
    # except errors.NoPathFound:
    #     return {'code': NO_PATH_FOUND, 'data': None}
    # except NotImplementedError:
    #     return {'code': WORK_IN_PROGRESS, 'data': None}
    # except Exception:
    #     return {'code': UNKNOWN_EXCEPTION, 'data': None}

    return path_dict


def gt_shortest_path_boat_wrapper(start, end, stop=None,
                                  motor=False, boat_speed=5,
                                  boat_width=0, boat_height=0,
                                  alternatives=False, avoid_public_transport=True,
                                  start_time=None,
                                  **kwargs):
    """
    WALK PATH NOT IMPLEMENTED YET
    It calculates the shortest path using a boat
    It returns 2 values, list of vertices and list of edges. If no path is found it raises a NoPathFound exception.
    """
    graph = current_app.graphs['water']
    # Define the weight that we will use
    if alternatives:
        raise errors.WorkInProgressError("Alternatives not implemented yet")
    else:
        weight = dqg_weight.get_weight(graph=graph['graph'], mode='boat',
                                       motor_boat=motor, boat_speed=boat_speed,
                                       boat_width=boat_width, boat_height=boat_height)
        weights = [weight]
    # get the path
    try:
        v_list, e_list, t_list = dqg_topo.calculate_path(
            graph=graph['graph'],
            coords_start=start,
            coords_end=end,
            coords_stop=stop,
            weight=weights,
            all_vertices=graph['all_vertices']
        )
    except dqg_err.NoPathFound:
        raise errors.NoPathFound(start, end)
    return v_list, e_list, t_list


def gt_shortest_path_walk_wrapper(start, end, stop=None,
                                  speed=5, avoid_bridges=False,
                                  avoid_tide=False, tide_level=None, boots_height=0,
                                  alternatives=False, avoid_public_transport=True,
                                  prefer_public_transport=False, start_time=None,
                                  transport_change_penalty=61,
                                  **kwargs):
    """
    It calculates the shortest path by calling the methods in lib_graph_tool.
    It returns 2 values, list of vertices and list of edges. If no path is found it raises a NoPathFound exception.
    """

    graph = current_app.graphs['waterbus']
    start_v, end_v, stop_v = dqg_topo.find_path_vertices(start, end, stop, all_vertices=graph['all_vertices'])
    if stop:
        vertices_stop = stop_v + [end_v]
    else:
        vertices_stop = [end_v]
    mandatory_transport = any(graph['graph'].vp.component_street[start_v] != graph['graph'].vp.component_street[v] for v in vertices_stop)
    if mandatory_transport or prefer_public_transport:
        avoid_public_transport = False
        available_transports = ["with_public_transport"]
    elif avoid_public_transport:
        available_transports = ["without_public_transport"]
    else:
        available_transports = ["with_public_transport", "without_public_transport"]
    v_list = []
    e_list = []
    t_list = []
    for transport in available_transports:
        # get the correct graph
        if transport == "without_public_transport":
            graph = current_app.graphs['street']
            use_public_transport = False
            prefer_public_transport = False
            time_edge_property = None
            transport_property = None
            timetable_property = None
            direction_property = None
        elif transport == "with_public_transport":
            graph = current_app.graphs['waterbus']
            use_public_transport = True
            # TODO
            # assegniamo le properties qua perche
            # speed non viene passata dentro calculate_path
            time_edge_property = dqg_weight.get_weight_time(graph=graph['graph'], speed=speed)
            transport_property = graph['graph'].vp.transport_stop
            timetable_property = dqg_weight.get_timetables(graph=graph['graph'], date=start_time)
            direction_property = graph['graph'].ep.direction

        # get tide if not present
        if avoid_tide and not tide_level:
            tide_level = get_current_tide_level()
        # Define the weight that we will use
        if alternatives:
            raise errors.WorkInProgressError("Alternatives not implemented yet")
        else:
            weight = dqg_weight.get_weight(graph=graph['graph'], mode='walk', speed=speed, avoid_bridges=avoid_bridges,
                                           avoid_tide=avoid_tide, tide_level=tide_level, boots_height=boots_height,
                                           prefer_public_transport=prefer_public_transport)
            weights = [weight]
        # get the path
        try:
            tmp_v_list, tmp_e_list, tmp_t_list = dqg_topo.calculate_path(
                graph=graph['graph'],
                coords_start=start,
                coords_end=end,
                coords_stop=stop,
                weight=weights,
                all_vertices=graph['all_vertices'],
                use_public_transport=use_public_transport,
                start_time=start_time,
                time_edge_property=time_edge_property,
                transport_property=transport_property,
                timetable_property=timetable_property,
                direction_property=direction_property,
                transport_change_penalty=transport_change_penalty
            )

        except dqg_err.NoPathFound:
            raise errors.NoPathFound(start, end)
        v_list += tmp_v_list
        e_list += tmp_e_list
        t_list += tmp_t_list
        # ipdb.set_trace()
        if transport == "with_public_transport" and any(graph["graph"].ep.transport[e]==1 for e in tmp_e_list[0][0]):
            continue
        else:
            break

    return v_list, e_list, t_list
    # # retrieve info of the path
    # info = lgt.retrieve_info_from_path_streets(
    #             graph=graph['graph'],
    #             paths_vertices=v_list,
    #             paths_edges=e_list
    #             )
    # return info


def format_path_walk_data(v_list, e_list, t_list, avoid_public_transport=False, start_time=None, **kwargs):
    """
    Function to format the data of a path
    """
    if avoid_public_transport:
        graph = current_app.graphs['street']['graph']
    else:
        graph = current_app.graphs['waterbus']['graph']
    info = dqg_form.retrieve_info_from_path_streets(
        graph=graph, paths_vertices=v_list, paths_edges=e_list,
        times_edges=t_list, start_time=start_time, **kwargs)

    return info


def format_path_boat_data(v_list, e_list, t_list, avoid_public_transport=False, start_time=None, **kwargs):
    """
    Function to format the data of a path
    """
    info = dqg_form.retrieve_info_from_path_water(
        graph=current_app.graphs['water']['graph'],
        paths_vertices=v_list, paths_edges=e_list, times_edges=t_list,
        start_time=start_time, **kwargs)
    return info


# def gt_shortest_path_wrapper(start, end, mode='WALKING'):
#     """
#     It calculates the shortest path by calling the methods in lib_graph_tool.
#     It returns 3 values, exit_code (0 good, > 0 bad), list of vertices and list of edges.
#     """
#     if mode == "BOAT": ### TODO
#         return WORK_IN_PROGRESS, None, None
#
#     elif mode == "WALKING":
#         v_list, e_list = dqg_topo.calculate_path(site_params.G_terra, start, end)
#         return ALL_GOOD, v_list, e_list
#
#     else:
#         return UNKNOWN_MODE, None, None


def get_current_tide_level():
    """
    Fetch the high tide level from the JSON file.
    """
    tide_level = current_app.tide_values.get('tide_level', None)

    return tide_level


def format_response_address(**kwargs):
    formatted_address = {
        'type': kwargs.get("type", "undefined"),
        'similarity': kwargs.get("similarity", 0),
        'title': kwargs.get("title", ""),
        'latitude': kwargs.get("latitude", 0),
        'longitude': kwargs.get("longitude", 0),
        'shape': kwargs.get("longitude", None),
        # ADDRESS
        'address_street': kwargs.get("address_street", ""),
        'address_neigh': kwargs.get("address_neigh", ""),
        'housenumber': kwargs.get("housenumber", ""),
        # POI
        'poiname': kwargs.get("poiname", ""),
        'poicategoryname': kwargs.get("poicategoryname", ""),
        'opening_hours': kwargs.get("opening_hours", ""),
        'wheelchair': kwargs.get("wheelchair", ""),
        'toilets': kwargs.get("toilets", False),
        'toilets_wheelchair': kwargs.get("toilets_wheelchair", False),
        'wikipedia': kwargs.get("wikipedia", ""),
        'phone': kwargs.get("phone", ""),
        # STREET
        'street_name': kwargs.get("street_name", ""),
        'name_alt': kwargs.get("name_alt", ""),
        'name_spe': kwargs.get("name_spe", ""),
        'name_den':  kwargs.get("name_den", ""),
        # NEIGHBORHOOD
        'neighborhood_name': kwargs.get("neighborhood_name", ""),
        'zipcode': kwargs.get("zipcode", 30100)
    }
    return formatted_address


def get_suggestions(input, max_num=5):
    """
    Retrieve from the databases addresses that have a partial match with the input string.
    """
    # clean the string
    clean_string = ls.correct_name(input)

    suggestions = ls.suggest_sql(clean_string, max_num)

    formatted_suggestions = [
        ## use method to be sure
        format_response_address(
            type=s[0],
            title=f"{s[5]}" if s[0] == "neighborhood"
                  else f"{s[4]}" if s[0] == "street"
                  else f"{s[5]} {s[6]}" if s[0] == "address"
                  else f"{s[7]}" if s[0] == "poi"
                  else "No name",
            latitude=s[1],
            longitude=s[2],
            shape=s[3],
            address_street=s[4],
            address_neigh=s[5],
            housenumber=s[6],
            poiname=s[7],
            poicategoryname=s[8],
            opening_hours=s[9],
            wheelchair=s[10],
            toilets=s[11],
            toilets_wheelchair=s[12],
            wikipedia=s[13],
            phone=s[14]
        ) for s in suggestions
    ]
    return formatted_suggestions


def get_places(input, max_num=20):
    """
    Retrieve from the databases addresses, streets, pois and whatever is the closest match to the input string.
    """
    # result_list = ls.find_address_in_db(input)
    # clean the string
    clean_string = ls.correct_name(input)

    result_list = ls.places_sql(clean_string, max_num)

    ## NEW FORMAT
    formatted_suggestions = [
            format_response_address(
                type=result[0],
                title=f"{result[8]}" if result[0] == "poi" else f"{result[6]} {result[7]}" if result[0] == "address" else f"{result[16]}" if result[0] == "street" else "Location",
                similarity=result[1],
                latitude=result[2],
                longitude=result[3],
                shape=result[4],
                # ADDRESS
                address_street=result[5],
                address_neigh=result[6],
                housenumber=result[7],
                # POI
                poiname=result[8],
                poicategoryname=result[9],
                opening_hours=result[10],
                wheelchair=result[11],
                toilets=result[12],
                toilets_wheelchair=result[13],
                wikipedia=result[14],
                phone=result[15],
                # STREET
                street_name=result[16],
                name_alt=result[17],
                name_spe=result[18],
                name_den=result[19],
                # NEIGHBORHOOD
                neighborhood_name=result[20],
                zipcode=result[21]
            )
        for result in result_list
    ]

    # # clean the string
    # clean_string = ls.correct_name(input)
    # # divide number and text
    # text, number, isAddress = ls.dividiEtImpera(clean_string)
    # # search in the db
    # places, score_list, exact = ls.fuzzy_search(input, isAddress, score_cutoff=70)
    # # suggestions = ls.suggest_address_from_db(text=text, number=number, max_n=max_num)
    ## OLD FORMAT
    # formatted_suggestions = [
    #     {'type': p.__tablename__,
    #      'description': p.get_description()
    #      } for p, s in zip(places, score_list)
    # ]

    return formatted_suggestions


def generate_short_url(payload: str, endpoint: str, length: int, words_code: bool):
    """
    Saves the payload in the database (as text in a json file) and the endpoint,
    generates a short code which is saved as well and returned to the frontend.
    """
    short_colde_valid = False
    while not short_colde_valid:
        if not words_code: # use words!
            short_code = generate_short_code(num_of_chars=length)
        else: # efficient short code
            short_code = generate_words_code()
        ipdb.set_trace()
        if not ShortURL.query.filter_by(shortcode=short_code).one_or_none():
            short_colde_valid = True
    generation_date = dt.datetime.today()
    expiration_date = generation_date + dt.timedelta(days=7)
    short_url = ShortURL(endpoint=endpoint, shortcode=short_code, payload=payload, generation_date=generation_date, expiration_date=expiration_date)
    db.session.add(short_url)
    db.session.commit()
    return {"short_code": short_code}


def generate_short_code(num_of_chars: int):
    """Function to generate short_id of specified number of characters"""
    return ''.join(choice(string.ascii_letters+string.digits) for _ in range(num_of_chars))

def generate_words_code():
    """Generates a short code based on words, which is less efficient but more human and fun"""
    # the wcg is created in __init__.py befor the graphs
    # and is hopefully loaded into the current_app variable
    return current_app.wcg.create_words_code()


def get_from_short_code(short_code):
    short_url = ShortURL.query.filter_by(shortcode=short_code).one_or_none()
    if not short_url:
        raise ValueError("Short code does not exist")
    return short_url.endpoint, short_url.payload
