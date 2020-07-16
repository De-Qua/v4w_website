list_of_searches = [
    #Esempio: ('Stringa di ricerca',['Soluzione1','Soluzione2','Soluzione3'], 'categoria')
    ('rialto', ["PONTE DE RIALTO", "SOTOPORTEGO DE RIALTO","CAMPO RIALTO NOVO"], [0.4, 0.3, 0.3], 'ambiguo'),
    ('rilato', ["PONTE DE RIALTO", "SOTOPORTEGO DE RIALTO","CAMPO RIALTO NOVO"], [0.5, 0.4, 0.1], 'errori'),
    ('accademia',["PONTE DE L'ACCADEMIA"], [1], 'ambiguo'),
    ('academia',["PONTE DE L'ACCADEMIA"], [1], 'errori'),
    ('acaedmia',["PONTE DE L'ACCADEMIA"], [1], 'errori'),
    ('campo dell accademia',["PONTE DE L'ACCADEMIA"], [1], 'stopwords'),
    ('fte nuove',["FONDAMENTE NOVE"],[1],'ambiguo'),
    ('fondamente nuove',["FONDAMENTE NOVE"],[1],'ambiguo'),
    ('fondmenta nve',["FONDAMENTE NOVE"],[1],'errori'),
    ('santa margherita',["CAMPO SANTA MARGARITA","PONTE SANTA MARGARITA"],[0.7,0.3],'ambiguo'),
    ('santa marghe',["CAMPO SANTA MARGARITA","PONTE SANTA MARGARITA"],[0.7,0.3],'ambiguo'),
    ('santa mazrgherta',["CAMPO SANTA MARGARITA","PONTE SANTA MARGARITA"],[0.7,0.3],'errori'),
    ('margherita',["CAMPO SANTA MARGARITA","PONTE SANTA MARGARITA"],[0.7,0.3],'stopwords'),
    ('cannaregio 3782/B',["CANNAREGIO 3782/B"],[1],'ambiguo'),
    ('canareggio 3782/B',["CANNAREGIO 3782/B"],[1],'errori'),
    ('canareiuoa 3782/B',["CANNAREGIO 3782/B"],[1],'errori'),
    ('santa marta',["PONTE NOVO DE SANTA MARTA","CALLE LARGA SANTA MARTA"],[0.5, 0.5],'ambiguo'),
    ('san basilio',["CAMPO DE SAN BASEGIO","FONDAMENTA DE SAN BASEGIO","PONTE DE SAN BASEGIO", "SALIZADA SAN BASEGIO"],[0.4, 0.3, 0.2, 0.1],'ambiguo'),
    ('gnecca 8',["GIUDECCA 8"],[1],'ambiguo'),
    ('2054 santa marta',["DORSODURO 2054"],[1],'delirio')
    ]

categories = ['ambiguo', 'errori', 'stopwords', 'delirio']

from app.src.libpy.library_coords import fuzzy_search
from fuzzywuzzy import fuzz
scorer_processor = [(fuzz.ratio,lambda x: x.__str__()),
                    (fuzz.partial_ratio,lambda x: x.__str__())
                    (fuzz.QRatio,)
                    (fuzz.WRatio,)
                    (fuzz.token_set_ratio,)
                    (fuzz.token_sort_ratio,)]
for search in list_of_searches:
    for scorer,processor in scorer_processor:
        clean_string = correct_name(input_string)
