import numpy as np
import networkx as nt
from networkx.exception import NetworkXNoPath
import sys
import os
import pdb
#utility per coordinates
from app.src.libpy.library_coords import civico2coord_first_result
from app.src.libpy.weights_libs import weight_bridge, weight_time
import pickle
from shapely.geometry import shape
import json
import logging
from app import app
import shapely, shapely.wkt
import geopy.distance

def load_files(pickle_path, civici_tpn_path, coords_path):

    with open(pickle_path, 'rb') as file:
        G_un = pickle.load(file)
    civici_tpn = np.loadtxt(civici_tpn_path, delimiter = ";" ,dtype='str')
    app.logger.debug("loaded civici {}".format(civici_tpn_path))
    coords = np.loadtxt(coords_path, delimiter = ",")
    app.logger.debug("loaded coords {}".format(coords_path))
    return G_un, civici_tpn, coords

def load_graphs(pickle_terra,pickle_acqua):
    with open(pickle_terra,'rb') as file:
        G_terra = pickle.load(file)
        app.logger.debug("loaded land graph {}".format(pickle_terra))
    with open(pickle_acqua,'rb') as file:
        G_acqua = pickle.load(file)
        app.logger.debug("loaded water graph {}".format(pickle_acqua))
    return G_terra, G_acqua

def dynamically_add_edges(water_graph, list_of_edges_node_with_their_distance, rive):
    """
    Al momento aggiunge solo 2 edges, indipendentemente dalla lunghezza della lista! TODO.
    """
    app.logger.warning("Warning: aggiunge solo 2 edges (e se la lista ne ha uno solo dara errore!), dobbiamo finirlo!")
    coord_riva_start = rive[0]
    coord_riva_end = rive[1]
    added_edges = []
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
    #water_graph.add_node(coord_riva)#?? --> NON SERVE
    # aggiungi archi partenza
    first_edge_linestring_first_node = shapely.geometry.LineString([first_edge_first_node, coord_riva_start])
    first_edge_linestring_second_node = shapely.geometry.LineString([first_edge_second_node, coord_riva_start])
    # aggiungi gli archi (per ora senza attributi)
    water_graph.add_edge(first_edge_first_node, coord_riva_start)
    water_graph.add_edge(first_edge_second_node, coord_riva_start)
    # aggiungi gli attributi
    # non ha tanto senso cosi, ma la documentazione lo da come esempio --> https://networkx.github.io/documentation/stable/reference/generated/networkx.classes.function.set_edge_attributes.html
    # il .wkt lo mette come una stringa come negli altri nodi del grafo
    attrs_first_edges = {(first_edge_first_node, coord_riva_start): {'length':first_edge_first_dist, 'Wkt':first_edge_linestring_first_node.wkt, 'vel_max':1, 'solo_remi':0, 'larghezza':0.0, 'senso_unic':None},
             (first_edge_second_node, coord_riva_start): {'length':first_edge_second_dist, 'Wkt':first_edge_linestring_second_node.wkt,'vel_max':1, 'solo_remi':0, 'larghezza':0.0, 'senso_unic':None}}
    nt.set_edge_attributes(water_graph, attrs_first_edges)
    #controlla
    added_edges.append((first_edge_first_node, coord_riva_start))
    app.logger.debug("Added {}".format(water_graph[first_edge_first_node][coord_riva_start]))
    added_edges.append((first_edge_second_node, coord_riva_start))
    app.logger.debug("Added {}".format(water_graph[first_edge_second_node][coord_riva_start]))

    # aggiungi archi arrivo
    second_edge_linestring_first_node = shapely.geometry.LineString([second_edge_first_node, coord_riva_end])
    second_edge_linestring_second_node = shapely.geometry.LineString([second_edge_second_node, coord_riva_end])
    # aggiungi gli archi (per ora senza attributi)
    water_graph.add_edge(second_edge_first_node, coord_riva_end)
    water_graph.add_edge(second_edge_second_node, coord_riva_end)
    # aggiungi gli attributi
    # non ha tanto senso cosi, ma la documentazione lo da come esempio --> https://networkx.github.io/documentation/stable/reference/generated/networkx.classes.function.set_edge_attributes.html
    # il .wkt lo mette come una stringa come negli altri nodi del grafo
    attrs_second_edges = {(second_edge_first_node, coord_riva_end): {'length':second_edge_first_dist, 'Wkt':second_edge_linestring_first_node.wkt, 'vel_max':1, 'solo_remi':0, 'larghezza':0.0, 'senso_unic':None},
             (second_edge_second_node, coord_riva_end): {'length':second_edge_second_dist, 'Wkt':second_edge_linestring_second_node.wkt, 'vel_max':1, 'solo_remi':0, 'larghezza':0.0, 'senso_unic':None}}
    nt.set_edge_attributes(water_graph, attrs_second_edges)
    #controlla
    added_edges.append((second_edge_first_node, coord_riva_end))
    app.logger.debug("Added {}".format(water_graph[second_edge_first_node][coord_riva_end]))
    added_edges.append((second_edge_second_node, coord_riva_end))
    app.logger.debug("Added {}".format(water_graph[second_edge_second_node][coord_riva_end]))


    return added_edges

