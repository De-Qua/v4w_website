"""
Library to handle graph-tool functions.
In general two graphs are used: graph_street and graph_water.

Properties of graph_street are the following:
latlon         (vertex)  (type: vector<double>)
accessible     (edge)    (type: int32_t)
avg_tide       (edge)    (type: double)
geometry       (edge)    (type: python::object)
length         (edge)    (type: double)
max_tide       (edge)    (type: double)
med_tide       (edge)    (type: double)
min_tide       (edge)    (type: double)
pas_cm_zps     (edge)    (type: double)
pas_height     (edge)    (type: double)
ponte          (edge)    (type: int32_t)
street_id      (edge)    (type: double)
vel_max        (edge)    (type: double)

Properties of graph_water are the following:
latlon         (vertex)  (type: vector<double>)
altezza        (edge)    (type: double)
dt_end         (edge)    (type: int32_t)
dt_start       (edge)    (type: int32_t)
geometry       (edge)    (type: python::object)
h_su_end       (edge)    (type: int32_t)
h_su_start     (edge)    (type: int32_t)
larghezza      (edge)    (type: double)
length         (edge)    (type: double)
nome           (edge)    (type: string)
senso_unic     (edge)    (type: double)
solo_remi      (edge)    (type: int32_t)
vel_max        (edge)    (type: double)
vel_max_mp     (edge)    (type: double)

"""
import time
import logging
from itertools import groupby

import numpy as np

import graph_tool.all as gt

logger = logging.getLogger('lib_graph')
logger.setLevel(logging.DEBUG)

def load_graphs(path_gt_street, path_gt_water):
    """Loads two graph-tool graphs, one for the street and one for the water"""
    graph_street = gt.load_graph(path_gt_street)
    graph_water = gt.load_graph(path_gt_water)

    return graph_street, graph_water


def get_all_coordinates(graph):
    """Return array with vertices coordinates from a graph"""
    pos = graph.vp['latlon']
    return np.array([pos[v].a for v in graph.get_vertices()])


