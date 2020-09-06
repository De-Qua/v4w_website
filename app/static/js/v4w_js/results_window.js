/* Licensed under AGPLv3
 /*!
  * Venessia4Working Javascripts
  * Copyleft 2020

  */


function showResultsWindow(result_type) {
		document.getElementById("results_search").style.display = "inline";
		document.getElementById("weird").style.display = "none";
		switch (result_type) {
			case 'single_address':
				document.getElementById("single_address").style.display = "inline";
				document.getElementById("percorso").style.display = "none";
				break;
			case 'percorso':
				document.getElementById("single_address").style.display = "none";
				document.getElementById("percorso").style.display = "inline";
				break;
			default:
				document.getElementById("single_address").style.display = "none";
				document.getElementById("percorso").style.display = "none";
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
	
}

function fillResultsWindowPercorso(dictJS) {
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
																	"gradino aggevolato",
																	"gradino aggevolato accessibile con accompagnatore",
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
