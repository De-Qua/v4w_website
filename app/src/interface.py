"""
This class is an interface between routes.py (the main page where the routing happens, where the communication and the redirecting happens)
and the libraries (in libpy), in order to maintain clean the routes page.
"""
import time
import datetime
from app.src.libpy.lib_search import find_closest_nodes, find_closest_edge, find_path_to_closest_riva, find_POI, find_address_in_db, give_me_the_dictionary, are_we_sure_of_the_results
from app.src.libpy.lib_communication import prepare_our_message_to_javascript, parseFeedbackFile
import pdb
from app.src.libpy import lib_graph, lib_communication, lib_search
from app.models import PoiCategoryType, Location, Poi, poi_types, PoiCategory
from app.models import Ideas
from app.models import Feedbacks, Errors
from sqlalchemy import and_
from app import app, db, getCurrentVersion
from app.forms import FeedbackForm
import numpy as np
import os
import json
import pickle
import traceback
import app.global_variables as global_variables
from app import mail

FEEDBACK_FOLDER = 'feedback'

def get_feedback_from_server():
    """
    Check for feedback files in the server, returns their names and their contents, in a dictionary for js.
    """
    feedback_files_names = os.listdir(FEEDBACK_FOLDER)
    feedback_files_names.sort()
    feedback_files_contents = []
    feedback_files_contents_as_dicts = []
    for fb_file in feedback_files_names:
        full_path = os.path.join(FEEDBACK_FOLDER, fb_file)
        with open(full_path, 'r') as content_file:
            cur_fb_content_as_text = content_file.read()
            cur_fb_content_as_dict = parseFeedbackFile(cur_fb_content_as_text)
        feedback_files_contents.append(cur_fb_content_as_text)
        feedback_files_contents_as_dicts.append(cur_fb_content_as_dict)

    feedback_dict = {'fb_names' : feedback_files_names, 'fb_contents' : feedback_files_contents, 'fb_dicts' : feedback_files_contents_as_dicts}
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
    params_dict['walking'] = arguments_GET_request.get('walk', default='off', type=str)
    params_dict['less_bridges'] = arguments_GET_request.get('lazy', default='off', type=str)
    params_dict['by_boat'] = arguments_GET_request.get('boat', default='off', type=str)
    params_dict['with_tide'] = arguments_GET_request.get('tide', default='off', type=str)
    params_dict['by_ambulance'] = arguments_GET_request.get('ambu', default='off', type=str)

    return params_dict

def initialize_votes():
    """
    Check and returns votes for each idea in the database (a dict of dictionaries).
    """
    all_ideas = Ideas.query.all()
    ideas_votes_dict = dict()
    #names_list = []
    for idea in all_ideas:
        cur_idea_votes_dict = {'id':idea.get_id(), 'title':idea.get_title(), 'description':idea.get_description(), 'cur_num':idea.get_num_of_votes()}
        ideas_votes_dict[idea.get_title()] = cur_idea_votes_dict
        #names_list.append(idea.get_title())

    #ideas_votes_dict['names'] = names_list
    return ideas_votes_dict

def update_votes_db(fake_dict):
    """
    Updates the votes of the new ideas we want to implement: the numbers are stored in the database.
    """
    # terribile ma temporaneo - non capisco come evitare questo immutable_multi_dict
    print("Dict: ", fake_dict)
    fake_list = list(fake_dict.keys())
    print("List: ", fake_list)
    text = fake_list[0]

    action, ideas_title, num = text.split("/")
    num_from_js = int(num)

    cur_idea = Ideas.query.filter_by(idea_title=ideas_title).one()
    num_before_vote = cur_idea.get_num_of_votes()
    if num_before_vote != num_from_js:
        print("js and python do not coincide! I trust python and our database")
    if action == 'upvote':
        cur_num = num_before_vote + 1
    elif action == 'downvote':
        cur_num = num_before_vote - 1
    else:
        print("what? ", action)
    cur_idea.set_num_of_votes(cur_num)
    # quando abbiamo finito di settare, committiamo
    db.session.commit()
    print("ideas_name: {}, num: {}".format(ideas_title, cur_num))
    response_dict = {'idea':ideas_title, 'cur_num':cur_num}

    return response_dict

