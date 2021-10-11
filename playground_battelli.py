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
import ipdb
# %% Load file
path = Path(os.getcwd()) / "app/static/gtfs/actv_nav.zip"
path = "/Users/ale/Downloads/actv_nav_494-1"

# %% Functions
URL_ACTV = "https://actv.avmspa.it/sites/default/files/attachments/opendata/navigazione/"
LAST_FILE = "actv_nav.zip"
OUTPUT_FOLDER = Path(os.getcwd()) / "app/static/gtfs"


def get_latest_data(url=URL_ACTV, file=LAST_FILE, output=OUTPUT_FOLDER):
    url_data = urljoin(url, file)
    output_name = Path(output) / file
    output_path, _ = urlretrieve(url_data, output_name)
    return output_path


def get_stops_from_name(feed, name):
    return feed.stops.loc[feed.stops['stop_name'].str.contains(name, case=False)]


def get_times_of_stop(feed, stop):
    return feed.stop_times.loc[feed.stop_times.stop_id.isin(stop.stop_id)]


def get_trips(feed, start_stop, end_stop):
    df_xy = pd.merge(start_stop, end_stop, on="trip_id", how="inner")
    df_xy = df_xy[df_xy['stop_sequence_x'] < df_xy['stop_sequence_y']]
    return feed.trips.merge(df_xy, on="trip_id")


def append_duration_to_stop_times(feed, append_to_end=False, column="arrival_time", inplace=True):
    df1 = feed.stop_times.groupby('trip_id')[column].diff()
    if append_to_end:
        feed.stop_times.loc[:, "duration"] = df1
    else:
        feed.stop_times.loc[:, "duration"] = df1.shift(-1)


def append_stop_to_shapes(feed):
    trip_stops = feed.stop_times[["trip_id", "stop_id"]].merge(feed.stops[["stop_id", "stop_lat", "stop_lon"]], on="stop_id")
    stop_shapes = trip_stops.merge(feed.trips[["trip_id", "shape_id"]], on="trip_id").drop("trip_id", axis=1).drop_duplicates()
    feed.shapes = feed.shapes.merge(stop_shapes[["stop_id", "stop_lat", "stop_lon", "shape_id"]], left_on=["shape_id", "shape_pt_lat", "shape_pt_lon"], right_on=["shape_id", "stop_lat", "stop_lon"], how="left").drop(["stop_lat", "stop_lon"], axis=1)
    return


def append_shape_to_stop_times(feed):
    # Add geometry column
    feed.stop_times["geometry"] = sg.LineString()
    # Add column with end stop
    feed.stop_times["end_stop_id"] = feed.stop_times.groupby("trip_id")["stop_id"].shift(-1)
    # Add column with shape id
    feed.stop_times = feed.stop_times.merge(feed.trips[["trip_id", "shape_id"]], on="trip_id")
    # Add stop id to shape
    append_stop_to_shapes(feed)
    g = feed.stop_times.groupby(["shape_id", "stop_id", "end_stop_id"]).apply(lambda row: pd.Series({"geometry": get_shape_between_stops(feed, row["shape_id"].values[0], row["stop_id"].values[0], row["end_stop_id"].values[0])}))
    feed.stop_times = feed.stop_times.drop("geometry", axis=1)
    feed.stop_times = feed.stop_times.join(g, on=["shape_id", "stop_id", "end_stop_id"])
    return


def get_service_from_date(feed, date):
    weekday = date.weekday()
    day_feed = None
    if weekday == 0:
        day_feed = feed.calendar[feed.calendar["monday"] == 1]
    elif weekday == 1:
        day_feed = feed.calendar[feed.calendar["tuesday"] == 1]
    elif weekday == 2:
        day_feed = feed.calendar[feed.calendar["wednesday"] == 1]
    elif weekday == 3:
        day_feed = feed.calendar[feed.calendar["thursday"] == 1]
    elif weekday == 4:
        day_feed = feed.calendar[feed.calendar["friday"] == 1]
    elif weekday == 5:
        day_feed = feed.calendar[feed.calendar["saturday"] == 1]
    elif weekday == 6:
        day_feed = feed.calendar[feed.calendar["sunday"] == 1]
    if day_feed is None:
        return []
    available_services = day_feed[(day_feed["start_date"] <= date) & (day_feed["end_date"] >= date)]
    return available_services["service_id"].values


