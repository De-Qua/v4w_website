#%% Import vari
import requests
import json
import numpy as np
import matplotlib
%matplotlib inline
import matplotlib.pyplot as plt
from library_database import progressbar_pip_style
import time
from shapely.geometry import Polygon
#%% Crea griglia di punti

# coordinate dei layer del comune
xmin = 1370031.99
ymin = 5688287.51
xmax = 1376401.67
ymax = 5692633.24

x_grid = np.linspace(xmin, xmax, 50)
y_grid = np.linspace(ymin, ymax, 50)
grid_xx, grid_yy = np.meshgrid(x_grid, y_grid)

plt.scatter(grid_xx, grid_yy)

#%%
# GET per il buffer
sito_b = "https://sampleserver6.arcgisonline.com/arcgis/rest/services/Utilities/Geometry/GeometryServer/buffer"
params_b = {'f': 'json',
 'unit': '9001',
 'unionResults': 'true',
 'geodesic': 'true',
 'geometries': '',
 'inSR': '102100',
 'distances': '250',
 'outSR': '102100',
 'bufferSR': '102100'}

# POST per i dati
# Layers:
#
#     FERMATE_TAXI (0)
#     TRAGHETTI_PARADA (1)
#     CONCESSIONI (2)
#     VINCOLI (3)
#     SPAZI A TEMPO (4)
#     IKW_SMA.SPAZI_A_TEMPO_PUNTI (5)
#     IKW_SMA.RIVE_GEO_ORD2014_3004 (6)
#     CONCESSIONI DISPONIBILI (7)

lista_layers = [0,1,3,4,6]
sito="http://geoportale.comune.venezia.it/Geocortex/Essentials/REST/local-proxy/SMA/13/SMA/MapServer/{}/query"
data={'f': 'json',
    'returnGeometry': 'true',
    'spatialRel': 'esriSpatialRelIntersects',
    'geometry': '',
    'geometryType': 'esriGeometryPolygon',
    'inSR': '102100',
    'outFields': '*',
    'outSR': '4326'}

#%%
tutti_i_posti = []
tutti_i_buffer = []
err = []

# Variabile, se true scarica anche i dati, se false scarica solo i buffer
download_data = True

#loop per scaricare i dati
i=0
for x in x_grid:
    for y in y_grid:
        i+=1
        progressbar_pip_style(i,len(x_grid)*len(y_grid))

        #print("Richiesta ring con centro {}, {}".format(x,y))

        params_b['geometries'] = '{"geometryType":"esriGeometryPoint","geometries":[{"x":' + str(x) + ',"y":' + str(y) + ',"spatialReference":{"wkid":102100}}]}',
        # Per evitare casini di connessione che salta
        get_response = False
        while not get_response:
            try:
                r_GET = requests.get(sito_b,params=params_b)
                get_response = True
            except:
                time.sleep(3)

        #print("Furto posti barca nel ring..")
        buffer = r_GET.json()['geometries'][0]
        tutti_i_buffer.append(buffer)

        if download_data:
            data['geometry'] = str(buffer)
            for layer in lista_layers:
                post_response = False
                # per evitare casini con connessione che salta
                while not post_response:
                    try:
                        r_POST = requests.post(sito.format(layer),data=data)
                        post_response = True
                    except:
                        time.sleep(3)
                # per evitare che la risposta sia vuota
                if not r_POST.content:
                    err.append(r_POST)
                    continue
                posti_rubati = len(r_POST.json()['features'])
                #print("rubati {} posti barca!".format())
                # per segnalare che abbiamo più di 1000 elementi nel buffer (limite imposto dal comune)
                if posti_rubati == 1000:
                    print("\n\n\n\naaaaaaaaaaaaaaaaaaaaaaa\n\n\n\n")

                tutti_i_posti += r_POST.json()['features']

print("Abbiamo rubato {} posti barca\nCi sono stati {} errori".format(len(tutti_i_posti),len(err)))
#%% Salva i dati scaricati in file json
json_posti = "mille_mila_posti_barca.json"
if len(tutti_i_posti)>0:
    with open(json_posti, 'w') as json_file:
        json.dump(tutti_i_posti, json_file)

json_buffer = "mille_mila_buffer.json"
with open(json_buffer,"w") as json_file:
    json.dump(tutti_i_buffer,json_file)

#%% Plot dei buffer
# se la variabile con i buffer non esiste la carico dal file
if 'tutti_i_buffer' not in locals():
    json_buffer = "mille_mila_buffer.json"
    with open(json_buffer,'r') as json_file:
        tutti_i_buffer = json.load(json_file)
polygons = [Polygon(b['rings'][0]) for b in tutti_i_buffer]
for polygon in polygons:
    plt.plot(*polygon.exterior.xy)

#%% Cerco posti doppi
if 'tutti_i_posti' not in locals():
    json_posti = "mille_mila_posti_barca.json"
    with open(json_posti, 'r') as json_file:
        tutti_i_posti = json.load(json_file)

posti_unici = dict(taxi=[],traghetti=[],rive_consentite=[],spazi_tempo=[],vincoli=[],altro=[])
id_posti_unici = dict(taxi=[],traghetti=[],rive_consentite=[],spazi_tempo=[],vincoli=[],altro=[])
skipped = dict(taxi=0,traghetti=0,rive_consentite=0,spazi_tempo=0,vincoli=0,altro=0)
i=0
for posto in tutti_i_posti:
    i+=1
    progressbar_pip_style(i,len(tutti_i_posti))
    # controllo di che tipo fa parte
    keys = posto['attributes'].keys()
    if 'PK_ID' in keys:
        if "ID_SPAZIO" in keys:
            tipo = "spazi_tempo"
        else:
            tipo = "vincoli"
        id = "PK_ID"
    elif 'OBJECTID_1' in keys:
        if posto['attributes']["DOC_TARIFFE"] == "tariffe_traghetti.pdf":
            tipo = "traghetti"
        else:
            tipo = "taxi"
        id = "OBJECTID"
    elif "COD_RIVA" in keys:
        tipo = "rive_consentite"
        id = "COD_RIVA"
    else:
        tipo = "altro"

    # Se è già nella lista skippo
    if posto in posti_unici[tipo]:
        skipped[tipo] += 1
        continue

    # altrimenti aggiungo alla lista
    posti_unici[tipo].append(posto)

    # if tipo != "altro":
    #     # se è già nella lista passo al prossimo
    #     if posto['attributes'][id] in id_posti_unici[tipo]:
    #         skipped[tipo] += 1
    #         continue
    #     # altrimenti:
    #     #1. aggiungo l'id alla lista
    #     id_posti_unici[tipo].append(posto['attributes'][id])
    # #2. aggiungo il posto alla lista
    # posti_unici[tipo].append(posto)

for key in posti_unici.keys():
    print('{key} - Unici: {un}, Doppioni {do}'.format(key=str(key),un=len(posti_unici[key]),do=skipped[key]))
#%%
