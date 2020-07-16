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
# Plot dei grafici dei risultati
folder_log = os.path.join(folder,"log_ricerca")
func.plot_figure(folder_log, src.categories)
# %%
# Test per StringGrouper
import pandas as pd
import numpy as np
from string_grouper import match_strings, match_most_similar, group_similar_strings, StringGrouper
company_names = os.path.join(os.getcwd(),'sec_edgar_company_info.csv')
# We only look at the first 50k as an example
companies = pd.read_csv(company_names)[0:50000]
c =  companies['Company Name']
# Create all matches:
matches = match_strings(companies['Company Name'])
# Look at only the non-exact matches:
matches[matches.left_side != matches.right_side].head()

# Create a small set of artifical company names
duplicates = pd.Series(['S MEDIA GROUP', '012 SMILE.COMMUNICATIONS', 'foo bar', 'B4UTRADE COM CORP'])
# Create all matches:
matches = match_strings(companies['Company Name'], duplicates)
matches
# Create a small set of artificial company names
new_companies = pd.Series(['S MEDIA GROUP', '012 SMILE.COMMUNICATIONS', 'foo bar', 'B4UTRADE COM CORP'])
# Create all matches:
matches = match_most_similar(companies['Company Name'], new_companies)
# Display the results:
pd.DataFrame({'new_companies': new_companies, 'duplicates': matches})
#%%
civici_tpn = pd.read_csv(path_civ,sep="\n",names=["ADDRESS"])

for i in range(len(civici_tpn["ADDRESS"])):
    civici_tpn["ADDRESS"][i] = civici_tpn["ADDRESS"][i][:-1]
c = civici_tpn["ADDRESS"]
src.list_of_searches
test_list = []
for name2search,desired,scores,category in src.list_of_searches:
    test_list.append(name2search.upper())
test_series = pd.Series(test_list)
test_single = pd.Series(["SAN PAOLO 1424"])
matches = match_strings(civici_tpn["ADDRESS"],test_series)
matches
# Display the results:
match_similar = match_most_similar(civici_tpn["ADDRESS"],test_series)
match_similar = match_most_similar(civici_tpn["ADDRESS"],pd.Series(["RIALTO"]))
pd.DataFrame({'new_companies': test_series, 'duplicates': match_similar})
