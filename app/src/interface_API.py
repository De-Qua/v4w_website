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

# FLASK APP
from app import app
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


def find_shortest_path_from_coordinates(start, end, mode='walk', **params):
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
    if mode == 'walk':
        fn_shortest_path = gt_shortest_path_walk_wrapper
        fn_info_path = format_path_walk_data
    elif mode == 'boat':
        fn_shortest_path = gt_shortest_path_boat_wrapper
        fn_info_path = format_path_boat_data
    else:
        return {'code': MISSING_PARAMETER, 'data': None}

    # get the edges and nodes
    # try:
    v_list, e_list = fn_shortest_path(start, end, **params)
    # and format for js
    info_dict = fn_info_path(v_list, e_list, params)
    # except errors.NoPathFound:
    #     return {'code': NO_PATH_FOUND, 'data': None}
    # except NotImplementedError:
    #     return {'code': WORK_IN_PROGRESS, 'data': None}
    # except Exception:
    #     return {'code': UNKNOWN_EXCEPTION, 'data': None}

    return info_dict


def gt_shortest_path_boat_wrapper(start, end, stop=None, **kwargs):
    """
    NOT IMPLEMENTED YET
    It calculates the shortest path using a boat
    It returns 2 values, list of vertices and list of edges. If no path is found it raises a NoPathFound exception.
    """
    graph = current_app.graphs['water']
    # Define the weight that we will use
    weight = dqg_weight.get_weight(graph=graph['graph'], mode='boat')
    # get the path
    try:
        v_list, e_list = dqg_topo.calculate_path(
                    graph=graph['graph'],
                    coords_start=start,
                    coords_end=end,
                    coords_stop=stop,
                    weight=weight,
                    all_vertices=graph['all_vertices']
                    )
    except dqg_err.NoPathFound:
        raise errors.NoPathFound(f"No path found between {start} and {end}")
    return v_list, e_list


def gt_shortest_path_walk_wrapper(start, end, stop=None, speed=5, avoid_bridges=False, avoid_tide=False, tide_level=None, boots_height=0, **kwargs):
    """
    It calculates the shortest path by calling the methods in lib_graph_tool.
    It returns 2 values, list of vertices and list of edges. If no path is found it raises a NoPathFound exception.
    """
    # get the correct graph
    graph = current_app.graphs['street']
    # get tide if not present
    if avoid_tide and not tide_level:
        tide_level = get_current_tide_level()
    # Define the weight that we will use
    weight = dqg_weight.get_weight(graph=graph['graph'], mode='walk', speed=speed, avoid_bridges=avoid_bridges, avoid_tide=avoid_tide, tide_level=tide_level, boots_height=boots_height)

    # get the path
    try:
        v_list, e_list = dqg_topo.calculate_path(
                    graph=graph['graph'],
                    coords_start=start,
                    coords_end=end,
                    coords_stop=stop,
                    weight=weight,
                    all_vertices=graph['all_vertices']
                    )

    except dqg_err.NoPathFound:
        raise errors.NoPathFound(f"No path found between {start} and {end}")

    return v_list, e_list
    # # retrieve info of the path
    # info = lgt.retrieve_info_from_path_streets(
    #             graph=graph['graph'],
    #             paths_vertices=v_list,
    #             paths_edges=e_list
    #             )
    # return info


def format_path_walk_data(v_list, e_list, mode, **kwargs):
    """
    Function to format the data of a path
    """

    info = dqg_form.retrieve_info_from_path_streets(graph=current_app.graphs['street']['graph'], paths_vertices=v_list, paths_edges=e_list, **kwargs)

    return info


def format_path_boat_data(v_list, e_list, mode, **kwargs):
    """
    Function to format the data of a path
    """

    info = dqg_form.retrieve_info_from_path_water(graph=current_app.graphs['water']['graph'], paths_vertices=v_list, paths_edges=e_list, **kwargs)
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
    tide_level_dict = None
    max_waiting_time = 10
    elapsed_time = 0
    start_time = time.time()
    while not tide_level_dict or elapsed_time < max_waiting_time:
        try:
            with open(os.path.join(os.getcwd(), site_params.high_tide_file),'r') as stream:
                tide_level_dict = json.load(stream)
        except:
            app.logger.error('Error in reading tide file')
            time.sleep(0.001)
            elapsed_time = time.time()-start_time
    tide_level_value = tide_level_dict.get('valore', None)
    tide_level = int(float(tide_level_value[:-2])*100) if tide_level_value else None

    return tide_level


def get_suggestions(input, max_num=5):
    """
    Retrieve from the databases addresses that have a partial match with the input string.
    """
    # clean the string
    clean_string = ls.correct_name(input)
    # divide number and text
    text, number, _ = ls.dividiEtImpera(clean_string)
    # get the suggestions
    suggestions = ls.suggest_address_from_db(text=text, number=number, max_n=max_num)

    formatted_suggestions = [
        {'address': f"{s.neighborhood.name} {s.housenumber}",
         'longitude': s.longitude,
         'latitude': s.latitude,
         'neighborhood': s.neighborhood.name,
         'street': s.street.name,
         'housenumber': s.housenumber
         } for s in suggestions
    ]

    return formatted_suggestions
