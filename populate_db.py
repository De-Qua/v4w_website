#%% Imports
from app import app, db
import os
import pandas as pd
from importlib import reload
from app.models import Neighborhood

#%% Files
folder = os.getcwd()
folder_file = os.path.join(folder,"app","static","files")

file_civici = "lista_civici_only.txt"
file_civici_denominazioni = "lista_denominazioni_csv.txt"
file_civici_coords = "lista_coords_civici_only.txt"

#%% Load files
civici_address = pd.read_csv(os.path.join(folder_file,file_civici),header=None,names=["civico","empty"])
civici_address = civici_address.drop("empty",axis=1)
civici_denominazioni = pd.read_csv(os.path.join(folder_file,file_civici_denominazioni),header=None,names=["denominazione","empty"])
civici_denominazioni = civici_denominazioni.drop("empty",axis=1)
civici_coords = pd.read_csv(os.path.join(folder_file,file_civici_coords),header=None,names=["longitude","latitude"])
civici = pd.concat([civici_address,civici_denominazioni,civici_coords],axis=1)
#%% Neighborhood
list_sest_cap = [
   ("CANNAREGIO",30121),
   ("CASTELLO",30122),
   ("DORSODURO",30123),
   ("SAN MARCO",30124),
   ("SAN POLO",30125),
   ("SANTA CROCE",30135),
   ("GIUDECCA",30133)
    ]
for s,c in list_sest_cap:
    if not Neighborhood.query.filter_by(name=s,zipcode=c).first():
        n = Neighborhood(name=s,zipcode=c)
        db.session.add(n)
        db.session.commit()
#%% Get poi_types
file_poi_types = os.path.join(folder,"app","static","files","poi_types.csv")
poi_types = pd.read_csv(file_poi_types)

Neighborhood.query.all()
