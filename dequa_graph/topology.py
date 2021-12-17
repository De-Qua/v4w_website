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
import ipdb
# from numbers import Number
from datetime import timedelta
import numpy as np

import graph_tool.all as gt

from . import set_up_logging
from .geographic import find_closest_vertices
from .utils import get_all_coordinates
from .errors import NoPathFound, MultipleSourcesError, FormatError
from .visitors import dequaVisitor


logger = set_up_logging()


def get_path(graph, vertex_start, vertex_end, vertices_stop=None, weights=None,
             use_public_transport=False, start_time=None, time_edge_property=None,
             transport_property=None, timetable_property=None):
    """Calculate the shortest path that starts with the first coodinates in the
    list, make stops for each intermediate coordinates, and end with the last
    coordinates in the list.
    """
    if vertices_stop is None:
        vertices_stop = []
    try:
        _ = iter(weights)
    except TypeError:
        weights = [weights]
    v_list = []
    e_list = []
    t_list = []

    vertices_stop.append(vertex_end)
    # loop over the alternatives
    for weight in weights:
        tmp_v_list = []
        tmp_e_list = []
        tmp_t_list = []
        last_v = vertex_start
        # loop over the stops
        for v in vertices_stop:
            if use_public_transport:
                # il nuovo visitor
                tmp_v_list_weight, tmp_e_list_weight, tmp_t_list_weight = td_shortest_path(graph, last_v, v, weight, start_time, time_edge_property, transport_property, timetable_property)
                start_time += timedelta(seconds=sum(tmp_t_list_weight))
            else:
                tmp_v_list_weight, tmp_e_list_weight = gt.shortest_path(graph, last_v, v, weight)
                # times are the weights since it is not time-dependent path
                tmp_t_list_weight = tmp_e_list_weight
            if not tmp_v_list_weight:
                logger.warning(f"No path between {last_v} and {v}")
                raise NoPathFound(last_v, v)
                # v_list = e_list = []
                # return v_list, e_list
            last_v = v
            tmp_v_list.append(tmp_v_list_weight)
            tmp_e_list.append(tmp_e_list_weight)
            tmp_t_list.append(tmp_t_list_weight)
        v_list.append(tmp_v_list)
        e_list.append(tmp_e_list)
        t_list.append(tmp_t_list)

    return v_list, e_list, t_list


def td_shortest_path(graph, source, target, weight, start_time, time_edge_property, transport_property, timetable_property):
    """
    Get the time-dependent shortest path by using Dijkstra algorithm
    """
    # convert start time to seconds
    start_seconds = start_time.weekday() * 24 * 3600 + start_time.hour * 3600 + start_time.minute * 60 + start_time.second

    # define some porperty for internal use
    touch_v = graph.new_vertex_property("bool")
    time_from_source = graph.new_vertex_property("double")
    dist, pred = gt.dijkstra_search(g=graph,
                                    weight=weight,
                                    source=source,
                                    visitor=dequaVisitor(touched_v=touch_v,
                                                         target=target,
                                                         time_from_source=time_from_source,
                                                         graph_weights=weight,
                                                         start_time=start_seconds,
                                                         time_edges=time_edge_property,
                                                         transport_property=transport_property,
                                                         timetable_property=timetable_property))
    # no path to target
    if pred[target] == int(target):
        return [], []
    # Create list of vertices and edges
    v = target
    vlist = [v]
    elist = []
    tlist = []  # times of each edge
    while v != source:
        p = graph.vertex(pred[v])
        vlist.append(p)
        elist.append(graph.edge(v, p))
        tlist.append(time_from_source[v]-time_from_source[p])
        v = p
    # reverse list of vertex and edges
    vlist.reverse()
    elist.reverse()
    tlist.reverse()

    return vlist, elist, tlist


def calculate_path(graph, coords_start, coords_end, coords_stop=None,
                   weight=None, all_vertices=np.ndarray(0),
                   use_public_transport=False, start_time=None, time_edge_property=None,
                   transport_property=None, timetable_property=None):
    """Calculate the shortest path between two coordinates."""
    # if all_vertices.size == 0:
    #     all_vertices = get_all_coordinates(graph)

    start_v = find_closest_vertices(coords_start, all_vertices)
    if len(start_v) > 1:
        logger.error(f"We cannot calculate the path from multiple sources")
        raise MultipleSourcesError
        # return [], []
    else:
        start_v = start_v[0]
    end_v = find_closest_vertices(coords_end, all_vertices)
    if len(end_v) > 1:
        logger.error(f"We cannot calculate the path from multiple sources")
        raise MultipleSourcesError
        # return [], []
    else:
        end_v = end_v[0]
    stop_v = find_closest_vertices(coords_stop, all_vertices)

    v_list, e_list, t_list = get_path(graph, start_v, end_v, stop_v, weight, use_public_transport, start_time, time_edge_property, transport_property, timetable_property)
    return v_list, e_list, t_list


def get_distance(graph, vertex_start, vertices_end, weight):
    """Calculates the shortest distance in the input graph between one source
    vertex and one (or a list of) target vertex.
    """
    dist = gt.shortest_distance(graph, vertex_start, vertices_end, weight)
    return dist


def calculate_distance(graph, coords_start, coords_end, weight, all_vertices=np.ndarray(0)):
    """Calculate the distance between two coordinates."""
    if all_vertices.size == 0:
        all_vertices = get_all_coordinates(graph)

    start_v = find_closest_vertices(coords_start, all_vertices)
    if len(start_v) == 1:
        start_v = start_v[0]
    else:
        logger.error(f"We cannot calculate the path from multiple sources")
        raise MultipleSourcesError
        # return -1
    end_v = find_closest_vertices(coords_end, all_vertices)

    dist = get_distance(graph, start_v, end_v, weight)
    return dist


def reorder_vertices_for_salesman(graph, vertex_start, vertices_stops, vertex_end=None, weight=None):
    """Reorder the coordinates to optimize the travelling salesman problem."""

    if not vertex_start or not vertices_stops:
        logger.error("You must give exactly one start and at least one stop coordinate")
        raise FormatError("You must give exactly one start and at least one stop coordinate")
        # return vertex_start, vertices_stops, vertex_end
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
