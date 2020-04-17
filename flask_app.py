from flask import Flask, render_template, request, send_from_directory
import os
import sys
import logging
import git
logging.basicConfig(filename='example.log',format='[%(asctime)s - %(filename)s:%(lineno)s - %(funcName)20s()] %(message)s',level=logging.DEBUG)
sys.path.append('/home/rafiki/v4w/src')
sys.path.append('/home/rafiki/v4w/libpy')
import pyAny_lib
from library_coords import civico2coord_first_result, civico2coord_find_address


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

@app.route('/update_server',method=['POST'])
def webhook():
    if request.methods == 'POST':
        repo = git.Repo('/home/rafiki')
        origin = repo.remotes.origin
        origin.pull()
        return 'Update PythonAnywhere succesfully', 200
    else:
        return 'Wrong event type', 400

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
