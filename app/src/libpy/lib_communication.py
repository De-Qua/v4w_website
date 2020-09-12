"""
It handles the communication between python/flask on the server and HTML/CSS/JavaScript on the site.
"""
import numpy as np
import pdb
import json
from app.src.libpy import lib_graph
import pdb

def prepare_our_message_to_javascript(mode, strings_input, dict_of_start_locations_candidates, params_research, estimated_path=[{"shape_list":"no_path", "tipo":-1}], dict_of_end_locations_candidates="no_end", start_type='unique', end_type='unique'):
    """
    It creates the standard message with geographical informations that leaflet expects for the communication.
    """
    # leaflet vuole le coordinate invertite (x e y).
    for start in dict_of_start_locations_candidates:
        # introduci shift per Leaflet
        start['coordinate'], start['shape'] = correct_coordinates_for_leaflet(start,shift_xy=[0,0])
        xy =start['coordinate'][:]
        start['coordinate'][0]=xy[1]
        start['coordinate'][1]=xy[0]
        xy=[]
        if start['shape']:
            for coo in start['shape']:
                xy.append([coo[1],coo[0]])
            start["shape"]=xy
        if start['geojson']:
            #start['geojson'] = json.dumps(start['geojson'])
            start['geojson'] = start['geojson']
    if dict_of_end_locations_candidates is not "no_end":
        for end in dict_of_end_locations_candidates:
            end['coordinate'], end['shape'] = correct_coordinates_for_leaflet(end,shift_xy=[0,0])
            xy =end['coordinate'][:]
            end['coordinate'][0]=xy[1]
            end['coordinate'][1]=xy[0]
            if end['shape']:
                xy=[]
                for coo in end['shape']:
                    xy.append([coo[1],coo[0]])
                end["shape"]=xy
    #for path in estimated_path:
     #   if not path["strada"]=="no_path":
      #      xy=[]
       #     for coo in path["strada"]:
        #        xy.append((coo[1],coo[0]))
         #   path["strada"]=xy
    msg = dict()
    msg["modus_operandi"] = mode
    msg["partenza"] = dict_of_start_locations_candidates
    msg['start_type'] = start_type
    msg["searched_start"] = strings_input[0]
    msg['searched_end'] = strings_input[1]
    msg["path"] = estimated_path
    #msg["length_path"] = estimated_path[1]
    msg["arrivo"] = dict_of_end_locations_candidates
    msg['end_type'] = end_type
    msg['params_research'] = params_research
    return msg

def correct_coordinates_for_leaflet(dic,shift_xy = [-0.000015, +0.000015]):
    """
    Corrects our coordinates with respect to OpenStreetMaps.
    """
    coordinates=dic['coordinate']
    polygon=dic['shape']
    geo_type=dic['geotype']
    shift = np.asarray(shift_xy)
    corrected_coords = coordinates + shift
    try:
        if not geo_type < 0:
            numpy_pol = np.asarray(polygon)
            numpy_corrected_polygon = numpy_pol + shift
            corrected_polygon = numpy_corrected_polygon.tolist()
            if geo_type==0:
                corrected_polygon = [(coo[0],coo[1]) for coo in corrected_polygon]
        else:
            corrected_polygon = None
    except:
        corrected_polygon = None
    return np.ndarray.tolist(corrected_coords), corrected_polygon

def merged_path_list(path_list):
    """
    Merge a list of paths in one single dictionary
    """
    # define a new empty dict
    merged_path = {
        'lunghezza': 0,
        'human_readable_length': '',
        'time': 0,
        'human_readable_time':'',
        'n_ponti': [0,[0,0,0,0,0,0,0,0]],
        'shape_list': [],
        'altezza': np.inf
        }
    # loop in the list retrieving data
    for path in path_list:
        if path is not None:
            merged_path['lunghezza'] += path['lunghezza']
            merged_path['time'] += path['time']
            merged_path['n_ponti'][0] += path['n_ponti'][0]
            merged_path['n_ponti'][1] = [x+y for x,y in zip(merged_path['n_ponti'][1],path['n_ponti'][1])]
            merged_path['shape_list'] += path['shape_list']
            merged_path['altezza'] = np.minimum(merged_path['altezza'], path['altezza'])

    # calculate new human readable data
    merged_path['human_readable_length'] = lib_graph.prettify_length(merged_path['lunghezza'])
    merged_path['human_readable_time'] = lib_graph.prettify_time(merged_path['time'])

    return merged_path

def parseFeedbackFile(file_content_as_text):
    """
    Parse the content of the file we wrote and creates a dict to pass to js.
    """
    #pdb.set_trace()