def take_care_of_the_feedback(form, feedback_folder):
    """
    Wrapper that try to validate and write the feedback
    """
    if form.is_submitted():
        if form.validate_on_submit():
            db_feedback = save_feedback_in_db(form, feedback_folder)
            all_good = write_feedback(db_feedback)

            app.logger.info("feedback inviato")
            return 1
        else:
            app.logger.info('errore nel feedback')
            return -1

def save_feedback_in_db(form, feedback_folder):
    """
    Save the feedback in the db.
    """
    fb = Feedbacks()
    fb.version = getCurrentVersion()
    fb.datetime = datetime.datetime.now()
    fb.name = form['name'].data
    fb.email = form['email'].data
    fb.category = dict(form.category.choices).get(form.category.data)
    fb.searched_string = form['searched_string'].data
    fb.searched_start = form['searched_start'].data
    fb.searched_end = form['searched_end'].data
    fb.found_string = form['found_string'].data
    fb.found_start = form['found_start'].data
    fb.found_end = form['found_end'].data
    fb.feedback = form['feedback'].data
    fb.json = form['dictJS'].data
    fb.start_coord = form['start_coord_fb'].data
    fb.end_coord = form['end_coord_fb'].data
    fb.report = os.path.join(feedback_folder,"dequa_fb_"+fb.datetime.strftime("%Y%m%d-%H%M%S.%f")+".md")
    db.session.add(fb)
    db.session.commit()
    return fb

def write_feedback(feedback):
    """
    Just writes the feedback to the given file as markdown.
    """
    curr_time = feedback.datetime
    file_feedback = feedback.report
    mdfile = '<h1>***** DEQUA FEEDBACK ***** </h1>\n'
    mdfile += '<h4>Website version</h4>\n'
    mdfile += feedback.version+'\n'
    mdfile += '<h4>Time</h2>\n'
    mdfile += curr_time.strftime("%Y-%m-%d %H:%M:%S.%f")+"\n"
    category = feedback.category
    mdfile += '<h4>Category</h4>\n'
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
        value = getattr(feedback,data)
        if value:
            mdfile += '<h4>'+title+'</h4>\n'
            mdfile += value+'\n'
    # write json file
    mdfile += '<h4>JSON</h4>\n'
    dictJson = json.loads(feedback.json)
    mdfile += json.dumps(dictJson,indent=2)
    with open(file_feedback,'w+') as f:
        f.write(mdfile)
    # send an email to ourself with the feedback
    # if app.debug:# if not app.debug:
    #     mail.send_email_to_ourself(subject="[FEEDBACK] "+ category,html_body=mdfile)

def take_care_of_the_error(request,err,error_folder):
    """
    Wrapper that save and write the error log
    """
    error_db = save_error_in_db(request, err, error_folder)
    save_error_pickle(error_db, err, request)
    write_error(error_db)
    return

def save_error_in_db(request,err,error_folder):
    """
    Wrapper that save the error in the db
    """
    curr_time = datetime.datetime.now()
    file_error_name = os.path.join(error_folder,"dequa_err_"+curr_time.strftime("%Y%m%d-%H%M%S.%f"))
    er = Errors()
    er.version = getCurrentVersion()
    er.datetime = curr_time
    er.error_type = type(err).__name__
    er.error_message = str(err)
    er.url = request.url
    er.method = request.method
    er.browser = request.user_agent.string
    er.pickle = file_error_name+".err"
    er.report = file_error_name+".md"
    db.session.add(er)
    db.session.commit()
    return er

