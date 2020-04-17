from flask import Flask, render_template, request, send_from_directory
import os
import sys
import logging
import git
import hmac
import hashlib

logging.basicConfig(filename='example.log',format='[%(asctime)s - %(filename)s:%(lineno)s - %(funcName)20s()] %(message)s',level=logging.DEBUG)
sys.path.append('/home/rafiki/v4w/src')
sys.path.append('/home/rafiki/v4w/libpy')
import pyAny_lib
from library_coords import civico2coord_first_result, civico2coord_find_address

# check webhook github signature
def is_valid_signature(x_hub_signature, data, private_key):
    # x_hub_signature and data are from the webhook payload
    # private key is your webhook secret
    hash_algorithm, github_signature = x_hub_signature.split('=',1)
    algorithm = hashlib.__dict__.get(hash_algorithm)
    encoded_key = bytes(private_key, 'latin_1')
    mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
    return hmac.compare_digest(mac.hexdigest(), github_signature)
w_secret = os.getenv("WEBHOOK_SECRET_KEY")

app = Flask(__name__)
app.config["DEBUG"] = True
logging.info('carico flask')
folder = os.getcwd()
folder_lib = folder + "/v4w/lib/"
folder_db = folder + "/v4w/db/"
path_pickle = folder_db + "grafo_pickle"
#path_civ = folder_db + "lista_civici_csv.txt"
#path_coords = folder_db + "lista_coords.txt"
path_civ = folder_db + "lista_key.txt"
path_coords = folder_db + "lista_coords.txt"
G_un, civici_tpn, coords = pyAny_lib.load_files(pickle_path=path_pickle, civici_tpn_path=path_civ, coords_path=path_coords)
G_list = list(G_un.nodes)
logging.info("Carico i nodi")

@app.route('/update_server',methods=['POST'])
def webhook():
    if request.method != 'POST':
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
        return 'Updated PythonAnywhere server to commit {commit}'.format(commit=commit_hash)

@app.route('/', methods=['GET', 'POST'])
def index():

    return render_template('index.html')

@app.route('/direzione', methods=['GET', 'POST'])
def short_path():

    logging.info('grazie per aver aperto short_path')

    if request.method == 'POST':
        da = request.form['partenza']
        a = request.form['arrivo']
        start_coord, start_name = civico2coord_first_result(G_list, da, civici_tpn, coords)
        stop_coord, stop_name =  civico2coord_first_result(G_list, a, civici_tpn, coords)
        if request.form.get('meno_ponti'):
            f_ponti=True
        else:
            f_ponti=False
        strada, length = pyAny_lib.calculate_path(G_un, start_coord, stop_coord, flag_ponti=f_ponti)
        logging.info(strada)
        return render_template('find_path.html', start_name=start_name, stop_name=stop_name, start_coordx=start_coord[1], start_coordy=start_coord[0], stop_coordx=stop_coord[1], stop_coordy=stop_coord[0],path=strada, tempi=length*12*3.6 )
    else:
        return render_template('find_path.html')

@app.route('/indirizzo', methods=['GET', 'POST'])
def find_address():

    if request.method == 'POST':
        logging.info('grazie per aver mandato il tuo indirizzo in find_address')
        da = request.form['partenza']
        logging.info('DEBUG: indirizzo: {}'.format(da))
        #a = request.form['arrivo']
        start_coord, start_name = civico2coord_find_address(da, civici_tpn, coords)
        #return render_template('index.html', start_name=start_name, stop_name=stop_name, start_coordx=start_coord[1], start_coordy=start_coord[0], stop_coordx=stop_coord[1], stop_coordy=stop_coord[0],path=strada)
        return render_template('map_pa.html', searched_name=da, start_name=start_name, start_coordx=start_coord[1], start_coordy=start_coord[0])
    else:
        logging.info('grazie per aver aperto find_address')
        return render_template('map_pa.html')

@app.route('/degoogling', methods=['GET', 'POST'])
def degoogle_us_please():

    if request.method == 'POST':
        logging.info('grazie per aver mandato il tuo indirizzo in find_address')
        da = request.form['partenza']
        #a = request.form['arrivo']
        start_coord, start_name = civico2coord_find_address(da, civici_tpn, coords)
        #return render_template('index.html', start_name=start_name, stop_name=stop_name, start_coordx=start_coord[1], start_coordy=start_coord[0], stop_coordx=stop_coord[1], stop_coordy=stop_coord[0],path=strada)
        return render_template('degoogling.html', searched_name=da, start_name=start_name, start_coordx=start_coord[1], start_coordy=start_coord[0])
    else:
        logging.info('grazie per aver aperto find_address')
        return render_template('degoogling.html')

@app.route('/download_path', methods=['GET', 'POST'])
def download():
    return send_from_directory(directory=folder+ "/v4w/tmp/", filename="path.gpx")
