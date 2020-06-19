from flask import render_template, request, send_from_directory
from app import app, db
from app.forms import FeedbackForm
import os
import git
import hmac
import hashlib
import time
from flask import json
import numpy as np
from app.src.libpy import pyAny_lib
from app.src.libpy.library_coords import civico2coord_find_address, find_address_in_db
from app.src.libpy.utils import find_closest_nodes, add_from_strada_to_porta, find_closest_edge, find_path_to_closest_riva
from app.src.libpy.library_communication import prepare_our_message_to_javascript
from app.models import PoiCategoryType, Location, Poi, poi_types, PoiCategory
from sqlalchemy import and_

# Useful paths
folder = os.getcwd()
folder_db = os.path.join(folder,"app","static","files")
path_pickle_terra = os.path.join(folder_db,"grafo_pickle_last")
path_pickle_acqua = os.path.join(folder_db,"grafo_acqueo_pickle_1106")

# Load graph
#G_un, civici_tpn, coords = pyAny_lib.load_files(pickle_path=path_pickle_terra, civici_tpn_path=path_civ, coords_path=path_coords)
G_terra, G_acqua = pyAny_lib.load_graphs(pickle_terra=path_pickle_terra,pickle_acqua=path_pickle_acqua)
G_terra_array = np.asarray(list(G_terra.nodes))
G_acqua_array = np.asarray(list(G_acqua.nodes))

file_feedback = os.path.join(folder,"file_feedback.txt")

html_file = 'map_acqua.html'
# Logging
app.logger.info("Carico i nodi")

@app.route('/', methods=['GET', 'POST'])
def index():
    app.logger.info('Prova info')
    app.logger.error('Prova error')
    app.logger.debug('Prova debug')
    app.logger.warning('Prova warning')
    app.logger.critical('Prova critical')
    app.logger.log(10,'Prova log debug')
    app.logger.log(20,'Prova log info')
    return render_template('index.html')

@app.route('/indirizzo', methods=['GET', 'POST'])
def find_address():
    html_land_file = html_file
    # usiamo questo per dirgli cosa disegnare!
    geo_type = -2
    da = request.args.get('partenza', default='', type=str)
    a = request.args.get('arrivo', default='', type=str)
    form = FeedbackForm()
    form.searched_string.data = da
    t0=time.perf_counter()
    if request.method == 'POST':
        if form.is_submitted():
            if form.validate_on_submit():
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
                app.logger.info("feedback inviato")
                return render_template(html_land_file, geo_type=geo_type, start_coordx=-1, searched_name=da, start_name=start_name, feedbacksent=1)
            else:
                app.logger.info('errore nel feedback')
                return render_template(html_land_file, geo_type=geo_type, start_coordx=-1, searched_name=da, start_name=start_name, form=form, feedbacksent=0)
    else:
        app.logger.info('grazie per aver mandato il tuo indirizzo in find_address')
        if da == '':
            print('primo caricamento')
            app.logger.info('grazie per aver aperto find_address')
            temp= render_template(html_land_file,results_dictionary="None", form=form, feedbacksent=0)
            app.logger.info('ci ho messo {tot} a caricare la prima volta'.format(tot=time.perf_counter() - t0))
            return temp
        elif a== '':
            app.logger.debug('indirizzo: {}'.format(da))
            match_dict = find_address_in_db(da)
            # per ora usiamo solo la coordinata (nel caso di un poligono ritorno il centroide) e il nome, ma poi cambieremo
            app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))
            # 0 significa che stiamo ritornando un indirizzo singolo
            final_dict = prepare_our_message_to_javascript(0, da, match_dict) # aggiunge da solo "no_path" e "no_end"
            print(final_dict)
            #dict_test = {"test":"ma va", "geotype":"0"}
            return render_template(html_land_file, form=form, results_dictionary=final_dict, feedbacksent=0)
        else:
            t0=time.perf_counter()
            match_dict_da = find_address_in_db(da)
            match_dict_a = find_address_in_db(a)
            # per i casi in cui abbiamo il civico qui andrà estratta la prima coordinate della shape... Stiamo ritornando la shape in quei casi?!? Servirà a java per disegnare il percorso completo!
            [start_coord, stop_coord] = find_closest_nodes([match_dict_da[0], match_dict_a[0]], G_terra_array)
            app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))
            if request.form.get('meno_ponti'):
                f_ponti=True
            else:
                f_ponti=False
            t2=time.perf_counter()
            strada, length = pyAny_lib.calculate_path(G_terra, start_coord, stop_coord, flag_ponti=f_ponti)
            #print("path, length", strada, length)
            strada = add_from_strada_to_porta(strada,match_dict_da[0], match_dict_a[0])
            app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
            # 1 significa che stiamo ritornando un percorso da plottare
            final_dict = prepare_our_message_to_javascript(1, da+" "+a,[match_dict_da[0]], [{"strada":strada,"lunghezza":length,"tipo":0}], [match_dict_a[0]]) # aggiunge da solo "no_path" e "no_end"
            print(final_dict)
            return render_template(html_land_file, form=form, results_dictionary=final_dict, feedbacksent=0)

