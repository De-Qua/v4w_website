"""
Module to check the state of our database
"""
#%% Imports
import os,sys
# IMPORT FOR THE DATABASE - db is the database object
from app import app, db
from app.models import Neighborhood, Street, Location, Area, Poi

if __name__ == "__main__":

    testPassed = True
    print("checking db: ", db)
    #%%
    # CHECK DELLE SHAPES
    #%%
    # CHECK SESTIERI
    print("CHECK SESTIERI")
    print("..generale:")
    hoods = Neighborhood.query.all()
    full_hoods = [hood for hood in hoods if hood.name and hood.shape and hood.zipcode]
    print("{} sestieri:\n{} con tutti i parametri\n{} con parametri mancanti".format(len(hoods), len(full_hoods), len(hoods)-len(full_hoods)))

    print("..nomi:")
    name_hoods = [hood for hood in hoods if hood.name]
    print("{} sestieri:\n{} con nome\n{} senza nome".format(len(hoods), len(name_hoods), len(hoods)-len(name_hoods)))

    print("..shapes:")
    hoods_with_empty_shapes = [hood for hood in hoods if not hood.shape]
    hoods_with_shapes = [hood for hood in hoods if hood.shape]
    hoods_with_polygon = [hood for hood in hoods_with_shapes if hood.shape.geom_type == "Polygon"]
    if len(sys.argv) > 1 and sys.argv[1] == "v":
        print("{} sestieri vuoti: \n{}".format(len(hoods_with_empty_shapes), hoods_with_empty_shapes))
        print("{} sestieri con poligoni: \n{}".format(len(hoods_with_polygon), hoods_with_polygon))
    else:
        print("{} sestieri:\n{} con poligoni\n{} vuoti".format(len(hoods), len(hoods_with_polygon), len(hoods_with_empty_shapes)))
    if len(full_hoods) == len(hoods) and len(hoods_with_empty_shapes) == 0:
        print("TEST - SESTIERI - SUPERATO")
        passedPart1 = True
    else:
        print("TEST - SESTIERI - FALLITO")
        passedPart1 = False
    testPassed = testPassed and passedPart1
    print("-------------")
    #%%
    # CHECK STRADE
    print("STRADE")
    print("..generale:")
    streets_list = Street.query.all()
    full_streets = [street for street in streets_list if street.name and street.shape]
    print("{} strade:\n{} con tutti i parametri\n{} con parametri mancanti".format(len(streets_list), len(full_streets), len(streets_list)-len(full_streets)))

    print("..nomi:")
    name_streets = [street for street in streets_list if street.name]
    print("{} strade:\n{} con il nome\n{} senza nome".format(len(streets_list), len(name_streets), len(streets_list)-len(name_streets)))

    print("..nomi alternativi (opzionale):")
    name_streets = [street for street in streets_list if street.name_alt]
    print("{} strade:\n{} con nome alternativo\n{} senza nome alternativo".format(len(streets_list), len(name_streets), len(streets_list)-len(name_streets)))

    print("..shapes:")
    streets_with_empty_shapes = [street for street in streets_list if not street.shape]
    streets_with_shapes = [street for street in streets_list if street.shape]
    streets_with_polygon = [street for street in streets_with_shapes if street.shape.geom_type == "Polygon"]
    other_streets = [street for street in streets_with_shapes if street.shape and not street.shape.geom_type == "Polygon"]
    if len(sys.argv) > 1 and sys.argv[1] == "v":
        print("{} strade vuote su {}: \n{}".format(len(streets_with_empty_shapes), len(streets_list), streets_with_empty_shapes))
        print("{} strade con poligoni su {}: \n{}".format(len(streets_with_polygon), len(streets_list), streets_with_polygon))
        print("{} strade con altre cose su {}: \n{}".format(len(other_streets), len(streets_list), other_streets))
        print("{}".format([street.shape.geom_type for street in other_streets]))
    else:
        print("{} strade:\n{} con poligoni,\n{} con altre cose (multipoligoni),\n{} vuote".format(len(streets_list), len(streets_with_polygon), len(other_streets), len(streets_with_empty_shapes)))
    if len(streets_list) == len(full_streets) and  len(hoods_with_empty_shapes) == 0:
        print("TEST - STRADE - SUPERATO")
        passedPart2 = True
    else:
        print("TEST - STRADE - FALLITO")
        passedPart2 = False
    testPassed = testPassed and passedPart2
    print("-------------")

    #%%
    # CHECK POI
    print("POI")
    print("..generale:")
    poi_list = Poi.query.all()
    full_pois = [pdi for pdi in poi_list if pdi.location_id]
    print("{} strade:\n{} con la location\n{} senza location".format(len(poi_list), len(full_pois), len(poi_list)-len(full_pois)))

    print("..nomi:")
    name_pois = [pdi for pdi in poi_list if pdi.name]
    print("{} strade:\n{} con il nome\n{} senza nome".format(len(poi_list), len(name_pois), len(poi_list)-len(name_pois)))

    if len(poi_list) == len(full_pois):
        print("TEST - POI - SUPERATO")
        passedPart3 = True
    else:
        print("TEST - POI - FALLITO")
        passedPart3 = False
    testPassed = testPassed and passedPart3
    print("-------------")
    #pois_with_empty_shapes = [cur_poi for cur_poi in poi_list if not cur_poi.shape]
    #pois_with_shapes = [cur_poi for cur_poi in poi_list if cur_poi.shape]
    #pois_with_polygon = [cur_poi for cur_poi in pois_with_shapes if cur_poi.shape.geom_type == "Polygon"]
    #print("{} strade vuote su {}: \n{}".format(len(pois_with_empty_shapes), len(streets_list), pois_with_empty_shapes))
    #print("{} strade con poligoni su {}: \n{}".format(len(pois_with_polygon), len(streets_list), pois_with_polygon))
    #other_pois = [cur_poi for cur_poi in pois_with_shapes if cur_poi.shape and not cur_poi.shape.geom_type == "Polygon"]
    #print("{} strade con altre cose su {}: \n{}".format(len(other_pois), len(streets_list), other_pois))

    if testPassed:
        print("*****************\n* TEST SUPERATO *\n*****************\n")
    else:
        print("*****************\n* TEST  FALLITO *\n*****************\n")
