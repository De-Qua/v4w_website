from pathlib import Path
import gtfs_kit as gk
import pandas as pd
import numpy as np
import geopandas as gpd
from datetime import timedelta, datetime
import shapely.geometry as sg
import os
import math
from urllib.request import urlretrieve
from urllib.parse import urljoin

URL_ACTV = "https://actv.avmspa.it/sites/default/files/attachments/opendata/navigazione/"
LAST_FILE = "actv_nav.zip"
OUTPUT_FOLDER = Path(os.getcwd()) / "app/static/gtfs"


def load_feed(path):
    feed = gk.read_feed(path, dist_units="km")
    # feed.validate()
    # feed.describe()
    # convert dates
    feed.stop_times.loc[:, "arrival_time"] = pd.to_timedelta(feed.stop_times["arrival_time"])
    feed.stop_times.loc[:, "departure_time"] = pd.to_timedelta(feed.stop_times["departure_time"])
    feed.calendar.loc[:, "start_date"] = pd.to_datetime(feed.calendar["start_date"])
    feed.calendar.loc[:, "end_date"] = pd.to_datetime(feed.calendar["end_date"])
    append_duration_to_stop_times(feed)
    append_shape_id_to_routes(feed)
    append_stop_to_shapes(feed)
    # this must be after the stops have been appended to the shapes!
    create_stops_for_round_trips(feed)
    # this must be after the creation of new stops!
    append_shape_to_stop_times(feed)

    return feed


def convert_departure_to_array(time_info, feed):
    """magie incredibili per gli orari"""
    time_info2 = time_info.merge(feed.calendar, on="service_id")
    time_info2 = time_info2.drop(["stop_id", "service_id", "stop_headsign", "start_date", "end_date"], axis=1)
    time_info2.departure_time = time_info2.departure_time.dt.total_seconds()  #  orrai in secondi
    weekdays = time_info2.drop("departure_time", axis=1).values  #  1 o 0 a seocnda del giorno
    dep = np.tile(time_info2["departure_time"].values, (weekdays.shape[1], 1)).transpose()  # ripetutti 7 volte lgi orari
    matrix_time = np.multiply(dep, weekdays) + np.multiply(weekdays, np.arange(0, 7)*24*3600)  # orari rispetto a lunedi
    flat_time = np.mod(np.ravel(matrix_time), 7*24*3600)  # notte tra domenica e lunedi riportata a lunedi
    return np.sort(flat_time[flat_time.nonzero()])


def get_latest_data(url=URL_ACTV, file=LAST_FILE, output=OUTPUT_FOLDER):
    url_data = urljoin(url, file)
    output_name = Path(output) / file
    output_path, _ = urlretrieve(url_data, output_name)
    return output_path


def get_stops_routes(feed):
    stops_routes = feed.stop_times.merge(feed.trips[["trip_id", "route_id"]], on="trip_id").groupby("stop_id")["route_id"].unique()
    df_stops_routes = feed.stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]].merge(stops_routes, on="stop_id", how="left")
    return df_stops_routes


def get_route_sequence(feed, route_id):
    all_stop_trips = feed.trips[feed.trips["route_id"] == route_id].merge(feed.stop_times, on="trip_id")
    stop_routes_trip = all_stop_trips.loc[all_stop_trips.groupby("route_id").stop_sequence.idxmax()].reset_index(drop=True)
    stop_routes_trip = stop_routes_trip[["route_id", "trip_id"]].drop_duplicates()
    route_df = stop_routes_trip.merge(feed.stop_times, on="trip_id")
    route_df["start_stop_id"] = route_df["stop_id"]
    route_df = route_df.merge(feed.routes[["route_id", "route_short_name", "route_color", "route_text_color"]])
    return route_df[["route_id", "route_short_name",  "stop_sequence", "pickup_type", "drop_off_type", "start_stop_id", "end_stop_id", "duration", "route_color", "route_text_color", "geometry"]]


def get_all_routes_id(feed):
    return feed.routes["route_id"].values


def check_stops_coordinates(feed, pos):
    return [x for x, y, z in feed.stops[["stop_id", "stop_lon", "stop_lat"]].values if not np.where((pos[:, 0] == y) & (pos[:, 1] == z))[0]]


def get_stop_coordinates(feed, stop_id):
    return feed.stops[feed.stops["stop_id"] == stop_id][["stop_lon", "stop_lat"]].values[0]


def get_routes_stops(feed):
    routes_stops = feed.stop_times.merge(feed.trips[["trip_id", "route_id"]], on="trip_id").groupby("route_id")["stop_id"].apply(list)
    df_stops_routes = feed.routes.merge(routes_stops, on="route_id", how="left")
    return df_stops_routes


