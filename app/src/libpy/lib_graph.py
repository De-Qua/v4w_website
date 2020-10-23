"""
Here you can find everything to work on the city graph. Networkx, Shapely, Geopy and Dictionary geeks will love to sneak around.
"""
import numpy as np
import networkx as nt
from networkx.exception import NetworkXNoPath
import sys
import os
import pdb
import pickle
from shapely.geometry import shape
import json
import logging
from app import app
import shapely, shapely.wkt
from shapely.geometry import mapping
import geopy.distance
import datetime
import app.global_variables as global_variables

from app import custom_errors

speed_global=2
# variabili per aiutarci a scegliere le funzioni peso
# (la funzione peso se no non ci avrebbe accesso)
flag_ponti_glob = False
flag_tide_glob = False
water_flag_glob = False

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

"""
 OLD VERSION OF dynamically_add_edges
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
"""


def dynamically_add_edges(water_graph, list_of_edges_node_with_their_distance, rive):
    """
    Ora chiama connect_land_to_water per ogni coppia (riva, dizionario). La dobbiamo modificare
    """
    app.logger.warning("Warning: aggiunge solo 2 edges (e se la lista ne ha uno solo dara errore!), dobbiamo finirlo!")
    coord_riva_start = rive[0]
    coord_riva_end = rive[1]
    added_edges = []

    assert(len(rive)==len(list_of_edges_node_with_their_distance), 'We need same number of edges-nodes dictionaries and rive (2 in most cases)')
    for i in range(len(rive)):
        cur_riva = rive[i]
        cur_edges_node_dist = list_of_edges_node_with_their_distance[i]
        added_eges = connect_land_to_water(water_graph, cur_edges_node_dist, cur_riva)
        app.logger.debug("Added:\n {}".format(added_edges))

    return added_edges

def connect_land_to_water(graph, node_and_dists_dict, coord_riva):
    """
    Add connection from the riva to the water graph. Now with 2 edges, later smarter with only one hopefully.
    """
    #### QUA METTERE LA MANIERA INTELLIGENTE DI UNIRE GLI ARCHI (tagliando un arco acqueo)
    # dal nodo 1 alla riva
    linestring_first_node = shapely.geometry.LineString([node_and_dists_dict['first_node'], coord_riva]).wkt
    create_edge(graph, node_and_dists_dict['first_node'], coord_riva, node_and_dists_dict['first_dist'], linestring_first_node)
    # dal nodo 2 alla riva
    linestring_second_node = shapely.geometry.LineString([node_and_dists_dict['second_node'], coord_riva]).wkt
    create_edge(graph, node_and_dists_dict['second_node'], coord_riva, node_and_dists_dict['second_dist'], linestring_second_node)

    return [(node_and_dists_dict['first_node'], coord_riva), (node_and_dists_dict['second_node'], coord_riva)]

def create_edge(graph, first_node, last_node, length=0, linestring=None, vel_max=20, vel_max_mp=20, solo_remi=0,
larghezza=10, altezza=1000, senso_unico=None, h_su_start=0, h_su_end=24, dt_start=24, dt_end=24, h_closed_start=None, h_closed_end=None, nome=""):
    """
    """
    graph.add_edge(first_node, last_node)
    attrs_edge = {(first_node, last_node): {'length':length, 'Wkt':linestring, 'vel_max':vel_max, 'solo_remi':solo_remi,
        'larghezza':larghezza, 'senso_unic':senso_unico,'h_su_start':h_su_start,'h_su_end':h_su_end,
        'h_closed_start':h_closed_start, 'h_closed_end':h_closed_end, 'nome':nome, 'altezza':altezza, 'dt_start':dt_start, 'dt_end':dt_end}}
    nt.set_edge_attributes(graph, attrs_edge)

def dynamically_remove_edges(G,list_of_edges):
    """
    Rimuove dal grafo degli edge. List_of_edges è una lista di tuple (nodo1,nodo2)
    """
    for edge in list_of_edges:
        G.remove_edge(edge[0], edge[1])
        app.logger.debug("removed edge {}".format(edge[0], edge[1]))

    return

def give_me_the_street(G, coords_start, coords_end, flag_ponti=False, speed=1, water_flag=False, flag_tide=False):
    """
    A wrapper for the path calculation. It calculates the path, that run again through all of it to create a the geojson information to draw it on Leaflet.
    """
    global flag_ponti_glob, water_flag_glob, flag_tide_glob
    flag_ponti_glob = flag_ponti
    water_flag_glob = water_flag
    flag_tide_glob = flag_tide

    path_nodes = []
    streets_info = {}
    if water_flag:
        weight_func = weight_motor_boat
    elif flag_tide_glob:
        weight_func = weight_high_tide #(dentro decide se ha ponti o no)
    elif flag_ponti:
        weight_func = weight_bridge
    else:
        weight_func = weight_time # ###temporary! weight_time

    global speed_global
    speed_global=speed
    path_nodes, length = calculate_path_wkt(G, coords_start, coords_end, weight_func)
    # non volevamo avere gli errori?
    # if not path_nodes:
    #   raise Exception("No street found between {} and {}".format(coords_start, coords_end))
    # else:
    if path_nodes:
        streets_info = go_again_through_the_street(G,path_nodes,speed,water_flag)
        #street = prepare_the_street_as_list_until_we_understand_how_to_use_the_geometry(G,coords_start,path_nodes)
    return streets_info

