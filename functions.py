"""
Solo funzioni
"""
import re
import difflib
from difflib import SequenceMatcher
import numpy as np
from heapq import nlargest
from fuzzywuzzy import fuzz, process
import matplotlib.pyplot as plt
import time

n = 3
cutoff = 0.5
import os
folder = os.getcwd() + "/logs_ricerca"

"""
La versione modificata di get_close_matches_indexes_original
"""
def get_close_matches_indexes(word, possibilities, junk_seq=None, n=3, cutoff=0.5):
    if not n >  0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result_ratio = []
    result_idx = []
    # se vogliamo escludere le "junk sequence" (in questo caso lo spazio) SequenceMatcher(lambda x: x==" "),
    if junk_seq:
        s = SequenceMatcher(isjunk=lambda x: x==junk_seq)
    else:
        s = SequenceMatcher()
    s.set_seq2(word)

    for idx, x in enumerate(possibilities):
        s.set_seq1(x)

        longest_match = s.find_longest_match(0, len(x), 0, len(word))
        our_ratio = (longest_match.size) / len(word)
        if our_ratio >= cutoff:
            match = s.find_longest_match(0, len(x), 0, len(word))
            #print(match)
            #print (word[match.a:match.a + match.size])
            result_ratio.append(our_ratio)
            result_idx.append(idx)


    max_idx = []
    if result_ratio:
        ratios = np.asarray(result_ratio)
        max_idx = []
        for i in range(n):
            arg_max_idx=np.argmax(result_ratio)
            if result_ratio[arg_max_idx] < cutoff:
                max_idx.append((-1, 0))
            else:
                max_idx.append((result_idx[arg_max_idx], result_ratio[arg_max_idx]))
            #messo a zero cosi la prossima volta prendiamo il prossimo "massimo"
            result_ratio[arg_max_idx] = 0

    #max_idx e una lista con
    #[(indice del match, score), (indice match, score)]
    final_result = []
    for i,s in max_idx:
        final_result.append((possibilities[i],s))
    return final_result


def get_close_matches_indexes_original(word, possibilities, junk_seq=None, n=3, cutoff=0.6):
    """Use SequenceMatcher to return a list of the indexes of the best
    "good enough" matches. word is a sequence for which close matches
    are desired (typically a string).
    possibilities is a list of sequences against which to match word
    (typically a list of strings).
    Optional arg n (default 3) is the maximum number of close matches to
    return.  n must be > 0.
    Optional arg cutoff (default 0.6) is a float in [0, 1].  Possibilities
    that don't score at least that similar to word are ignored.
    """

    if not n >  0:
        raise ValueError("n must be > 0: %r" % (n,))
    if not 0.0 <= cutoff <= 1.0:
        raise ValueError("cutoff must be in [0.0, 1.0]: %r" % (cutoff,))
    result = []
    s = SequenceMatcher()
    s.set_seq2(word)
    for idx, x in enumerate(possibilities):
        s.set_seq1(x)
        if s.real_quick_ratio() >= cutoff and \
           s.quick_ratio() >= cutoff and \
           s.ratio() >= cutoff:
            name_result = possibilities[idx]
            result.append((name_result,(s.ratio())))

    # Move the best scorers to head of list
    result = nlargest(n, result)

    # Strip scores for the best n matches
    #return [x for score, x in result]
    # Modified by Ale
    return result

    #%%
def fuzzy_extract_matches(word, possibilities, junk_seq=None, n=3, cutoff=0.5):
    score_cutoff = int(cutoff*100)
    matches = process.extractBests(word,possibilities,score_cutoff=score_cutoff,limit=n)
    final_matches = []
    for m,s in matches:
        final_matches.append((m,s/100))
    return final_matches
#%%

def correct_name(name):
    # prende la stringa in ingresso e fa delle sostituzioni
    # 0. Eliminare spazi iniziali e finali
    name = name.strip()
    # 1. Sostituzione s.->san
    name = name.replace("s.","san ")
    # 2. Rimozione doppi spazi
    name = name.replace("  "," ")
    # Ritorna stringa corretta
    return name.upper()

