/* Licensed under AGPLv3
/*!
* Venessia4Working Javascripts
* Copyleft 2020

*/

function onMapClick(e) {
	var address_string = e.latlng.toString();
	popup
	.setLatLng(e.latlng)
    //.setContent("<div class='text-center'>Posizione: " + address_string + "<br><button  class='btn btn-sm btn-light v4wbtn mr-3' style='font-size: 0.8em;' id='btnMapStart'>DA QUA</button><button  class='btn btn-sm btn-light v4wbtn' style='font-size: 0.8em;' id='btnMapTo'>A</button><br></div>")
	.setContent("<button  class='btn btn-sm btn-light v4wbtn mr-3' style='font-size: 0.8em;' id='btnMapStart'>Parti<br> DA QUA</button><button  class='btn btn-sm btn-light v4wbtn' style='font-size: 0.8em;' id='btnMapTo'>Vai <br>QUA</button><br></div>")
	.openOn(mymap);
	document.getElementById('btnMapStart').onclick = function() { copyStartingPosition(address_string); addMarkerStart(e.latlng); popup.remove();};
	document.getElementById('btnMapTo').onclick = function() { copyEndingPosition(address_string); addMarkerEnd(e.latlng);popup.remove();};
}

function changeMap(currentMap) {
	console.log("changing map.. from " + allMaps[whichmap])

	whichmap = (currentMap+1)%allMaps.length;

	mymap.removeLayer(baseMaps[allMaps[currentMap]]);
	baseMaps[allMaps[whichmap]].addTo(mymap);

	console.log("to " + allMaps[whichmap])
}

function addMarkerStart(latlng) {
	marker_start.setLatLng(latlng);
	marker_start.bindPopup("Partenza!")
	marker_start.addTo(mymap);
}

function addMarkerEnd(latlng) {
	marker_end.setLatLng(latlng);
	marker_end.bindPopup("Arrivo!")
	marker_end.addTo(mymap);
}

function addMarkerPosition(latlng, radius){
	L.circle(latlng, radius).addTo(mymap);
}

function showHighlight(card) {
	var clicked_coords = [card.lat,card.lng];

	console.log("sei sopra a: " + clicked_coords);
	//highlight.clearLayers().addLayer(L.circleMarker([clicked_coords[1], clicked_coords[0]], highlightStyle));
	highlight.clearLayers().addLayer(L.circleMarker([clicked_coords[0], clicked_coords[1]], highlightStyle));
	highlight.bringToFront();
	console.log("highlight: "+ highlight);
	// highlight the card
	// childNodes[0] = header; childNodes[1] = body
	card.childNodes[0].style.background = "#bbb";
	card.childNodes[1].style.background = "#ccc";
}

function clearHighlight(card) {
	highlight.clearLayers();
	// dehighlight the card
	// childNodes[0] = header; childNodes[1] = body
	card.childNodes[0].style.background = "rgb(247, 247, 247)";
	card.childNodes[1].style.background = "rgb(255, 255, 255)";
}

function addMarkerLocation(coords, cur_result_name, cur_result_description) {
	marker_location.setLatLng(coords)
	// marker_location = L.marker(coords, markerOptions);
	// Popup se uno clicca sul marker
	marker_location.bindPopup("<div class='text-center'><b>"+cur_result_name+"</b><br>"+cur_result_description);
	// aggiungi il marker sulla mappa
	marker_location.addTo(mymap);
}

function addPathLines(lines) {
	pathLines.addData(lines);
	pathLines.addTo(mymap);
}

function addPathLinesGT(lines) {
	pathLinesGT.addData(lines);
	pathLinesGT.addTo(mymap);
}

function updateButtonsAfterResizeWindow(){
	if (is_keyboard){
		scale_button.remove();
		loc_control.remove();
		map_button.remove();
		settings_button.remove();
		social_button.remove();
	} else {
		scale_button.addTo(mymap);
		loc_control.addTo(mymap);
		map_button.addTo(mymap);
		settings_button.addTo(mymap);
		addSocialButton();
	}
}
