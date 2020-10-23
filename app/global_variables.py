from app.models import Street, Poi

G_terra = None
G_acqua = None
boat_speed=5/3.6
walk_speed=5/3.6
# distanza minima per considerare che partiamo dall'ACQUA
min_dist_to_go_by_boat=40
min_dist_to_suggest_boat=60
# tabelle in cui cercare anche per il nome alternativo
tables_with_alt_name=[Street, Poi]
# un altro script su pythonanywhere aggiornerà questi dati
dati_json_previsione = 'app/src/static/json/dati_previsione_marea'
dati_json_livello = 'app/src/static/json/livello_marea_5_min'
tideflag = True
current_tide = 110
safety_diff_tide = 5

height_low_boots = 40
height_high_boots = 75
