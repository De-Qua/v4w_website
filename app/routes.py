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
import pdb
import app.src.interface as interface
from app.src.libpy import lib_graph

# Useful paths
folder = os.getcwd()
folder_db = os.path.join(folder,"app","static","files")
path_pickle_terra = os.path.join(folder_db,"grafo_pickle_4326VE")
path_pickle_acqua = os.path.join(folder_db,"grafo_acqueo_pickle_4326VE")

# Logging
app.logger.info("loading the graphs..")
# Load graph
#G_un, civici_tpn, coords = lib_graph.load_files(pickle_path=path_pickle_terra, civici_tpn_path=path_civ, coords_path=path_coords)
G_terra, G_acqua = lib_graph.load_graphs(pickle_terra=path_pickle_terra,pickle_acqua=path_pickle_acqua)
G_objects = {'land_graph':G_terra, 'water_graph':G_acqua}

file_feedback = os.path.join(folder,"file_feedback.txt")

html_file = 'dequa_map.html'
app.logger.setLevel(1)
app.logger.info("ready to go!")


@app.route('/info', methods=['GET', 'POST'])
def index():
    app.logger.info('Prova info')
    app.logger.error('Prova error')
    app.logger.debug('Prova debug')
    app.logger.warning('Prova warning')
    app.logger.critical('Prova critical')
    app.logger.log(10,'Prova log debug')
    app.logger.log(20,'Prova log info')
    return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
def navigation():

    arguments_GET_request = request.args
    params_research = interface.retrieve_parameters_from_GET(arguments_GET_request)

    # usiamo questo per dirgli cosa disegnare!
    # assumiamo nulla per ora
    geo_type = -2
    f_ponti = False

    # se e stato inviato il form, scriviamo sul feedback file
    # anche questo da spostare su un metodo
    form = FeedbackForm()
    form.searched_string.data = params_research[0] # equivalente al precedente "da"
    t0=time.perf_counter()
    if request.method == 'POST':
        feedbacksent = interface.take_care_of_the_feedback(form, file_feedback)
        return render_template(html_file, geo_type=geo_type, start_coordx=-1,
            searched_name=da, start_name=start_name,
            form=form, feedbacksent=feedbacksent)
            # non sono 100% sicuro che form vada ritornato sempre (nel caso precedente era ritornato solo in caso di 0)
            # ma dovrebbe funzionare
    # altrimenti, dobbiamo fare qualocsa
    else:
        dictionary_of_stuff_found = interface.find_what_needs_to_be_found(params_research, G_objects)
        return render_template(html_file, form=form, results_dictionary=dictionary_of_stuff_found, feedbacksent=0)



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
