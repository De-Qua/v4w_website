"""
Everything about databases, mostly sqlite at the moment. Queries like there is no tomorrow.
"""
#%% Imports
import os,sys
# IMPORT FOR THE DATABASE - db is the database object
from app import app, db
from app.models import Feedbacks
import pandas as pd
import re
import json
import pdb


def fetch_usage_data_from_db():
    """
    Fetch the usage data to use it further
    """
    # big_data = FlaskUsage.query.all()
    pd_db = pd.read_sql_table('flask_usage', db.get_engine(bind='collected_data'))
    usage_dict = {}
    col_names = []
    for col_name in pd_db.columns:
        usage_dict[col_name] = pd_db[col_name] # it's a dataframe!
        col_names.append(col_name)

    return usage_dict, col_names, pd_db



def fetch_feedbacks_from_db():
    """
    Fetch the feedback list from db, returns their names and their contents as dictionary.
    """
    all_feedbacks = Feedbacks.query.all()
    feedback_dicts = []
    for feed in all_feedbacks:
        start_coord_as_num = 0
        end_coord_as_num = 0
        if feed.start_coord and len(feed.start_coord) > 0:
            start_coord_as_num = LatLng2List(feed.start_coord)
        if feed.end_coord and len(feed.end_coord) > 0:
            end_coord_as_num = LatLng2List(feed.end_coord)
        cur_feed_dict = {'name':feed.name, 'category':feed.category,
            'searched_start':feed.searched_start, 'searched_end':feed.searched_end, 'searched_string':feed.searched_string,
            'found_start':feed.found_start, 'found_end':feed.found_end, 'found_string':feed.found_string,
            'start_coord':start_coord_as_num, 'end_coord':end_coord_as_num,
            'feedback':feed.feedback, 'json':json.loads(feed.json), 'datetime':feed.datetime.strftime("%d-%m-%Y %H:%M:%S"),
            'report':feed.report, 'solved':feed.solved}
        feedback_dicts.append(cur_feed_dict)
        print(feed.start_coord)
    return feedback_dicts

def LatLng2List(latlng):
    """
    Convert a string in the format LatLng() in a list of coordinates
    """
    pattern = r"(\d+\.\d+)"
    list_coord = re.findall(pattern, latlng)
    return list_coord
