import requests
import json
import numpy as np
import matplotlib.pyplot as plt# Collect coords into list
import ipdb

def download_data(bbox, filters, what='nodes'):

    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    """
    if type(bbox) is list:
        overpass_query += """("""
        # convert list in string without [ ]
        bbox_query = str(bbox)[1:-1]
    elif type(bbox is int):
        overpass_query += "relation   ({rel}) -> .c ; \
        .c map_to_area -> .myarea ; \
        ( ".format(rel=bbox)
        # set the new object as bbox
        bbox_query = "area.myarea"
    if what == 'nodes':
        for filter in filters:
            overpass_query += "\n"
            overpass_query += "node[{filter}]({bbox});".format(filter=filter, bbox=bbox_query);
    elif what == 'ways':
        for filter in filters:
            overpass_query += "\n"
            overpass_query += "way[{filter}]({bbox});".format(filter=filter, bbox=bbox_query);
    elif what == 'relations':
        for filter in filters:
            overpass_query += "\n"
            overpass_query += "relation[{filter}]({bbox});".format(filter=filter, bbox=bbox_query);
    elif what == 'all':
        for filter in filters:
            overpass_query += "\n"
            overpass_query += "node[{filter}]({bbox}); \
            way[{filter}]({bbox}); \
            relation[{filter}]({bbox});".format(filter=filter, bbox=bbox_query);

    overpass_query += """
    );
    out center;
    """
    print(overpass_query)
    response = requests.get(overpass_url,params={'data': overpass_query})
    # ipdb.set_trace()
    data = response.json()

    return data

def save_data_as(data, path):

    with open(path, 'w') as outfile:
        json.dump(data, outfile)

def remove_headers_and_tolist(data):

    values_data = data.values()
    return list(values_data)[3]

def show_us_how_one_node_look_like(data):

    values_data = data.values()
    print(values_data[0])


def draw_the_data(data, titlePlot):

    coords = []
    for element in data['elements']:
      if element['type'] == 'node':
        lon = element['lon']
        lat = element['lat']
        coords.append((lon, lat))
      elif 'center' in element:
        lon = element['center']['lon']
        lat = element['center']['lat']
        coords.append((lon, lat))# Convert coordinates into numpy array
    X = np.array(coords)
    plt.plot(X[:, 0], X[:, 1], 'o')
    plt.title(titlePlot)
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.axis('equal')
    plt.show()
