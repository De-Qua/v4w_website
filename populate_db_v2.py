import os, sys
import library_database as lb
import pdb
from app import db
import psycopg2
import pickle, json
from app.models import *

folder_file = "~/dequa/OpenDataVE/"
LENGTH_ASTERISK_ROW = 50
DEBUG = True
if len(sys.argv) > 1:
    if sys.argv[1] == '--no-debug':
        DEBUG = False
working = 'y'

"""
To create all databases,
psql -f create_dbs.sql
The .sql file contains the 4 commands to create the 4 databases.

After that the code creates the tables inside the databases.
"""

if DEBUG:
    print('=' * LENGTH_ASTERISK_ROW)
    print()
    print("RUNNING IN DEBUG MODE")
    print("if you want just to run, add --no-debug when calling the script")
    print()
    print('=' * LENGTH_ASTERISK_ROW)
    print("\n")
    print('#' * LENGTH_ASTERISK_ROW)
    print("WARNING:\nif there is no postgresql service active \nor no database opendata_ve_pg, it will fail!")
    print("check the code for hints")
    print('#' * LENGTH_ASTERISK_ROW)
else:
    print('=' * LENGTH_ASTERISK_ROW)
    print()
    print("RUNNING IN FAST MODE")
    print("If errors, run it in debug mode")
    print()
    print('=' * LENGTH_ASTERISK_ROW)

### IN CASE OF ERROR
# sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) FATAL: database "opendata_ve_pg" does not exist
# we did not create the database
#
# to create the database, use the command
# CREATE DATABASE opendata_ve_pg;
# probably also the others are needed (see config.py for the names)
# from postgresql (psql postgres if using brew for example)
# `psql -f create_dbs.sql` will creat all 4 databases


"""
In case of error:
sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  database "dequa_collected_data" does not exist


"""
if DEBUG:
    working = input("Want to create tables? (y = yes, s = skip)   ")

if working == 'y':
    print("")
    print('*' * LENGTH_ASTERISK_ROW)
    print("creating all tables..")
    db.create_all()
    print("done, next comes the query objects.")
    print('*' * LENGTH_ASTERISK_ROW)
    print("")
else:
    print('skipping tables creation..')
# IF ERROR
#sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedObject) type "geometry" does not exist
# LINE 6:  shape geometry(POINT,-1) NOT NULL,
#
# missing postgis!

# CREATE EXTENSION postgis;
# da dentro il database

print("")
print('*' * LENGTH_ASTERISK_ROW)
print("creating query objects..")
lb.create_query_objects()
print("done")
print('*' * LENGTH_ASTERISK_ROW)
print("")
if DEBUG:
    working = input("Need for the debugger? (y = yes, s = skip)   ")
if working == 'y':
    pdb.set_trace()

if DEBUG:
    working = input("Want to add sestieri? (y = yes, s = skip)    ")

if working == 'y':
    print("")
    print('*' * LENGTH_ASTERISK_ROW)
    print("adding sestieri..")
    path_shp_sestieri = os.path.join(folder_file, 'Sestieri_Localita_Isole', 'Localita_v5.shp')
    # "Localita", "Localita_v4.shp")
    err_sestieri = lb.update_sestieri(path_shp_sestieri, showFig=False, explain=True)
    print(f"done.\n\nReport: Error in:\n{err_sestieri}.\n\nnext comes the streets.")
    print('*' * LENGTH_ASTERISK_ROW)
    print("")
else:
    print('skipping sestieri..')

if DEBUG:
    working = input("Want to add streets? (y = yes, s = skip)     ")

if working == 'y':
    print("")
    print('*' * LENGTH_ASTERISK_ROW)
    print("adding streets..")
    path_shp_streets = os.path.join(folder_file, 'Strade', "TP_STR_v3.shp")# "Localita", "Localita_v4.shp")
    err_streets = lb.update_streets(path_shp_streets, showFig=False, explain=True)
    print(f"done.\n\nReport: Error in:\n{err_streets}.\n\nnext comes the addresses.")
    print('*' * LENGTH_ASTERISK_ROW)
    print("")
else:
    print('skipping streets..')

if DEBUG:
    working = input("Want to add addresses? (y = yes, s = skip)   ")

if working == 'y':
    print("")
    print('*' * LENGTH_ASTERISK_ROW)
    print("adding addresses..")
    path_shp_addresses = os.path.join(folder_file, "Civici", "CIVICO_4326VE_v2.shp")
    err_addresses = lb.update_addresses(path_shp_addresses, showFig=False, explain=True)
    print(f"done.\n\nReport: Error in:\n{err_addresses}.\n\nnext comes the pois.")
    print('*' * LENGTH_ASTERISK_ROW)
    print("")
else:
    print('skipping addresses..')

if DEBUG:
    working = input("Want to add POIs? (y = yes, s = skip)        ")

if working == 'y':
    print("")
    print('*' * LENGTH_ASTERISK_ROW)
    print("adding POIs..")
    pkl_file = 'all_poi_20210702' #input("Insert pickle file name or skip:\n")
    if not pkl_file:
        list_category = [
            "amenity",
            "shop",
            "cuisine",
            "tourism",
            "building",
            "sport"
            ]
        all_pois = lb.download_POI(list_category,explain=True)
    else:
        path_poi_file = os.path.join(folder_file, "POI", pkl_file)
        with open(path_poi_file,'rb') as stream:
            all_pois = pickle.load(stream)

    err_poi = lb.update_POI(all_pois, explain=True)
    print(f"done.\n\nReport: {len(err_poi)} errors.\n\nnext comes the water pois.")
    print('*' * LENGTH_ASTERISK_ROW)
    print("")
else:
    print('skipping pois..')

if DEBUG:
    working = input("Want to add water POIs? (y = yes, s = skip)  ")

if working == 'y':
    print("")
    print('*' * LENGTH_ASTERISK_ROW)
    print("adding Water POIs..")
    json_file = input("Insert json file name:\n")
    if not json_file:
        print("Without file we will not go very far.. :( ")
        print("we try 'posti_barca.json' but otherwise it will fail")
        json_file = 'posti_barca.json'
    #else:
    wPOI_path = os.path.join(folder_file, "waterPOI", json_file)
    print('loading file..')
    wPOIs = lb.upload_waterPOIS(wPOI_path, explain=True)
    print('loaded file, writing to db..')
    err_wpoi = lb.update_waterPois(wPOIs, type='all', explain=True)
    print(f"done.\n\nReport: {len(err_wpoi)} errors.\n")
    print('*' * LENGTH_ASTERISK_ROW)
    print("")
else:
    print('skipping water pois..')

print('*' * LENGTH_ASTERISK_ROW)
print("")
print("we are done!")
print("")
print('*' * LENGTH_ASTERISK_ROW)
