import functions as func
import searches as src
import numpy as np
import os

# %% File utili
folder = os.getcwd()
folder_db = os.path.join(folder,"app","static","files")

# LISTA
path_civ = os.path.join(folder_db,"lista_key.txt")
civici_tpn = np.loadtxt(path_civ, delimiter = ";" , comments=",",dtype='str')

# FUNZIONI DA TESTARE
functions_to_test = [func.get_close_matches_indexes, func.fuzzy_extract_matches]

# TESTARE
punti = func.test_functions(functions_to_test, civici_tpn, src.list_of_searches, src.categories)
