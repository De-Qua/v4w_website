"""
Response format
[
    PATH1
    [
        start_time
        end_time
        distances
        time
        num_bridges
        num_edges
        num_transports
        routes
        edges
    ]
    PATH2
    [
        start_time
        end_time
        distances
        time
        num_bridges
        num_edges
        num_transports

        edges
        path_steps
        [
            {
                type (walk/boat/ferry/passerella)
                start_time
                end_time
                distances
                time
                num_bridges
                route_color
                route_text_color
                route_name
                route_short_name
            }
            for route_piece
        ]
    ]
]
"""

import numpy as np
from shapely.geometry import mapping
import ipdb
from datetime import datetime, timedelta

from .utils import adjacent_one


def format_path_steps(**kwargs):
    """
    Format a single step of a path.
    A path consists of (possibly) many steps.
    A step finishes when you change mean of transportation (walk, ferry, boat).
    """
    step = {
        # General info
        "type": kwargs.get("type", "unknown"),
        "order": kwargs.get("order", -1),
        "start_time": kwargs.get("start_time", ""),
        "end_time": kwargs.get("type", ""),
        "distance": kwargs.get("distances", 0),
        "time": kwargs.get("time", 0),
        # Bridges
        "num_bridges": kwargs.get("num_bridges", 0),
        # Ferry
        "route_color": kwargs.get("route_color", "unknown"),
        "route_text_color": kwargs.get("route_text_color", "unknown"),
        "route_name": kwargs.get("route_name", "unknown"),
        "route_short_name": kwargs.get("route_short_name", "unknown"),
        "route_stops": kwargs.get("route_stops", [])
    }
    return step


