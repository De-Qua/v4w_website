"""Useful functions."""

import numpy as np
from itertools import groupby
from shapely.geometry import LineString
from shapely.ops import transform

import graph_tool.all as gt
import ipdb
# IMPORT OUR LIBRARIES
from . import set_up_logging
from . import lib_gtfs as gtfs

logger = set_up_logging()

def load_graphs(*paths_gt_graphs):
    """Load graph-tool graphs, one for each input path."""
    all_graphs = []
    for path_gt in paths_gt_graphs:
        all_graphs.append(gt.load_graph(path_gt))

    if len(all_graphs) == 1:
        all_graphs = all_graphs[0]
    return all_graphs


def add_waterbus_to_street(graph, path_gtfs):
    """Add gtfs vertices and edges to graph"""
    # add transport boolean vertex property
    transport = graph.new_vp("bool")
    graph.vp.transport = transport
    # add timetable edge property
    timetable = graph.new_ep("python::object")
    graph.ep.timetable = timetable
    # add route edge property
    route = graph.new_ep("python::object")
    graph.ep.route = timetable
    # add duration edge property
    duration = graph.new_ep("double")
    graph.ep.duration = duration
    # get a copy of the original graph without the transports
    g_orig = gt.GraphView(graph, vfilt=lambda v: not transport[v])
    pos = get_all_coordinates(g_orig)
    # load feed gtfs
    feed = gtfs.load_feed(path_gtfs)
    missing_stops = gtfs.check_stops_coordinates(feed, pos)
    if len(missing_stops) > 0:
        logger.warning(f"Some stops are not present in the graph: {missing_stops}")
    else:
        logger.info("All the stops are present in the graph!")
    count = 1
    all_routes = gtfs.get_all_routes_id(feed)
    for route_id in all_routes:
        logger.debug(f"{count}/{len(all_routes)} - Route: {route_id}")
        count += 1
        route_df = gtfs.get_route_sequence(feed, route_id)
        last_v = None
        for idx, row in route_df.iterrows():
            # logger.debug(f"\t{idx+1}/{len(route_df)}")
            if row["end_stop_id"] is np.nan:
                continue
            if (row["start_stop_id"] in missing_stops) or (row["end_stop_id"] in missing_stops):
                logger.warning(f"Missing stop {row['start_stop_id']} in route {route_id}")
                last_v = None
                continue
            if last_v is None:
                last_v = add_route_vertex_and_edge(graph, g_orig, pos, feed, row["start_stop_id"], row)
            new_v = add_route_vertex_and_edge(graph, g_orig, pos, feed, row["end_stop_id"], row)
            edge = graph.add_edge(last_v, new_v)
            # ipdb.set_trace()
            graph.ep.duration[edge] = int(row["duration"].total_seconds())
            graph.ep.route[edge] = row[["route_id", "route_short_name", "route_color", "route_text_color"]]
            graph.ep.geometry[edge] = transform(lambda x, y: (y, x), row["geometry"])
            last_v = new_v
    comp, hist = gt.label_components(graph)
    comp.a += 1
    graph.vp.component_waterbus = comp

    return g_orig, graph


def get_all_coordinates(graph):
    """Return array with vertices coordinates from a graph."""
    pos = graph.vp['latlon']
    return np.array([pos[v].a for v in graph.get_vertices()])


def get_id_from_coordinates(pos, coordinates):
    try:
        return np.where((pos[:, 0] == coordinates[0]) & (pos[:, 1] == coordinates[1]))[0][0]
    except IndexError:
        ipdb.set_trace()

def add_route_vertex_and_edge(graph, graph_orig, pos, feed, stop_id, row):
    # find the platform on the original graph
    start_stop_coordinate = gtfs.get_stop_coordinates(feed, stop_id)
    platform = graph_orig.vertex(get_id_from_coordinates(pos, start_stop_coordinate))
    # add a vertex for the route-specific platform
    v = graph.add_vertex()
    graph.vp.transport[v] = True
    graph.vp.latlon[v] = start_stop_coordinate
    # add edge between platform and route
    e = graph.add_edge(platform, v)
    # add timetable to e
    time_info = gtfs.get_stop_times_from_stop_route(feed, stop_id, row["route_id"])
    graph.ep.timetable[e] = time_info[["service_id", "departure_time"]]
    graph.ep.route[e] = row[["route_id", "route_short_name", "route_color", "route_text_color"]]
    graph.ep.geometry[e] = LineString()
    return v


def _len_iter(items):
    return sum(1 for _ in items)


def consecutive_one(data):
    """Helper to count the maximum number of consecutive items in a list.
    Thanks to Veedrac: https://codereview.stackexchange.com/questions/138550/count-consecutive-ones-in-a-binary-list
    """
    try:
        return max(_len_iter(run) for val, run in groupby(data) if val)
    except ValueError:
        return 0


def adjacent_one(data, item=1):
    """
    Helper to count the number of adjacent items in a list
    """
    adjacent_data = list(val for val, run in groupby(data))
    return adjacent_data.count(item)
