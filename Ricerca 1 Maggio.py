# %% codecell
import sys, importlib
reload(sys.modules["functions"])
reload(sys.modules["searches"])
import functions as func
import searches as src
import numpy as np
import os
from functools import partial, update_wrapper

# %% codecell
folder = os.getcwd()
folder_db = os.path.join(folder,"app","static","files")
# %% codecell
# Lista completa
path_civ = os.path.join(folder_db,"lista_key.txt")
civici_tpn = np.loadtxt(path_civ, delimiter = ";" , comments=",",dtype='str')
# Lista solo indirizzi
path_indirizzi = os.path.join(folder_db,"lista_civici_only.txt")
indirizzi = np.loadtxt(path_indirizzi, delimiter = ";", comments=",",dtype='str')
# Lista solo denominazioni
path_denominazioni = os.path.join(folder_db,"lista_denominazioni_csv.txt")
denominazioni = np.loadtxt(path_denominazioni, delimiter = ";", comments="," ,dtype='str')
# Lista solo toponimi
path_toponimi = os.path.join(folder_db,"lista_TP_csv.txt")
toponimi = np.loadtxt(path_toponimi, delimiter = ";", comments="," ,dtype='str')

# %% codecell
# FUNZIONI DA TESTARE
functions_to_test = [func.get_close_matches_indexes_original, func.get_close_matches_indexes, func.fuzzy_extract_matches]
# %% codecell
# TESTARE
punti = func.test_functions(functions_to_test, civici_tpn, src.list_of_searches, src.categories, saveresults=True, savelog=True)

# %%
search_functions_to_test = [func.get_close_matches_indexes_original, func.get_close_matches_indexes, func.fuzzy_extract_matches]
possibilities = [indirizzi, denominazioni, toponimi]
punti_search = func.test_search_functions(search_functions_to_test, possibilities, src.list_of_searches, src.categories, saveresults=True, savelog=True)
# %% codecell
## NON FUNZIONANTE
# IDEA DI PLOTTARE I GRAFICI DEI RISULTATI
# %% codecell
folder_log = os.path.join(folder,"log_ricerca")
func.plot_figure(folder_log, src.categories)
