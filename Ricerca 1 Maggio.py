# %% codecell
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
import matplotlib.pyplot as plt
%matplotlib

print(punti)
for punti_func in punti:

plt.bar([0, 1, 2, 3], punti[:,0]);
plt.bar([0, 1, 2, 3], punti[:,1])

# %%
import re
name = "CANNAREGIO 3782/B"
format_civico = re.compile("(^\d+([ |/]?\w )?)|(\d+[ |/]?\w?$)")
is_civico = format_civico.search(name)
if is_civico:
    # se il nome cercato rientra nel format del civico estrae il numero
    numero = is_civico.group(0)
    # formatta il numero nel format in cui è salvato nel database
    numero_cifra = re.findall(r'\d+',numero)
    numero_lettera = re.findall(r'[A-z]',numero)
    numero = numero_cifra[0]
    if numero_lettera:
        numero += '/' + numero_lettera[0]



numero
numero_lettera
