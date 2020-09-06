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
				document.getElementById("percorso_terra").style.display = "inline";
				document.getElementById("percorso_acqua").style.display = "none";
				break;
			case 2:
				document.getElementById("results_search").style.display = "none";
				document.getElementById("weird").style.display = "none";
				document.getElementById("single_address").style.display = "none";
				document.getElementById("percorso_terra").style.display = "none";
				document.getElementById("percorso_acqua").style.display = "none";
			default:
				document.getElementById("single_address").style.display = "none";
				document.getElementById("percorso_terra").style.display = "none";
				document.getElementById("percorso_acqua").style.display = "none";
				document.getElementById("weird").style.display = "inline";
				break;
	}
	if (areWeUsingBottomBar()) {
		moveResultsToSidebar();
	}
}

function closeResultsWindow() {
	console.log("chiudo");
	document.getElementById("results_search").style.display = "none";
	document.getElementById("single_address").style.display = "none";
	document.getElementById("percorso").style.display = "none";
	document.getElementById("weird").style.display = "none";
}
function moveResultsToSidebar() {
	console.log("sposto i risultati nella sidebar")
	document.getElementById("results_search").style.display = "none";
	document.getElementById("possibilitiesFather").appendChild(document.getElementById("percorso"));
	document.getElementById("possibilitiesFather").appendChild(document.getElementById("single_address"));
	document.getElementById("possibilitiesFather").appendChild(document.getElementById("weird"));
	hideSidebar();
}

function fillResultsWindow(dictJS) {
	switch (dictJS.modus_operandi) {
		case 0:
			fillResultsWindowSingleAddress(dictJS);
			break
		case 1:
			fillResultsWindowPercorso(dictJS);
			break
	}
}

function fillResultsWindowSingleAddress(dictJS) {
	var name_location = dictJS.params_research.da;
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
	var nome_partenza = dictJS.params_research.da;
	document.getElementById("da_text").innerHTML = "<i>"+nome_partenza+"</i>";
	var nome_arrivo = dictJS.params_research.a;
	document.getElementById("a_text").innerHTML = "<i>"+nome_arrivo+"</i>";
	var path_length = dictJS.path.human_readable_length;
	document.getElementById("length_text").innerHTML = "<i>"+path_length+"</i>";
	var time_description = dictJS.path.human_readable_time;
	document.getElementById("time_text").innerHTML = "<i>"+time_description+"</i>";
	var num_of_bridges = dictJS.path.n_ponti[0];
	document.getElementById("ponti_text").innerHTML = "<i>strada con "+num_of_bridges+" "+ponte_sing_plur(num_of_bridges)+"</i>";
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
			document.getElementById("ponti_text").innerHTML += "<i><br>"+"&emsp;- "+
																											num_bridges_accessible[i]+ " " +
																											ponte_sing_plur(num_bridges_accessible[i]) +
																											" con "+bridge_accessibility_name[i]+
																											"</i>";
		}
	}
}

function fillResultsWindowPercorsoBoat(dictJS) {
	var nome_partenza = dictJS.params_research.da;
	document.getElementById("da_text").innerHTML = "<i>"+nome_partenza+"</i>";
	var nome_arrivo = dictJS.params_research.a;
	document.getElementById("a_text").innerHTML = "<i>"+nome_arrivo+"</i>";
	var path_length = dictJS.path.human_readable_length;
	document.getElementById("length_text").innerHTML = "<i>"+path_length+"</i>";
	var time_description = dictJS.path.human_readable_time;
	document.getElementById("time_text").innerHTML = "<i>"+time_description+"</i>";
	var num_of_bridges = dictJS.path.n_ponti[0];
	document.getElementById("ponti_text").innerHTML = "<i>strada con "+num_of_bridges+" "+ponte_sing_plur(num_of_bridges)+"</i>";
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
			document.getElementById("ponti_text").innerHTML += "<i><br>"+"&emsp;- "+
																											num_bridges_accessible[i]+ " " +
																											ponte_sing_plur(num_bridges_accessible[i]) +
																											" con "+bridge_accessibility_name[i]+
																											"</i>";
		}
	}
}
function ponte_sing_plur(num){
	if (num == 1) {
		return "ponte"
	} else{
		return "ponti"
	}
}