def save_error_pickle(error,err,request):
    curr_time = error.datetime
    file_error_pickle = error.pickle
    file_error_md = error.report
    request_to_save = {
        'headers': request.headers.to_wsgi_list(),
        'method': request.method,
        'user_agent': request.user_agent,
        'url': request.url,
        'args': request.args,
        'form': request.form,
    }
    error_info = {
        'time': error.datetime,
        'version': error.version,
        'request': request_to_save,
        'error': err,
        'traceback': traceback.format_exc(),
        'markdown': error.report
    }
    # save info in a pickle file
    pickle.dump(error_info, open(error.pickle,"wb"))

def write_error(error):
    mdfile = '<h1>***** DEQUA ERROR ***** </h1>\n'
    mdfile += '<h2>Website version</h2>\n'
    mdfile += error.version+'\n'
    mdfile += '<h2>Time</h2>\n'
    mdfile += error.datetime.strftime("%Y-%m-%d %H:%M:%S.%f")+"\n"
    mdfile += '<h2>Error type</h2>\n'
    mdfile += error.error_type+'\n'
    mdfile += '<h2>Error message</h2>\n'
    mdfile += error.error_message+'\n'
    mdfile += '<h2>URL</h2>\n'
    mdfile += error.url+'\n'
    mdfile += '<h2>Method</h2>\n'
    mdfile += error.method+'\n'
    mdfile += '<h2>Browser</h2>\n'
    mdfile += error.browser+'\n'
    mdfile += '<h2>Pickle file</h2>'
    mdfile += error.pickle+'\n'
    # save info in a md file
    with open(error.report,'w+') as f:
        f.write(mdfile)
    # send an email with the error
    # if app.debug:# if not app.debug:
    #     mail.send_email_to_ourself(subject="[ERROR] "+ str(err),html_body=mdfile)

def ask_yourself(params_research):
    """
    In search for the truth, we try to find out if you are looking for the happiness, an address or a path from A to B.
    """
    if not(params_research['da']) and not(params_research['a']):
        mode = "nothing"
    elif not(params_research['da']) or not(params_research['a']):
        mode = "address"
    elif params_research['by_boat'] == "on":
        mode = "by_boat"
    else:
        mode = "path"
    return mode

def set_choice_mode(da, a):
    """
    set which query needs a choice
    """
    start_type = "unique"
    end_type = "unique"
    if not da:
        start_type = "multiple"
        app.logger.debug("non siamo sicuri di da")
    if not a:
        end_type = "multiple"
        app.logger.debug("non siamo sicuri di a")
    return start_type, end_type

def only_by_boat_or_also_by_walk(match_dicts_list, params_research):

    return None, None


