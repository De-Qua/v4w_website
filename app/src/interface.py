"""
This class is an interface between routes.py (the main page where the routing happens, where the communication and the redirecting happens)
and the libraries (in libpy), in order to maintain clean the routes page.
"""
import time
import datetime
from app.src.libpy.lib_search import find_closest_nodes, find_closest_edge, find_path_to_closest_riva, find_POI, find_address_in_db, give_me_the_dictionary, are_we_sure_of_the_results
from app.src.libpy.lib_communication import prepare_our_message_to_javascript
import pdb
from app.src.libpy import lib_graph, lib_communication, lib_search
from app.models import PoiCategoryType, Location, Poi, poi_types, PoiCategory
from sqlalchemy import and_
from app import app, db, getCurrentVersion
from app.forms import FeedbackForm
import numpy as np
import os
import json
import pickle
import traceback
from app import mail

FEEDBACK_FOLDER = 'feedback'

def get_feedback_from_server():
    """
    Check for feedback files in the server, returns their names and their contents, in a dictionary for js.
    """
    feedback_files_names = os.listdir(FEEDBACK_FOLDER)
    feedback_files_content = []
    for fb_file in feedback_files_names:
        with open(os.path.join(FEEDBACK_FOLDER, fb_file), 'r') as content_file:
            cur_fb_content = content_file.read()
        feedback_files_content.append(cur_fb_content)

    feedback_dict = {'fb_names' : feedback_files_names, 'fb_contents' : feedback_files_content}
    return feedback_dict

def retrieve_parameters_from_GET(arguments_GET_request):
    """
    Returns the parameters sent from the map page through the get method during a research.
    """
    params_dict = {}
    # this could go in a method retrieve_parameters_from_GET
    params_dict['da'] = arguments_GET_request.get('partenza', default='', type=str)
    params_dict['start_coord'] = arguments_GET_request.get('start_coord', default='', type=str)
    params_dict['a'] = arguments_GET_request.get('arrivo', default='', type=str)
    params_dict['end_coord'] = arguments_GET_request.get('end_coord', default='', type=str)
    # new code! i bottoni sono 'off' o 'on'
    params_dict['less_bridges'] = arguments_GET_request.get('lazy', default='off', type=str)
    params_dict['by_boat'] = arguments_GET_request.get('boat', default='off', type=str)
    params_dict['with_tide'] = arguments_GET_request.get('tide', default='off', type=str)
    params_dict['by_ambulance'] = arguments_GET_request.get('ambu', default='off', type=str)

    return params_dict

def take_care_of_the_feedback(form, feedback_folder):
    """
    Wrapper that try to validate and write the feedback
    """
    if form.is_submitted():
        if form.validate_on_submit():
            all_good = write_feedback(form, feedback_folder)
            app.logger.info("feedback inviato")
            return 1
        else:
            app.logger.info('errore nel feedback')
            return -1


def write_feedback(form, feedback_folder):
    """
    Just writes the feedback to the given file as markdown.
    """
    curr_time = datetime.datetime.now()
    file_feedback = os.path.join(feedback_folder,"dequa_fb_"+curr_time.strftime("%Y%m%d-%H%M%S.%f")+".md")
    mdfile = '<h1>***** DEQUA FEEDBACK ***** </h1>\n'
    mdfile += '<h2>Website version</h2>\n'
    mdfile += getCurrentVersion()+'\n'
    mdfile += '<h2>Time</h2>\n'
    mdfile += curr_time.strftime("%Y-%m-%d %H:%M:%S.%f")+"\n"
    category = dict(form.category.choices).get(form.category.data)
    mdfile += '<h2>Category</h2>\n'
    mdfile += category+'\n'
    dict_data_title = {
        'name': 'Name',
        'email': 'Email',
        'searched_string': 'Searched string',
        'searched_start': 'Searched start',
        'searched_end': 'Searched end',
        'found_string': 'Result string',
        'found_start': 'Result start',
        'found_end': 'Result end',
        'feedback': 'Comments',
    }
    for (data,title) in dict_data_title.items():
        value = form[data].data
        if value:
            mdfile += '<h2>'+title+'</h2>\n'
            mdfile += value+'\n'
    # write json file
    mdfile += '<h2>JSON</h2>\n'
    dictJson = json.loads(form['dictJS'].data)
    mdfile += json.dumps(dictJson,indent=2)
    with open(file_feedback,'w+') as f:
        f.write(mdfile)
    # send an email to ourself with the feedback
    # if app.debug:# if not app.debug:
    #     mail.send_email_to_ourself(subject="[FEEDBACK] "+ category,html_body=mdfile)