def search_name(name,search_func,n=3,cutoff=0.6):
    # in base alla formattazione del nome cerca nel database civici o toponimi
    # prima di tutto correggere il nome
    name = correct_name(name)
    # format del civico:
    # 1. inizia con un numero (es. "2054 santa marta")
    # 2. finisce con un numero (es. "san polo 1424")
    # 3. finisce con un numero e una lettera (es. "santa croce 1062b" oppure "1062 b" oppure "1062/b")
    # nb se il numero è seguito da una lettera ed è all'inizio del nome, la lettera viene riconosciuta solo se seguita da uno spazio
    format_civico = re.compile("(^\d+([ |/]?\w )?)|(\d+[ |/]?\w?$)")
    is_civico = format_civico.search(name)
    if is_civico:
        # se il nome cercato rientra nel format del civico estrae il numero
        numero = is_civico.group(0)
        # formatta il numero nel format in cui è salvato nel database
        numero_cifra = re.findall(r'\d+',numero)
        numero_lettera = re.findall(r'[a-z]',numero)
        numero = numero_cifra[0]
        if numero_lettera:
            numero += '/' + numero_lettera[0]

        sestiere = name[:is_civico.start()]+name[is_civico.end():]
        sestiere = sestiere.strip() # elimina spazi che possono essersi creati togliendo il numero

        sestieri_list = np.array(['SAN POLO','SANTA CROCE','SAN MARCO','DORSODURO','CANNAREGIO','CASTELLO','GIUDECCA'])
        sestiere_found = difflib.get_close_matches(sestiere,sestieri_list,n=1,cutoff=0.6)
        if len(sestiere_found) == 1 or (len(sestiere_found)>1 and SequenceMatcher(None, sestiere, sestiere_found[0]).ratio()>0.85):
            # concatena sestiere e numero
            name2search = sestiere_found[0] + " " + numero
            # TODO lista INDIRIZZI
            list_of_possibilities = civici_only
        else:
            name2search = sestiere + " " + numero
            list_of_possibilities = denominazioni_only
    else:
        name2search = name
        list_of_possibilities = toponimi_only
    return search_func(name2search,list_of_possibilities,n=n,cutoff=cutoff)

"""
Ritorna due punteggi in base ai risultati migliori
------
@param:
    - result_tuples: i risultati (dati dall'algoritmo, migliori n, almeno 3)
    - desired_results: i risultati desiderati (li abbiamo messi noi a mano)
    - desired_results_scores: i punteggi dei risultati desiderati (li abbiamo messi noi a mano)

@return
    - score_perfect: il punteggio basato solo sulla prima risposta - (o 1 o 0, binario)
    - score_general: il punteggio basato sui migliori 3 - (i valori sono dati in input e sommano a 1, discreto)
"""
def calculate_points(results_tuples, desired_results, desired_results_scores):

    score_general = 0
    score_perfect = 0
    for result_tuple in results_tuples:
        # prendiamo la string (result_tupe[1] e lo score)
        string_found = result_tuple[0]

        # controlliamo se abbiamo trovato
        for k in range(len(desired_results)):
            if string_found == desired_results[k]:
                score_general += desired_results_scores[k]

        # controlla solo il primo!
        if string_found == desired_results[0]:
            score_perfect += 1

    return score_perfect, score_general

