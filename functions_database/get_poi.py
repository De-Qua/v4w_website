#%% Import libraries
import os
import pandas as pd
import numpy as np
import geopy.distance
from app.src.libpy import pyAny_lib
from app.src.libpy.pyAny_lib import save_graph_pickle
from app.src.libpy.pyAny_lib import load_files
from app.src.libpy.library_coords import civico2coord_find_address
import networkx as nt
import time
#%% path
folder_file = os.path.join(os.getcwd(),"app","static","files")
file_poi_nordest = "POI_nordest_completo.csv"
file_poi_types = "poi_types.csv"
path_poi = os.path.join(folder_file,file_poi_nordest)
path_poi_types = os.path.join(folder_file,file_poi_types)

file_save_poi = "POI_venezia_completo.csv"
# file_save_coords = "lista_coords_poi.txt"
path_save_poi = os.path.join(folder_file,file_save_poi)
# path_save_coords = os.path.join(folder_file,file_save_coords)
#
# file_civici = "lista_key.txt"
# file_civici_coords = "lista_coords.txt"
# path_civici = os.path.join(folder_file,file_civici)
# path_civici_coords = os.path.join(folder_file,file_civici_coords)
#
# pickle_graph = "grafo_pickle"
# path_graph = os.path.join(folder_file,pickle_graph)
#%% utilities
latitude_ve = [45.420807, 45.45044]
longitude_ve = [12.303462, 12.365979]

#%% Crop files
poi_ne = pd.read_csv(path_poi,sep="|",dtype='str')
# convert lat and lon to float
poi_ne[["lat","lon"]]=poi_ne[["lat","lon"]].apply(pd.to_numeric)
print("POI total: {}".format(len(poi_ne)))
poi_ve = poi_ne.loc[(poi_ne['lat']>=latitude_ve[0]) & (poi_ne['lat']<=latitude_ve[1]) & (poi_ne['lon']>=longitude_ve[0]) & (poi_ne['lon']<=longitude_ve[1])]
print("POI in Venice: {}".format(len(poi_ve)))
poi_ve.to_csv(path_save_poi,sep="|",index=False)
print("POI saved in {}".format(path_save_poi))
#%% Load files
poi_types = pd.read_csv(path_poi_types)
poi_ne = pd.read_csv(path_poi,sep="|",
                    names=["poi-type","osm-id","latitude","longitude","name"],
                    dtype={"poi-type":int,"osm-id":str,"latitude":float,"longitude":float,"name":str})
print("POI total: {}".format(len(poi_ne)))

poi_ve = poi_ne.loc[(poi_ne['latitude']>=latitude_ve[0]) & (poi_ne['latitude']<=latitude_ve[1]) & (poi_ne['longitude']>=longitude_ve[0]) & (poi_ne['longitude']<=longitude_ve[1])]
print("POI in Venice: {}".format(len(poi_ve)))

# Save files
poi_ve.to_csv(path_save_poi,index=False,header=False,columns=["name"])
print("POI names saved in {}".format(path_save_poi))
poi_ve.to_csv(path_save_coords,index=False,header=False,columns=["longitude","latitude"],float_format="%.8f")
print("POI coordinates saved in {}".format(path_save_coords))

#%% Test
from app.src.libpy.pyAny_lib import load_files
G,np_civici,np_civici_coords = load_files(path_graph,path_civici,path_civici_coords)
# civici = pd.read_csv(path_civici,names=["address","empty"])
# civici = civici.drop(["empty"],axis=1) # delete empty column
# civici_coords = pd.read_csv(path_civici_coords,names=["longitude","latitude"])
# civici_total = pd.concat([civici,civici_coords],axis=1)
civici_address = pd.DataFrame(data=np_civici,columns=["address"])
civici_coords = pd.DataFrame(data=np_civici_coords,columns=["longitude","latitude"])
civici = pd.concat([civici_address,civici_coords],axis=1)
# Caffé Rosso: indirizzo Dorsoduro 2963
rosso_civico = civici.loc[civici["address"]=="DORSODURO 2963,"]
rosso_poi = poi_ve.loc[poi_ve['name']=="Caffé Rosso"]

if (rosso_poi["longitude"].iloc[0]==rosso_civico["longitude"].iloc[0]) and ((rosso_poi["latitude"].iloc[0]==rosso_civico["latitude"].iloc[0])):
    print("PERFETTO!")
else:
    coords_1 = (rosso_poi["latitude"].iloc[0],rosso_poi["longitude"].iloc[0])
    coords_2 = (rosso_civico["latitude"].iloc[0],rosso_civico["longitude"].iloc[0])
    dist = geopy.distance.geodesic(coords_1,coords_2).meters
    print("La distanza tra i due punti è di {dist} metri".format(dist=dist))
