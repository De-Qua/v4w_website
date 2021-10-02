from pathlib import Path
import gtfs_kit as gk
import pandas as pd
import geopandas as gpd
from datetime import timedelta, datetime
import shapely.geometry as sg
import os

# %% Load file
os.getcwd()
path = Path(os.getcwd() / "app/static/gtfs/actv_nav.zip")

# %% Read feed
feed = gk.read_feed(path, dist_units="km")
feed.validate()
feed.describe()
# convert dates
feed.stop_times.loc[:, "arrival_time"] = pd.to_timedelta(feed.stop_times["arrival_time"])
feed.stop_times.loc[:, "departure_time"] = pd.to_timedelta(feed.stop_times["departure_time"])
feed.calendar.loc[:, "start_date"] = pd.to_datetime(feed.calendar["start_date"])
feed.calendar.loc[:, "end_date"] = pd.to_datetime(feed.calendar["end_date"])


# %% Functions
def get_stops_from_name(feed, name):
    return feed.stops.loc[feed.stops['stop_name'].str.contains(name)]


def get_times_of_stop(feed, stop):
    return feed.stop_times.loc[feed.stop_times.stop_id.isin(stop.stop_id)]


def get_trips(feed, start_stop, end_stop):
    df_xy = pd.merge(start_stop, end_stop, on="trip_id", how="inner")
    df_xy = df_xy[df_xy['stop_sequence_x'] < df_xy['stop_sequence_y']]
    return feed.trips.merge(df_xy, on="trip_id")


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
    geometry_df = gpd.GeoDataFrame(columns=["shape_id", "geometry"])
    geometry_df.loc[0, "shape_id"] = shape_id
    shape_df = feed.shapes[feed.shapes["shape_id"] == shape_id]
    x_points = feed.stops[feed.stops["stop_id"] == stop_id_x][["stop_lat", "stop_lon"]].values[0]
    y_points = feed.stops[feed.stops["stop_id"] == stop_id_y][["stop_lat", "stop_lon"]].values[0]
    try:
        idx_x = shape_df.loc[(shape_df["shape_pt_lat"] == x_points[0]) & (shape_df["shape_pt_lon"] == x_points[1])].index[0]
        idx_y = shape_df.loc[(shape_df["shape_pt_lat"] == y_points[0]) & (shape_df["shape_pt_lon"] == y_points[1])].index[0]
        geometry = sg.LineString(feed.shapes.iloc[idx_x:idx_y][["shape_pt_lat", "shape_pt_lon"]].values)
    except IndexError:
        geometry = sg.LineString()
    geometry_df.loc[0, "geometry"] = geometry
    # return geometry_df
    return geometry


def get_trips_by_time(feed, merged_trip, start_date, start_time, max_wait_time=None):
    # get available services based on date
    service = get_service_from_date(feed, start_date)
    # find trips between the two stops
    if max_wait_time:
        return trips[
            (trips['departure_time_x'] >= start_time) &
            (trips['departure_time_x'] <= start_time + max_wait_time) &
            (trips["service_id"].isin(service))
            ]
    else:
        return trips[
            (trips['departure_time_x'] >= start_time) &
            (trips["service_id"].isin(service))
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


# %%
# Extract stop
start_name = "Zaccaria"
end_name = "LIDO"
s_start = feed.stops.loc[feed.stops['stop_name'].str.contains(start_name)]
s_end = feed.stops.loc[feed.stops['stop_name'].str.contains(end_name)]
# Extract times of stop
t_start = feed.stop_times.loc[feed.stop_times.stop_id.isin(s_start.stop_id)]
t_end = feed.stop_times.loc[feed.stop_times.stop_id.isin(s_end.stop_id)]

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
start_date = datetime(year=2021, month=9, day=20)
next_trips = get_trips_by_time(feed, trips, start_date, start_time, max_wait_time)

# extract trips info
trips_info = get_trips_info(feed, next_trips, sort="arrival")
trips_info
