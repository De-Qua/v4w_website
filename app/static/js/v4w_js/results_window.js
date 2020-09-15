/* Licensed under AGPLv3
 /*!
  * Venessia4Working Javascripts
  * Copyleft 2020

  */


function showResultsWindow(dictJS) {

		document.getElementById("results_search").style.display = "inline";
		document.getElementById("weird").style.display = "none";
		switch (dictJS.modus_operandi) {
			case 0:
				document.getElementById("single_address").style.display = "inline";
				document.getElementById("percorso_terra").style.display = "none";
				document.getElementById("percorso_acqua").style.display = "none";
				break;
			case 1:
				document.getElementById("single_address").style.display = "none";
				switch(dictJS.params_research.by_boat){
					case "on":
						document.getElementById("percorso_terra").style.display = "none";
						document.getElementById("percorso_acqua").style.display = "inline";
						break;
					case "off":
						document.getElementById("percorso_terra").style.display = "inline";
						document.getElementById("percorso_acqua").style.display = "none";
						break;
				}
				break;
			case 2:
				document.getElementById("results_search").style.display = "none";
				document.getElementById("weird").style.display = "none";
				document.getElementById("single_address").style.display = "none";
				document.getElementById("percorso_terra").style.display = "none";
				document.getElementById("percorso_acqua").style.display = "none";
				break;
			default:
				document.getElementById("single_address").style.display = "none";
				document.getElementById("percorso_terra").style.display = "none";
				document.getElementById("percorso_acqua").style.display = "none";
				document.getElementById("weird").style.display = "none";
				break;
	}
	fillResultsWindow(dictJS)
	if (areWeUsingBottomBar()) {
		moveResultsToSidebar();
	}
}

function closeResultsWindow() {
	console.log("chiudo");
	document.getElementById("results_search").style.display = "none";
	document.getElementById("single_address").style.display = "none";
	document.getElementById("percorso_terra").style.display = "none";
	document.getElementById("percorso_acqua").style.display = "none";
	document.getElementById("weird").style.display = "none";
}
function moveResultsToSidebar() {
	console.log("sposto i risultati nella sidebar")
	document.getElementById("results_search").style.display = "none";
	document.getElementById("resultsSidebar").appendChild(document.getElementById("percorso_terra"));
	document.getElementById("resultsSidebar").appendChild(document.getElementById("percorso_acqua"));
	document.getElementById("resultsSidebar").appendChild(document.getElementById("single_address"));
	document.getElementById("resultsSidebar").appendChild(document.getElementById("weird"));
	hideSidebar();
}

function moveResultsToMainWindow() {
	$("#results_search").append($("#percorso_terra"));
	$("#results_search").append($("#percorso_acqua"));
	$("#results_search").append($("#single_address"));
	$("#results_search").append($("#weird"));
	$("#results_search").show();
}

function fillResultsWindow(dictJS) {
	switch (dictJS.modus_operandi) {
		case 0:
			fillResultsWindowSingleAddress(dictJS);
			break;
		case 1:
			fillResultsWindowPercorso(dictJS);
			break;
		case 2:
			break;
	}
}

function fillResultsWindowSingleAddress(dictJS) {
	var name_location = dictJS.partenza[0].nome;
	document.getElementById("found_text").innerHTML = "<i>"+name_location+"</i>";
	switch (dict_in_JS.partenza[0].geotype) {
		case 0:
			document.getElementById("type_text").innerHTML = "<i>indirizzo</i>";
			break;
		case 1:
      document.getElementById("type_text").innerHTML = "<i>area</i>";
			break;
	}
}

function fillResultsWindowPercorso(dictJS) {
	if (dictJS.params_research.by_boat == "on") {
		fillResultsWindowPercorsoBoat(dictJS);
	} else {
		fillResultsWindowPercorsoWalk(dictJS);
	}
}

function fillResultsWindowPercorsoWalk(dictJS) {
	var nome_partenza = dictJS.partenza[0].nome;
	document.getElementById("walk_da_text").innerHTML = "<i>"+nome_partenza+"</i>";
	var nome_arrivo = dictJS.arrivo[0].nome;
	document.getElementById("walk_a_text").innerHTML = "<i>"+nome_arrivo+"</i>";
	var path_length = dictJS.path.human_readable_length;
	document.getElementById("walk_length_text").innerHTML = "<i>"+path_length+"</i>";
	var time_description = dictJS.path.human_readable_time;
	document.getElementById("walk_time_text").innerHTML = "<i>"+time_description+"</i>";
	var num_of_bridges = dictJS.path.n_ponti[0];
	document.getElementById("walk_ponti_text").innerHTML = "<i>strada con "+num_of_bridges+" "+ponte_sing_plur(num_of_bridges)+"</i>";
	var bridge_accessibility_name = ["gradini normali",
																	"nessuna barriera architettonica",
																	"gradino agevolato",
																	"gradino agevolato accessibile con accompagnatore",
																	"rampa fissa",
																	"rampa provvisoria da Feb a Nov",
																	"rampa provvisoria da Set a Giu",
																	"rampa provvisoria da Mag a Nov"]
	var num_bridges_accessible = dictJS.path.n_ponti[1];
	for (i=0; i<num_bridges_accessible.length; i++){
		if (num_bridges_accessible[i] > 0){
			document.getElementById("walk_ponti_text").innerHTML += "<i><br>"+"&emsp;- "+
																											num_bridges_accessible[i]+ " " +
																											ponte_sing_plur(num_bridges_accessible[i]) +
																											" con "+bridge_accessibility_name[i]+
																											"</i>";
		}
	}
}

function fillResultsWindowPercorsoBoat(dictJS) {
	var nome_partenza = dictJS.partenza[0].nome;
	document.getElementById("boat_da_text").innerHTML = "<i>"+nome_partenza+"</i>";
	var nome_arrivo = dictJS.arrivo[0].nome;
	document.getElementById("boat_a_text").innerHTML = "<i>"+nome_arrivo+"</i>";
	var path_length = dictJS.path.human_readable_length;
	document.getElementById("boat_length_text").innerHTML = "<i>"+path_length+"</i>";
	var time_description = dictJS.path.human_readable_time;
	document.getElementById("boat_time_text").innerHTML = "<i>"+time_description+"</i>";
	var min_altezza = dictJS.path.altezza;
	if (min_altezza == undefined) {
		document.getElementById("boat_info_text").innerHTML = "<i>Non ci sono altre informazioni particolari</i>";
	} else {
		document.getElementById("boat_info_text").innerHTML = "<i>- altezza minima dei ponti attraversati: "+
																													min_altezza+"m</i>";
	}
}
function ponte_sing_plur(num){
	if (num == 1) {
		return "ponte"
	} else{
		return "ponti"
	}
}
