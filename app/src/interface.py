"""
This class is an interface between routes.py (the main page where the routing happens, where the communication and the redirecting happens)
and the libraries (in libpy), in order to maintain clean the routes page.
"""
import time
from app.src.libpy.lib_search import find_closest_nodes, find_closest_edge, find_path_to_closest_riva, find_POI, find_address_in_db, give_me_the_dictionary, are_we_sure_of_the_results
from app.src.libpy.lib_communication import prepare_our_message_to_javascript
import pdb
from app.src.libpy import lib_graph, lib_communication, lib_search
from app.models import PoiCategoryType, Location, Poi, poi_types, PoiCategory
from sqlalchemy import and_
from app import app, db
from app.forms import FeedbackForm
import numpy as np

def retrieve_parameters_from_GET(arguments_GET_request):
    """
    Returns the parameters sent from the map page through the get method during a research.
    """
    # this could go in a method retrieve_parameters_from_GET
    da = arguments_GET_request.get('partenza', default='', type=str)
    a = arguments_GET_request.get('arrivo', default='', type=str)
    # new code! i bottoni sono 'off' o 'on'
    less_bridges = arguments_GET_request.get('lazy', default='off', type=str)
    by_boat = arguments_GET_request.get('boat', default='off', type=str)
    with_tide = arguments_GET_request.get('tide', default='off', type=str)
    by_ambulance = arguments_GET_request.get('ambu', default='off', type=str)

    return [da, a, less_bridges, by_boat, with_tide, by_ambulance]

def take_care_of_the_feedback(form, file_feedback):
    """
    Wrapper that try to validate and write the feedback
    """
    if form.is_submitted():
        if form.validate_on_submit():
            all_good = write_feedback(form, file_feedback)
            app.logger.info("feedback inviato")
            return 1
        else:
            app.logger.info('errore nel feedback')
            return 0


def write_feedback(form, file_feedback):
    """
    Just writes the feedback to the given file.
    """
    with open(file_feedback,'a') as f:
        f.write('*****\n')
        f.write(time.asctime( time.localtime(time.time()))+"\n")
        categoria = dict(form.category.choices).get(form.category.data)
        f.write(categoria+'\n')
        f.write(form.name.data+'\n')
        f.write(form.email.data+'\n')
        f.write(form.searched_string.data+'\n')
        f.write(form.found_string.data+'\n')
        f.write(form.feedback.data + "\n")
        f.write('*****\n')

def ask_yourself(params_research):
    """
    In search for the truth, we try to find out if you are looking for the happiness, an address or a path from A to B.
    """
    da, a, less_bridges, by_boat, with_tide, by_ambulance = params_research
    if da == "":
        return "nothing", "irrelevant"
    elif a == "":
        return "address", "irrelevant"
    elif by_boat == "on":
        return "path", "by_boat"
    elif less_bridges == "on":
        return "path", "less_bridges"
    else:
        return "path", "path_walking"


