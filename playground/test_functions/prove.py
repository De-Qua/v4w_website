streets = gpd.read_file(folder + "/../data_bkp" + "/EL_STR.shp")
streets = streets.to_crs(epsg=4326)
nome
civico = gpd.read_file(folder + "/../data_bkp" + "/CIVICO_4326.shp")
civico.columns
denomina=civico["DENOMINAZI"]
denomina=civico["DENOMINAZI"].to_list()
denomina_corrected=[x for x in denomina if x]
matches_index = [i for i,x in enumerate(denomina_corrected) if 'CALLE DEL FORNO'in x]
civico['SUBCOD_VIA'][matches_index]
cod=civico['SUBCOD_VIA'][matches_index]
den_streets=streets['TP_STR_NOM']
den_streets_corrected=[x for x in den_streets if x]
matches_ind_tpn = [i for i,x in enumerate(den_streets_corrected) if 'CALLE DEL FORNO'in x]
cod_tpn=streets['CVE_COD_VI'][matches_ind_tpn]
[print(x) for x in cod if int(x)==10610]