def retrieve_info_from_path_streets(graph, paths_vertices, paths_edges, start_time,
                                    speed=5/3.6, times_edges=None, **kwargs):
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
        'path_steps' (list of dict): info about transportations.
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
    for alternative_path, alternative_times in zip(paths_edges, times_edges):
        info = []
        for edges, edge_times in zip(alternative_path, alternative_times):
            distances = []
            durations = []
            is_bridge = []
            is_transport = []
            geojsons = []
            ferry_routes = {}  # []
            # list of the path steps (remember to use format method to append)
            path_steps = []
            current_step = {
                "type": "walk",
                "order": 0,
                "distance": 0,
                "time": 0,
                "num_bridges": 0,
                'start_time': start_time,
            }
            # stops = []
            time_at_edge = start_time

            for e, e_time in zip(edges, edge_times):

                if graph.ep["transport"][e] == 1:
                    duration = graph.ep['duration'][e]
                    time_at_edge += timedelta(seconds=duration)
                    route = graph.ep["route"][e]["route_short_name"]
                    stop = graph.vp.stop_info[e.source()]
                    stop['clock_time'] = time_at_edge.strftime("%H:%M:%S")
                    # routes[route] exists because we passed through ferry stop
                    ferry_routes[route]["stops"].append(stop)
                else:
                    # check for the fake edges for ferry stops
                    if graph.ep["route"][e] is not None and times_edges is not None:
                        # pontile / tempo d'attesa
                        duration = e_time
                        time_at_edge += timedelta(seconds=duration)
                        route = graph.ep["route"][e]["route_short_name"]
                        # add a list with the route key
                        if route not in ferry_routes.keys():
                            first_stop = graph.vp.stop_info[e.source()]
                            first_stop['clock_time'] = time_at_edge.strftime("%H:%M:%S")
                            ferry_routes[route] = {
                                "text_color": graph.ep["route"][e]["route_text_color"],
                                "route_color": graph.ep["route"][e]["route_color"],
                                "stops": [first_stop],
                                "initial_waiting_time": e_time
                            }
                        elif e_time != 0:
                            print("DOPPIO BATTELLO CON LO STESSO NUMERO!")

                    else:
                        duration = graph.ep['length'][e]/speed
                        time_at_edge += timedelta(seconds=duration)
                    route = None
                    stop = None

                #time_at_edge += timedelta(seconds=time)

                edge_info = {
                    # Calculate distance
                    'distance': graph.ep['length'][e],
                    # Get hour at the edge
                    'clock_time': time_at_edge.strftime("%H:%M:%S"),
                    # Check if it is a transport
                    'transport': graph.ep['transport'][e],
                    # Duration (fixed for trasnport, calculated for walk/boat)
                    'duration': duration,  # graph.ep['duration'][e],
                    # Route
                    'route': route,
                    # Stop
                    'stop': stop,
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
                    if k not in ["route", "stop", "clock_time"]:
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
                durations.append(edge_info['duration'])
                is_bridge.append(edge_info['bridge'])
                is_transport.append(edge_info["transport"])

                if graph.ep["transport"][e] == 0 and current_step['type'] == 'walk':
                    # update values
                    current_step['distance'] += graph.ep['length'][e]
                    current_step['duration'] += duration
                    current_step['num_bridges'] += int(graph.ep['ponte'][e])
                elif graph.ep["transport"][e] == 1 and current_step['type'] == 'ferry':
                    # update step values
                    current_step['distance'] += graph.ep['length'][e]
                    current_step['duration'] += duration
                elif graph.ep["transport"][e] == 1 and current_step['type'] == 'walk':
                    # close walking and start transportation step
                    current_step['end_time'] = time_at_edge.strftime("%H:%M:%S")
                    # new step
                    path_steps.append(format(current_step))
                    current_step = {
                        "type": "ferry",
                        "order": path_steps[-1]['order'] + 1,
                        "distance": 0,
                        "time": 0,
                        "num_bridges": 0,
                        "start_time": time_at_edge.strftime("%H:%M:%S"),
                        # Ferry
                        "route_text_color": graph.ep["route"][e]["route_text_color"],
                        "route_color": graph.ep["route"][e]["route_color"],
                        "route_name": graph.ep["route_name"][e]["route_color"],
                        "route_short_name": graph.ep["route_short_name"][e]["route_color"]
                    }

                elif graph.ep["transport"][e] == 0 and current_step['type'] == 'ferry':
                    # close transportation step and start walking step
                    current_step["route_stops"] = ferry_routes[route]["stops"]
                    current_step['end_time'] = time_at_edge.strftime("%H:%M:%S")
                    path_steps.append(format(current_step))
                    # new one
                    current_step = {
                        "type": "walk",
                        "order": path_steps[-1]['order'] + 1,
                        "distance": 0,
                        "time": 0,
                        "num_bridges": 0,
                        'start_time': time_at_edge.strftime("%H:%M:%S"),
                    }

            tot_distance = sum(distances)
            tot_duration = sum(durations)
            num_bridges = adjacent_one(is_bridge)
            num_transports = adjacent_one(is_transport)
            info.append({
                'start_time': start_time.strftime("%d-%m-%Y %H:%M:%S"),
                'end_time': time_at_edge.strftime("%d-%m-%Y %H:%M:%S"),
                'distance': tot_distance,
                'duration': tot_duration,
                'num_bridges': num_bridges,
                'num_edges': len(edges),
                'num_transports': num_transports,
                'ferry_routes': ferry_routes,
                #'stops': stops,
                'edges': geojsons
            })
        all_info.append(info)
    return all_info


def retrieve_info_from_path_water(graph, paths_vertices, paths_edges, speed=5, **kwargs):
    """Retrieve useful informations from the output of a path of canals (list
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
            geojsons = []

            for e in edges:
                max_speed = graph.ep['vel_max'][e]
                edge_info = {
                    # Calculate distance
                    'distance': graph.ep['length'][e],
                    # Calculate time
                    'time': graph.ep['length'][e]/min(speed, max_speed),
                    # append the width
                    'width': graph.ep['larghezza'][e],
                    # append height
                    'height': graph.ep['altezza'][e],
                    # append the max speed allowed
                    'max_speed': graph.ep['vel_max'][e],
                    # append alternative max speed allowed
                    'max_speed_alt': graph.ep['vel_max_mp'][e],
                    # append rii blu
                    'rio_blu': graph.ep['solo_remi'][e],
                    # append name
                    'name': graph.ep['nome'][e],
                    # append one way
                    'one_way': graph.ep['senso_unic'][e],
                    # append starting hour
                    'start_h': graph.ep['h_su_start'][e],
                    # append ending hour
                    'end_h': graph.ep['h_su_end'][e],
                    # append starting dt
                    'start_dt': graph.ep['dt_start'][e],
                    # append ending dt
                    'end_dt': graph.ep['dt_end'][e]
                }
                # correct for NaN values
                for k, v in edge_info.items():
                    if type(v) is not str and np.isnan(v):
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

            distance = sum(distances)
            time = sum(times)

            info.append({
                'distance': distance,
                'time': time,
                'num_edges': len(edges),
                'edges': geojsons
            })
        all_info.append(info)
    return all_info


def length_of_edges(graph, edge_list):
    """Calculate the length of a list of edges"""
    return sum([graph.ep['length'][e] for e in edge_list])
