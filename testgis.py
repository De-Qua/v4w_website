import requests
import json
import numpy as np
import matplotlib.pyplot as plt
from library_database import progressbar_pip_style
import time
xmin = 1370031.99
ymin = 5688287.51
xmax = 1376401.67
ymax = 5692633.24

x_grid = np.linspace(xmin, xmax, 50)
y_grid = np.linspace(ymin, ymax, 50)
grid_xx, grid_yy = np.meshgrid(x_grid, y_grid)

#plt.scatter(grid_xx, grid_yy)

# GET PER IL buffer
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

# POST
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

lista_layers = [0,1,3,4,5,6]
sito="http://geoportale.comune.venezia.it/Geocortex/Essentials/REST/local-proxy/SMA/13/SMA/MapServer/{}/query"
data={'f': 'json',
    'returnGeometry': 'true',
    'spatialRel': 'esriSpatialRelIntersects',
    'geometry': '',
    'geometryType': 'esriGeometryPolygon',
    'inSR': '102100',
    'outFields': '*',
    'outSR': '4326'}

tutti_i_posti = []
tutti_i_boundary = []
err = []

#for (x,y) in zip(x_grid, y_grid):
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
        boundary = r_GET.json()['geometries'][0]
        tutti_i_boundary.append(boundary)

        data['geometry'] = str(boundary)
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

            if posti_rubati == 1000:
                print("\n\n\n\naaaaaaaaaaaaaaaaaaaaaaa\n\n\n\n")

            tutti_i_posti += r_POST.json()['features']

print("Abbiamo rubato {} posti barca\nCi sono stati {} errori".format(len(tutti_i_posti),len(err)))
jsonpath = "mille_mila_posti_barca.json"
with open(jsonpath, 'w') as json_file:
    json.dump(tutti_i_posti, json_file)
