from flask import current_app
import os
import yaml
import time
import datetime
import json
from dequa_graph.utils import load_graphs_binary, add_waterbus_to_street, get_all_coordinates

from app.models import Tide
from app.data_versions.models import CurrentData


def update_graphs_and_variables():
    """
    Function to update the internally stored graphs and variables
    """
    current_app.logger.info("Updating the variables...")
    # load the new variables from the db
    curr_data = CurrentData.query.first()
    new_variables = curr_data.get_graphs_versions()

    if current_app.current_variables == new_variables:
        current_app.logger.info("Internal variables are up to date")
        return
    # set the internal flag that the app is updating
    current_app.is_updating = True
    current_app.logger.info("Some variables are not up to date...")
        
    # load the new graphs
    # folder_files = os.path.join(folder, new_variables["file_folder"])
    # folder_graph = os.path.join(folder_files, new_variables["graph_folder"])

    # path_graph_street = os.path.join(folder_graph, new_variables["graph_street_file"])
    # path_graph_water = os.path.join(folder_graph, new_variables["graph_water_file"])
    # path_graph_street_plus_waterbus = os.path.join(folder_graph, new_variables["graph_street_plus_waterbus_file"])
    # path_graph_street_only = os.path.join(folder_graph, new_variables["graph_street_only_file"])

    # path_gtfs_file = os.path.join(folder_files, new_variables["gtfs_folder"], new_variables["gtfs_file"])

    # street and waterbus graph
    if (new_variables["graph_street_version"] != current_app.current_variables["graph_street_version"]) \
        or (new_variables["gtfs_number"] != current_app.current_variables["gtfs_number"]):
        # The street graph has changed: let's update graph_street, graph_street_only and graph_street_plus_waterbus
        current_app.logger.info("Street and/or gtfs file is different: updating street and waterbus...")

        graph_street_only, graph_street_plus_waterbus = load_graphs_binary(curr_data.street_graph.data, curr_data.waterbus_graph.data)

        current_app.graphs["street"] = {
            'graph': graph_street_only,
            'all_vertices': get_all_coordinates(graph_street_only),
        }
        current_app.graphs["waterbus"] = {
            'graph': graph_street_plus_waterbus,
            'all_vertices': get_all_coordinates(graph_street_plus_waterbus),
        }

    # water graph
    if new_variables["graph_water_version"] != current_app.current_variables["graph_water_version"]:
        # The street graph has changed: let's update graph_street, graph_street_only and graph_street_plus_waterbus
        current_app.logger.info("Water file is different: updating water...")

        graph_water = load_graphs_binary(curr_data.water_graph.data)
        current_app.graphs["water"] = {
            'graph': graph_water,
            'all_vertices': get_all_coordinates(graph_water),
        }
    # update internal variable list
    current_app.current_variables = new_variables
    current_app.is_updating = False
    updated_at = datetime.datetime.now()
    current_app.info["updated_at"] = updated_at.strftime("%d/%m/%Y %H:%M:%S")
    current_app.logger.info("Variables are now up to date")
    return


def old_update_tide():
    """
    Function to update the tide level
    """
    current_app.logger.debug("Updating the tide...")
    tide_level_dict = {}
    max_waiting_time = 10
    elapsed_time = 0
    start_time = time.time()
    while not tide_level_dict and elapsed_time < max_waiting_time:
        try:
            # with open(os.path.join(os.getcwd(), site_params.high_tide_file), 'r') as stream:
            with open(current_app.high_tide_file, 'r') as stream:
                tide_level_dict = json.load(stream)
        except:
            current_app.logger.error('Error in reading tide file')
            time.sleep(0.001)
            elapsed_time = time.time() - start_time

    tide_level_value = tide_level_dict.get('valore', None)
    tide_level = int(round(
        float(tide_level_value[:-2]) * 100)) if tide_level_value else None
    tide_level_dict['tide_level'] = tide_level
    # update the saved values
    if not tide_level:
        current_app.logger.error("No tide level! Tide not updated!")
    elif tide_level_dict.get("data", None) is None:
        current_app.logger.error("No data! Tide not updated!")
    elif tide_level_dict["data"] == current_app.tide_values.get("data", None):
        current_app.logger.error("Current data already in memory! Tide not updated!")
    else:
        current_app.tide_values = tide_level_dict
        current_app.logger.debug(f"Tide updated. Time of record: {tide_level_dict.get('data', None)}. Value: {tide_level}cm")

    return


def update_tide():
    """
    Function to retrieve tide level from the database
    """
    try:
        curr_data = CurrentData.query.first()
        current_app.tide_values = curr_data.tide.get_dict()
        current_app.logger.info(f"Tide updated. Value: {current_app.tide_values.get('tide_level', None)}cm")
    except Exception:
        current_app.logger.error("Error retrieving the tide from the database! Tide not updated!")

    return
