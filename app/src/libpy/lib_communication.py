"""
It handles the communication between python/flask on the server and HTML/CSS/JavaScript on the site.
"""
import numpy as np
import pdb
import json
from app.src.libpy import lib_graph
import pdb
import re
from flask import g

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

def info_path_to_dictionary(path_list):
    """
    Merge a list of paths in one single dictionary
    """
    if not type(path_list) == list:
        path_list = [path_list]
    # define a new empty dict
    merged_path = {
        'lunghezza': 0,
        'human_readable_length': '',
        'time': 0,
        'human_readable_time':'',
        'n_ponti': [0,[0,0,0,0,0,0,0,0]],
        'shape_list': [],
        'altezza': np.inf,
        'tide_level': 0,
        'tide_level_current': 0,
        'm_wet': 0,
        'm_under_water': 0,
        'm_passerelle': 0,
        'human_readable_tide': '',
        }
    # loop in the list retrieving data
    for path in path_list:
        if path is not None:
            merged_path['lunghezza'] += path['lunghezza']
            merged_path['time'] += path['time']
            merged_path['n_ponti'][0] += path['n_ponti'][0]
            merged_path['n_ponti'][1] = [x+y for x,y in zip(merged_path['n_ponti'][1],path['n_ponti'][1])]
            merged_path['shape_list'] += path['shape_list']
            merged_path['altezza'] = np.minimum(merged_path['altezza'], path['altezza']) if path['altezza'] else np.inf
            merged_path['m_wet'] += path.get('m_wet', 0)
            merged_path['m_under_water'] += path.get('m_under_water', 0)
            merged_path['m_passerelle'] += path.get('m_passerelle', 0)
    # calculate new human readable data
    merged_path['human_readable_length'] = lib_graph.prettify_length(merged_path['lunghezza'])
    merged_path['human_readable_time'] = lib_graph.prettify_time(merged_path['time'])

    # change inf to none because of json
    merged_path['altezza'] = merged_path['altezza'] if merged_path['altezza'] < np.inf else None

    # tide info
    merged_path['tide_level'] = g.tide_level
    merged_path['tide_level_current'] = g.tide_level_current
    merged_path['human_readable_tide'] = lib_graph.prettify_tide(merged_path['m_wet'], merged_path['m_under_water'], merged_path['m_passerelle'])

    return merged_path

def parseFeedbackFile(file_content_as_text):
    """
    Parse the content of the file we wrote and creates a dict to pass to js.
    """
    title = get_title_from_feedback_text(file_content_as_text)
    json_to_be_drawn = get_json_from_feedback_text(file_content_as_text)
    infos = get_infos_from_feedback_text(file_content_as_text)

    contents_dict = {'title':title,
                        'infos':infos,
                        'json_to_be_drawn':json_to_be_drawn}

    return contents_dict
    #pdb.set_trace()

def get_title_from_feedback_text(text):
    """
    Extract the title between the <h1>/</h1> tags
    """
    indices_h1 = [m.start() for m in re.finditer('h1>', text)]
    if len(indices_h1) > 0:
        title = text[indices_h1[0]+4:indices_h1[1]-2]
    else:
        return "title not found"

    return title[5:-6]

def get_json_from_feedback_text(text):
    """
    Extract the json object (after <h2>JSON</h2>), loads and returns it
    """
    ind_json = text.find('JSON')
    if ind_json > 0:
        json_obj = json.loads(text[ind_json+9:])
    else:
        return "json not found"

    return json_obj

def get_infos_from_feedback_text(text):
    """
    Temporary version to be improved. Just takes everything between title and json.
    """
    ind_title_end = text.find('</h1>')
    ind_json_start = text.find('JSON')
    if ind_title_end > 0 and ind_json_start > 0:
        infos = text[ind_title_end+5:ind_json_start-4]
    else:
        return "something wrong but too lazy to document it properly: either title or json missing in the feedback file"

    return infos
