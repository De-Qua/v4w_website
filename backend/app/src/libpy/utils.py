import numpy as np
import shapely, shapely.wkt, shapely.geometry

def find_closest_edge(list_of_node_coordinates, graph):
    """
    Return the two nodes that belongs to the closes edge in the graph.
    """
    outcome_list = []
    for node_coordinates in list_of_node_coordinates:
        edges = [edge for edge in graph.edges]
        shapely_canali = [shapely.wkt.loads(graph[cur_edge[0]][cur_edge[1]]['Wkt']) for cur_edge in edges]
        shape_riva = shapely.geometry.Point([node_coordinates[0], node_coordinates[1]])
        distances_riva_canale = [shape_riva.distance(canale) for canale in shapely_canali]
        distanza_piu_corta_index = np.argmin(distances_riva_canale)
        assert (len(distances_riva_canale) == len(edges))
        start_node, end_node = edges[distanza_piu_corta_index]
        start_dist = shape_riva.distance(shapely.geometry.Point([start_node[0], start_node[1]]))
        end_dist = shape_riva.distance(shapely.geometry.Point([end_node[0], end_node[1]]))
        dict_for_a_node = {}
        dict_for_a_node["first_node"] = start_node
        dict_for_a_node["second_node"] = end_node
        dict_for_a_node["first_dist"] = start_dist
        dict_for_a_node["second_dist"] = end_dist
        outcome_list.append(dict_for_a_node)

    return outcome_list

def find_closest_nodes(dict_list,G_array):
    """
    Returns list of nodes in G_array closest to coordinate_list (euclidean distance).
    """
    coord_beg_end=[]
    for d in dict_list:
        if d.get("geotype")==0 and d.get("shape"):
            coord_beg_end.append(d.get("shape")[0])
            #print("node start",d.get("shape")[0])
        else:
            coord_beg_end.append(d.get("coordinate"))
    nodes_list=[]
    for coordinate in coord_beg_end:
        #print(coordinate)
        tmp = np.subtract(np.ones(G_array.shape) * coordinate, G_array)
        # indice del nodo piu vicino
        idx = np.argmin(np.sum(tmp * tmp, axis=1))
        #print("distance to node", tmp[idx]**2)
        #print("node grafo",(G_array[idx][0], G_array[idx][1] ))
        nodes_list.append((G_array[idx][0], G_array[idx][1]))
    return nodes_list

def add_from_strada_to_porta(path, da, a):

    print("first node path", path[0])
    print("last node path", path[-1])
    print("da",da["shape"])
    print("a",a["shape"])
    #print("distanza, da-primo punto di path", (end_from[0]-path[0][0])**2+(end_from[1]-path[0][1])**2)
    #print("distanza, rev(da)-primo punto di path",(end_from_rev[0]-path[0][0])**2+(end_from_rev[1]-path[0][1])**2)
    #print("distanza, primo punto da- secondo punto da", (end_from[0]-end_from_2[0])**2+(end_from[1]- end_from_2[1])**2)
    #print("distanza, primo punto rev(da)-secondo punto rev(da)",(end_from_rev[0]-end_from_rev_2[0])**2+(end_from_rev[1]- end_from_rev_2[1])**2)
    fro=[]
    to=[]
    if da["geotype"]==0 and da["shape"]:
        fro =da["shape"][::-1]
        print("added fro")
    if a["geotype"]==0 and a["shape"]:
        to =a["shape"]
        print("added to")
    path=[fro+[coo for coo in path]+to]
    return path[0]