@app.route('/acqueo', methods=['GET', 'POST'])
def find_water_path():
    proximity = [0.001,0.001]
    html_water_file = html_file
    # usiamo questo per dirgli cosa disegnare!
    geo_type = -2
    da = request.args.get('partenza', default='', type=str)
    a = request.args.get('arrivo', default='', type=str)
    form = FeedbackForm()
    form.searched_string.data = da
    t0=time.perf_counter()
    if request.method == 'POST':
        if form.is_submitted():
            if form.validate_on_submit():
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
                app.logger.info("feedback inviato")
                return render_template(html_water_file, geo_type=geo_type, start_coordx=-1, searched_name=da, start_name=start_name, feedbacksent=1)
            else:
                app.logger.info('errore nel feedback')
                return render_template(html_water_file, geo_type=geo_type, start_coordx=-1, searched_name=da, start_name=start_name, form=form, feedbacksent=0)
    else:
        app.logger.info('grazie per aver mandato il tuo indirizzo in find_address')
        if da == '':
            print('primo caricamento')
            app.logger.info('grazie per aver aperto find_address')
            temp= render_template(html_water_file,results_dictionary="None", form=form, feedbacksent=0)
            app.logger.info('ci ho messo {tot} a caricare la prima volta'.format(tot=time.perf_counter() - t0))
            return temp
        elif a== '':
            app.logger.debug('indirizzo: {}'.format(da))
            match_dict = find_address_in_db(da)
            # per ora usiamo solo la coordinata (nel caso di un poligono ritorno il centroide) e il nome, ma poi cambieremo
            app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))
            # 0 significa che stiamo ritornando un indirizzo singolo
            final_dict = prepare_our_message_to_javascript(0, da, match_dict) # aggiunge da solo "no_path" e "no_end"
            print(final_dict)
            #dict_test = {"test":"ma va", "geotype":"0"}
            return render_template(html_water_file, form=form, results_dictionary=final_dict, feedbacksent=0)
        else:
            t0=time.perf_counter()
            match_dict_da = find_address_in_db(da)
            match_dict_a = find_address_in_db(a)
            [start_coord, stop_coord] = find_closest_nodes([match_dict_da[0], match_dict_a[0]], G_terra_array)

            #rive_vicine=PoiCategoryType.query.filter_by(name="Riva").one().pois.join(Location).filter(and_(db.between(Location.longitude,start_coord[0]-0.0003,start_coord[0]+0.0003),db.between(Location.latitude,start_coord[1]-0.003,start_coord[1]+0.003))).all()
            #per tutti gli accessi all'acqua
            rive_vicine=Poi.query.join(poi_types).join(PoiCategoryType).join(PoiCategory).filter_by(name="vincolo").join(Location).filter(and_(db.between(Location.longitude,start_coord[0]-proximity[0],start_coord[0]+proximity[0]),db.between(Location.latitude,start_coord[1]-proximity[1],start_coord[1]+proximity[1]))).all()
            print("rive vicine alla partenza", len(rive_vicine))
            rive_start_list = [{"coordinate":(riva.location.longitude, riva.location.latitude)} for riva in rive_vicine]
            rive_start_nodes_list = find_closest_nodes(rive_start_list, G_terra_array)
            start_path=find_path_to_closest_riva(G_terra, start_coord, rive_start_nodes_list)
            #print("start path", start_path)
            riva_start = start_path[-1]
            #print("riva start", riva_start)
            # per le rive vere e prorie
