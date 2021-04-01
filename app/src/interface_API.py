"""
Interfaccia intesa come punto di controllo tra le API e i metodi interni.
Qui controlliamo che i parametri in ingresso dalle API siano settati nel modo corretto, se no ritorniamo indietro un avviso.
Avere una struttura fissa e ben definita penso sia utile se poi le API sono usate da esterni.
"""
# non importiamo lib_graph // questa libreria deve usare solo graph_tool
# se no ha poco senso avere il nuovo file, era per aiutare nel cambio

# CODICI DI ERRORE
from app.src.api.constants import *
# PARAMETERS (like the graph)
import app.site_parameters as site_params
# lib graph tool / la giusta
from app.src.libpy import lib_graph_tool as lgt
# communication for formatting
from app.src.libpy.libcommunication import format_path_data

def find_shortest_path_from_coordinates(params_research):
    """
    Search for the shortest path from coordinates A to B.
    If A or B are not coordinates, gives back a warning and does not calculate anything.
    It returns a dict with 'code' (0 = good, anything else, did not work)
    and 'data' (the shortest path or None).
    """
    start_coord = params_research['start_coord']
    end_coord = params_research['end_coord']

    # check that they actually are coordinates
    if not start_coord or not end_coord:
        return {'code':INPUT_SHOULD_BE_COORDINATES, 'data':None}

    # check how the street should be calculated
    mode = 'BOAT' if params_research['by_boat'] == "on" else 'WALKING'

    # get the edges and nodes
    exit_code, v_list, e_list = gt_shortest_path_wrapper(start_coord, end_coord, mode)
    if exit_code > 0:
        return {'code':exit_code, 'data':None}

    # and format for js
    data_dict = format_path_data(v_list, e_list)

    return {'code': ALL_GOOD, 'data': data_dict}

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
            with open(os.path.join(os.getcwd(), site_parameters.high_tide_file),'r') as stream:
                tide_level_dict = json.load(stream)
        except:
            app.logger.debug('Error in reading tide file')
            time.sleep(0.001)
    tide_level_value = tide_level_dict.get('valore', None)
    tide_level = int(float(tide_level_value[:-2])*100) if tide_level_value else None
    return tide_level