def get_shape_between_stops(feed, shape_id, stop_id_x, stop_id_y):
    if not shape_id:
        return sg.LineString()
    if not stop_id_x or stop_id_x is np.nan:
        return sg.LineString()
    if not stop_id_y or stop_id_y is np.nan:
        return sg.LineString()
    shp = feed.shapes[feed.shapes["shape_id"] == shape_id].reset_index(drop=True)
    try:
        idx_x = shp.index[shp["stop_id"] == stop_id_x][0]
        idx_y = shp.index[shp["stop_id"] == stop_id_y][0]
        start_idx = min(idx_x, idx_y)
        end_idx = max(idx_x, idx_y) + 1
        geometry = sg.LineString(shp.iloc[start_idx:end_idx][["shape_pt_lat", "shape_pt_lon"]].values)
    except IndexError:
        geometry = sg.LineString()
    return geometry


def get_trips_by_time(feed, merged_trip, start_date, start_time, max_wait_time=None):
    # get available services based on date
    service = get_service_from_date(feed, start_date)
    # find trips between the two stops
    if max_wait_time:
        return trips[
            (trips['departure_time_x'] >= start_time)
            & (trips['departure_time_x'] <= start_time + max_wait_time)
            & (trips["service_id"].isin(service))
            ]
    else:
        return trips[
            (trips['departure_time_x'] >= start_time)
            & (trips["service_id"].isin(service))
            ]


def get_trips_info(feed, trips, sort="arrival"):
    info = trips[["stop_id_x", "departure_time_x", "stop_id_y", "arrival_time_y", "trip_headsign", "route_id", "shape_id"]]
    # merge with stop to get names
    info = info.merge(feed.stops[["stop_id", "stop_name"]], left_on="stop_id_x", right_on="stop_id", how="left").drop(["stop_id"], axis=1)
    info = info.merge(feed.stops[["stop_id", "stop_name"]], left_on="stop_id_y", right_on="stop_id", how="left").drop(["stop_id"], axis=1)
    # merge with route to get route ingo
    info = info.merge(feed.routes[["route_id", "route_short_name", "route_long_name", "route_type", "route_color", "route_text_color"]], on="route_id")
    # extract shape of the route
    geometries = {}
    shape_list = []
    for idx, row in info.iterrows():
        # save the shape in a dict to avoid repeating the same operation multiple times
        if row["shape_id"] not in geometries.keys():
            geometries[row["shape_id"]] = get_shape_between_stops(feed, row["shape_id"], row["stop_id_x"], row["stop_id_y"])
        shape_list.append(geometries[row["shape_id"]])
    # convert to a geodataframe and assign the shapes
    geoinfo = gpd.GeoDataFrame(info, geometry=shape_list)
    # drop useless columns
    geoinfo.drop(["stop_id_x", "stop_id_y", "route_id", "shape_id"], axis=1, inplace=True)
    # rename columns
    column_renames = {
        "stop_name_x": "stop_name_start",
        "stop_name_y": "stop_name_end",
        "departure_time_x": "departure_time",
        "arrival_time_y": "arrival_time",
    }
    geoinfo.columns = [column_renames.get(x, x) for x in geoinfo.columns]
    # Add duration
    geoinfo["duration"] = geoinfo["arrival_time"]-geoinfo["departure_time"]
    # reorder columns
    geoinfo = geoinfo[[
        "stop_name_start",
        "departure_time",
        "stop_name_end",
        "arrival_time",
        "duration",
        "route_short_name",
        "trip_headsign",
        "route_long_name",
        "route_type",
        "route_color",
        "route_text_color",
        "geometry"
        ]
    ]
    if sort == "arrival":
        return geoinfo.sort_values(by="arrival_time").reset_index(drop=True)
    elif sort == "departure":
        return geoinfo.sort_values(by="departure_time").reset_index(drop=True)
    else:
        return geoinfo


