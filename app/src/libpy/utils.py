import numpy as np

def find_closest_nodes(dict_list,G_array):
    """
    Returns list of nodes in G_array closest to coordinate_list (euclidean distance) 
    """
    coord_beg_end=[]
    for d in dict_list:
        if d.get("geotype")==0 and d.get("shape"):
            coord_beg_end.append(d.get("shape")[0])
            print("node start",d.get("shape")[0])
        else:
            coord_beg_end.append(d.get("coordinate"))
    nodes_list=[]
    for coordinate in coord_beg_end:
        print(coordinate)
        tmp = np.subtract(np.ones(G_array.shape) * coordinate, G_array)
        # indice del nodo piu vicino
        idx = np.argmin(np.sum(tmp * tmp, axis=1))
        print("distance to node", tmp[idx]**2)
        print("node grafo",(G_array[idx][0], G_array[idx][1] ))
        nodes_list.append((G_array[idx][0], G_array[idx][1]))
    return nodes_list

from app.src.libpy.pyAny_lib import calculate_path

def find_path_to_closest_riva(G_un, coords_start, rive_list):
    """
    It finds the path to the closest riva with respect to the starting coordinates.
    """
    length_paths=[]
    paths=[]
    for riva in rive_list:
        path, length = calculate_path(G_un, coords_start, riva, flag_ponti=True)
        length_paths.append(length)
        paths.append(path)

    # qua abbiamo la lista delle strade
    np_lengths = np.asarray(length_paths)
    idx_shortest_path = np.argmin(np_lengths)
    shortest_path = paths[idx_shortest_path]

    # la riva sara l'ultimo nodo della strada
    # closest_riva = shortest_path[-1]
    return shortest_path

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