def test_functions(functions_to_test, lista_su_cui_cercare, list_of_searches, categories, saveresults=False, savelog=False):

    points_functions = []
    for function_to_test in functions_to_test:

        print("testiamo ora {func}".format(func=function_to_test.__name__))
        punti = np.zeros((len(categories),3))
        if savelog:
            file = open("{fd}/log_{met}.txt".format(fd=folder, met=function_to_test.__name__), 'w')

        # loop through searches
        for i in range(len(list_of_searches)):

     #      print("ricerca: {}".format(list_of_searches[i]))
            challenging_search = list_of_searches[i][0].upper()
            desired_results = list_of_searches[i][1]
            desired_results_scores = list_of_searches[i][2]
            category = list_of_searches[i][3]
            time_start = time.time()
            results_tuples = function_to_test(challenging_search, lista_su_cui_cercare, n=n, cutoff=cutoff)
            time_end = time.time()
            search_time = time_end - time_start
            score_perfect, score_general = calculate_points(results_tuples, desired_results, desired_results_scores)
            if savelog:
                file.write("###############################################\n")
                file.write("{pt} punti ottenuti per la ricerca di: ({search})\n".format(pt=score_general, search=challenging_search))
                file.write("trovato: {}, volevamo che trovasse {}\n".format(results_tuples, desired_results))
                file.write("ci ha messo {sec} secondi\n".format(sec=search_time))
            else:
                print("###############################################")
                print("{pt} punti ottenuti per la ricerca di: ({search})".format(pt=score_general, search=challenging_search))
                print("trovato: {}, volevamo che trovasse {}".format(results_tuples, desired_results))
                print("ci ha messo {sec} secondi".format(sec=search_time))
            for j in range(len(categories)):
                if (category == categories[j]):
                    punti[j,0] += score_perfect
                    punti[j,1] += score_general
            punti[0,2] += search_time

        punti[0,2] /= len(list_of_searches)
        avg_search_time = punti[0,2]
        print("Il metodo {met} riceve {x} punti".format(met=function_to_test.__name__, x=np.sum(punti)))
        print("In media ci mette {tempo} per ogni ricerca".format(tempo=avg_search_time))
        if savelog:
            file.write("Il metodo {met} riceve {x} punti\n".format(met=function_to_test.__name__, x=np.sum(punti)))
            file.write("In media ci mette {tempo} per ogni ricerca\n".format(tempo=avg_search_time))
        for j in range(len(categories)):
            print("per la categoria {c}, {p} punti per la perfezione (solo il primo) e {g} punti per i matches in generale".format(c=categories[j], p=punti[j,0], g=punti[j,1]))
            if savelog:
                file.write("per la categoria {c}, {p} punti per la perfezione (solo il primo) e {g} punti per i matches in generale\n".format(c=categories[j], p=punti[j,0], g=punti[j,1]))

        points_functions.append(punti)
        if savelog:
            file.close()
        # salva un file con i risultati
        if saveresults:
            np.savetxt("{fd}/punti_{met}.csv".format(fd=folder, met=function_to_test.__name__), punti)
            print("saving a csv file with results")
    print("finished")
    return points_functions

def plot_figure(folder_with_results, categories):

    files = os.listdir(folder_with_results)
    csv_files = [file for file in files if (file[-4:] == '.csv')]

    plt.figure(figsize=(16, 16), dpi=80, facecolor='w', edgecolor='k')
    how_many = len(csv_files)
    mid_val = how_many / 2
    x_fake = np.asarray([0, 2, 4, 6])
    x_fake_times = np.asarray([0])
    ax = plt.subplot(221)
    for i in range(how_many):

        cur_file_rel_path = csv_files[i]
        cur_path = os.path.join(folder_with_results, cur_file_rel_path)
        cur_func_res = np.loadtxt(cur_path)

        ax.bar(x_fake+(0.2*(i-mid_val)), cur_func_res[:,0], width=0.2, label = cur_file_rel_path[6:-4])
        plt.xticks(x_fake, categories)
        plt.title("PERFETTO")
        plt.legend()

    ax = plt.subplot(222)
    for i in range(how_many):

        cur_file_rel_path = csv_files[i]
        cur_path = os.path.join(folder_with_results, cur_file_rel_path)
        cur_func_res = np.loadtxt(cur_path)
        ax.bar(x_fake+(0.2*(i-mid_val)), cur_func_res[:,1], width=0.2, label = cur_file_rel_path[6:-4])
        plt.xticks(x_fake, categories)
        plt.title("GENERALE")
        plt.legend()

    ax = plt.subplot(223)
    for i in range(how_many):

        cur_file_rel_path = csv_files[i]
        cur_path = os.path.join(folder_with_results, cur_file_rel_path)
        cur_func_res = np.loadtxt(cur_path)
        ax.bar((0.2*(i)), cur_func_res[0,2], width=0.2, label = cur_file_rel_path[6:-4])
        plt.xticks([], [])
        plt.xlabel("secondi")
        plt.xlabel("tempo")
        plt.title("TEMPO (in secondi)")
        plt.legend()




