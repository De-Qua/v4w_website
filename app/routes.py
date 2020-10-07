from flask import render_template, request, send_from_directory, jsonify, make_response
from app import app, db, t, getCurrentVersion
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
import traceback
from flask import g
import app.global_variables as global_variables
from app import custom_errors
import datetime
from urllib.parse import urlparse
# Useful paths
folder = os.getcwd()
folder_db = os.path.join(folder,"app","static","files")
path_pickle_terra = os.path.join(folder_db,"dequa_ve_terra_v8_dequa_ve_terra_0509_pickle_4326VE")
path_pickle_acqua = os.path.join(folder_db,"dequa_ve_acqua_v7_1609_pickle_4326VE")

# Logging
app.logger.info("loading the graphs..")
# Load graph
#G_un, civici_tpn, coords = lib_graph.load_files(pickle_path=path_pickle_terra, civici_tpn_path=path_civ, coords_path=path_coords)
global_variables.G_terra, global_variables.G_acqua = lib_graph.load_graphs(pickle_terra=path_pickle_terra,pickle_acqua=path_pickle_acqua)

feedback_folder = os.path.join(folder,"feedback")
error_folder = os.path.join(folder,"error")
if not os.path.exists(feedback_folder):
    os.mkdir(feedback_folder)
if not os.path.exists(error_folder):
    os.mkdir(error_folder)

html_file = 'dequa_map.html'
app.logger.setLevel(1)
app.logger.info("ready to go!")

# lista di url da non mappare dopo il merge cambia anche site_map in modo che ne usiamo uno comune
urls_to_not_map = ["/admin", "/user", # no pagine di admin e di utenti
                   "/update", "/initialize", # no ajax
                   ".js", # no service worker o manifest
                   "log", "register", "verify", # no login, logout, registrazione
                   "r2d2", "degoogling", # no feedback e degoogling
                   "robots.txt", # no file per i robot
                   "sitemap"] # no se stesso
dirs_to_not_cache = ["static/files", "static/vids"]

# cos'e il t.include?
@t.include
@app.route('/info', methods=['GET', 'POST'])
def index():
    # add version to the track usage
    g.track_var["version"] = getCurrentVersion()
    # do everything
    app.logger.info('Prova info')
    app.logger.error('Prova error')
    app.logger.debug('Prova debug')
    app.logger.warning('Prova warning')
    app.logger.critical('Prova critical')
    app.logger.log(10,'Prova log debug')
    app.logger.log(20,'Prova log info')
    return render_template('info.html')

# manifest.json serve per la PWA
@t.include
@app.route('/manifest.json', methods=['GET', 'POST'])
def manifest():
    app.logger.info('manifest ')
    return render_template('manifest.json')

# for the javascript file I need to fetch from a different folder
# not templates anymore
from flask import make_response, send_from_directory
@app.route('/serviceWorker.js')
def serviceworker():
    response=make_response(send_from_directory('',filename='serviceWorker.js'))
    #change the content header file
    response.headers['Content-Type'] = 'application/javascript'
    return response

# info sub-pages
@t.include
@app.route('/comesiusa', methods=['GET', 'POST'])
def howto():
    app.logger.info('Come si usa page + 1')
    return render_template('info/comesiusa.html')

@t.include
@app.route('/howitsmade', methods=['GET', 'POST'])
def howitsmade():
    app.logger.info('How its made page + 1')
    return render_template('info/howitsmade.html')

@t.include
@app.route('/idee', methods=['GET', 'POST'])
def idea():
    app.logger.info('idea page + 1')
    return render_template('info/idee.html')

@t.include
@app.route('/chisiamo', methods=['GET', 'POST'])
def aboutus():
    app.logger.info('aboutus page + 1')
    return render_template('info/aboutus.html')

@t.include
@app.route('/partecipare', methods=['GET', 'POST'])
def participation():
    app.logger.info('participation page + 1')
    return render_template('info/partecipare.html')

@t.include
@app.route('/contatti', methods=['GET', 'POST'])
def contact():
    app.logger.info('contact page + 1')
    return render_template('info/contatti.html')

# feedback
@t.include
@app.route('/r2d2', methods=['GET', 'POST'])
def feedback():
    app.logger.info('Pagina di feedback aperta')
    #get list of feedback files
    feedback_dict = interface.get_feedback_from_server()
    return render_template('feedback.html', feedback_dict = feedback_dict)

