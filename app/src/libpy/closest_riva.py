from pyAny_lib import calculate_path
import numpy as np

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
