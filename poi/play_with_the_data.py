import poi.library_overpass as lib_over
%load_ext autoreload
%autoreload 2

bbox_venezia = [45.36, 12.32, 45.47, 12.41]
osm_id_venezia = 44741
# doppie virgolette servono!
filters = ["'alt_name'"]
#filters = ["'operator'='ACTV'"]
what_we_get = lib_over.download_data(osm_id_venezia, filters, what='nodes')

lib_over.draw_the_data(what_we_get, 'our search drawn on a map')
lib_over.save_data_as(what_we_get, 'poi/poi_search.json')

# riceviamo una lista di dict!
data_as_list = lib_over.remove_headers_and_tolist(what_we_get)

# per esempio, il primo e il caffe rosso (sempre lui!)
primo_nodo = data_as_list[0]
print("il primo nodo e ",primo_nodo)
print("con coppie (chiavi, valori)", primo_nodo.items())
"ciao".split(";")
# il nostro poi ha:
# category|osm_id|lat|lon|name|amenity|shop|wheelchair|cuisine|toilets|toilets:wheelchair|tourism|alt_name|building|opening_hours|wikipedia|atm|outdoor_seeting|diet|diet:vegetarian|phone|denomination|transport|health|sport|accommo

# quindi potremmo fare
# doppie virgolette servono!
amenity_filters = ["'amenity'"]
amenity_pois = lib_over.download_data(bbox_venezia, amenity_filters, what='nodes')
amenity_pois_as_list = lib_over.remove_headers_and_tolist(amenity_pois)

shop_filters = ["'shop'"]
shop_pois = lib_over.download_data(bbox_venezia, shop_filters, what='nodes')
shop_pois_as_list = lib_over.remove_headers_and_tolist(shop_pois)

name_filters = ["'name'"]
name_pois = lib_over.download_data(bbox_venezia, name_filters, what='nodes')
name_pois_as_list = lib_over.remove_headers_and_tolist(name_pois)

sport_filters = ["'sport'"]
sport_pois = lib_over.download_data(bbox_venezia, sport_filters, what='nodes')
sport_pois_as_list = lib_over.remove_headers_and_tolist(sport_pois)

# e poi qua uniamo i file, usando l'id!
# se due poi hanno lo stesso id, scartiamo
import time
time1 = time.time()
all_pois = []
ids_already_there = [looped_poi['id'] for looped_poi in all_pois]
poi_lists = [amenity_pois_as_list, shop_pois_as_list, name_pois_as_list, sport_pois_as_list]
poi_list_names = [amenity_filters, shop_filters, name_filters, sport_filters]
for j in range(len(poi_lists)):
    poi_list = poi_lists[j]
    poi_list_name = poi_list_names[j]
    added = 0
    for add_poi in poi_list:
        #print(type(add_poi))
        if add_poi['id'] not in ids_already_there:
            ids_already_there.append(add_poi['id'])
            all_pois.append(add_poi)
            added += 1
    print("aggiunti {} su {} poi dalla lista {}".format(added, len(poi_list), poi_list_name))
time2 = time.time()
print("abbiamo {} in totale. ci abbiamo messo {} a unirli".format(len(all_pois), time2-time1))
