from app import app, db, user_datastore, security, admin
from app.models import Location,Street,Neighborhood,Poi
from flask_admin import helpers as admin_helpers
from flask import url_for
from flask_security import utils

@app.shell_context_processor
def make_shell_context():
    return {"db": db,
    "Location": Location,
    "Street": Street,
    "Neighborhood": Neighborhood,
    "Poi": Poi}

# Create the tables for the users and roles and add a user to the user table
# This decorator registers a function to be run before the first request to the app
#  i.e. calling localhost:5000 from the browser
@app.before_first_request
def before_first_request():
    if app.debug:
        # Create any database tables that don't exist yet.
        db.create_all(bind='users')

        # Create the Roles "admin" and "end-user" -- unless they already exist
        user_datastore.find_or_create_role(name='admin', description='Administrator')
        user_datastore.find_or_create_role(name='end-user', description='End user')

        # Create two Users for testing purposes -- unless they already exists.
        # In each case, use Flask-Security utility function to encrypt the password.
        someone_password = 'someone'
        admin_password = 'admin'
        if not user_datastore.get_user('someone'):
            user_datastore.create_user(email='someone', password=utils.encrypt_password(someone_password))
        if not user_datastore.get_user('admin'):
            user_datastore.create_user(email='admin', password=utils.encrypt_password(admin_password))

        # Commit any database changes; the User and Roles must exist before we can add a Role to the User
        db.session.commit()

        # Give one User has the "end-user" role, while the other has the "admin" role. (This will have no effect if the
        # Users already have these Roles.) Again, commit any database changes.
        user_datastore.add_role_to_user('someone', 'end-user')
        user_datastore.add_role_to_user('admin', 'admin')
        db.session.commit()

# Include security variable to admin views
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template = admin.base_template,
        admin_view = admin.index_view,
        h = admin_helpers,
        get_url = url_for
    )
# from flask import Flask, render_template, request, send_from_directory
# import os
# import sys
# import logging
# import git
# import hmac
# import hashlib

# logging.basicConfig(filename='example.log',format='[%(asctime)s - %(filename)s:%(lineno)s - %(funcName)20s()] %(message)s',level=logging.DEBUG)
# sys.path.append(os.path.join(os.getcwd(), "v4w", "src"))
# sys.path.append(os.path.join(os.getcwd(), "v4w", "libpy"))
# import pyAny_lib
# from library_coords import civico2coord_first_result, civico2coord_find_address

# # check webhook github signature
# def is_valid_signature(x_hub_signature, data, private_key):
#     # x_hub_signature and data are from the webhook payload
#     # private key is your webhook secret
#     hash_algorithm, github_signature = x_hub_signature.split('=',1)
#     algorithm = hashlib.__dict__.get(hash_algorithm)
#     encoded_key = bytes(private_key, 'latin_1')
#     mac = hmac.new(encoded_key, msg=data, digestmod=algorithm)
#     return hmac.compare_digest(mac.hexdigest(), github_signature)
# w_secret = os.getenv("WEBHOOK_SECRET_KEY")

# app = Flask(__name__,
#     template_folder=sys.path.append(os.path.join(os.getcwd(),'templates')))
# app.config["DEBUG"] = True
# logging.info('carico flask')
# folder = os.getcwd()
# folder_lib = folder + "/v4w/lib/"
# folder_db = folder + "/v4w/db/"
# path_pickle = folder_db + "grafo_pickle"
# #path_civ = folder_db + "lista_civici_csv.txt"
# #path_coords = folder_db + "lista_coords.txt"
# path_civ = folder_db + "lista_key.txt"
# path_coords = folder_db + "lista_coords.txt"
# G_un, civici_tpn, coords = pyAny_lib.load_files(pickle_path=path_pickle, civici_tpn_path=path_civ, coords_path=path_coords)
# G_list = list(G_un.nodes)
# logging.info("Carico i nodi")

# @app.route('/update_server',methods=['POST'])
# def webhook():
#     if request.method != 'POST':
#         return 'OK'
#     else:
#         abort_code = 418
#         # Do initial validations on required headers
#         if 'X-Github-Event' not in request.headers:
#             abort(abort_code)
#         if 'X-Github-Delivery' not in request.headers:
#             abort(abort_code)
#         if 'X-Hub-Signature' not in request.headers:
#             abort(abort_code)
#         if not request.is_json:
#             abort(abort_code)
#         if 'User-Agent' not in request.headers:
#             abort(abort_code)
#         ua = request.headers.get('User-Agent')
#         if not ua.startswith('GitHub-Hookshot/'):
#             abort(abort_code)