# %% Read feed
feed = gk.read_feed(path, dist_units="km")
feed.validate()
feed.describe()
# convert dates
feed.stop_times.loc[:, "arrival_time"] = pd.to_timedelta(feed.stop_times["arrival_time"])
feed.stop_times.loc[:, "departure_time"] = pd.to_timedelta(feed.stop_times["departure_time"])
feed.calendar.loc[:, "start_date"] = pd.to_datetime(feed.calendar["start_date"])
feed.calendar.loc[:, "end_date"] = pd.to_datetime(feed.calendar["end_date"])
append_duration_to_stop_times(feed)
feed.stop_times
get_shape_between_stops(feed, '1026_1_2', '5050', '15022')
shape_id = '1026_1_2'
stop_id_x = '5050'
stop_id_y = '15022'
# %%
# Extract stop
start_name = "Palanca"
end_name = "LIDO"
s_start = get_stops_from_name(feed, start_name)
s_end = get_stops_from_name(feed, end_name)
# Extract times of stop
t_start = get_times_of_stop(feed, s_start)
t_end = get_times_of_stop(feed, s_end)

# Find trips
# merge the df of the two stops
df_xy = pd.merge(t_start, t_end, on="trip_id", how="inner")
# take only the one with stop sequence of the start greater than the stop sequence of the end
df_xy = df_xy[df_xy['stop_sequence_x'] < df_xy['stop_sequence_y']]
# merge with the trips based on trip_id
trips = feed.trips.merge(df_xy, on="trip_id")
# Check with respect to a time
start_time = timedelta(hours=23, minutes=50)
max_wait_time = timedelta(hours=1)
start_date = datetime(year=2021, month=10, day=2)
next_trips = get_trips_by_time(feed, trips, start_date, start_time, max_wait_time)

# extract trips info
trips_info = get_trips_info(feed, next_trips, sort="arrival")
trips_info

# %% Check all possible direct connections

number_direct_connections = feed.trips.merge(feed.stop_times, on="trip_id").groupby("route_id")["stop_id"].apply(lambda g: math.comb(len(np.unique(g)), 2))
print(f"Ci sono {number_direct_connections.sum()} possibili collegamenti")


aa = feed.stop_times.merge(feed.trips, on="trip_id")
aa[aa["stop_id"] == "5203"]

feed.routes
feed.trips

# %% Get all routes from all stops
stop_routes = feed.stop_times.merge(feed.trips[["trip_id", "route_id"]], on="trip_id").groupby("stop_id")["route_id"].unique()
all_stop_routes = feed.stops.merge(stop_routes, on="stop_id", how="left")
# %% Get all times of a stop based on a route
stop = feed.stops.iloc[30]
stop_times = feed.stop_times.loc[feed.stop_times.stop_id == stop.stop_id]
stop_times_w_routes = stop_times.merge(feed.trips[["trip_id", "route_id", "service_id"]], on="trip_id")
service_id = "1A0504_000"
route_id = "101"

stop_times_of_route = stop_times_w_routes.loc[(stop_times_w_routes["route_id"] == route_id) & (stop_times_w_routes["service_id"] == service_id)].sort_values(by="arrival_time")

# %% Extract edge between one stop and the following
one_trip = stop_times_of_route.iloc[0]
trip_times = feed.stop_times.loc[feed.stop_times["trip_id"] == one_trip["trip_id"]]
edge_data = one_trip[["route_id", "stop_headsign", "duration"]]
edge_data["start_stop_id"] = one_trip["stop_id"]
end_stop_id = trip_times.loc[trip_times["stop_sequence"] == one_trip.stop_sequence+1]["stop_id"].values[0]
edge_data["end_stop_id"] = end_stop_id
route = feed.routes.loc[feed.routes["route_id"] == edge_data["route_id"]]
shape_id = feed.trips[feed.trips["trip_id"] == one_trip.trip_id]["shape_id"].values[0]
shape = get_shape_between_stops(feed, shape_id, one_trip["stop_id"], end_stop_id)
edge_data["geometry"] = shape
edge_data["route_short_name"] = route["route_short_name"].values[0]
edge_data["route_color"] = route["route_color"].values[0]
edge_data["route_text_color"] = route["route_text_color"].values[0]