def take_care_of_the_error(request,err,error_folder):
    """
    Wrapper that write the error log
    """
    curr_time = datetime.datetime.now()
    file_error_name = os.path.join(error_folder,"dequa_err_"+curr_time.strftime("%Y%m%d-%H%M%S.%f"))
    file_error_pickle = file_error_name+".err"
    file_error_md = file_error_name+".md"
    request_to_save = {
        'headers': request.headers.to_wsgi_list(),
        'method': request.method,
        'user_agent': request.user_agent,
        'url': request.url,
        'args': request.args,
        'form': request.form,
    }
    error_info = {
        'time': curr_time,
        'version': getCurrentVersion(),
        'request': request_to_save,
        'error': err,
        'traceback': traceback.format_exc(),
        'markdown': file_error_md
    }
    # save info in a pickle file
    pickle.dump(error_info, open(file_error_pickle,"wb"))
    mdfile = '<h1>***** DEQUA ERROR ***** </h1>\n'
    mdfile += '<h2>Website version</h2>\n'
    mdfile += getCurrentVersion()+'\n'
    mdfile += '<h2>Time</h2>\n'
    mdfile += curr_time.strftime("%Y-%m-%d %H:%M:%S.%f")+"\n"
    mdfile += '<h2>Error type</h2>\n'
    mdfile += type(err).__name__+'\n'
    mdfile += '<h2>Error message</h2>\n'
    mdfile += str(err)+'\n'
    mdfile += '<h2>URL</h2>\n'
    mdfile += request.url+'\n'
    mdfile += '<h2>Method</h2>\n'
    mdfile += request.method+'\n'
    mdfile += '<h2>Browser</h2>\n'
    mdfile += request.user_agent.string+'\n'
    mdfile += '<h2>Pickle file</h2>'
    mdfile += file_error_pickle+'\n'
    # save info in a md file
    with open(file_error_md,'w+') as f:
        f.write(mdfile)

    # send an email with the error
    # if app.debug:# if not app.debug:
    #     mail.send_email_to_ourself(subject="[ERROR] "+ str(err),html_body=mdfile)


def ask_yourself(params_research):
    """
    In search for the truth, we try to find out if you are looking for the happiness, an address or a path from A to B.
    """
    if params_research['da'] == "":
        mode="nothing"
    elif params_research['a'] == "":
        mode="address"
    elif params_research['by_boat'] == "on":
        mode="by_boat"
    elif params_research['less_bridges'] == "on":
        mode="less_bridges"
    else:
        mode="path"

    return mode