def weight_bridge(x,y,dic, bridge_factor=100):
    """
    It weights bridges different, so that dijkstra may find the optimal path as a path with less bridges.
    """
    return dic["length"] + dic["ponte"]*bridge_factor*dic['length']

def weight_time(x,y,dic):
    """
    It weights the street in terms of time and not of length: in case different streets have different speeds, it may be better to take a faster longer road.
    """
    # ma se spped e fisso, non ha senso no?
    # 4kmh in metri al minuto
    global speed_global
    speed = speed_global/3.6
    # speed = np.min(speed, dic["VEL_MAX"]) ?
    return dic["length"]/speed

def weight_high_tide(x,y,dic):

    global flag_ponti_glob
    print("\n\n***\nvariabile globale flag ponti: ", flag_ponti_glob)
    #qui o solo all'inizio va fatta la query alle api dell'acqua alta
    if not dic['max_tide']:
        # do something even if we don't have the level of the ground
        if flag_ponti_glob:
            return weight_bridge(x,y,dic)
        else:
            return weight_time(x,y,dic)
    elif dic['max_tide']<global_variables.current_tide+global_variables.safety_diff_tide: # ci diamo un margine per non mandare la gente nella merda
        return 100000
    else:
        if flag_ponti_glob:
            return weight_bridge(x,y,dic)
        else:
            return weight_time(x,y,dic)

def weight_high_tide_low_boots(x,y,dic):
    #qui o solo all'inizio va fatta la query alle api dell'acqua alta
    if dic['max_tide']<global_variables.current_tide+global_variables.safety_diff_tide+global_variables.height_low_boots: # ci diamo un margine per non mandare la gente nella merda
        return 100000
    else:
        return weight_time(x,y,dic)

def weight_high_tide_high_boots(x,y,dic):
    #qui o solo all'inizio va fatta la query alle api dell'acqua alta
    if dic['max_tide']<global_variables.current_tide+global_variables.safety_diff_tide+global_variables.height_high_boots: # ci diamo un margine per non mandare la gente nella merda
        return 100000
    else:
        return weight_time(x,y,dic)

def weight_motor_boat(x,y,dic):
    """
    It weights the street in terms of time and not of length: in case different streets have different speeds, it may be better to take a faster longer road.
    """
    global speed_global
    actual_hour=int(datetime.datetime.now().strftime("%H"))
    #if dic['altezza']<1000:
        #app.logger.info("Stai passando sotto un ponte alto {} metri".format(dic['altezza']))
    #if (dic['senso_unic'] is not None) and (dic['h_su_start']<=actual_hour<dic['h_su_end']):
    if (dic['senso_unic'] is not None) and (dic['h_su_start'] <= actual_hour < dic['h_su_end']):
        verso=None
        line=mapping(shapely.wkt.loads(dic['Wkt']))
        first_point_in_linestring = line['coordinates'][0]
        if (first_point_in_linestring[0]-x[0])<10e-15 and (first_point_in_linestring[1]-x[1])<10e-15:
            verso=-1
        elif  (first_point_in_linestring[0]-y[0])<10e-15 and (first_point_in_linestring[1]-y[1])<10e-15:
            verso=1
        else:
            app.logger.debug("something wrong here!")
        if dic['senso_unic'] != verso:
            #app.logger.debug("Sei nel verso sbagliato per questo senso unico {} !".format(dic))
#            pdb.set_trace()
            return None
    if dic['dt_start'] <= actual_hour < dic['dt_end']:
        return None
    if dic['solo_remi']:
        #app.logger.debug("le barche a motore non passano per {} !".format(dic))
        return None
    elif dic['vel_max'] == 0:
        #app.logger.debug("Il canale è chiuso {} !".format(dic))
        return None
    else:
        max_speed=dic['vel_max']/3.6
        speed=np.minimum(speed_global, max_speed)
        #app.logger.debug("limite di velocita {} !".format(max_speed))
        #app.logger.debug(" velocita scelta {} !".format(speed))
#        pdb.set_trace()
        # speed = np.min(speed, dic["VEL_MAX"]) ?
        return dic["length"]/speed

def calculate_path_wkt(G_un, coords_start, coords_end, weight_func):
    """
    It calculates the path from coords_start to coords_end using the shape contained in the edges of the G_un graph.
    """
    try:
        length_path, path = nt.algorithms.shortest_paths.weighted.single_source_dijkstra(G_un,coords_start,coords_end, weight=weight_func)
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
        raise custom_errors.UserError("Non esiste un percorso tra A e B. Devi forse andare in barca?")

    return path_nodes, length_path #json.dumps(x_tot), length_path



