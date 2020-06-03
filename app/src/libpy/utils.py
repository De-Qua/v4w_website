import numpy as np

def find_closest_nodes(dict_list,G_array):
    """
    Returns list of nodes in G_array closest to coordinate_list (euclidean distance) 
    """
    coord_beg_end=[]
    for d in dict_list:
        if d.get("geo_type")==0:
            coord_beg_end.append(d.get("shape")[0])
        else:
            coord_beg_end.append(d.get("coordinate"))
    nodes_list=[]
    for coordinate in coord_beg_end:
        tmp = np.subtract(np.ones(G_array.shape) * coordinate, G_array)
        # indice del nodo piu vicino
        idx = np.argmin(np.sum(tmp * tmp, axis=1))
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