def find_what_needs_to_be_found(params_research, G_objects):
    """
    Take care of the whole research (many cases) calling smaller methods.
    """

    what_am_I_really_searching_for, how_to_get_there = ask_yourself(params_research)

    da = params_research[0]
    a = params_research[1]
    G_terra = G_objects['land_graph']
    G_acqua = G_objects['water_graph']
    G_terra_array = np.asarray(list(G_terra.nodes))
    G_acqua_array = np.asarray(list(G_acqua.nodes))

    if what_am_I_really_searching_for == "nothing":
        return "None"

    elif what_am_I_really_searching_for == "address":
        app.logger.debug('ricerca singolo indirizzo: {}'.format(da))
        t0 = time.perf_counter()
        match_dict = lib_search.give_me_the_dictionary(da)
        if are_we_sure_of_the_results(match_dict):
            # per ora usiamo solo la coordinata (nel caso di un poligono ritorno il centroide) e il nome, ma poi cambieremo
            app.logger.info('ci ho messo {tot} a calcolare la posizione di un indirizzo'.format(tot=time.perf_counter() - t0))
            modus_operandi = 0
            final_dict = prepare_our_message_to_javascript(modus_operandi, da, match_dict) # aggiunge da solo "no_path" e "no_end"
            app.logger.debug("risposta per indirizzo singolo: {}".format(final_dict))
        else:
            modus_operandi = 2
            final_dict = prepare_our_message_to_javascript(modus_operandi, da, match_dict, start_type='multiple')

    else:

        t0=time.perf_counter()
        match_dict_da = lib_search.give_me_the_dictionary(da)
        match_dict_a = lib_search.give_me_the_dictionary(a)
        app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))
        app.logger.info("ricerca percorso da {} a {}..".format(da, a))

        if are_we_sure_of_the_results(match_dict_da):

            app.logger.info("Andiamo a botta sicura! Abbiamo trovato quello che cercavamo e calcoliamo il percorso!")

            if are_we_sure_of_the_results(match_dict_a):

                if how_to_get_there == "by_boat":

                    app.logger.info("andiamo in barca..")
                    min_number_of_rive = 10
                    name_of_rive_as_poi = "vincolo"
                    [start_coord, stop_coord] = lib_search.find_closest_nodes([match_dict_da[0], match_dict_a[0]], G_terra_array)
                    #per tutti gli accessi all'acqua
                    rive_vicine_start, how_many_start = lib_search.find_POI(min_number_of_rive, start_coord, name_of_rive_as_poi)
                    app.logger.info("rive vicine alla partenza: {}".format(how_many_start))

                    rive_start_list = [{"coordinate":(riva.location.longitude, riva.location.latitude)} for riva in rive_vicine_start]
                    rive_start_nodes_list = lib_search.find_closest_nodes(rive_start_list, G_terra_array)
                    # ritorna la strada con properties e la riva scelta!
                    geojson_path_from_land_to_water, riva_start = lib_search.find_path_to_closest_riva(G_terra, start_coord, rive_start_nodes_list)
                    #    rive_vicine_stop=Poi.query.join(poi_types).join(PoiCategoryType).join(PoiCategory).filter_by(name="vincolo").join(Location).filter(and_(db.between(Location.longitude,stop_coord[0]-proximity[0],stop_coord[0]+proximity[0]),db.between(Location.latitude,stop_coord[1]-proximity[1],stop_coord[1]+proximity[1]))).all()
                    rive_vicine_stop, how_many_stop = lib_search.find_POI(min_number_of_rive, stop_coord, name_of_rive_as_poi)
                    app.logger.info("rive vicine all'arrivo: {}".format(how_many_stop))
                    rive_stop_list = [{"coordinate":(riva.location.longitude, riva.location.latitude)} for riva in rive_vicine_stop]
                    rive_stop_nodes_list = lib_search.find_closest_nodes(rive_stop_list, G_terra_array)
                    # ritorna la strada con properties e la riva scelta!
                    geojson_path_from_water_to_land, riva_stop = lib_search.find_path_to_closest_riva(G_terra, stop_coord, rive_stop_nodes_list)
                    #print("riva stop", riva_stop)
                    t2=time.perf_counter()
                    # per i casi in cui abbiamo il civico qui andrà estratta la prima coordinate della shape... Stiamo ritornando la shape in quei casi?!? Servirà a java per disegnare il percorso completo!
                    # lista degli archi
                    list_of_edges_node_with_their_distance = lib_search.find_closest_edge([riva_start, riva_stop], G_acqua)
                    # aggiungere gli archi!
                    list_of_added_edges = lib_graph.dynamically_add_edges(G_acqua, list_of_edges_node_with_their_distance, [riva_start,riva_stop])
                    # trova la strada
                    water_streets_info = lib_graph.give_me_the_street(G_acqua, riva_start, riva_stop, flag_ponti=False, water_flag=True)
                    app.logger.debug("the dictionary with all the info: {}".format(water_streets_info))
                    # togli gli archi
                    lib_graph.dynamically_remove_edges(G_acqua, list_of_added_edges)
                    #print("path, length", strada, length)
                    #trada = add_from_strada_to_porta(strada,match_dict_da[0], match_dict_a[0])
                    app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
                    # 1 significa che stiamo ritornando un percorso da plottare
                    water_streets_info = lib_graph.add_from_strada_to_porta(water_streets_info, match_dict_da[0], match_dict_a[0])
                    # una lista con il dizionario che ha tutte le info sulle strade (una lista perche usiamo un ciclo di la su js)
                    path_list_of_dictionaries = [geojson_path_from_land_to_water, water_streets_info, geojson_path_from_water_to_land]
                    # comprimiamo la lista di dizionari in una lista con un unico dizionario
                    path_list_of_dictionaries = lib_communication.merged_path_list(path_list_of_dictionaries)
                    #path_list_of_dictionaries=[{"strada":strada, "lunghezza":length, "tipo":1},{"strada":start_path, "lunghezza":length, "tipo":0},{"strada":stop_path, "lunghezza":length, "tipo":0}]
                    #final_dict = prepare_our_message_to_javascript(1, da+" "+a,[match_dict_da[0]], path_list_of_dictionaries, [match_dict_a[0]]) # aggiunge da solo "no_path" e "no_end"
                    #print(final_dict)
                    #return render_template(html_file, form=form, results_dictionary=final_dict, feedbacksent=0)

                else: # cerchiamo per terra
                    app.logger.info("andiamo a piedi..")
                    t0=time.perf_counter()
                    # per i casi in cui abbiamo il civico qui andrà estratta la prima coordinate della shape... Stiamo ritornando la shape in quei casi?!? Servirà a java per disegnare il percorso completo!
                    [start_coord, stop_coord] = lib_search.find_closest_nodes([match_dict_da[0], match_dict_a[0]], G_terra_array)
                    app.logger.info('ci ho messo {tot} a trovare il nodo piu vicino'.format(tot=time.perf_counter() - t0))
                    if how_to_get_there == 'less_bridges':
                        f_ponti = True
                        app.logger.info("con meno ponti possibile!")
                    else:
                        f_ponti = False
                    t2=time.perf_counter()
                    streets_info = lib_graph.give_me_the_street(G_terra, start_coord, stop_coord, flag_ponti=f_ponti)
                    app.logger.debug(streets_info)
                    #print("path, length", strada, length)
                    streets_info = lib_graph.add_from_strada_to_porta(streets_info, match_dict_da[0], match_dict_a[0])
                    app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
                    streets_info['tipo']=0
                    # una lista con il dizionario che ha tutte le info sulle strade (una lista perche usiamo un ciclo di la su js)
                    path_list_of_dictionaries=streets_info

                # prepara il messaggio da mandare a javascript
                modus_operandi = 1
                final_dict = prepare_our_message_to_javascript(modus_operandi, da+" "+a,[match_dict_da[0]], path_list_of_dictionaries, [match_dict_a[0]])

            else: # non siamo sicuri di a!
                modus_operandi = 2
                final_dict = prepare_our_message_to_javascript(modus_operandi, a, match_dict_da, dict_of_end_locations_candidates=match_dict_a, start_type='unique', end_type='multiple')

        else: # non siamo sicuro di da!
            modus_operandi = 2
            final_dict = prepare_our_message_to_javascript(modus_operandi, da, match_dict_da, dict_of_end_locations_candidates=match_dict_a, start_type='multiple')


    return final_dict
