import numpy as np
from shapely.geometry import mapping

from .utils import adjacent_one


def retrieve_info_from_path_streets(graph, paths_vertices, paths_edges, speed=5, **kwargs):
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
    all_info = []
    for alternative_path in paths_edges:
        info = []
        for edges in alternative_path:
            distances = []
            times = []
            is_bridge = []
            geojsons = []

            for e in edges:

                edge_info = {
                    # Calculate distance
                    'distance': graph.ep['length'][e],
                    # Calculate time
                    'time': graph.ep['length'][e]/speed,
                    # Calculate number of bridges
                    'bridge': graph.ep['ponte'][e],
                    # append maximum tide level
                    'max_tide': graph.ep['max_tide'][e],
                    # append accessibility
                    'accessibility': graph.ep['accessible'][e],
                    # append walkways zps activation
                    'walkway_zps': graph.ep['pas_cm_zps'][e],
                    # append walkways height
                    'walkway_cm': graph.ep['pas_height'][e],
                    # append street id
                    'street_id': graph.ep['street_id'][e]
                }
                # correct for NaN values
                for k, v in edge_info.items():
                    if np.isnan(v):
                        edge_info[k] = None
                # append geometries
                geojson = {
                    "type": "Feature",
                    "properties": edge_info,
                    "geometry": mapping(graph.ep['geometry'][e])
                }
                geojsons.append(geojson)

                # update distance, time and bridges
                distances.append(edge_info['distance'])
                times.append(edge_info['time'])
                is_bridge.append(edge_info['bridge'])

            distance = sum(distances)
            time = sum(times)
            num_bridges = adjacent_one(is_bridge)

            info.append({
                'distance': distance,
                'time': time,
                'num_bridges': num_bridges,
                'num_edges': len(edges),
                'edges': geojsons
            })
        all_info.append(info)
    return all_info


def retrieve_info_from_path_water(graph, paths_vertices, paths_edges, speed=5, **kwargs):
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
    all_info = []
    for alternative_path in paths_edges:
        info = []
        for edges in alternative_path:
            distances = []
            geometries = []

            for e in edges:
                # Calculate distance
                distances.append(graph.ep['length'][e])
                # append geometries
                geojson = {
                    "type": "Feature",
                    "geometry": mapping(graph.ep['geometry'][e])
                }
                geometries.append(geojson)

            distance = sum(distances)

            info.append({
                'distance': distance,
                'num_edges': len(edges),
                'edges': {
                    'distances': distances,
                    'geometry': geometries,
                }
            })
        all_info.append(info)
    return all_info


def length_of_edges(graph, edge_list):
    """Calculate the length of a list of edges"""
    return sum([graph.ep['length'][e] for e in edge_list])
