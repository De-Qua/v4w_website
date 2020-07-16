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
functions_to_test = [func.get_close_matches_indexes, func.fuzzy_extract_matches, func.get_close_matches_indexes_original]

# TESTARE
punti = func.test_functions(functions_to_test, civici_tpn, src.list_of_searches, src.categories, saveresults=True, savelog=True)

import matplotlib.pyplot as plt
print(punti)
%matplotlib
plt.scatter([0, 1, 2, 3], punti[:,0]);

plt.scatter([0, 1, 2, 3], punti[:,1])

for punti_func in punti:
    print(punti_func)
    plt.scatter(punti_func[0,:], punti_func[1,:])
