import requests
import json
import numpy as np
import matplotlib.pyplot as plt# Collect coords into list

def download_data(bbox, filters, what='nodes'):

    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = """
    [out:json];
    ("""
    if what == 'nodes':
        for filter in filters:
            overpass_query += "\n"
            overpass_query += "node[{filter}]({b1}, {b2}, {b3}, {b4});".format(filter=filter, b1=bbox[0], b2=bbox[1], b3=bbox[2], b4=bbox[3]);
    elif what == 'all':
        for filter in filters:
            overpass_query += "\n"
            overpass_query += """node[{filter}]({b1}, {b2}, {b3}, {b4});
            way[{filter}](bbox[0], bbox[1], bbox[2], bbox[3]);
            relation[{filter}](bbox[0], bbox[1], bbox[2], bbox[3]);""".format(filter=filter, b1=bbox[0], b2=bbox[1], b3=bbox[2], b4=bbox[3]);
    overpass_query += """
    );
    out center;
    """
    print(overpass_query)
    response = requests.get(overpass_url,params={'data': overpass_query})
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
