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
# lib graph tool / la giusta
from app.src.libpy import lib_graph_tool as lgt
# graph tool weights
from app.src.libpy import lib_weights as lw
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
                raise errors.CoordinatesError(f'You must give exactly two coordinates')
            except AttributeError:
                raise errors.CoordinatesError(f'Input coordinates "{coord}" do not match the example format "12.339041,45.434268"')

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


def find_shortest_path_from_coordinates(**params):
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
    if params['mode'] == 'walk':
        fn_shortest_path = gt_shortest_path_walk_wrapper
        fn_info_path = format_path_walk_data
    elif params['mode'] == 'boat':
        fn_shortest_path = gt_shortest_path_boat_wrapper
        fn_info_path = format_path_boat_data
    else:
        return {'code': MISSING_PARAMETER, 'data': None}

    # get the edges and nodes
    try:
        v_list, e_list = fn_shortest_path(params)
        # and format for js
        info_dict = fn_info_path(v_list, e_list, params)
    except errors.NoPathFound:
        return {'code': NO_PATH_FOUND, 'data': None}
    except NotImplementedError:
        return {'code': WORK_IN_PROGRESS, 'data': None}
    except Exception:
        return {'code': UNKNOWN_EXCEPTION, 'data': None}

    return {'code': ALL_GOOD, 'data': info_dict}


def gt_shortest_path_boat_wrapper(start, end, stop=None, **kwargs):
    """
    NOT IMPLEMENTED YET
    It calculates the shortest path using a boat
    It returns 2 values, list of vertices and list of edges. If no path is found it raises a NoPathFound exception.
    """

    raise NotImplementedError("The path by boat is not yet implemented")


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
    weight = lw.get_weight(graph=graph['graph'], mode='walk', speed=speed, avoid_bridges=avoid_bridges, avoid_tide=avoid_tide, tide_level=tide_level, boots_height=boots_height)

    # get the path
    v_list, e_list = lgt.calculate_path(
                graph=graph,
                coords_start=start,
                coords_end=end,
                coords_stop=stop,
                weight=weight,
                all_vertices=graph['all_vertices']
                )

    if not v_list:
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

    info = lgt.retrieve_info_from_path_streets(graph=current_app.graphs['street']['graph'], paths_vertices=v_list, paths_edges=e_list, **kwargs)

    return info


def format_path_boat_data(v_list, e_list, mode, **kwargs):
    """
    Function to format the data of a path
    """

    raise NotImplementedError("Retrieving info of path by boat is not yet implemented")


def gt_shortest_path_wrapper(start, end, mode='WALKING'):
    """
    It calculates the shortest path by calling the methods in lib_graph_tool.
    It returns 3 values, exit_code (0 good, > 0 bad), list of vertices and list of edges.
    """
    if mode == "BOAT": ### TODO
        return WORK_IN_PROGRESS, None, None

    elif mode == "WALKING":
        v_list, e_list = lgt.calculate_path(site_params.G_terra, start, end)
        return ALL_GOOD, v_list, e_list

    else:
        return UNKNOWN_MODE, None, None


def get_current_tide_level():
    """
    Fetch the high tide level from the JSON file.
    """
    tide_level_dict = None
    while not tide_level_dict:
        try:
            with open(os.path.join(os.getcwd(), site_params.high_tide_file),'r') as stream:
                tide_level_dict = json.load(stream)
        except:
            app.logger.error('Error in reading tide file')
            time.sleep(0.001)
    tide_level_value = tide_level_dict.get('valore', None)
    tide_level = int(float(tide_level_value[:-2])*100) if tide_level_value else None

    return tide_level
