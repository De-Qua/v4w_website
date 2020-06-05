import numpy as np

def prepare_our_message_to_javascript(mode,  string_input, start_location, estimated_path=["no_path",0], end_location="no_end"):
    """
    It creates the standard message with geographical informations that leaflet expects for the communication.
    """
    
    # leaflet vuole le coordinate invertite (x e y). Per le path lo facciamo già in calculate_path
    for start in start_location:
        # introduci shift per Leaflet
        start['coordinates'], start['shape'] = correct_coordinates_for_leaflet(start)
        xy =start['coordinate'][:]
        start['coordinate'][0]=xy[1]
        start['coordinate'][1]=xy[0]
        xy=[]
        for coo in start['shape']:
            xy.append([coo[1],coo[0]])
        start["shape"]=xy
    if end_location is not "no_end":
        for end in end_location:
            end['coordinates'], end['shape'] = correct_coordinates_for_leaflet(end)
            xy =end['coordinate'][:]
            end['coordinate'][0]=xy[1]
            end['coordinate'][1]=xy[0]
            xy=[]
            for coo in end['shape']:
                xy.append([coo[1],coo[0]])
            end["shape"]=xy

    if not estimated_path==["no_path",0]:
        xy=[]
        for coo in estimated_path[0]:
            xy.append((coo[1],coo[0]))
        estimated_path[0]=xy

    msg = dict()
    msg["modus_operandi"] = mode
    msg["partenza"] = start_location
    msg["searched_name"] = string_input
    msg["path"] = estimated_path[0]
    msg["length_path"] = estimated_path[1]
    msg["arrivo"] = end_location

    return msg

def correct_coordinates_for_leaflet(dic):
    """
    Corrects our coordinates with respect to OpenStreetMaps.
    """
    coordinates=dic['coordinate']
    polygon=dic['shape']
    geo_type=dic['geotype']
    shift = np.asarray([-0.000015, +0.000015])
    corrected_coords = coordinates + shift
    if not geo_type < 0:
        numpy_pol = np.asarray(polygon)
        numpy_corrected_polygon = numpy_pol + shift
        corrected_polygon = numpy_corrected_polygon.tolist()
        if geo_type==0:
            corrected_polygon = [(coo[0],coo[1]) for coo in corrected_polygon]
    else:
        corrected_polygon = None

    return np.ndarray.tolist(corrected_coords), corrected_polygon
