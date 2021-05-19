"""Useful functions."""

import numpy as np
from itertools import groupby

import graph_tool.all as gt

def load_graphs(*paths_gt_graphs):
    """Load graph-tool graphs, one for each input path."""
    all_graphs = []
    for path_gt in paths_gt_graphs:
        all_graphs.append(gt.load_graph(path_gt))

    if len(all_graphs) == 1:
        all_graphs = all_graphs[0]
    return all_graphs


def get_all_coordinates(graph):
    """Return array with vertices coordinates from a graph."""
    pos = graph.vp['latlon']
    return np.array([pos[v].a for v in graph.get_vertices()])


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
