"""
Library to handle the weights that will be used in the search of the shortest
path.
All the functions return an edge property with the required weights.
For each function the only required input is the graph, all the other arguments
are optional, nonetheless some of the arguments are crucial for determining the
weight, therefore in that case a custom value should be used.

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

import numpy as np
import datetime

import graph_tool.all as gt

def get_weight(graph, mode='walk', speed=5, avoid_bridges=False, avoid_tide=False, tide_level=80, boots_height=0,
boat_speed=5, starting_hour=None):
    """
    Helper function to get the correct weight base on the requested mode and the other variables.
    Available modes:
        walk:   get_weight_time()
        bridge: get_weight_bridges()
        tide:   get_weight_tide()
    """
    if mode == 'walk':
        if avoid_tide:
            return get_weight_tide(graph=graph, tide_level=tide_level,
                                boots_height=boots_height, speed=speed,
                                use_weight_bridges=avoid_bridges)
        elif avoid_bridges:
            return get_weight_bridges(graph=graph, speed=speed)
        else:
            return get_weight_time(graph=graph, speed=speed)
    elif mode == 'boat':
        return get_weight_motorboat(graph=graph, speed=boat_speed)
    else:
        raise ValueError(f"Mode {mode} not implemented")


def get_weight_length(graph):
    """Returns a graph edge property that can be used in searching the shortest
    path.
    Weights correspond to the length of each edge.
    """
    # retrieve the length as a copy of the internal edge property 'length'
    weight = graph.new_ep('double')
    weight.a = graph.ep['length'].a
    return weight


def get_weight_time(graph, speed=5):
    """Returns a graph edge property that can be used in searching the shortest
    path.
    Weights correspond to the length of each edge.
    """
    if not speed:
        return get_weight_length(graph)
    weight = graph.new_ep('double')
    weight.a = graph.ep['length'].a/speed
    return weight


def get_weight_bridges(graph, bridge_multiplier=100, speed=5):
    """Returns a graph edge property that can be used in searching the shortest
    path.
    Weights correspond to the length of each edge if the edge is not a
    bridge, otherwise the length multiplied by the bridge_multiplier factor.
    """

    # retrieve from edges basic ltimeength and which edge is a bridge
    weight = get_weight_time(graph, speed)
    # calculate the weight adding the bridge multiplier only to the bridges
    weight.a += graph.ep['ponte'].a * bridge_multiplier
    return weight


def get_weight_tide(graph, tide_level, high_tide_multiplier=10000,
                    edge_default_height=80, safety_diff_tide=5,
                    boots_height=0, boots_speed=2.5, speed=5,
                    use_weight_bridges=False, bridge_multiplier=100):
    """Returns a graph edge property that can be used in searching the shortest
    path.
    Weights correspond to get_weight_length or get_weight_bridges (if
    use_weight_bridges is True) if the edge is above the requested tide_level,
    otherwise the length multiplied by the tide_multiplier factor.
    If the height of the edge is not present it is used the minimum value for
    the walkways, or the edge_default_height.
    If there on the edge there are walkways and these are active, the edge
    height is calculated as the height plus the height of the walkways.
    Finally, to the edge height it is added the boots_height.
    """
    # initially define the weight as a length
    if use_weight_bridges:
        weight_tide = get_weight_bridges(graph, bridge_multiplier, speed=None)
    else:
        weight_tide = get_weight_length(graph)

    # retrieve the edge height
    # otherwise use the walkways (passerelle) height
    # otherwise use default value
    edges_height = graph.ep['max_tide'].a + 0  # trick to copy the array
    walkways_zps = graph.ep['pas_cm_zps'].a + 0  # trick to copy the array
    edges_height[np.isnan(edges_height)] = walkways_zps[np.isnan(edges_height)]
    edges_height = np.nan_to_num(edges_height, nan=edge_default_height)
    # determine if walkways are active and their height
    walkways_active = walkways_zps <= tide_level
    walkways_height = graph.ep['pas_height'].a + 0  # trick to copy the array
    walkways_height = np.nan_to_num(walkways_height, nan=0.0)

    total_height = edges_height + walkways_active * walkways_height

    cm_below_boots = np.maximum(0,
                                tide_level + safety_diff_tide - total_height)
    cm_below_boots[cm_below_boots >= boots_height] = 0
    # calculate for each edge the cm under water (if negative put 0)
    cm_under_water = np.maximum(0,
                                tide_level + safety_diff_tide
                                - total_height - boots_height)

    # if it is a bridge it is never under water
    bridges = graph.ep['ponte'].a
    cm_below_boots[bridges] = 0
    cm_under_water[bridges] = 0
    # calculate the weight adding to the length the tide multiplier times the
    # cm under water
    weight_tide.a[cm_below_boots == 0] /= speed
    weight_tide.a[cm_below_boots > 0] /= boots_speed

    weight_tide.a += high_tide_multiplier * cm_under_water

    return weight_tide

#
# WEIGHTS FOR BOATS
#

def get_weight_rowboat(graph, speed=5):
    """Returns a graph edge property that can be used in searching the shortest path in a water graph.
    Weights correspond to the time of each edge (length/speed).
    Since rowboat do not have any restriction all the canals are allowed, and the graph is considered undirected.
    """
    graph_row = gt.GraphView(graph, directed=False)
    weight = get_weight_time(graph_row, speed)

    return weight


def get_weight_motorboat(graph, speed=5, start_time=None, type="private", width=0, height=0, rio_blu_multiplier=1e6, dimension_multiplier=1e6):
    """Returns a graph edge property that can be used in searching the shortest path in a water graph.
    Weights correspond to the time of each edge (length/speed).
    Speed is calculated as the minimum between the speed of the boat and the limit of the canals.
    Boat type can be "private" (default) or "taxi". This will change the speed limit.
    Rii blu are excluded (big multiplier to avoid problem if the path starts there).
    Canals with a width (or height) greater than the width (or height) of the boat are excluded (big multiplier to avoid problem if the path starts there).
    """
    weight = get_weight_length(graph)

    # speed limits
    if type == "private":
        speed = np.minimum(speed, graph.ep['vel_max'].a)
    elif type == "taxi":
        speed = np.minimum(speed, graph.ep['vel_max_mp'].a)
    else:
        speed = np.minimum(speed, graph.ep['vel_max'].a)

    weight.a /= speed

    # exclude rii blu (big multiplier to avoid problem if the path starts from there)
    weight.a += graph.ep['solo_remi'].a * rio_blu_multiplier
    # exclude small canals (big multiplier to avoid problem if the path starts from there)
    can_width = graph.ep['larghezza'].a+0
    can_width[can_width==0] = np.inf
    weight.a[can_width < width] += dimension_multiplier
    # exclude low canals (big multiplier to avoid problem if the path starts from there)
    weight.a[graph.ep['altezza'].a < height] += dimension_multiplier

    return weight
