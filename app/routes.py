from flask import render_template, request, send_from_directory
from app import app
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
from app.src.libpy.utils import find_closest_nodes, add_from_strada_to_porta, find_closest_edge
from app.src.libpy.library_communication import prepare_our_message_to_javascript

# Useful paths
folder = os.getcwd()
folder_db = os.path.join(folder,"app","static","files")
path_pickle_terra = os.path.join(folder_db,"grafo_pickle_last")
path_pickle_acqua = os.path.join(folder_db,"grafo_acqueo_pickle_1106")
#path_civ = folder_db + "lista_civici_csv.txt"
#path_coords = folder_db + "lista_coords.txt"
path_civ = os.path.join(folder_db,"lista_key.txt")
path_coords = os.path.join(folder_db,"lista_coords.txt")

# Load graph
#G_un, civici_tpn, coords = pyAny_lib.load_files(pickle_path=path_pickle_terra, civici_tpn_path=path_civ, coords_path=path_coords)
G_terra, G_acqua = pyAny_lib.load_graphs(pickle_terra=path_pickle_terra,pickle_acqua=path_pickle_acqua)
G_terra_array = np.asarray(list(G_terra.nodes))
G_acqua_array = np.asarray(list(G_acqua.nodes))

file_feedback = os.path.join(folder,"file_feedback.txt")

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

@app.route('/direzione', methods=['GET', 'POST'])
def short_path():

    app.logger.info('grazie per aver aperto short_path')
    t1=time.perf_counter()
    if request.method == 'POST':
        da = request.form['partenza']
        a = request.form['arrivo']
        t0=time.perf_counter()
        start_coord, start_name = civico2coord_find_address(da, civici_tpn, coords, G_list)
        stop_coord, stop_name =  civico2coord_find_address(a, civici_tpn, coords, G_list)
        #logging.info('ci ho messo {t11} e {t12} per trovare la stringa'.format(t11=timing[0], t12=timing1[0]))
        #logging.info('ci ho messo {t21} e {t22} per trovare il nodo'.format(t21=timing[1], t22=timing1[1]))
        #logging.info('ci ho messo {t31} e {t32} per trovare l\'indice'.format(t31=timing[2], t32=timing1[2]))
        app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))
        if request.form.get('meno_ponti'):
            f_ponti=True
        else:
            f_ponti=False

        t2=time.perf_counter()
        strada, length = pyAny_lib.calculate_path(G_un, start_coord, stop_coord, flag_ponti=f_ponti)
        app.logger.info('ci ho messo {tot} a processare la richiesta'.format(tot=time.perf_counter() - t1))
        app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
        return render_template('find_path.html', start_name=start_name, stop_name=stop_name, start_coordx=start_coord[1], start_coordy=start_coord[0], stop_coordx=stop_coord[1], stop_coordy=stop_coord[0],path=strada, tempi=length*12*3.6 )
    else:
        app.logger.info('ci ho messo {tot} a processare la richiesta senza ricerca di indirizzo'.format(tot=time.perf_counter() - t1))
        return render_template('find_path.html')

@app.route('/indirizzo', methods=['GET', 'POST'])
def find_address():
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
                return render_template('map_pa.html', geo_type=geo_type, start_coordx=-1, searched_name=da, start_name=start_name, feedbacksent=1)
            else:
                app.logger.info('errore nel feedback')
                return render_template('map_pa.html', geo_type=geo_type, start_coordx=-1, searched_name=da, start_name=start_name, form=form, feedbacksent=0)
    else:
        app.logger.info('grazie per aver mandato il tuo indirizzo in find_address')
        if da == '':
            print('primo caricamento')
            app.logger.info('grazie per aver aperto find_address')
            temp= render_template('map_pa.html',results_dictionary="None", form=form, feedbacksent=0)
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
            return render_template('map_pa.html', form=form, results_dictionary=final_dict, feedbacksent=0)
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
            final_dict = prepare_our_message_to_javascript(1, da+" "+a,[match_dict_da[0]], [strada,length], [match_dict_a[0]]) # aggiunge da solo "no_path" e "no_end"
            print(final_dict)
            return render_template('map_pa.html', form=form, results_dictionary=final_dict, feedbacksent=0)

@app.route('/acqueo', methods=['GET', 'POST'])
def find_water_path():
    html_water_file = 'map_acqua.html'
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
            app.logger.info('ci ho messo {tot} a calcolare la posizione degli indirizzi'.format(tot=time.perf_counter() - t0))
            if request.form.get('meno_ponti'):
                f_ponti=True
            else:
                f_ponti=False
            t2=time.perf_counter()
            # per i casi in cui abbiamo il civico qui andrà estratta la prima coordinate della shape... Stiamo ritornando la shape in quei casi?!? Servirà a java per disegnare il percorso completo!
            #[start_coord, stop_coord] # old version
            [start_coord, stop_coord] = find_closest_nodes([match_dict_da[0], match_dict_a[0]], G_acqua_array)
            list_coord_rive = [start_coord, stop_coord]
            # lista degli archi
            list_of_edges_node_with_their_distance = find_closest_edge(list_coord_rive, G_acqua)
            # aggiungere gli archi!
            list_of_added_edges = pyAny_lib.dynamically_add_edges(G_acqua, list_of_edges_node_with_their_distance, list_coord_rive)
            # trova la strada
            strada, length = pyAny_lib.calculate_path_wkt(G_acqua, start_coord, stop_coord, flag_ponti=f_ponti)
            # togli gli archi
            pyAny_lib.dynamically_remove_edges(G_acqua, list_of_added_edges)
            #print("path, length", strada, length)
            strada = add_from_strada_to_porta(strada,match_dict_da[0], match_dict_a[0])
            app.logger.info('ci ho messo {tot} a calcolare la strada'.format(tot=time.perf_counter() - t2))
            # 1 significa che stiamo ritornando un percorso da plottare
            final_dict = prepare_our_message_to_javascript(1, da+" "+a,[match_dict_da[0]], [strada,length], [match_dict_a[0]]) # aggiunge da solo "no_path" e "no_end"
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
