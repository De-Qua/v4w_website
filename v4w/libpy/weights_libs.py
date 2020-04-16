# %% codecell
# weight_bridge come funzione peso
def weight_bridge(x,y,dic):
#    if dic["altezza"]< 110:
#        w = 100
#    else:
#        w=0
    return dic["length"] + dic["ponte"]*100
    #weight = dic["length"] if dic["ponte"]==0 else None
 #   return weight

# %% codecell
def plot_shortest_path(path_nodes,map_shp):
    # path_nodes lista di nodi attraversati
    # map_shp shapefile generale della mappa su cui si cerca il percorso

    # Converte la lista di nodi in file json
    shapes = []
    for i in range(len(path_nodes)-1):
        shapes.append(shape(json.loads(G_un[path_nodes[i] ][path_nodes[i+1] ]['Json'])))
    x_tot = []
    for sha in shapes:
    #   print(sha.coords.xy)
        x = []
        for i in range(len(sha.coords.xy[0])):
            x.append((sha.coords.xy[0][i],sha.coords.xy[1][i]))
        # to be corrected with x_start
        if not x_tot:
            x_tot+=x
        elif x[0] == x_tot[-1]:
    #        print(x[0], "uguali",x_tot[-1])
            x_tot+=x
        else:
    #        print(x[0],"diversi", x_tot[-1])
            x_tot+=x[::-1]

    x_tot = np.asarray(x_tot)
    plt.figure()
    map_shp.plot()
    plt.plot(x_tot[:,0], x_tot[:,1], c="r")
    return