@t.include
@app.route('/', methods=['GET', 'POST'])
def navigation():
    # add version to the track usage
    g.track_var["version"] = getCurrentVersion()
    # do everything
    form = FeedbackForm()
    try:
        arguments_GET_request = request.args
        params_research = interface.retrieve_parameters_from_GET(arguments_GET_request)

        # usiamo questo per dirgli cosa disegnare!
        # assumiamo nulla per ora
        # geo_type = -2
        # f_ponti = False

        # se e stato inviato il form, scriviamo sul feedback file
        # anche questo da spostare su un metodo

        # form.searched_string.data = params_research['da'] # equivalente al precedente "da"
        t0=time.perf_counter()
        if request.method == 'POST':
            feedbacksent = interface.take_care_of_the_feedback(form, feedback_folder)
            # return render_template(html_file, geo_type=geo_type, start_coordx=-1,
            #     searched_name=da, start_name=start_name,
            #     form=form, feedbacksent=feedbacksent)
            return render_template(html_file, form=form, results_dictionary="None", feedbacksent=feedbacksent)
                # non sono 100% sicuro che form vada ritornato sempre (nel caso precedente era ritornato solo in caso di 0)
                # ma dovrebbe funzionare
        # altrimenti, dobbiamo fare qualocsa
        else:
            dictionary_of_stuff_found = interface.find_what_needs_to_be_found(params_research)
            return render_template(html_file, form=form, results_dictionary=dictionary_of_stuff_found, feedbacksent=0)

    except Exception as e:
        interface.take_care_of_the_error(request, e, error_folder)
        dictionary_of_err = {"error": True,
                            "repr": repr(e),
                            "type": type(e).__name__,
                            "msg": str(e),
                            "traceback": traceback.format_exc()}
        #app.logger.info("error: {}".format(traceback.format_exc()))
        return render_template(html_file, form=form, results_dictionary=dictionary_of_err, feedbacksent=0)

@t.include
@app.route('/update_results', methods=['GET'])
def asynch_navigation():
    # add version to the track usage
    g.track_var["version"] = getCurrentVersion()
    try:
        arguments_GET_request = request.args
        params_research = interface.retrieve_parameters_from_GET(arguments_GET_request)
        dictionary_of_stuff_found = interface.find_what_needs_to_be_found(params_research)
        return jsonify(dictionary_of_stuff_found)
    except Exception as e:
        interface.take_care_of_the_error(request,e,error_folder)
        dictionary_of_err = {"error": True,
                            "repr": repr(e),
                            "type": type(e).__name__,
                            "msg": str(e),
                            "traceback": traceback.format_exc()}
        app.logger.info("error: {}".format(traceback.format_exc()))
        # in case of error, reload the page
        #return render_template(html_file, form=form, results_dictionary=dictionary_of_err, feedbacksent=0)

        return jsonify(dictionary_of_err)

@t.include
@app.route('/offline')
def offline():
    app.logger.info('loading offline page')
    return render_template('offline.html')


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

@app.route("/files_to_cache")
def files_to_cache():
    """
    Route to analyze the website and extract the files that needs to be cached 
    """
    urls_to_cache = list()
    host_components = urlparse(request.host_url)
    host_base = host_components.scheme + "://" + host_components.netloc
    for rule in app.url_map.iter_rules():
        if not(any(url in str(rule) for url in urls_to_not_map)):
            if "GET" in rule.methods and len(rule.arguments) == 0:
                urls_to_cache.append(str(rule))
    static_path = os.path.join(folder,"app","static")
    static_folders = [(dirpath, filenames) for (dirpath, dirnames, filenames) in  os.walk(static_path)]
    for static_folder in static_folders:
        relative_path = os.path.relpath(static_folder[0], os.path.join(folder, "app"))
        print(relative_path)
        for static_file in static_folder[1]:
            if relative_path not in dirs_to_not_cache:
                urls_to_cache.append(os.path.join(relative_path, static_file))
    urls_to_cache.append("static/font-awesome-4.7.0/fonts/fontawesome-webfont.ttf?v=4.7.0")
    urls_to_cache.append("static/font-awesome-4.7.0/fonts/fontawesome-webfont.woff?v=4.7.0")
    urls_to_cache.append("static/font-awesome-4.7.0/fonts/fontawesome-webfont.woff2?v=4.7.0")
    return jsonify(urls_to_cache)

    
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
