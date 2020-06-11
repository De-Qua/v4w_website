# %% CELL FOR TESTING GRAFO ACQUEO
#%% IMPORTS
import flask
from flask import render_template, request, send_from_directory
from app import app
from app.models import Neighborhood, Street, Location, Area, Poi
from app.src.libpy.library_coords import find_address_in_db
%load_ext autoreload
%autoreload 2
import app.src.libpy.utils as utils
#casa = Location.query(housenumber=1157).join(Neighborhood).filter_by(name="DORSODURO").first()
import numpy as np
import shapely, shapely.wkt, shapely.geometry
import networkx as nx
import pickle
import json
import os

# %% LEGGI IL GRAFO

folder = os.getcwd()
folder_db = os.path.join(folder,"app","static","files")
pickle_path=os.path.join(folder_db, "grafo_acqueo_pickle_1106")
with open(pickle_path, 'rb') as file:
    G_un = pickle.load(file)

# %% locations
da="dorsoduro 1157"
a ="santa croce 363"
# trova nel database
match_dict_da = find_address_in_db(da)
match_dict_a = find_address_in_db(a)
# coordinate delle rive
coord_riva_start = match_dict_da[0].get("shape")[0]
coord_riva_end = match_dict_a[0].get("shape")[0]
# creat una lista con le coordinates
list_coord_rive = [coord_riva_start, coord_riva_end]

# %% TROVA LE RIVE E I NODI E GLI ARCHI

# se questa riga da un errore (not found Wkt o simili) e perche abbiamo aggiunto al grafo un edge senza wkt!
# in quel caso rileggere il grafo vero - la rimozione non e ancora pronta
list_of_edges_node_with_their_distance = utils.find_closest_edge(list_coord_rive, G_un)

# Chiaramente, questa parte puo essere riassunta in un ciclo for
# for edge_dict--> add both edges!
# l'idea era che ora abbiamo 2 edges da aggiungere, ma magari possiamo averne N!

# la lista ritornata da find_closest_edge e una lista di dizionari, con la stessa lunghezza della lista di input
# i due nodi del primo arco!
first_edge_first_node = list_of_edges_node_with_their_distance[0]["first_node"]
first_edge_second_node = list_of_edges_node_with_their_distance[0]["second_node"]
first_edge_first_dist = list_of_edges_node_with_their_distance[0]["first_dist"]
first_edge_second_dist = list_of_edges_node_with_their_distance[0]["second_dist"]
# ! i due nodi del secondo arco!
second_edge_first_node = list_of_edges_node_with_their_distance[1]["first_node"]
second_edge_second_node = list_of_edges_node_with_their_distance[1]["second_node"]
second_edge_first_dist = list_of_edges_node_with_their_distance[1]["first_dist"]
second_edge_second_dist = list_of_edges_node_with_their_distance[1]["second_dist"]
# non serve aggiungere il nodo singolarmente, basta aggiungere i 4 archi (due per la partenza, due per l'arrivo)
# se dobbiamo fare dall'ospedale, basterebbero 2
#G_un.add_node(coord_riva)#?? --> NON SERVE
# aggiungi archi partenza
first_edge_linestring_first_node = shapely.geometry.LineString([first_edge_first_node, coord_riva_start])
first_edge_linestring_second_node = shapely.geometry.LineString([first_edge_second_node, coord_riva_start])
# aggiungi gli archi (per ora senza attributi)
G_un.add_edge(first_edge_first_node, coord_riva_start)
G_un.add_edge(first_edge_second_node, coord_riva_start)
# aggiungi gli attributi
# non ha tanto senso cosi, ma la documentazione lo da come esempio --> https://networkx.github.io/documentation/stable/reference/generated/networkx.classes.function.set_edge_attributes.html
# il .wkt lo mette come una stringa come negli altri nodi del grafo
attrs_first_edges = {(first_edge_first_node, coord_riva_start): {'length':first_edge_first_dist, 'Wkt':first_edge_linestring_first_node.wkt},
         (first_edge_second_node, coord_riva_start): {'length':first_edge_second_dist, 'Wkt':first_edge_linestring_second_node.wkt}}
nx.set_edge_attributes(G_un, attrs_first_edges)
#controlla
print(G_un[first_edge_first_node][coord_riva_start])
print(G_un[first_edge_second_node][coord_riva_start])
# aggiungi archi arrivo
second_edge_linestring_first_node = shapely.geometry.LineString([second_edge_first_node, coord_riva_end])
second_edge_linestring_second_node = shapely.geometry.LineString([second_edge_second_node, coord_riva_end])
# aggiungi gli archi (per ora senza attributi)
G_un.add_edge(second_edge_first_node, coord_riva_end)
G_un.add_edge(second_edge_second_node, coord_riva_end)
# aggiungi gli attributi
# non ha tanto senso cosi, ma la documentazione lo da come esempio --> https://networkx.github.io/documentation/stable/reference/generated/networkx.classes.function.set_edge_attributes.html
# il .wkt lo mette come una stringa come negli altri nodi del grafo
attrs_second_edges = {(second_edge_first_node, coord_riva_end): {'length':second_edge_first_dist, 'Wkt':second_edge_linestring_first_node.wkt},
         (second_edge_second_node, coord_riva_end): {'length':second_edge_second_dist, 'Wkt':second_edge_linestring_second_node.wkt}}
nx.set_edge_attributes(G_un, attrs_second_edges)
#controlla
print(G_un[second_edge_first_node][coord_riva_end])
print(G_un[second_edge_second_node][coord_riva_end])

# %% CALCOLA LA STRADA

from app.src.libpy import pyAny_lib
# ho fatto un secondo metodo in calculate_path che usa Wkt invece di json. (la vecchia version funziona ancora)
# sembra una cosa migliore, perche usiamo shapely invece di json.
# da capire, ma sembra la scelta migliore
strada, length = pyAny_lib.calculate_path_wkt(G_un, coord_riva_start, coord_riva_end, flag_ponti=False)
# TODO: capire cosa manca nell'arco che abbiamo aggiunto, probabilmente bisogna copiare i due nodi!
# WARNING:root:Coordinata iniziale non trovata nel primo arco
# WARNING:root:(12.325011193845679, 45.4317264336331)
# WARNING:root:(12.32452203133604, 45.4323857354059)
# WARNING:root:(12.32501119384568, 45.4317264336331)

# disegna!
import matplotlib.pyplot as plt
%matplotlib inline
strada
xs = [node[0] for node in strada]
ys = [node[1] for node in strada]
plt.plot(ys, xs)

# eh?

####### TODO:
# la rimozione degli archi aggiunti!!!!
G_un.remove_edge(first_edge_first_node, coord_riva_start)
G_un.remove_edge(first_edge_second_node, coord_riva_start)
G_un.remove_edge(second_edge_first_node, coord_riva_end)
G_un.remove_edge(second_edge_second_node, coord_riva_end)
