/* Licensed under AGPLv3
 /*!
  * Venessia4Working Javascripts
  * Copyleft 2020

  */


function getNextStep(element, what_are_we_doing, cur_result_name, searched_end, start_found) {
	var clicked_coords = [element.lat, element.lng];
	var new_site_to_go = "";
  var stringBoxes = retrieveBoxesSituationAsAString();
	if (what_are_we_doing == "choosing_start" || what_are_we_doing == "address") {
		new_site_to_go = "/?partenza="+escape(cur_result_name).replace(/%20/g, "+")+"&start_coord=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")&arrivo="+escape(searched_end).replace(/%20/g, "+")+"&end_coord="+stringBoxes;
    // document.getElementById("search_field_1").value = cur_result_name
    // document.getElementById("start_coord").value = "LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")";
  }
	else if (what_are_we_doing == "choosing_end") {
		var strt_coords = start_found.coordinate;
    var strt_name = start_found.nome;
		//alert('start found e: ' + start_found);
		// vecchia Versione
		//new_site_to_go = "/?partenza="+escape(strt_name).replace(/%20/g, "+")+"&start_coord=LatLng("+strt_coords[0]+", "+strt_coords[1]+")&arrivo="+escape(cur_result_name).replace(/%20/g, "+")+"&end_coord=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")"+stringBoxes;
		// nuova!
		new_site_to_go = "/?partenza="+escape(strt_name).replace(/%20/g, "+")+"&start_coord="+escape(strt_coords)+")&arrivo="+escape(cur_result_name).replace(/%20/g, "+")+"&end_coord=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")"+stringBoxes;
    // document.getElementById("search_field_1").value = strt_name
    // document.getElementById("start_coord").value = "LatLng("+strt_coords[0]+", "+strt_coords[1]+")";
    // document.getElementById("search_field_2").value = cur_result_name
    // document.getElementById("end_coord").value = "LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")";
  }
	return new_site_to_go;
}

function retrieveBoxesSituationAsAString() {
  var by_boat_checked = document.getElementById("boat_setting").checked ? "&boat=on" : "&boat=off";
  var less_bridges_checked = document.getElementById("less_bridges_setting").checked ? "&lazy=on" : "&lazy=off";
	var walk_setting_checked = document.getElementById("walk_setting").checked ? "&walking=on" : "&walking=off";
  return by_boat_checked + less_bridges_checked;
}