# %% Extract all the direct trips

all_pairs = []
for idx, stop in feed.stops.iterrows():
    stop_times = feed.stop_times.loc[feed.stop_times.stop_id == stop.stop_id]
    stop_times_w_routes = stop_times.merge(feed.trips[["trip_id", "route_id", "service_id"]], on="trip_id")
    stop_times_w_routes.loc[(stop_times_w_routes["route_id"] == "64") & (stop_times_w_routes["service_id"] == "1A0104_000")].sort_values(by="arrival_time")
    stop_routes_series = stop_times.merge(feed.trips, on="trip_id")["route_id"].drop_duplicates()

    stop_routes = feed.routes[feed.routes["route_id"].isin(stop_routes_series)]
    all_stop_trips = feed.trips.merge(stop_routes, on="route_id").merge(feed.stop_times, on="trip_id")
    stop_routes_trip = all_stop_trips.loc[all_stop_trips.groupby("route_id").stop_sequence.idxmax()].reset_index(drop=True)
    stop_routes_trip = stop_routes_trip[["route_id", "trip_id"]].drop_duplicates()
    reachable_stops = stop_routes_trip.merge(feed.stop_times, on="trip_id")[["route_id", "stop_id"]].drop_duplicates()
    # stop_routes_trip = feed.trips.merge(stop_routes, on="route_id").groupby("route_id").first().reset_index()
    # stop_routes_trip.merge(feed.stop_times, on="trip_id")[["route_id", "stop_id"]].drop_duplicates()
    # reachable_stops = stop_routes_trip.merge(feed.stop_times, on="trip_id")[["route_id", "stop_id"]].drop_duplicates()
    # reachable_stops = feed.stop_times[feed.stop_times["trip_id"].isin(stop_routes_trip.trip_id)]["stop_id"].unique()
    reachable_pairs = [(route_id, stop.stop_id, stop_id) for route_id, stop_id in reachable_stops.values if stop_id != stop.stop_id]
    all_pairs += reachable_pairs

data = pd.DataFrame(all_pairs, columns=["route_id", "start_stop", "end_stop"])
columns = ["start_stop", "end_stop"]
data[columns] = pd.DataFrame(np.sort(data[columns].values, axis=1), columns=columns)
all_direct_trips = data.drop_duplicates()


num_all_direct_trips = all_direct_trips.groupby("route_id").count()
num_all_direct_trips["theorical"] = number_direct_connections.astype(int)

diff_comb = num_all_direct_trips[num_all_direct_trips["end_stop"] != num_all_direct_trips["theorical"]].values

print(f"Ci sono {diff_comb} differenze con il risultato teorico")

"""
Premesse
Nel grafo base c'è già un vertice per ogni pontile

1. Archi percorso battelli
PRO
Non è più necessario fare gli archi finti perché su graph-tool non si basano sulla posizione
Basta:
    - Aggiungere un vertice per ogni stop e collegarlo tramite arco fittizio con il vertice del grafo che ha le stesse coordinate
    - Così facendo c'è un pontile per ogni linea e per passare da un pontile all'altro bisogna fare pontile-arcofittizio-pontile
    - Presa ogni route creare un arco che collega i vari pontili

Approcio più intuitivo
Meno nuovi archi
Avendo l'arco fittizio il percorso con cambi ha meno archi del percorso senza cambi
Questo però non è vero in alcuni casi
Una soluzione potrebbe essere chiamare all_short_paths invece di short_paths e restituire tutte le soluzioni

CONTRO
Da terminale le performance di all_short_paths sembrano comunque ottime, bisogna capire se effettivamente è così

2. Sottografi completamente connessi
Un arco per ogni coppia di pontili che hanno un possibile collegamento senza cambi
PRO
Non sussiste il problema del numero di archi sui cambi

grafo
VP1
    VP1A E(VP1A-VP1)
    VP1B E(VP1B-VP1)

VP2
    VP2A E(VP2A-VP2)

VP3
    VP3A E(VP3A-VP3)

VP3-VP3A-VP2A-VP1A-VP1-VP1B



"""
