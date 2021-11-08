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

URL_ACTV = "https://actv.avmspa.it/sites/default/files/attachments/opendata/navigazione/"
LAST_FILE = "actv_nav.zip"
OUTPUT_FOLDER = Path(os.getcwd()) / "app/static/gtfs"
WEEKDAYS = np.array(["monday", "tuesday", "wednesday",
                     "thursday", "friday", "saturday", "sunday"])


def load_feed(path):
    feed = gk.read_feed(path, dist_units="km")
    # feed.validate()
    # feed.describe()
    # convert dates
    feed.stop_times.loc[:, "arrival_time"] = pd.to_timedelta(
        feed.stop_times["arrival_time"])
    feed.stop_times.loc[:, "departure_time"] = pd.to_timedelta(
        feed.stop_times["departure_time"])
    feed.calendar.loc[:, "start_date"] = pd.to_datetime(
        feed.calendar["start_date"])
    feed.calendar.loc[:, "end_date"] = pd.to_datetime(
        feed.calendar["end_date"])
    if feed.calendar_dates is not None:
        feed.calendar_dates.loc[:, "date"] = pd.to_datetime(
            feed.calendar_dates["date"])
    append_duration_to_stop_times(feed)
    append_shape_id_to_routes(feed)
    append_stop_to_shapes(feed)
    # this must be after the stops have been appended to the shapes!
    create_stops_for_round_trips(feed)
    # this must be after the creation of new stops!
    append_shape_to_stop_times(feed)

    return feed


def convert_departure_to_array(time_info, feed):
    """
    magie incredibili per gli orari
    returns a dictionary with date as string
    """
    # Standard dates
    standard_dates_array = create_array_from_calendar(
        feed.calendar, time_info)

    # exceptional dates
    exceptional_dates = {}
    if feed.calendar_dates is not None:

        # removed_dates = feed.calendar_dates[feed.calendar_dates["exception_type"] == 2]
        # ipdb.set_trace()

        # create a calendar adding to the standard one all the special dates
        calendar_exceptions = create_calendar_exceptions(feed)

        # loop over the special dates
        # for each date we create a exception perido calendar
        # with 3 days: the one before, the special, and the one after
        unique_dates = np.unique(feed.calendar_dates['date'].values)
        for unique_date in unique_dates:
            # get the days before and after
            day_before = unique_date - np.timedelta64(1, 'D')
            day_after = unique_date + np.timedelta64(1, 'D')
            exception_period = [day_before, unique_date, day_after]
            # filter the calendar excluding services that are not included in our dates
            calendar = calendar_exceptions[(calendar_exceptions.start_date <= exception_period[-1]) & (calendar_exceptions.end_date >= exception_period[0])]
            # get from the calendar_dates, the service in the exception period that should be removed
            dates_to_remove = feed.calendar_dates[(feed.calendar_dates.date.isin(exception_period)) & (feed.calendar_dates.exception_type == 2)]
            # get the weekday of the dates to remove
            dates_to_remove["weekday"] = WEEKDAYS[dates_to_remove.date.dt.weekday]
            # remove the service for that single day
            for idx, row in dates_to_remove.iterrows():
                calendar.loc[calendar.service_id == row.service_id, row.weekday] = 0

            # loop on the days to get the active services
            service_period = []
            for day in exception_period:
                c_weekday = pd.to_datetime(day).weekday()
                service = calendar.loc[(calendar[WEEKDAYS[c_weekday]] == 1)
                                       & (calendar.start_date <= day)
                                       & (calendar.end_date >= day),
                                       "service_id"]
                service_period = np.concatenate([service_period, service])
            # filter the calendar with only the correct services
            calendar = calendar[calendar.service_id.isin(service_period)]
            # add to exceptional dates
            # date_as_string = pd.to_datetime(unique_date).strftime("%Y-%m-%d")
            date_as_key = pd.to_datetime(unique_date).date()
            exceptional_dates[date_as_key] = create_array_from_calendar(calendar, time_info)

    return standard_dates_array, exceptional_dates


def create_calendar_exceptions(feed):
    """
    Formats the calendar dates better as the calendar exceptions we need.
    It contains stadnard and exceptional fares.
    """
    new_dates = feed.calendar_dates.loc[feed.calendar_dates["exception_type"] == 1, :]
    n_original_col = len(new_dates.columns)
    new_dates[WEEKDAYS] = 0
    new_dates["start_date"] = new_dates.date
    new_dates["end_date"] = new_dates.date
    for idx, row in new_dates.iterrows():
        weekday = row.date.weekday()
        col_weekday = n_original_col+weekday
        new_dates.loc[idx, new_dates.columns[col_weekday]] = 1
    calendar_exceptions = pd.concat([feed.calendar, new_dates.drop(["date", "exception_type"], axis=1)]).reset_index(drop=True)
    return calendar_exceptions


def create_special_array(weekday: int,
                         time_info: pd.core.frame.DataFrame,
                         calendar: pd.core.frame.DataFrame):
    """
    It creates the timetable for the special date
    and the day before/after in our format.
    - weekday should be int in range (0-7)
    where 0 is monday
    - time_info is the timetables for the stop
    - calendar the dates
    """
    if weekday == 1:  # monday
        # leave only sunday and tuesday
        calendar[calendar.columns[3:7]] = 0
    elif weekday == 7:  # sunday bloody sunday
        # leave saturday and monday
        calendar[calendar.columns[2:6]] = 0
    elif weekday == 2:  # tuesday, panda throws error for i:i
        # leave saturday and monday
        calendar[calendar.columns[4:8]] = 0
    elif weekday == 6:  # saturday, panda throws error for i:i
        # leave saturday and monday
        calendar[calendar.columns[1:5]] = 0
    else:
        # set to zero all day until the weekday - 1
        calendar[calendar.columns[1:weekday]] = 0
        # set to zero all day after weekday + 1 (not included)
        calendar[calendar.columns[1+weekday+1:8]] = 0
    # create array (it will cancel all zero values)
    timetable_standard = create_array_from_calendar(calendar, time_info)

    return timetable_standard