def find_what_needs_to_be_found(params_research):
    """
    Take care of the whole research (many cases) calling smaller methods.
    """
    what_am_I_really_searching_for = ask_yourself(params_research)
    da = params_research['da']
    a = params_research['a']
    start_coord = params_research['start_coord']
    end_coord = params_research['end_coord']

    if not(da) and a:
        da = a
        a = ""
        start_coord = end_coord
        end_coord = ""

    if what_am_I_really_searching_for == "nothing":
        return "None"

    elif what_am_I_really_searching_for == "address":
        app.logger.debug('ricerca singolo indirizzo: {}'.format(da) )
        t0 = time.perf_counter()
        match_dict = lib_search.give_me_the_dictionary(da, start_coord)
        if are_we_sure_of_the_results(match_dict):
            # per ora usiamo solo la coordinata (nel caso di un poligono ritorno il centroide) e il nome, ma poi cambieremo
            app.logger.info('ci ho messo {tot} a calcolare la posizione di un indirizzo'.format(tot=time.perf_counter() - t0))
            modus_operandi = 0
            final_dict = prepare_our_message_to_javascript(modus_operandi, [da, a], match_dict, params_research) # aggiunge da solo "no_path" e "no_end"
            app.logger.debug("risposta per indirizzo singolo: {}".format(final_dict))
        else:
            modus_operandi = 2
            final_dict = prepare_our_message_to_javascript(modus_operandi, [da, a], match_dict, params_research, start_type='multiple')

    else: # we are in path mode
        t0=time.perf_counter()
        match_dict_da = lib_search.give_me_the_dictionary(da, start_coord)
        match_dict_a = lib_search.give_me_the_dictionary(a, end_coord)
        app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))

        da_is_sure = are_we_sure_of_the_results(match_dict_da)
        a_is_sure = are_we_sure_of_the_results(match_dict_a)
        if not da_is_sure or not a_is_sure:
            modus_operandi = 2
            start_type, end_type = set_choice_mode(da_is_sure, a_is_sure)
            final_dict = prepare_our_message_to_javascript(modus_operandi, [da, a], match_dict_da, params_research, dict_of_end_locations_candidates=match_dict_a, start_type=start_type, end_type=end_type)

        else:
            app.logger.info("Andiamo a botta sicura! Abbiamo trovato quello che cercavamo e calcoliamo il percorso!")
            app.logger.info("ricerca percorso da {} a {}..".format(da, a))
            if what_am_I_really_searching_for=='by_boat':
                start_from_water, end_to_water = only_by_boat_or_also_by_walk([match_dict_da[0], match_dict_a[0]], params_research)
                start_from_water = params_research["da"]=="La Mia Posizione"
                end_to_water = params_research["a"]=="La Mia Posizione"
                path_list_of_dictionaries = by_boat_path_calculator([match_dict_da[0], match_dict_a[0]], start_from_water, end_to_water, params_research["less_bridges"]=="on")

            else: # cerchiamo per terra

                path_list_of_dictionaries = by_foot_path_calculator([match_dict_da[0], match_dict_a[0]], params_research["less_bridges"]=="on")
            # prepara il messaggio da mandare a javascript
            modus_operandi = 1
            final_dict = prepare_our_message_to_javascript(modus_operandi, [da, a],[match_dict_da[0]], params_research, path_list_of_dictionaries, [match_dict_a[0]])

    return final_dict