def get_stop_times_from_stop_route(feed, stop_id, route_id):
    stop_times = feed.stop_times.loc[feed.stop_times.stop_id == stop_id]
    stop_times_w_routes = stop_times.merge(feed.trips[["trip_id", "route_id", "service_id"]], on="trip_id")
    stop_times_of_route = stop_times_w_routes.loc[stop_times_w_routes["route_id"] == route_id]
    return stop_times_of_route[["stop_id", "service_id", "departure_time", "stop_headsign"]].sort_values(by=["service_id", "departure_time"]).reset_index(drop=True)


def append_duration_to_stop_times(feed, append_to_end=False, column="arrival_time"):
    df1 = feed.stop_times.groupby('trip_id')[column].diff()
    if append_to_end:
        feed.stop_times.loc[:, "duration"] = df1
    else:
        feed.stop_times.loc[:, "duration"] = df1.shift(-1)
    return


def append_shape_id_to_routes(feed):
    feed.routes = feed.routes.merge(feed.trips[["route_id", "shape_id"]].drop_duplicates(subset="route_id"), on="route_id", how="left")
    return


def append_stop_to_shapes(feed):
    trip_stops = feed.stop_times[["trip_id", "stop_id"]].merge(feed.stops[["stop_id", "stop_lat", "stop_lon"]], on="stop_id")
    stop_shapes = trip_stops.merge(feed.trips[["trip_id", "shape_id"]], on="trip_id").drop("trip_id", axis=1).drop_duplicates()
    feed.shapes = feed.shapes.merge(stop_shapes[["stop_id", "stop_lat", "stop_lon", "shape_id"]], left_on=["shape_id", "shape_pt_lat", "shape_pt_lon"], right_on=["shape_id", "stop_lat", "stop_lon"], how="left").drop(["stop_lat", "stop_lon"], axis=1)
    return


def append_shape_to_stop_times(feed):
    # Add column with end stop
    feed.stop_times["end_stop_id"] = feed.stop_times.groupby("trip_id")["stop_id"].shift(-1)
    # Add column with shape id
    feed.stop_times = feed.stop_times.merge(feed.trips[["trip_id", "shape_id"]], on="trip_id")

    g = feed.stop_times.groupby(["shape_id", "stop_id", "end_stop_id"]).apply(lambda row: pd.Series({"geometry": get_shape_between_stops(feed, row["shape_id"].values[0], row["stop_id"].values[0], row["end_stop_id"].values[0])}))
    feed.stop_times = feed.stop_times.join(g, on=["shape_id", "stop_id", "end_stop_id"])
    return


def create_stops_for_round_trips(feed):
    # find stops that are present more than once in the trips
    dup = feed.stop_times[["trip_id", "stop_id"]][feed.stop_times[["trip_id", "stop_id"]].duplicated()]
    curr_trip = dup.iloc[0].trip_id
    added_stops = []
    for idx, row in dup.iterrows():
        # if new trip reset the counters
        if row["trip_id"] != curr_trip:
            curr_trip = row["trip_id"]
            added_stops = []
        # get the stop id
        stop_id = row["stop_id"]
        # append the stop to the list of the trip
        added_stops.append(stop_id)
        # check how many of that stops are in the list
        stop_iter = added_stops.count(stop_id)
        # create the new name
        new_id = f"{stop_id}_{stop_iter}"
        # check if the new stop is already present in the dataframe
        if len(feed.stops[feed.stops["stop_id"] == new_id]) == 0:
            # find the original stop
            original_stop = feed.stops[feed.stops["stop_id"] == stop_id]
            # change the id
            original_stop["stop_id"] = new_id
            # append the new stop to the dataframe
            feed.stops = feed.stops.append(original_stop).reset_index(drop=True)
        # update the stop id in the stop_times dataframe
        feed.stop_times.loc[idx, "stop_id"] = new_id
    return


def get_shape_between_stops(feed, shape_id, stop_id_x, stop_id_y):
    if not shape_id:
        return sg.LineString()
    if not stop_id_x or stop_id_x is np.nan:
        return sg.LineString()
    if not stop_id_y or stop_id_y is np.nan:
        return sg.LineString()
    shp = feed.shapes[feed.shapes["shape_id"] == shape_id].reset_index(drop=True)
    # in order to avoid problems with fake stops
    stop_id_x = stop_id_x.split("_")[0]
    stop_id_y = stop_id_y.split("_")[0]
    try:
        idx_x = shp.index[shp["stop_id"] == stop_id_x][0]
        idx_y = shp.index[shp["stop_id"] == stop_id_y][0]
        start_idx = min(idx_x, idx_y)
        end_idx = max(idx_x, idx_y) + 1
        geometry = sg.LineString(shp.iloc[start_idx:end_idx][["shape_pt_lat", "shape_pt_lon"]].values)
    except IndexError:
        geometry = sg.LineString()
    return geometry
