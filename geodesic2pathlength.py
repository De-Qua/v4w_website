"""
Script to study the relationship between the geodesic distance of two points
in Venice and the real length of the path
"""
import random
import pickle
import numpy as np
from matplotlib import pyplot as plt

from app import db
from app.models import *
from app.src.libpy import lib_search, lib_graph
from app.api import set_default_request_variables
from app.src.interface import find_what_needs_to_be_found

#%% Configuration parameters

neighborhoods_list = [
    "CANNAREGIO",
    "CASTELLO",
    "DORSODURO",
    "SAN MARCO",
    "SAN POLO",
    "SANTA CROCE",
    "SANT'ELENA"
]

number_of_points_for_neighborhood = 20

path_graph = '/Users/ale/Documents/Venezia/MappaDisabili/code/v4w_website/app/static/files/dequa_ve_terra_v13_1711_pickle_4326VE'

#%% Load the graph

G = pickle.load(open(path_graph, 'rb'))
G_array = np.asarray(list(G.nodes))

#%% Extract the locations that will be used for the analysis

coords = []
for n in neighborhoods_list:
    all_locations = Location.query.join(Neighborhood).filter_by(name=n).distinct()
    idx_locations = [l.id for l in all_locations]
    selected_idx = random.sample(idx_locations, number_of_points_for_neighborhood)
    for idx in selected_idx:
        l = Location.query.get(idx)
        lon_lat = (l.longitude, l.latitude)
        coords.append(lon_lat)

# plot of selected points
plt.scatter(*zip(*coords))

#%% Shuffle the list in order to create a list of start points and one of end points


def shuffle_list(some_list):
    """
    Function that returns a shuffled list with all the idx different from the
    original list
    """
    randomized_list = some_list[:]
    while True:
        random.shuffle(randomized_list)
        for a, b in zip(some_list, randomized_list):
            if a == b:
                break
        else:
            return randomized_list


start_coords = coords
end_coords = shuffle_list(start_coords)

# plot of selected paths
for coords_start, coords_end in zip(*[start_coords, end_coords]):
    plt.plot([coords_start[0], coords_end[0]], [coords_start[1], coords_end[1]])

#%% For each couple of start-end points calculates geodesic distance and path

# coords_start = start_coords[0]
# coords_end = end_coords[0]
# loop over start-end points
geo_length = []
path_length = []
for coords_start, coords_end in zip(*[start_coords, end_coords]):
    #geodesic distance
    length_geo = lib_search.distance_from_point_to_point(coords_start, coords_end)
    #path
    dists = [lib_search.distance_from_a_list_of_geo_coordinates(c, G_array) for c in [coords_start, coords_end]]
    closest_ids = [np.argmin(d) for d in dists]
    node_start = tuple(G_array[closest_ids[0]])
    node_end = tuple(G_array[closest_ids[1]])
    try:
        _, length_path = lib_graph.calculate_path_wkt(G, node_start, node_end, 'length')
    except:
        length_geo = np.nan
        length_path = np.nan
        print(f"No path between {coords_start} and {coords_end}")

    geo_length.append(length_geo)
    path_length.append(length_path)