def by_boat_path_calculator(match_dicts_list, start_from_water, end_to_water, f_ponti):

    G_terra_array = np.asarray(list(global_variables.G_terra.nodes))
    G_acqua_array = np.asarray(list(global_variables.G_acqua.nodes))

    app.logger.info("andiamo in barca..")
    min_number_of_rive = 10
    name_of_rive_as_poi = "vincolo"

    # questo blocco non distingue tra partenza e arrivo, potrebbe anche andare bene,
    # aggiungendo un flag che blocchi la ricerca successiva della riva vicina e setti come riva_start e riva_stop il nodo acqueo piu vicino.
    # Altrimenti bisogna creare un sistema che capisca quale delle due è troppo distante da un nodo terrestre,
    # attivi 2 flag diversi e nei due casi imposti il nodo acqueo più vicino.
    try:
        [start_coord] = lib_search.find_closest_nodes([match_dicts_list[0]], G_terra_array, global_variables.min_dist_to_go_by_boat)
        start_from_water = False or start_from_water
    except:
        app.logger.info('start_coord is far from land nodes')
        start_coord = match_dicts_list[0]['coordinate']
        start_from_water = True
    try:
        [stop_coord] = lib_search.find_closest_nodes([match_dicts_list[1]], G_terra_array, global_variables.min_dist_to_go_by_boat)
        end_to_water = False or end_to_water
    except:
        app.logger.info('stop_coord is far from land nodes')
        stop_coord = match_dicts_list[1]['coordinate']
        end_to_water = True
        #per tutti gli accessi all'acqua
    if not start_from_water:
        # classico vecchio - strada fino alla riva, poi strada in barca
        rive_vicine_start, how_many_start = lib_search.find_POI(min_number_of_rive, start_coord, name_of_rive_as_poi)
        app.logger.info("rive vicine alla partenza: {}".format(how_many_start))
        rive_start_list = [{"coordinate":(riva.location.longitude, riva.location.latitude)} for riva in rive_vicine_start]

        rive_start_nodes_list = lib_search.find_closest_nodes(rive_start_list, G_terra_array)
        geojson_path_from_land_to_water, riva_start = lib_search.find_path_to_closest_riva(global_variables.G_terra, start_coord, rive_start_nodes_list,f_ponti)
    if start_from_water or riva_start==-1:
        # usiamo le coordinate come riva di Partenza
        # che poi viene collegato all'arco piu vicino nel grafo acqueo
        riva_start = tuple(start_coord)
        geojson_path_from_land_to_water = None
        #    rive_vicine_stop=Poi.query.join(poi_types).join(PoiCategoryType).join(PoiCategory).filter_by(name="vincolo").join(Location).filter(and_(db.between(Location.longitude,stop_coord[0]-proximity[0],stop_coord[0]+proximity[0]),db.between(Location.latitude,stop_coord[1]-proximity[1],stop_coord[1]+proximity[1]))).all()
    if not end_to_water:
        rive_vicine_stop, how_many_stop = lib_search.find_POI(min_number_of_rive, stop_coord, name_of_rive_as_poi)
        app.logger.info("rive vicine all'arrivo: {}".format(how_many_stop))
        rive_stop_list = [{"coordinate":(riva.location.longitude, riva.location.latitude)} for riva in rive_vicine_stop]

        rive_stop_nodes_list = lib_search.find_closest_nodes(rive_stop_list, G_terra_array)
        # ritorna la strada con properties e la riva scelta!
        geojson_path_from_water_to_land, riva_stop = lib_search.find_path_to_closest_riva(global_variables.G_terra, stop_coord, rive_stop_nodes_list,f_ponti)
    if end_to_water or riva_stop==-1:
        riva_stop = tuple(stop_coord)
        geojson_path_from_water_to_land = None
    #print("riva stop", riva_stop)
    t2=time.perf_counter()
    # lista degli archi
    list_of_edges_node_with_their_distance = lib_search.find_closest_edge([riva_start, riva_stop], global_variables.G_acqua)
    # aggiungere gli archi!
    list_of_added_edges = lib_graph.dynamically_add_edges(global_variables.G_acqua, list_of_edges_node_with_their_distance, [riva_start,riva_stop])
    # trova la strada
    water_streets_info = lib_graph.give_me_the_street(global_variables.G_acqua, riva_start, riva_stop, flag_ponti=False, water_flag=True, speed=global_variables.boat_speed)
    # app.logger.debug("the dictionary with all the info: {}".format(water_streets_info))
    # togli gli archi
    lib_graph.dynamically_remove_edges(global_variables.G_acqua, list_of_added_edges)
    app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
    water_streets_info = lib_graph.add_from_strada_to_porta(water_streets_info, match_dicts_list[0], match_dicts_list[0])
    # una lista con il dizionario che ha tutte le info sulle strade (una lista perche usiamo un ciclo di la su js)
    path_list_of_dictionaries = [geojson_path_from_land_to_water, water_streets_info, geojson_path_from_water_to_land]
    # comprimiamo la lista di dizionari in una lista con un unico dizionario
    return lib_communication.merged_path_list(path_list_of_dictionaries)

def by_foot_path_calculator(match_dicts_list, f_ponti):
    app.logger.info("andiamo a piedi..")
    G_terra_array = np.asarray(list(global_variables.G_terra.nodes))
    t0=time.perf_counter()
    [start_coord, stop_coord] = lib_search.find_closest_nodes(match_dicts_list, G_terra_array, global_variables.min_dist_to_suggest_boat)
    app.logger.info('ci ho messo {tot} a trovare il nodo piu vicino'.format(tot=time.perf_counter() - t0))
    t2=time.perf_counter()
    streets_info = lib_graph.give_me_the_street(global_variables.G_terra, start_coord, stop_coord, flag_ponti=f_ponti, speed=global_variables.walk_speed)
    streets_info = lib_graph.add_from_strada_to_porta(streets_info, match_dicts_list[0], match_dicts_list[1])
    app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
    streets_info['tipo']=0

    return streets_info
