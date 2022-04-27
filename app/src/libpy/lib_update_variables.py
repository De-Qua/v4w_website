from flask import current_app
import os
import yaml
import time
import datetime
import json
from dequa_graph.utils import load_graphs, add_waterbus_to_street, get_all_coordinates


def update_graphs_and_variables():
    """
    Function to update the internally stored graphs and variables
    """
    current_app.logger.info("Updating the variables...")
    # load the static file
    folder = current_app.config.get("STATIC_PATH")
    yaml_static_files = current_app.config.get("STATIC_FILE_NAME")
    new_variables = load_new_variables(os.path.join(folder, yaml_static_files))
    if current_app.current_variables == new_variables:
        current_app.logger.info("Internal variables are up to date")
        return
    # set the internal flag that the app is updating
    current_app.is_updating = True
    current_app.logger.info("Some variables are not up to date...")
    # load the new graphs
    folder_files = os.path.join(folder, new_variables["file_folder"])
    folder_graph = os.path.join(folder_files, new_variables["graph_folder"])

    path_graph_street = os.path.join(folder_graph, new_variables["graph_street_file"])
    path_graph_water = os.path.join(folder_graph, new_variables["graph_water_file"])
    path_graph_street_plus_waterbus = os.path.join(folder_graph, new_variables["graph_street_plus_waterbus_file"])
    path_graph_street_only = os.path.join(folder_graph, new_variables["graph_street_only_file"])

    path_gtfs_file = os.path.join(folder_files, new_variables["gtfs_folder"], new_variables["gtfs_file"])

    # street and waterbus graph
    if new_variables["graph_street_file"] != current_app.current_variables["graph_street_file"]:
        # The street graph has changed: let's update graph_street, graph_street_only and graph_street_plus_waterbus
        current_app.logger.info("Street file is different: updating street and waterbus...")

        graph_street = load_graphs(path_graph_street)
        graph_street_only, graph_street_plus_waterbus = add_waterbus_to_street(graph_street, path_gtfs_file)
        current_app.graphs["street"] = {
            'graph': graph_street_only,
            'all_vertices': get_all_coordinates(graph_street_only),
        }
        current_app.graphs["waterbus"] = {
            'graph': graph_street_plus_waterbus,
            'all_vertices': get_all_coordinates(graph_street_plus_waterbus),
        }
    elif (new_variables["gtfs_last_number"] != current_app.current_variables["gtfs_last_number"]) \
            or (new_variables["graph_street_only_file"] != current_app.current_variables["graph_street_only_file"]) \
            or (new_variables["graph_street_plus_waterbus_file"] != current_app.current_variables["graph_street_plus_waterbus_file"]):
        # Something about waterbus has changed: let's update graph_street_only and graph_street_plus_waterbus
        current_app.logger.info("Waterbus file is different: updating waterbus...")

        graph_street_only, graph_street_plus_waterbus = load_graphs(path_graph_street_only, path_graph_street_plus_waterbus)
        current_app.graphs["street"] = {
            'graph': graph_street_only,
            'all_vertices': get_all_coordinates(graph_street_only),
        }
        current_app.graphs["waterbus"] = {
            'graph': graph_street_plus_waterbus,
            'all_vertices': get_all_coordinates(graph_street_plus_waterbus),
        }
    # water graph
    if new_variables["graph_water_file"] != current_app.current_variables["graph_water_file"]:
        # The street graph has changed: let's update graph_street, graph_street_only and graph_street_plus_waterbus
        current_app.logger.info("Water file is different: updating water...")

        graph_water = load_graphs(path_graph_water)
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


def load_new_variables(file_path):
    """
    Function to load the new static variables names
    """
    new_variables = {}
    with open(os.path.join(file_path), 'r') as f:
        new_variables = yaml.load(f, Loader=yaml.FullLoader)
    return new_variables


def update_tide():
    """
    Function to update the tide level
    """
    current_app.logger.debug("Updating the tide...")
    tide_level_dict = None
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
    tide_level = int(
        float(tide_level_value[:-2]) * 100) if tide_level_value else None
    tide_level_dict['tide_level'] = tide_level
    # update the saved values
    current_app.tide_values = tide_level_dict
    if tide_level:
        current_app.logger.debug(f"Tide updated. Time of record: {tide_level_dict.get('data', None)}. Value: {tide_level}cm")
    else:
        current_app.logger.error("Tide not updated!")
    return
