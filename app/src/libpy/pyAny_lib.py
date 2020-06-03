import numpy as np
import networkx as nt
from networkx.exception import NetworkXNoPath
import sys
import os
#sys.path.append(os.path.join(os.getcwd(), "app"))
#utility per coordinates
from app.src.libpy.library_coords import civico2coord_first_result
from app.src.libpy.weights_libs import weight_bridge, weight_time
import pickle
from shapely.geometry import shape
import json
import logging

def load_files(pickle_path, civici_tpn_path, coords_path):

    with open(pickle_path, 'rb') as file:
        G_un = pickle.load(file)
    civici_tpn = np.loadtxt(civici_tpn_path, delimiter = ";" ,dtype='str')
    coords = np.loadtxt(coords_path, delimiter = ",")
    return G_un, civici_tpn, coords


def calculate_path(G_un, coords_start, coords_end, flag_ponti=False):

    try:
        # Dijkstra algorithm, funzione peso lunghezza
        if flag_ponti == False:
            length_path, path = nt.algorithms.shortest_paths.weighted.single_source_dijkstra(G_un,coords_start,coords_end, weight=weight_time)
            # lista dei nodi attraversati
        # Dijkstra algorithm, funzione peso ponti
        elif flag_ponti == True:
            length_path, path = nt.algorithms.shortest_paths.weighted.single_source_dijkstra(G_un, coords_start,coords_end, weight = weight_bridge)
                # lista dei nodi attraversati
            #print(length_path)
        path_nodes = [n for n in path]
        # Converte la lista di nodi in file json
        shapes = []
        for i in range(len(path_nodes)-1):
            shapes.append(shape(json.loads(G_un[path_nodes[i] ][path_nodes[i+1] ]['Json'])))

        x_tot = []
        for sha in shapes:
        # print(sha.coords.xy)
            x = []
            for i in range(len(sha.coords.xy[0])):
                x.append((sha.coords.xy[1][i],sha.coords.xy[0][i]))
            # to be corrected with x_start
            if not x_tot:
                x_tot+=x
                coords_start_inv = (coords_start[1], coords_start[0])
                if coords_start_inv == x[0]:
                    x_tot+=x
                elif coords_start_inv == x[-1]:
                    x_tot+=x[::-1]
                else:
                    logging.warning("Coordinata iniziale non trovata nel primo arco")
                    logging.warning(coords_start)
                    logging.warning(x[0])
                    logging.warning(x[-1])
                    x_tot+=x
            elif x[0] == x_tot[-1]:
                # print(x[0], "uguali",x_tot[-1])
                x_tot+=x
            else:
                # print(x[0],"diversi", x_tot[-1])
                x_tot+=x[::-1]

        #print("\n#########\n##TEST2##\n#########")
        #print("strada con meno ponti: ", len(path_nodes), " nodi!")
        #print(path_nodes)
        #print("lunghezza (in metri, contando 100 metri per ponte: ", length_path)
    except NetworkXNoPath:
        print("Non esiste un percorso tra i due nodi")
        x_tot = []
        length_path = 0
    return x_tot, length_path #json.dumps(x_tot), length_path

def save_graph_pickle(shp_file,pickle_name):
    G = nt.read_shp(shp_file)
    G_un = G.to_undirected()

    with open(pickle_name, 'wb') as file:
        pickle.dump(G_un, file)
    return
