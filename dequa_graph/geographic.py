"""Functions that make geographic calculations."""

import numpy as np
import time

from . import set_up_logging

logger = set_up_logging()


def distance_from_a_list_of_geo_coordinates(thePoint, coordinates_list):
    """A python implementation from the answer here
    https://stackoverflow.com/questions/639695/how-to-convert-latitude-or-longitude-to-meters.
    Calculate the distance in meters between 1 geographical point (longitude,
    latitude) and a list of geographical points (list of tuples) or between two
    geographical points passing through distance_from_point_to_point.
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
    elif type(coords_list) is not list or type(coords_list[0]) is not list:
        coords_list = [coords_list]

    # loop over the coords_list and find the closest verices
    nodes_list = []
    for coords in coords_list:
        dists = distance_from_a_list_of_geo_coordinates(thePoint=coords,
                                coordinates_list=vertices_coords)

        closest_id = np.argmin(dists)
        closest_dist = dists[closest_id]
        logger.debug(f"Distance between your node and the vertex: {closest_dist:.9f}m")
        # se la distanza e troppo grande, salutiamo i campagnoli
        if closest_dist > MIN_DIST_FOR_THE_CLOSEST_NODE:
            logger.error(f"No close vertex: closest vertex is {closest_dist}m)")
            return []
        nodes_list.append(closest_id)

    return nodes_list