def dynamically_remove_edges(G,list_of_edges):
    """
    Rimuove dal grafo degli edge. List_of_edges è una lista di tuple (nodo1,nodo2)
    """
    for edge in list_of_edges:
        G.remove_edge(edge[0], edge[1])
        app.logger.debug("removed edge {}".format(edge[0], edge[1]))

    return


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
        app.logger.debug("Strada lunga {} !".format(length_path))
        app.logger.debug("Nodi della strada: {}".format(path))
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
                x.append((sha.coords.xy[0][i],sha.coords.xy[1][i]))
            # to be corrected with x_start
            if not x_tot:
                if coords_start == x[0]:
                    x_tot+=x
                elif coords_start == x[-1]:
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
        app.logger.info("Non esiste un percorso tra i due nodi")
        x_tot = []
        length_path = 0
    return x_tot, length_path #json.dumps(x_tot), length_path

def give_me_the_street(G, coords_start, coords_end, flag_ponti=False, speed=5, water_flag=False):
    path_nodes = x_tot = street = []
    streets_info = {}

    path_nodes, length = calculate_path_wkt(G, coords_start, coords_end, flag_ponti)
    if path_nodes:
        streets_info = go_again_through_the_street(G,path_nodes,speed,water_flag)
        street = prepare_the_street_as_list_until_we_understand_how_to_use_the_geometry(G,coords_start,path_nodes)
        pdb.set_trace()
    return path_nodes, length, streets_info, street

def calculate_path_wkt(G_un, coords_start, coords_end, flag_ponti=False):

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
        app.logger.debug("Strada lunga {} !".format(length_path))
        app.logger.debug("Nodi della strada: {}".format(path))
        #print("strada---------------------------",path)
        path_nodes = [n for n in path]
        #print("\n#########\n##TEST2##\n#########")
        #print("strada con meno ponti: ", len(path_nodes), " nodi!")
        #print(path_nodes)
        #print("lunghezza (in metri, contando 100 metri per ponte: ", length_path)
    except NetworkXNoPath:
        # exeption --> raise exception
        app.logger.info("Non esiste un percorso tra i due nodi")
        path_nodes = []
        length_path = 0

    return path_nodes, length_path #json.dumps(x_tot), length_path

def go_again_through_the_street(G, path_nodes, speed=5, water_flag=False):
    """
    Go through the path and retrieve informations about it (bridges, speed, ecc..).
    """

    # edges_info diventera un array di geojson - ogni edge e un geojson
    # ogni edge avra prpoperty che determinera come viene disegnato
    # link qua --> https://leafletjs.com/examples/geojson/

    # crea il dizionario da ritornare
    streets_info = {}
    edges_info = []
    # Converte la lista di nodi in file json
    shapes = []
    time=0
    n_ponti=0
    for i in range(len(path_nodes)-1):
        isBridge = 0
        edge_attuale = G[path_nodes[i]][path_nodes[i+1]]
        edge_info_dict = {}
        if water_flag:
            #print(edge_attuale)
            #edge_info_dict['']
            speed = np.minimum(speed, edge_attuale['vel_max'])
            edge_info_dict['vel_max'] = edge_attuale['vel_max']
            edge_info_dict['solo_remi'] = edge_attuale['solo_remi']
            # prendiamo informazioni sulle ordinanze in modo da creare un warning
        else:
            isBridge = edge_attuale['ponte']
            edge_info_dict['bridge'] = isBridge
            if isBridge:
                n_ponti += 1
        time += how_long_does_it_take_from_a_to_b(edge_attuale['length'], speed, isBridge)
        edges_info.append(edge_info_dict)
    streets_info['time'] = time
    streets_info['n_ponti'] = n_ponti
    streets_info['edges_info'] = edges_info
    return streets_info

def how_long_does_it_take_from_a_to_b(length, speed, isBridge):
    return (length + length/5*isBridge)/speed

def prepare_the_street_as_list_until_we_understand_how_to_use_the_geometry(G_un, coords_start, path_nodes):

    epsilon = 1e-10
    # Converte la lista di nodi in file json
    shapes = []
    for i in range(len(path_nodes)-1):
        shapes.append(shapely.wkt.loads(G_un[path_nodes[i] ][path_nodes[i+1] ]['Wkt']))
    #print(shapes)
    x_tot = []
    for sha in shapes:
    # print(sha.coords.xy)
        x = []
        for i in range(len(sha.coords.xy[0])):
            x.append((sha.coords.xy[0][i],sha.coords.xy[1][i]))
        # to be corrected with x_start
        if not x_tot:
            if geopy.distance.distance(coords_start, x[0]) < epsilon:
                x_tot+=x
            elif geopy.distance.distance(coords_start, x[-1]) < epsilon:
                x_tot+=x[::-1]
            else:
                logging.warning("Coordinata iniziale non trovata nel primo arco")
                logging.warning(coords_start)
                logging.warning(x[0])
                logging.warning(x[-1])
                x_tot+=x
        elif geopy.distance.distance(x[0], x_tot[-1]) < epsilon:
            # print(x[0], "uguali",x_tot[-1])
            x_tot+=x
        else:
            # print(x[0],"diversi", x_tot[-1])
            x_tot+=x[::-1]

    return x_tot

def save_graph_pickle(shp_file,pickle_name):
    G = nt.read_shp(shp_file)
    G_un = G.to_undirected()

    with open(pickle_name, 'wb') as file:
        pickle.dump(G_un, file)
    return