def create_array_from_calendar(calendar, time_info):
    # can we put this inside a method?
    time_info_standard = time_info.merge(calendar, on="service_id")
    time_info_standard = time_info_standard.drop(
        ["stop_id", "service_id", "stop_headsign", "start_date", "end_date"], axis=1)
    #  orrai in secondi
    time_info_standard.departure_time = time_info_standard.departure_time.dt.total_seconds()
    weekdays = time_info_standard.drop(
        "departure_time", axis=1).values  #  1 o 0 a seocnda del giorno
    # ripetutti 7 volte lgi orari
    dep = np.tile(
        time_info_standard["departure_time"].values, (weekdays.shape[1], 1)).transpose()
    matrix_time = np.multiply(dep, weekdays) + np.multiply(weekdays,
                                                           np.arange(0, 7) * 24 * 3600)  # orari rispetto a lunedi
    # notte tra domenica e lunedi riportata a lunedi
    flat_time = np.mod(np.ravel(matrix_time), 7 * 24 * 3600)
    timetables_array = np.sort(flat_time[flat_time.nonzero()])

    return timetables_array


def get_latest_data(url=URL_ACTV, file=LAST_FILE, output=OUTPUT_FOLDER):
    url_data = urljoin(url, file)
    output_name = Path(output) / file
    output_path, _ = urlretrieve(url_data, output_name)
    return output_path


def get_stops_routes(feed):
    stops_routes = feed.stop_times.merge(
        feed.trips[["trip_id", "route_id"]], on="trip_id").groupby("stop_id")["route_id"].unique()
    df_stops_routes = feed.stops[["stop_id", "stop_name", "stop_lat", "stop_lon"]].merge(
        stops_routes, on="stop_id", how="left")
    return df_stops_routes


def get_route_sequence(feed, route_id):
    all_stop_trips = feed.trips[feed.trips["route_id"]
                                == route_id].merge(feed.stop_times, on="trip_id")
    stop_routes_trip = all_stop_trips.loc[all_stop_trips.groupby(
        "route_id").stop_sequence.idxmax()].reset_index(drop=True)
    stop_routes_trip = stop_routes_trip[[
        "route_id", "trip_id"]].drop_duplicates()
    route_df = stop_routes_trip.merge(feed.stop_times, on="trip_id")
    route_df["start_stop_id"] = route_df["stop_id"]
    route_df = route_df.merge(
        feed.routes[["route_id", "route_short_name", "route_color", "route_text_color"]])
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
    stop_times_w_routes = stop_times.merge(
        feed.trips[["trip_id", "route_id", "service_id"]], on="trip_id")
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
    feed.routes = feed.routes.merge(feed.trips[["route_id", "shape_id"]].drop_duplicates(
        subset="route_id"), on="route_id", how="left")
    return


def append_stop_to_shapes(feed):
    trip_stops = feed.stop_times[["trip_id", "stop_id"]].merge(
        feed.stops[["stop_id", "stop_lat", "stop_lon"]], on="stop_id")
    stop_shapes = trip_stops.merge(feed.trips[["trip_id", "shape_id"]], on="trip_id").drop(
        "trip_id", axis=1).drop_duplicates()
    feed.shapes = feed.shapes.merge(stop_shapes[["stop_id", "stop_lat", "stop_lon", "shape_id"]], left_on=[
        "shape_id", "shape_pt_lat", "shape_pt_lon"], right_on=["shape_id", "stop_lat", "stop_lon"], how="left").drop(["stop_lat", "stop_lon"], axis=1)
    return


def append_shape_to_stop_times(feed):
    # Add column with end stop
    feed.stop_times["end_stop_id"] = feed.stop_times.groupby("trip_id")[
        "stop_id"].shift(-1)
    # Add column with shape id
    feed.stop_times = feed.stop_times.merge(
        feed.trips[["trip_id", "shape_id"]], on="trip_id")

    g = feed.stop_times.groupby(["shape_id", "stop_id", "end_stop_id"]).apply(lambda row: pd.Series(
        {"geometry": get_shape_between_stops(feed, row["shape_id"].values[0], row["stop_id"].values[0], row["end_stop_id"].values[0])}))
    feed.stop_times = feed.stop_times.join(
        g, on=["shape_id", "stop_id", "end_stop_id"])
    return


def create_stops_for_round_trips(feed):
    # find stops that are present more than once in the trips
    dup = feed.stop_times[["trip_id", "stop_id"]
                          ][feed.stop_times[["trip_id", "stop_id"]].duplicated()]
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
            feed.stops = feed.stops.append(
                original_stop).reset_index(drop=True)
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
    shp = feed.shapes[feed.shapes["shape_id"]
                      == shape_id].reset_index(drop=True)
    # in order to avoid problems with fake stops
    stop_id_x = stop_id_x.split("_")[0]
    stop_id_y = stop_id_y.split("_")[0]
    try:
        idx_x = shp.index[shp["stop_id"] == stop_id_x][0]
        idx_y = shp.index[shp["stop_id"] == stop_id_y][0]
        start_idx = min(idx_x, idx_y)
        end_idx = max(idx_x, idx_y) + 1
        geometry = sg.LineString(
            shp.iloc[start_idx:end_idx][["shape_pt_lat", "shape_pt_lon"]].values)
    except IndexError:
        geometry = sg.LineString()
    return geometry
