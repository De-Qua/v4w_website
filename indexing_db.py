from app.models import Location, Address, Poi,Street, Neighborhood
import pandas as pd

def main():

    # DATAFRAME
    dqdf = pd.DataFrame(
        columns=['search_id',               # a unique id for the result of the search (this as an index)
                 'full_text_info',          # a lot of text, everything about this entry
                 'name',                    # more like what could be displayed
                 'type',                    # what is it? (related to the table)
                 'p_id',                    # personal id to get back to the actual entry in different tables
                 'neighborhood',            # sestiere
                 'street',                  # street name (full)
                 'numero',                  # numero civico
                 'CAP',                     # codice postale
                 'entry_type_text',        # street type (ponte, calle, salizada, fondamenta, ecc...)
                 'entry_type_category',    # street type as category (0: strada, calle.. 1: ponte, 2: piazza, campo.. )
                 'latitude',                # latitude
                 'longitude']               # longitude
    )

    s_id = 0
    s_id += add_locations(s_id)

def create_entry(values):
    """
    It just converts a list in a dict that we can use with pd.DataFrame.insert(dict, ignore_index=True).
    """
    if len(values) != len(dqdf.columns):
        print(f'Error, we need exactly {len(dqdf.columns)} values (we got {len(values)}} )')
        return None

    entry = {'search_id':values[0],
             'full_text_info':values[1],          # a lot of text, everything about this entry
             'name':values[2],                    # more like what could be displayed
             'table':values[3],                   # which table it belongs to?
             'p_id':values[4],                    # personal id to get back to the actual entry in different tables
             'neighborhood':values[5],            # sestiere
             'street':values[6],                  # street name (full)
             'numero':values[7],                  # numero civico
             'CAP':values[8],                     # codice postale
             'entry_type_text':values[9],         # entry type (indirizzo, ponte, calle, salizada, fondamenta, ecc...)
             'entry_type_category':values[10],    # street type as category (0: strada, calle.. 1: ponte, 2: piazza, campo.. )
             'latitude':values[11],               # latitude
             'longitude':values[12]]              # longitude}

    return

def classify_entry_type(entry_table, entry_type_text, entry):
    """
    Classifying types:
    # locations
    0: location (no address)
    1: address (indirizzo)
    2: street (strada, calle, salizada, fondamenta, sotoportego, )
    3: open_space (piazza, piazzale, campo, )
    4: bridge (ponte, )
    5: area (area, zona, )
    6: neighborhood (sestiere, )
    # pois
    7: restaurant (poi-restaurant, poi-cuisine, )
    8: bar (poi-bar, )
    9: cafe (poi-caffe, )
    10: apotheke (poi-farmacia, )
    11: supermarket (poi-supermercato)
    12: shop (poi-negozio, )
    13: hotels (poi-hotel, albergo, )
    14: building (stazione, ospedale, )
    15: sport (campo sportivo, )
    # water pois
    16: stop (fermata battelli, fermata traghetti, )
    17: riva (riva pubblica, )
    18: vincolo (posto barca, )
    ..
    51: OSM_poi (poi non specificato, )
    ..
    99: other (non specificato, )
    """

    if entry_table == 'location':
        return 0
    elif entry_table == 'address':
        return 1
    elif entry_table == 'street':
        # decide 2, 3 or 4
        type_2_den = ['CALLE', 'SALIZADA', 'FONDAMENTA', 'SOTOPORTEGO']
        type_3_den = ['PIAZZA', 'PIAZZALE', 'P.LE', 'CAMPO', 'CAMPIELLO']
        type_4_den = ['PONTE']

        if any(w in entry.name_den for w in type_2_den):
            return 2
        elif any(w in entry.name_den for w in type_3_den):
            return 3
        elif any(w in entry.name_den for w in type_4_den):
            return 4
        else:
            print('weird, street, but what?', entry.name_den)
            return 99
    elif entry_table == 'area':
        return 5
    elif entry_table == 'neighborhood':
        return 6
    elif entry_table == 'poi':
        poi_7_words = ['restaurant', 'ristorante', 'risto', 'cucina', 'cuisine', 'trattoria']
        poi_8_words = ['bar', 'pub', 'locanda']
        poi_9_words = ['caff', 'coff']
        poi_10_words = ['apothe', 'farmacia', 'croce verde']
        poi_11_words = ['supermarket', 'supermercato', 'minimarket', 'kiosk']
        poi_12_words = ['shop', 'negozio']
        poi_13_words = ['hotel', 'hostel', 'albergo', 'pension']
        poi_14_words = ['building', 'station', 'stazione', 'ospedale', 'hospital']
        poi_15_words = ['sport', 'swimming', 'pool', 'palestra']
        poi_16_words = ['stop', 'fermata', 'battello']
        poi_17_words = ['riva', 'pubblica']
        poi_17_words = ['vincolo']
    if any(w in entry.name_den for w in type_2_den):
        return 2
    elif any(w in entry.name_den for w in type_3_den):
        return 3
    elif any(w in entry.name_den for w in type_4_den):
        return 4
    else:
        print('weird, street, but what?', entry.name_den)
        return 99


def add_locations(search_id):

    locations = Location.query.all()
    for loc in locations:
        loc_s_id = search_id
        loc_type = 'address' if loc.address else 'location'
        loc_id = loc.id
        loc_n = loc.neighborhood.name if loc.neighborhood else ""
        loc_s = loc.street.street if loc.street else ""
        loc_num = loc.address[0].housenumber if loc.address else ""
        loc_cap = loc.neighborhood.zipcode if loc.neighborhood else ""
        loc_str_type_t = loc_type
        loc_str_type_c =
        loc_name = ''
        loc_full_text_info =

        dqdf.append({'c1':0, 'c2':1, 'c3':2}, ignore_index=True)
        search_id += 1
    return search_id

if __name__ == '__main__':
    main()
