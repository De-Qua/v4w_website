from datetime import datetime
import numpy as np
import graph_tool.all as gt
import time
import ipdb
from weights import get_weight_time
from graph_tool.util import find_vertex
speed = 5/3.6

TOTAL_SECONDS_IN_WEEK = 24*7*3600


class dequaVisitor(gt.DijkstraVisitor):

    def __init__(self, g, touched_v, touched_e, target, time_from_source, graph_weights, start_time, time_edges):
        self.g = g
        self.touched_v = touched_v
        self.touched_e = touched_e
        self.target = target
        self.weight = graph_weights
        self.time_from_source = time_from_source
        self.time_edges = time_edges
        self.name = np.random.rand()
        self.start_time = start_time

    def discover_vertex(self, u):
        self.touched_v[u] = True

    def examine_edge(self, e):
        self.touched_e[e] = True
        # andando in pontile, metto il tempo d'attesa
        if g.vp['transport'][e.target()] and not g.vp['transport'][e.source()]:
            waiting_time = self.calculate_waiting_time(e)
            self.weight[e] = waiting_time
            if self.touched_v[e.target()]:
                self.time_from_source[e.target()] = np.minimum(self.time_from_source[e.source()] + waiting_time, self.time_from_source[e.target()])
            else:
                self.time_from_source[e.target()] = self.time_from_source[e.source()] + waiting_time
            print(f"visitor now between {e.source()} and {e.target()} with time {self.time_from_source[e.target()]:.3f}, avendo appena aggiunto {waiting_time}")
        else:
            if self.touched_v[e.target()]:
                self.time_from_source[e.target()] = np.minimum(self.time_from_source[e.source()] + self.time_edges[e], self.time_from_source[e.target()])
            else:
                self.time_from_source[e.target()] = self.time_from_source[e.source()] + self.time_edges[e]
                # print(f"visitor {self.name:.3f} è adesso al tempo {self.real_time:.3f}, avendo appena ggiunto {waiting_time}")

        # if g.ep['ponte'][e]:
        #     #print("lunghezza ", g.ep['length'][e])
        #     self.weight = g.ep['length'][e]

    def edge_relaxed(self, e):
        if e.target() == self.target:
            raise gt.StopSearch()

    def calculate_waiting_time(self, e):
        try:
            if g.ep['timetable'][e].a.size == 0:
                print(f"Edge {e} tra {e.source()} e {e.target()}")
                print("# WARNING: non c'è nulla nell'array! é una corsa che c'è solo nei giorni speciali?")
                return int(TOTAL_SECONDS_IN_WEEK)

            moduled_week_time = (self.time_from_source[e.source()] + self.start_time) % TOTAL_SECONDS_IN_WEEK
            diff_times = g.ep['timetable'][e].a - moduled_week_time
            if np.abs(moduled_week_time - (self.time_from_source[e.source()] + self.start_time)) > 100:
                print(f"siamo alle {datetime.fromtimestamp(moduled_week_time)}, primo battello alle {g.ep['timetable'][e].a[0]}")
            waiting_times = diff_times[diff_times > 0]
            if len(waiting_times) > 0:
                return np.min(waiting_times)
            else:
                if TOTAL_SECONDS_IN_WEEK - (self.time_from_source[e.source()] + self.start_time) > 0:
                    print(g.ep['timetable'][e].a[0])
                    return g.ep['timetable'][e].a[0] + TOTAL_SECONDS_IN_WEEK - (self.time_from_source[e.source()] + self.start_time)
                else:
                    print("\n\n\nè per caso domenica sera??! Sera tardi: pesi negativi, strano\n\n\n")
                    ipdb.set_trace()
        except IndexError:
            print(f"Edge {e} tra {e.source()} e {e.target()}")
            print("# WARNING: non c'è nulla nell'array! é una corsa che c'è solo nei giorni speciali?")
            return int(TOTAL_SECONDS_IN_WEEK)


# ERRORE
# 61979 --> 63458
# esiste solo nei giorni speciali?