def go_again_through_the_street(G, path_nodes, speed, water_flag=False, tide_flag=False):
    """
    Go through the path and retrieve informations about it (bridges, speed, ecc..).
    """
    # edges_info diventera un array di geojson - ogni edge e un geojson
    # ogni edge avra prpoperty che determinera come viene disegnato
    # link qua --> https://leafletjs.com/examples/geojson/

    # crea il dizionario da ritornare
    streets_info = {}
    edges_info = []
    shapes = []
    time=0
    lunghezza = 0.0
    # ponti can have 8 accessible values:
    # 0: not accessible (i.e. bridge with steps)
    # 1: flat (i.e. no bridge)
    # 2: gradino_agevolato
    # 3: gradino_agevolato_con_accompagnatore
    # 4: rampa_fissa
    # 5: rampa_provvisoria da feb a nov
    # 6: rampa_provvisoria da set a giu
    # 7: rampa_provvisoria da mag a nov
    tot_ponti_accessible = [0,0,0,0,0,0,0,0]
    tot_ponti=0
    last_edge_was_a_bridge = False
    altezza = np.inf
    for i in range(len(path_nodes)-1):
        isBridge = 0
        edge_attuale = G[path_nodes[i]][path_nodes[i+1]]
        edge_info_dict = {}
        if water_flag:
            edge_info_dict['street_type'] = 'canale'
            #print(edge_attuale)
            #edge_info_dict['']
            speed_edge = np.minimum(speed, edge_attuale['vel_max']/3.6)
            edge_info_dict['vel_max'] = edge_attuale['vel_max']
            edge_info_dict['solo_remi'] = edge_attuale['solo_remi']
            edge_info_dict['larghezza'] = edge_attuale['larghezza']
            altezza = np.minimum(altezza, edge_attuale['altezza'])
            # prendiamo informazioni sulle ordinanze in modo da creare un warning
        else:
            speed_edge = np.minimum(speed, edge_attuale['vel_max']/3.6)
            isBridge = edge_attuale['ponte']
            if global_variables.tideflag:
                if not edge_attuale['min_tide']:
                    # do something even if we don't have the level of the ground
                    edge_info_dict['wet_warning'] = True;
                elif edge_attuale['min_tide']<=global_variables.current_tide:
                    edge_info_dict['wet_warning'] = True;
            if isBridge:
                edge_info_dict['street_type'] = 'ponte'
                accessibleLevel = edge_attuale['accessible']
                if not last_edge_was_a_bridge:
                    tot_ponti += 1
                    tot_ponti_accessible[accessibleLevel] += 1
                last_edge_was_a_bridge = True
            else:
                edge_info_dict['street_type'] = 'calle'
                last_edge_was_a_bridge = False

            edge_info_dict['bridge'] = isBridge

        time += how_long_does_it_take_from_a_to_b(edge_attuale['length'], speed_edge, isBridge)
        lunghezza += edge_attuale['length']
        geojson = {
            "type": "Feature",
            "properties": edge_info_dict,
            "geometry": dict(mapping(shapely.wkt.loads(edge_attuale['Wkt'])))
        }
        shapes.append(geojson)
    streets_info['lunghezza'] = lunghezza
    streets_info['human_readable_length'] = prettify_length(lunghezza)
    streets_info['time'] = time
    streets_info['human_readable_time'] = prettify_time(time)
    streets_info['n_ponti'] = [tot_ponti, tot_ponti_accessible]
    streets_info['shape_list'] = shapes
    streets_info['altezza'] = altezza if altezza < np.inf else None
    return streets_info

def how_long_does_it_take_from_a_to_b(length, speed, isBridge):
    return (length + length/5*isBridge)/speed

def prettify_length(length):
    """
    It returns a string describing the amount of time.
    """
    range = 0.15
    if length < (1000 - range*1000):
        return "{} metri".format(np.round(length).astype(int))
    #else:
    # un chilometro?
    if np.abs(length - 1000) < range:
        return "circa 1 chilometro ({} metri)".format(np.round(length).astype(int))
    # x chilometri?
    km_length = length/1000
    if np.round(km_length) - km_length < range:
        return "circa {} chilometri ({} metri)".format(np.round(km_length).astype(int), np.round(length).astype(int))

    return "{} metri".format(np.round(length).astype(int))

def prettify_time(time):
    """
    It returns a string describing the amount of time.
    """
    if time < 60:
        return "un batter d'occhio!"
    #else:
    minutes = np.round(time/60).astype(int)
    range = 3
    if minutes == 1:
        return "un minuto"
    if np.abs(minutes - 15) < range:
        return "circa un quarto d'ora"
    elif np.abs(minutes - 30) < range:
        return "mezz'oretta"
    elif np.abs(minutes - 45) < range:
        return "tre quarti d'ora"
    elif np.abs(minutes - 60) < range:
        return "un'oretta"
    elif minutes > 60:
        return "tantissimo (circa {} minuti). Dove stai andando?".format(minutes)
    #
    return "circa {} minuti.".format(minutes)

def add_from_strada_to_porta(path, da, a):
    """
    It adds address linestring to connect doors with streets.
    """
    path['shape_list'].insert(0,da['geojson'])
    path['shape_list'].append(a['geojson'])
    return path

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
