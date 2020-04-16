# una libreria per leggere gli shapefile --> info qui: http://geopandas.org/index.html
# per le cartelle
import os
#test per il push
import networkx as nt
from networkx.exception import NetworkXNoPath
import numpy as np
import sys
sys.path.append('/home/rafiki/v4w')
#utility per coordinates
from libpy.library_coords import civico2coord
from libpy.weights_libs import weight_bridge

folder = os.getcwd()
folder_lib = folder + "/../lib/"
folder_db = folder + "/../db/"

import time


time1 = time.time()
for i in range(100):

    G = nt.read_shp(folder_db + "pontiDivisi_solo_venezia_l.shp")
time2 = time.time()
print("Networkx ci ha messo: ", (time2-time1 ) / 100)
time3 = time.time()
import pickle
for i in range(100):
    with open(folder_db + "grafo_pickle", 'rb') as file:
        pickle.load(file)
time4 = time.time()
print("Pickle ci ha messo: ", (time4-time3) / 100)

# per renderlo bidirezionale
G_un = G.to_undirected()
G_list = list(G_un.nodes)
# carica lista degli indirizzi con relativa posizione
civico_tpn = np.loadtxt(folder_db + "lista_civici_csv.txt", delimiter = ";" ,dtype='str')
## TODO: AGGIUNGI LA POSSIBILITA DEI TOPONIMI NELLA RICERCA
toponimo =  np.loadtxt(folder_db + "lista_toponimi_csv.txt", delimiter = ";" ,dtype='str')
coords = np.loadtxt(folder_db + "lista_coords.txt")

# definizione di partenza e arrivo (da implementare con search bar e deve ammettere i click sulla mappa)
# per ora usiamo solo i civici, i toponimi sono ancora da fare
starting_address = input('Da dove parti?\n')
coord = civico2coord(G_list, starting_address, civico_tpn, coords)
ending_address = input('Dove vai?\n')
coord2 = civico2coord(G_list, ending_address, civico_tpn, coords)

# Dijkstra algorithm, funzione peso lunghezza
try:
    path = nt.algorithms.shortest_paths.weighted.dijkstra_path(G_un,coord,coord2, weight="length")
    # lista dei nodi attraversati
    path_nodes = [n for n in path]
    print("\n#########\n##TEST1##\n#########")
    print("strada con ponti: ", len(path_nodes), " nodi!")
    print(path_nodes)
except NetworkXNoPath:
    print("Non esiste un percorso tra i due nodi")
# %% codecell
# Dijkstra algorithm, funzione peso ponti
try:
    length_path, path_nobridges = nt.algorithms.shortest_paths.weighted.single_source_dijkstra(G_un, coord,coord2, weight = weight_bridge)
    # lista dei nodi attraversati
    path_nodes_nobridges = [n for n in path_nobridges]
    #print(length_path)
    print("\n#########\n##TEST2##\n#########")
    print("strada con meno ponti: ", len(path_nodes_nobridges), " nodi!")
    print(path_nodes_nobridges)
    print("lunghezza (in metri, contando 100 metri per ponte: ", length_path)
except NetworkXNoPath:
    print("Non esiste un percorso tra i due nodi")