def distance_from_a_list_of_geo_coordinates(thePoint, coordinates_list):
    """
    A python implementation from the answer here https://stackoverflow.com/questions/639695/how-to-convert-latitude-or-longitude-to-meters.
    Calculate the distance in meters between 1 geographical point (longitude, latitude) and a list of geographical points (list of tuples) or between 2 geographical points passing through distance_from_point_to_point
    """
    # maybe we need to invert
    lat_index = 1
    lon_index = 0
    # parameters
    earth_radius = 6378.137  # Radius of earth in KM
    deg2rad = np.pi / 180
    # single point
    lat1 = thePoint[lat_index] * deg2rad
    lon1 = thePoint[lon_index] * deg2rad
    # test the whole list again the single point
    lat2 = coordinates_list[:, lat_index] * deg2rad
    lon2 = coordinates_list[:, lon_index] * deg2rad
    dLat = lat2 - lat1
    dLon = lon2 - lon1
    a = np.sin(dLat/2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dLon/2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    d = earth_radius * c
    distances_in_meters = d * 1000

    return distances_in_meters


def find_closest_vertices(coord_list, vertices_latlon_list, MIN_DIST_FOR_THE_CLOSEST_NODE=100):
    """
    Returns list of nodes in vertices_latlon_list closest to coordinate_list (euclidean distance).
    """
    nodes_list = []
    for coordinate in coord_list:
        # coordinate = np.asarray(d.get("coordinate"))
        #time1 = time.time()
        #tmp = np.subtract(np.ones(G_array.shape) * coordinate, G_array)
        #dists = np.sum(np.sqrt(tmp * tmp), axis=1)
        time2 = time.time()
        dists = distance_from_a_list_of_geo_coordinates(coordinate, vertices_latlon_list)
        time3 = time.time()
        # app.logger.debug("it took {} to calculate distances".format(time3-time2))
        print(f"it took {time3-time2} to calculate distances")
        #dists=d.get("shape").distance(G_array)
        closest_id = np.argmin(dists)
        closest_dist = dists[closest_id]
        # app.logger.debug("il tuo nodo è distante {}".format(closest_dist))
        print(f"il tuo nodo è distante {closest_dist}")
        # se la distanza e troppo grande, salutiamo i campagnoli
        if closest_dist > MIN_DIST_FOR_THE_CLOSEST_NODE:
            # app.logger.error("Sei troppo distante da Venezia, cosa ci fai là?? (il punto del grafo piu vicino dista {} metri)".format(closest_dist))
            print("Sei troppo distante da Venezia, cosa ci fai là?? (il punto del grafo piu vicino dista {closest_dist} metri)")
            # raise custom_errors.UserError("Non abbiamo trovato nulla qua - magari cercavi di andare fuori venezia o forse vorresti andare in barca?")
            return []
        nodes_list.append(closest_id)

    return nodes_list  # , dists


if __name__ == "__main__":

    graph_path = "/Users/ale/Documents/Venezia/MappaDisabili/code/v4w_website/app/static/files/dequa_ve_terra_v14_1110_battelli.gt"
    g = gt.load_graph(graph_path)
    pos = g.vp['latlon']
    all_pos = np.array([pos[v].a for v in g.iter_vertices()])
    #map_coords = [np.array([12.331366730532233, 45.43670740765949])]
    #id_closest_vertex = find_closest_vertices(map_coords, all_pos)
    touch_v = g.new_vertex_property("bool")
    touch_e = g.new_edge_property("bool")
    venice_weight = g.new_edge_property("double")
    weight_time = get_weight_time(g)
    time_from_source = g.new_vertex_property("double")
    # paretnza 45.43988044474121   12.339807563546461
    # arrivo 45.43170127993013 12.325036058157616
    coord_source = [np.array([12.339807563546461, 45.43988044474121])]  # rialto (quasi, non proprio)
    #coord_source = [np.array([12.355488828203178, 45.419738395449336])]  # san servolo
    #coord_source = [np.array([12.342391, 45.42943])]  # san giorgio
    id_closest_vertex_source = find_closest_vertices(coord_source, all_pos)

    coord_target = [np.array([12.325005472560107, 45.42545331547442])]  # giudecc
    #coord_target = [np.array([12.342707496284957, 45.43381763225837])]  # s.zaccaria
    id_closest_vertex_target = find_closest_vertices(coord_target, all_pos)
    latlon = g.vertex_properties['latlon']
    # source = find_vertex(g, latlon, coord_source)
    # target = find_vertex(g, latlon, coord_target)
    # print(f'Source {source}')
    # print(f'Target {target}')elaxed(
    target = g.vertex(id_closest_vertex_target[0])
    source = g.vertex(id_closest_vertex_source[0])
    today = datetime.today()
    start_time = today.weekday() * 24 * 3600 + today.hour * 3600 + today.minute * 60 + today.second
    time_from_source[source] = 0  # start_time
    dist, pred = gt.dijkstra_search(g=g,
                                    weight=weight_time,
                                    source=source,
                                    visitor=dequaVisitor(g=g,
                                                         touched_v=touch_v,
                                                         touched_e=touch_e,
                                                         target=target,
                                                         time_from_source=time_from_source,
                                                         graph_weights=weight_time,
                                                         start_time=start_time,
                                                         time_edges=weight_time))

    v = target
    counter = 0
    counter_vertices = 0
    while v != source:
        counter_vertices += 1
        #print(f"siamo a {time_from_source[v]} secondi")
        p = g.vertex(pred[v])
        if g.vp['transport'][p]:
            salita_timestamp = start_time + time_from_source[v]
            salita = datetime.fromtimestamp(salita_timestamp)
            print(f"pontile finale alle {salita} - da {p} a {v}")
            scesa_timestamp = start_time + time_from_source[p]
            scesi = datetime.fromtimestamp(scesa_timestamp)
            print(f"pontile iniziale dalle {scesi} - da {p} a {v}")
            linea = g.ep.route[g.edge(p, v)].route_short_name
            print(f"linea {linea}")
            for trip_time in g.ep.timetable[g.edge(p, v)]:
                print(datetime.fromtimestamp(trip_time))
        v = p

    time_trip = (time_from_source[target]-time_from_source[source])
    time_trip_min = time_trip/60
    time_trip_hours = time_trip_min/60
    print(f"ci abbiamo messo {time_trip_min} minuti o {time_trip_hours} ore")
    arrivo_timestamp = start_time + time_trip
    partenza = datetime.fromtimestamp(start_time)
    arrivo = datetime.fromtimestamp(arrivo_timestamp)
    print(f"partenza: {partenza}, arrivo: {arrivo}")

    ipdb.set_trace()