def find_what_needs_to_be_found(params_research, G_objects):
    """
    Take care of the whole research (many cases) calling smaller methods.
    """

    what_am_I_really_searching_for = ask_yourself(params_research)

    if params_research['start_coord']:
        da = params_research['start_coord']
    else:
        da=params_research['da']
    if params_research['end_coord']:
        a = params_research['end_coord']
    else:
        a=params_research['a']

    G_terra = G_objects['land_graph']
    G_acqua = G_objects['water_graph']
    G_terra_array = np.asarray(list(G_terra.nodes))
    G_acqua_array = np.asarray(list(G_acqua.nodes))

    boat_speed=5/3.6
    walk_speed=5/3.6

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
            final_dict = prepare_our_message_to_javascript(modus_operandi, [da, a], match_dict, params_research) # aggiunge da solo "no_path" e "no_end"
            app.logger.debug("risposta per indirizzo singolo: {}".format(final_dict))
        else:
            modus_operandi = 2
            final_dict = prepare_our_message_to_javascript(modus_operandi, [da, a], match_dict, params_research, start_type='multiple')

    else:

        t0=time.perf_counter()
        match_dict_da = lib_search.give_me_the_dictionary(da)
        match_dict_a = lib_search.give_me_the_dictionary(a)

        #match_dict_a = dict() #lib_search.give_me_the_dictionary(a)
        app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))

        if not are_we_sure_of_the_results(match_dict_da) or not are_we_sure_of_the_results(match_dict_a):
            start_type = "unique"
            end_type = "unique"
            modus_operandi = 2
            if not are_we_sure_of_the_results(match_dict_da):
                start_type = "multiple"
                app.logger.debug("non siamo sicuri di da")
            if not are_we_sure_of_the_results(match_dict_a):
                end_type = "multiple"
                app.logger.debug("non siamo sicuri di a")

            final_dict = prepare_our_message_to_javascript(modus_operandi, [da, a], match_dict_da, params_research, dict_of_end_locations_candidates=match_dict_a, start_type=start_type, end_type=end_type)

        else:

            app.logger.info("Andiamo a botta sicura! Abbiamo trovato quello che cercavamo e calcoliamo il percorso!")
            app.logger.info("ricerca percorso da {} a {}..".format(da, a))

            if params_research["by_boat"]=='on':

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
                geojson_path_from_land_to_water, riva_start = lib_search.find_path_to_closest_riva(G_terra, start_coord, rive_start_nodes_list,flag_ponti=params_research["less_bridges"]=="on")
                if riva_start==-1:
                    riva_start=start_coord
                #    rive_vicine_stop=Poi.query.join(poi_types).join(PoiCategoryType).join(PoiCategory).filter_by(name="vincolo").join(Location).filter(and_(db.between(Location.longitude,stop_coord[0]-proximity[0],stop_coord[0]+proximity[0]),db.between(Location.latitude,stop_coord[1]-proximity[1],stop_coord[1]+proximity[1]))).all()
                rive_vicine_stop, how_many_stop = lib_search.find_POI(min_number_of_rive, stop_coord, name_of_rive_as_poi)
                app.logger.info("rive vicine all'arrivo: {}".format(how_many_stop))
                rive_stop_list = [{"coordinate":(riva.location.longitude, riva.location.latitude)} for riva in rive_vicine_stop]
                rive_stop_nodes_list = lib_search.find_closest_nodes(rive_stop_list, G_terra_array)
                # ritorna la strada con properties e la riva scelta!
                geojson_path_from_water_to_land, riva_stop = lib_search.find_path_to_closest_riva(G_terra, stop_coord, rive_stop_nodes_list,flag_ponti=params_research["less_bridges"]=="on")
                if riva_stop==-1:
                    riva_stop=stop_coord

                #print("riva stop", riva_stop)
                t2=time.perf_counter()
                # per i casi in cui abbiamo il civico qui andrà estratta la prima coordinate della shape... Stiamo ritornando la shape in quei casi?!? Servirà a java per disegnare il percorso completo!
                # lista degli archi
                list_of_edges_node_with_their_distance = lib_search.find_closest_edge([riva_start, riva_stop], G_acqua)
                # aggiungere gli archi!
                list_of_added_edges = lib_graph.dynamically_add_edges(G_acqua, list_of_edges_node_with_their_distance, [riva_start,riva_stop])
                # trova la strada
                water_streets_info = lib_graph.give_me_the_street(G_acqua, riva_start, riva_stop, flag_ponti=False, water_flag=True, speed=boat_speed)
                # app.logger.debug("the dictionary with all the info: {}".format(water_streets_info))
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
                if params_research['less_bridges'] == 'on':
                    f_ponti = True
                    app.logger.info("con meno ponti possibile!")
                else:
                    f_ponti = False
                t2=time.perf_counter()
                streets_info = lib_graph.give_me_the_street(G_terra, start_coord, stop_coord, flag_ponti=f_ponti, speed=walk_speed)
                #app.logger.debug(streets_info)
                #print("path, length", strada, length)
                streets_info = lib_graph.add_from_strada_to_porta(streets_info, match_dict_da[0], match_dict_a[0])
                app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
                streets_info['tipo']=0
                # una lista con il dizionario che ha tutte le info sulle strade (una lista perche usiamo un ciclo di la su js)
                path_list_of_dictionaries=streets_info

            # prepara il messaggio da mandare a javascript
            modus_operandi = 1
            final_dict = prepare_our_message_to_javascript(modus_operandi, [da, a],[match_dict_da[0]], params_research, path_list_of_dictionaries, [match_dict_a[0]])

    return final_dict
