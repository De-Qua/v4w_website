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
