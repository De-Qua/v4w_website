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


def get_weight_motorboat(graph, boat_speed=5, starting_hour=None):
    """ TBD: La funzione non è implementata. Bisogna controllare come fare per
    i sensi unici """
    # TODO: Utilizzare grafo directed per grafo acqueo
    if starting_hour is None:
        starting_hour = int(datetime.datetime.now().strftime("%H"))
    length = get_weight_length(graph)
    max_speed = graph.ep['vel_max'].a + 0  # trick to copy the array
    speed = np.minimum(boat_speed, max_speed)
    length.a /= speed

    return length
