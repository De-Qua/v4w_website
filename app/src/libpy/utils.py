import numpy as np

def find_closest_node(G_array):
    tmp = np.subtract(np.ones((coordinate.shape)) * coord, G_array)
    # indice del nodo piu vicino
    idx = np.argmin(np.sum(tmp * tmp, axis=1))
    return (coordinate[idx][0], coordinate[idx][1])
