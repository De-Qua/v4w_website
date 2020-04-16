from flask import Flask, redirect, render_template, request, url_for
import os
import sys
sys.path.append('/home/rafiki/v4w/src')
sys.path.append('/home/rafiki/v4w/libpy')
import pyAny_lib
from library_coords import civico2coord_first_result


app = Flask(__name__)
app.config["DEBUG"] = True

folder = os.getcwd()
folder_lib = folder + "/v4w/lib/"
folder_db = folder + "/v4w/db/"


@app.route('/', methods=['GET', 'POST'])
def index():

    path_shp = folder_db + "pontiDivisi_solo_venezia_l.shp"
    path_civ = folder_db + "lista_civici_csv.txt"
    path_coords = folder_db + "lista_coords.txt"
    G_un, civici_tpn, coords = pyAny_lib.init(shp_path=path_shp, civici_tpn_path=path_civ, coords_path=path_coords)
    G_list = list(G_un.nodes)

    if request.method == 'POST':
        da = request.form['partenza']
        a = request.form['arrivo']
        start = civico2coord_first_result(G_list, da, civici_tpn, coords)
        stop =  civico2coord_first_result(G_list, a, civici_tpn, coords)
        strada, no_ponti, length = pyAny_lib.calculate_path(G_un, start, stop)
        #session['path_result'] = strada
        return render_template('index.html', start=da, stop=a, path=strada)
    else:
        return render_template('index.html')