def distance_from_a_list_of_geo_coordinates(thePoint, coordinates_list):
    """
    A python implementation from the answer here
    https://stackoverflow.com/questions/639695/how-to-convert-latitude-or-longitude-to-meters.
    Calculate the distance in meters between 1 geographical point (longitude,
    latitude) and a list of geographical points (list of tuples) or between two
    geographical points passing through distance_from_point_to_point
    """
    # maybe we need to invert
    lat_index = 1
    lon_index = 0
    # parameters
    earth_radius = 6378.137  # Radius of earth in KM
    deg2rad = np.pi / 180
    # single point
    lat1 = thePoint[lat_index] * deg2rad
    lon1 = thePoint[lon_index] * deg2rad
    # test the whole list again the single point
    lat2 = coordinates_list[:, lat_index] * deg2rad
    lon2 = coordinates_list[:, lon_index] * deg2rad
    dLat = lat2 - lat1
    dLon = lon2 - lon1
    a = np.sin(dLat/2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dLon/2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    d = earth_radius * c
    distances_in_meters = d * 1000

    return distances_in_meters


def find_closest_vertices(coords_list, vertices_coords,
                          MIN_DIST_FOR_THE_CLOSEST_NODE=100):
    """Returns list of nodes in vertices_latlon_list closest to coordinate_list
    (euclidean distance).
    """
    # check coords_list format
    if not coords_list:
        return []
    elif type(coords_list) is not list:
        coords_list = [coords_list]

    # loop over the coords_list and find the closest verices
    nodes_list = []
    for coords in coords_list:
        t1 = time.time()
        dists = distance_from_a_list_of_geo_coordinates(thePoint=coords,
                                coordinates_list=vertices_coords)
        t2 = time.time()
        logger.debug(f"it took {t2-t1:.5f} to calculate distances")

        closest_id = np.argmin(dists)
        closest_dist = dists[closest_id]
        logger.debug(f"Distance between your node and the vertex: {closest_dist:.9f}m")
        # se la distanza e troppo grande, salutiamo i campagnoli
        if closest_dist > MIN_DIST_FOR_THE_CLOSEST_NODE:
            logger.error(f"No close vertex: closest vertex is {closest_dist}m)")
            return []
        nodes_list.append(closest_id)

    return nodes_list


def get_path(graph, vertex_start, vertex_end, vertices_stop=[], weight=None):
    """Calculate the shortest path that starts with the first coodinates in the
    list, make stops for each intermediate coordinates, and end with the last
    coordinates in the list.
    """

    v_list = []
    e_list = []
    last_v = vertex_start
    vertices_stop.append(vertex_end)
    for v in vertices_stop:
        tmp_v_list, tmp_e_list = gt.shortest_path(graph, last_v, v, weight)
        if not tmp_v_list:
            logger.warning(f"No path between {last_v} and {v}")
            v_list = e_list = []
            return v_list, e_list
        last_v = v
        v_list.append(tmp_v_list)
        e_list.append(tmp_e_list)

    return v_list, e_list


def calculate_path(graph, coords_start, coords_end, coords_stop=None,
                   weight=None, all_vertices=np.ndarray(0)):
    """Calculate the shortest path between two coordinates
    """
    # if all_vertices.size == 0:
    #     all_vertices = get_all_coordinates(graph)

    start_v = find_closest_vertices(coords_start, all_vertices)
    if len(start_v) > 1:
        logger.error(f"We cannot calculate the path from multiple sources")
        return [], []
    else:
        start_v = start_v[0]
    end_v = find_closest_vertices(coords_end, all_vertices)
    if len(end_v) > 1:
        logger.error(f"We cannot calculate the path from multiple sources")
        return [], []
    else:
        end_v = end_v[0]
    stop_v = find_closest_vertices(coords_stop, all_vertices)

    v_list, e_list = get_path(graph, start_v, end_v, stop_v, weight)
    return v_list, e_list


def get_distance(graph, vertex_start, vertices_end, weight):
    """Calculates the shortest distance in the input graph between one source
    vertex and one (or a list of) target vertex.
    """
    dist = gt.shortest_distance(graph, vertex_start, vertices_end, weight)
    return dist


def calculate_distance(graph, coords_start, coords_end, weight, all_vertices=np.ndarray(0)):
    """Calculate the shortest path between two coordinates
    """
    if all_vertices.size == 0:
        all_vertices = get_all_coordinates(graph)

    start_v = find_closest_vertices(coords_start, all_vertices)
    if len(start_v) == 1:
        start_v = start_v[0]
    else:
        logger.error(f"We cannot calculate the path from multiple sources")
        return -1
    end_v = find_closest_vertices(coords_end, all_vertices)

    dist = get_distance(graph, start_v, end_v, weight)
    return dist


def reorder_vertices_for_salesman(graph, vertex_start, vertices_stops, vertex_end=None, weight=None):
    """Reorder the coordinates to optimize the travelling salesman problem.
    """

    if not vertex_start or not vertices_stops:
        logger.error("You must give exactly one start and at least one stop coordinate")
        return vertex_start, vertices_stops, vertex_end
    if len(vertices_stops) == 1:
        return vertex_start, vertices_stops, vertex_end
    last_v = vertex_start
    best_stops = []
    remaining_v = vertices_stops[:]
    while remaining_v:
        dist = get_distance(graph, last_v, remaining_v, weight)
        best_idx = np.argmin(dist)
        best_stops.append(remaining_v[best_idx])
        last_v = remaining_v[best_idx]
        remaining_v.pop(best_idx)

    return vertex_start, best_stops, vertex_end


def length_of_edges(graph, edge_list):
    """Calculate the length of a list of edges"""
    return sum([graph.ep['length'][e] for e in edge_list])


def retrieve_info_from_path_streets(graph, paths_vertices, paths_edges):
    """Retrieve useful informations from the output of a path of streets (list
    of list of vertices and edges). The length of the two lists corresponds to
    the number of paths, i.e. if there are no stops betweem the start and the
    end point there will be only one path, otherwise there will be multiple
    paths.
    The output is a dictionary with the following keys:
        'n_paths' (int): indicates the number of paths
        'info' (list(dict)): informations of each path
    Each path has the following informations:
        'distance' (float): distance in meters
        'num_bridges' (int): the number of bridges
        'num_edges' (int): number of contained edges
        'edges' (dict): info for each single edge.
                        Each key is a list of the dimension num_edges.
            'distances' (float): distance in meters
            'bridges' (boolean): True if the edge is a bridge
            'geometries' (geometry): Geometry of the edge
            'max_tides' (float): Maximum tide for the edge in cm
            'accessibility' (int): Accessibility value
            'walkways_zps' (float): If present, tide level for activation of walkways
            'walkways_cm' (float): Height of walkways in cm
            'streets_id' (int): Database id of the street
    """
    info = {'n_paths': len(paths_edges),
            'info': []}
    for idx, edges in enumerate(paths_edges):
        distances = []
        is_bridge = []
        geometries = []
        max_tides = []
        accessibility = []
        walkways_zps = []
        walkways_cm = []
        streets_id = []

        for e in edges:
            # Calculate distance
            distances.append(graph.ep['length'][e])
            # Calculate number of bridges
            is_bridge.append(graph.ep['ponte'][e])
            # append geometries
            geometries.append(graph.ep['geometry'][e])
            # append maximum tide level
            max_tides.append(graph.ep['max_tide'][e])
            # append accessibility
            accessibility.append(graph.ep['accessible'][e])
            # append walkways zps activation
            walkways_zps.append(graph.ep['pas_cm_zps'][e])
            # append walkways height
            walkways_cm.append(graph.ep['pas_height'][e])
            # append street id
            streets_id.append(graph.ep['street_id'][e])

        distance = sum(distances)
        num_bridges = _consecutive_one(is_bridge)

        info['info'].append({
            'distance': distance,
            'num_bridges': num_bridges,
            'num_edges': len(edges)
            'edges': {
                'distances': distances,
                'bridges': is_bridge,
                'geometries': geometries,
                'max_tides': max_tides,
                'accessibility': accessibility,
                'walkways_zps': walkways_zps,
                'walkways_cm': walkways_cm,
                'streets_id': streets_id
            }
        })
    return info


def _len_iter(items):
    return sum(1 for _ in items)


def _consecutive_one(data):
    """Helper to count the maximum number of consecutive items in a list.
    Thanks to Veedrac: https://codereview.stackexchange.com/questions/138550/count-consecutive-ones-in-a-binary-list
    """
    try:
        return max(_len_iter(run) for val, run in groupby(data) if val)
    except ValueError:
        return 0