#         event = request.headers.get('X-GitHub-Event')
#         if event == "ping":
#             return json.dumps({'msg': 'Hi!'})
#         if event != "push":
#             return json.dumps({'msg': "Wrong event type"})

#         x_hub_signature = request.headers.get('X-Hub-Signature')
#         # webhook content type should be application/json for request.data to have the payload
#         # request.data is empty in case of x-www-form-urlencoded
#         if not is_valid_signature(x_hub_signature, request.data, w_secret):
#             print('Deploy signature failed: {sig}'.format(sig=x_hub_signature))
#             abort(abort_code)

#         payload = request.get_json()
#         if payload is None:
#             print('Deploy payload is empty: {payload}'.format(
#                 payload=payload))
#             abort(abort_code)

#         if payload['ref'] != 'refs/heads/master':
#             return json.dumps({'msg': 'Not master; ignoring'})

#         repo = git.Repo('/home/rafiki')
#         origin = repo.remotes.origin

#         pull_info = origin.pull()

#         if len(pull_info) == 0:
#             return json.dumps({'msg': "Didn't pull any information from remote!"})
#         if pull_info[0].flags > 128:
#             return json.dumps({'msg': "Didn't pull any information from remote!"})

#         commit_hash = pull_info[0].commit.hexsha
#         build_commit = f'build_commit = "{commit_hash}"'
#         print(f'{build_commit}')
#         return 'Updated PythonAnywhere server to commit {commit}'.format(commit=commit_hash)

# @app.route('/', methods=['GET', 'POST'])
# def index():

#     return render_template('index.html')

# @app.route('/direzione', methods=['GET', 'POST'])
# def short_path():

#     logging.info('grazie per aver aperto short_path')

#     if request.method == 'POST':
#         da = request.form['partenza']
#         a = request.form['arrivo']
#         start_coord, start_name = civico2coord_first_result(G_list, da, civici_tpn, coords)
#         stop_coord, stop_name =  civico2coord_first_result(G_list, a, civici_tpn, coords)
#         if request.form.get('meno_ponti'):
#             f_ponti=True
#         else:
#             f_ponti=False
#         strada, length = pyAny_lib.calculate_path(G_un, start_coord, stop_coord, flag_ponti=f_ponti)
#         logging.info(strada)
#         return render_template('find_path.html', start_name=start_name, stop_name=stop_name, start_coordx=start_coord[1], start_coordy=start_coord[0], stop_coordx=stop_coord[1], stop_coordy=stop_coord[0],path=strada, tempi=length*12*3.6 )
#     else:
#         return render_template('find_path.html')

# @app.route('/indirizzo', methods=['GET', 'POST'])
# def find_address():

#     if request.method == 'POST':
#         logging.info('grazie per aver mandato il tuo indirizzo in find_address')
#         da = request.form['partenza']
#         #a = request.form['arrivo']
#         start_coord, start_name = civico2coord_find_address(da, civici_tpn, coords)
#         #return render_template('index.html', start_name=start_name, stop_name=stop_name, start_coordx=start_coord[1], start_coordy=start_coord[0], stop_coordx=stop_coord[1], stop_coordy=stop_coord[0],path=strada)
#         return render_template('map_pa.html', searched_name=da, start_name=start_name, start_coordx=start_coord[1], start_coordy=start_coord[0])
#     else:
#         logging.info('grazie per aver aperto find_address')
#         return render_template('map_pa.html')

# @app.route('/degoogling', methods=['GET', 'POST'])
# def degoogle_us_please():

#     if request.method == 'POST':
#         logging.info('grazie per aver mandato il tuo indirizzo in find_address')
#         da = request.form['partenza']
#         #a = request.form['arrivo']
#         start_coord, start_name = civico2coord_find_address(da, civici_tpn, coords)
#         #return render_template('index.html', start_name=start_name, stop_name=stop_name, start_coordx=start_coord[1], start_coordy=start_coord[0], stop_coordx=stop_coord[1], stop_coordy=stop_coord[0],path=strada)
#         return render_template('degoogling.html', searched_name=da, start_name=start_name, start_coordx=start_coord[1], start_coordy=start_coord[0])
#     else:
#         logging.info('grazie per aver aperto find_address')
#         return render_template('degoogling.html')

# @app.route('/download_path', methods=['GET', 'POST'])
# def download():
#     return send_from_directory(directory=folder+ "/v4w/tmp/", filename="path.gpx")
