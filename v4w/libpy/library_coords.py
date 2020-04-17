from libpy.mydifflib import get_close_matches_indexes
import numpy as np
import logging
import time


"""
da civico, ritorna una coordinata (x,y), che e anche la stringa di accesso a un nodo
"""
def civico2coord(coord_list,civico_name,civico_list, civico_coord):
    coordinate = np.asarray(coord_list)
    # removing one (or more) annoying none values
    #streets_corrected = [street if street else "" for street in streets_list]
    option_number = 3 #rimetto 3 per adesso, poi cambiamo
    matches = get_close_matches_indexes(civico_name.upper(), civico_list, option_number)
    streets_founds = []
    if civico_list[matches[0]] == civico_name.upper():
        which_one = 0
    else:
        for i in range(len(matches)):
            streets_founds.append(civico_list[matches[i]])
            print("Trovato: {}:{}".format(i, streets_founds[i]))
        which_one = int(input("Quale intendi? Scrivi il numero\n"))

    coord = civico_coord[matches[which_one]]
    tmp = np.subtract(np.ones((coordinate.shape)) * coord, coordinate)
    idx = np.argmin(np.sum(tmp * tmp, axis=1))
    return (coordinate[idx][0], coordinate[idx][1])

"""
Cerca la coordinata e ritorna senza nessuna interazione:
Piu in dettaglio,
1 - cerchiamo il civico nella lista,
2 - estraiamo la sua coordinata,
3 - cerchiamo il nodo piu vicino NEL GRAFO
4 - ritorniamo le sue coordinate

@param:
    - coord_list: lista di coordinate DEI NODI DEL GRAFO
    - civico_name: il nome da trovare tra quelli in civico_list
    - civico_list: lista dei civici DALLO SHAPEFILE
    - civico_coord: le coordinate dei civici relativi alla lista civico_list SHAPEFILE

@return:
    - coordinata: tupla (x,y) - relativa alle coordinate del GRAFO
    - nome scelto - relativo alla lista dei civici ottenuta dallo SHAPEFILE
"""
def civico2coord_first_result(coord_list, civico_name, civico_list, civico_coord):
    # numpy array delle coordinate
    coordinate = np.asarray(coord_list)
    # solo il match migliore!
    option_number = 1 #rimetto 3 per adesso, poi cambiamo
    # trova il nome piu vicino
    t1=time.perf_counter()
    matches = get_close_matches_indexes(civico_name.upper(), civico_list, option_number)
    logging.info('ci ho messo {tot} a trovare il match'.format(tot=time.perf_counter() - t1))
    # estrae la sua coordinata

    if not matches:
        indice_lista_civico = 0
    elif matches[0] < 0 or matches[0] > len(civico_coord):
        indice_lista_civico = 0
    else:
        indice_lista_civico = matches[0]
    coord = civico_coord[indice_lista_civico]
    # nome del civico/toponimo piu vicino
    name_chosen = civico_list[indice_lista_civico]
    # cerca il nodo piu vicino
    t2 = time.perf_counter()
    tmp = np.subtract(np.ones((coordinate.shape)) * coord, coordinate)
    logging.info('ci ho messo {tot} a trovare il match'.format(tot=time.perf_counter() - t2))
    t3 = time.perf_counter()
    # indice del nodo piu vicino
    idx = np.argmin(np.sum(tmp * tmp, axis=1))
    logging.info('ci ho messo {tot} trovare l indice'.format(tot=time.perf_counter() - t3))

    return (coordinate[idx][0], coordinate[idx][1]), name_chosen[:-1]

def civico2coord_find_address(civico_name, civico_list, civico_coord):

    # solo il match migliore!
    option_number = 1 #rimetto 3 per adesso, poi cambiamo
    # trova il nome piu vicino
    matches = get_close_matches_indexes(civico_name.upper(), civico_list, option_number)
    # estrae la sua coordinata
    if not matches:
        indice_lista_civico = 0
    elif matches[0] < 0 or matches[0] > len(civico_coord):
        indice_lista_civico = 0
    else:
        indice_lista_civico = matches[0]
    coord = civico_coord[indice_lista_civico]
    # nome del civico/toponimo piu vicino
    name_chosen = civico_list[indice_lista_civico]



    return (coord[0], coord[1]), name_chosen[:-1]