#            PoiCategoryType.query.filter_by(name="Riva").one().pois.join(Location).filter(and_(db.between(Location.longitude,stop_coord[0]-0.003,stop_coord[0]+0.003),db.between(Location.latitude,stop_coord[1]-0.03,stop_coord[1]+0.03))).all()
            rive_vicine_stop=Poi.query.join(poi_types).join(PoiCategoryType).join(PoiCategory).filter_by(name="vincolo").join(Location).filter(and_(db.between(Location.longitude,stop_coord[0]-proximity[0],stop_coord[0]+proximity[0]),db.between(Location.latitude,stop_coord[1]-proximity[1],stop_coord[1]+proximity[1]))).all()
            print("rive vicine all'arrivo",len(rive_vicine_stop))
            rive_stop_list = [{"coordinate":(riva.location.longitude, riva.location.latitude)} for riva in rive_vicine_stop]
            rive_stop_nodes_list = find_closest_nodes(rive_stop_list, G_terra_array)
            stop_path=find_path_to_closest_riva(G_terra, stop_coord, rive_stop_nodes_list)
            riva_stop = stop_path[-1]
            #print("riva stop", riva_stop)
            app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))
            if request.form.get('meno_ponti'):
                f_ponti=True
            else:
                f_ponti=False
            t2=time.perf_counter()
            # per i casi in cui abbiamo il civico qui andrà estratta la prima coordinate della shape... Stiamo ritornando la shape in quei casi?!? Servirà a java per disegnare il percorso completo!
            # lista degli archi
            list_of_edges_node_with_their_distance = find_closest_edge([riva_start, riva_stop], G_acqua)
            # aggiungere gli archi!
            list_of_added_edges = pyAny_lib.dynamically_add_edges(G_acqua, list_of_edges_node_with_their_distance, [riva_start,riva_stop])
            print(list_of_added_edges)
            # trova la strada
            strada, length = pyAny_lib.calculate_path_wkt(G_acqua, riva_start, riva_stop, flag_ponti=f_ponti)
            # togli gli archi
            pyAny_lib.dynamically_remove_edges(G_acqua, list_of_added_edges)
            #print("path, length", strada, length)
            #trada = add_from_strada_to_porta(strada,match_dict_da[0], match_dict_a[0])
            app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
            # 1 significa che stiamo ritornando un percorso da plottare
            #strada_totale = add_from_strada_to_porta(strada_totale,match_dict_da[0], match_dict_a[0])
            path_list_of_dictionaries=[{"strada":strada, "lunghezza":length, "tipo":1},{"strada":start_path, "lunghezza":length, "tipo":0},{"strada":stop_path, "lunghezza":length, "tipo":0}]
            final_dict = prepare_our_message_to_javascript(1, da+" "+a,[match_dict_da[0]], path_list_of_dictionaries, [match_dict_a[0]]) # aggiunge da solo "no_path" e "no_end"
            print(final_dict)
            return render_template(html_water_file, form=form, results_dictionary=final_dict, feedbacksent=0)


@app.route('/degoogling', methods=['GET', 'POST'])
def degoogle_us_please():

    if request.method == 'POST':
        app.logger.info('grazie per aver mandato il tuo indirizzo in find_address')
        da = request.form['partenza']
        #a = request.form['arrivo']
        start_coord, start_name = civico2coord_find_address(da, civici_tpn, coords)
        #return render_template('index.html', start_name=start_name, stop_name=stop_name, start_coordx=start_coord[1], start_coordy=start_coord[0], stop_coordx=stop_coord[1], stop_coordy=stop_coord[0],path=strada)
        return render_template('degoogling.html', searched_name=da, start_name=start_name, start_coordx=start_coord[1], start_coordy=start_coord[0])
    else:
        app.logger.info('grazie per aver aperto find_address')
        return render_template('degoogling.html')

# check webhook github signature
def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=',1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin_1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)

# Webhook secret key
w_secret = os.getenv("WEBHOOK_SECRET_KEY")

# webhook to sync with github
@app.route('/update_server',methods=['POST'])
def webhook():
    app.logger.info("Webhook request")
    if request.method != 'POST':
        app.logger.info("Webhook is not POST")
        return 'OK'
    else:
        abort_code = 418
        # Do initial validations on required headers
        if 'X-Github-Event' not in request.headers:
            abort(abort_code)
        if 'X-Github-Delivery' not in request.headers:
            abort(abort_code)
        if 'X-Hub-Signature' not in request.headers:
            abort(abort_code)
        if not request.is_json:
            abort(abort_code)
        if 'User-Agent' not in request.headers:
            abort(abort_code)
        ua = request.headers.get('User-Agent')
        if not ua.startswith('GitHub-Hookshot/'):
            abort(abort_code)

        event = request.headers.get('X-GitHub-Event')
        if event == "ping":
            return json.dumps({'msg': 'Hi!'})
        if event != "push":
            return json.dumps({'msg': "Wrong event type"})

        x_hub_signature = request.headers.get('X-Hub-Signature')
        # webhook content type should be application/json for request.data to have the payload
        # request.data is empty in case of x-www-form-urlencoded
        if not is_valid_signature(x_hub_signature, request.data, w_secret):
            print('Deploy signature failed: {sig}'.format(sig=x_hub_signature))
            abort(abort_code)

        payload = request.get_json()
        if payload is None:
            print('Deploy payload is empty: {payload}'.format(
                payload=payload))
            abort(abort_code)

        if payload['ref'] != 'refs/heads/master':
            return json.dumps({'msg': 'Not master; ignoring'})

        repo = git.Repo('/home/rafiki')
        origin = repo.remotes.origin

        pull_info = origin.pull()

        if len(pull_info) == 0:
            return json.dumps({'msg': "Didn't pull any information from remote!"})
        if pull_info[0].flags > 128:
            return json.dumps({'msg': "Didn't pull any information from remote!"})

        commit_hash = pull_info[0].commit.hexsha
        build_commit = f'build_commit = "{commit_hash}"'
        print(f'{build_commit}')
        app.logger.info('Updated PythonAnywhere server to commit {commit}'.format(commit=commit_hash))
        return 'Updated PythonAnywhere server to commit {commit}'.format(commit=commit_hash)
