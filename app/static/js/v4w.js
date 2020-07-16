//import L from 'leaflet';
//import Modal from '../../templates/index';
 /*!
  * Venessia4Working Javascripts
  * Copyleft 2020
  * Licensed under AGPLv3
  */


/* Open a window visualizing a help message on how to make the correct search.
	In the window a button to close it should be available, calling closeHelpWindow().
	The actual happening is just making the element with id "helpwindow" visible.
*/
function showHelpWindow() {
	hideSettingsWindow();
	document.getElementById("helpwindow").style.display = "block";
	document.getElementById("searchbar").style.display = "none";
	var thingstoBeHidden = document.getElementsByClassName("onlyMap");
	for (i = 0; i < thingstoBeHidden.length; i++) {
		thingstoBeHidden[i].style.display = "none";
	}
}

/* Close the window visualizing a help message on how to make the correct search.
	The actual happening is just making the element with id "helpwindow" invisible.
*/
function closeHelpWindow() {
	document.getElementById("mapid").style.opacity = 1.0;
	document.getElementById("helpwindow").style.display = "none";
	document.getElementById("searchbar").style.display = "block";
	var thingstoBeShown = document.getElementsByClassName("onlyMap");
	for (i = 0; i < thingstoBeShown.length; i++) {
		thingstoBeShown[i].style.display = "inline";
	}
}

/* Open a window visualizing a help message on how to make the correct search.
	In the window a button to close it should be available, calling closeHelpWindow().
	The actual happening is just making the element with id "helpwindow" visible.
*/
function showFeedbackWindow() {
	hideSettingsWindow();
	document.getElementById("feedbackwindow").style.display = "block";
	document.getElementById("searchbar").style.display = "none";
	var thingstoBeHidden = document.getElementsByClassName("onlyMap");
	for (i = 0; i < thingstoBeHidden.length; i++) {
		thingstoBeHidden[i].style.display = "none";
	}
}

/* Close the window visualizing a help message on how to make the correct search.
	The actual happening is just making the element with id "helpwindow" invisible.
*/
function changeFeedbackandClose() {
	console.log("Prima: ");
	console.log(feedbackjs);
	feedbackjs = 0;
	console.log("Dopo: ")
	console.log(feedbackjs);
	toggleFeedbackWindowLayout();
	closeFeedbackWindow();
}

function toggleFeedbackWindowLayout() {
	if (feedbackjs == 0) {
		document.getElementById("formid").style.display = "block";
		document.getElementById("grazieid").style.display = "none";
	}
	else if (feedbackjs == 1) {
		showFeedbackWindow();
		document.getElementById("formid").style.display = "none";
		document.getElementById("grazieid").style.display = "block";
	}
}

function closeFeedbackWindow() {
	document.getElementById("mapid").style.opacity = 1.0;
	document.getElementById("feedbackwindow").style.display = "none";
	document.getElementById("searchbar").style.display = "block";
	var thingstoBeShown = document.getElementsByClassName("onlyMap");
	for (i = 0; i < thingstoBeShown.length; i++) {
		thingstoBeShown[i].style.display = "inline";
	}
}

function searchAgain() {
    document.getElementById("trovato").style.display = "none";
	document.getElementById("searchbar").style.display = "block";
}

function changeMap(currentMap) {
	console.log("changing map.. from " + currentMap)
	if (currentMap == "osm") {
		mymap.attributionControl._attributions = {};
		var Esri_WorldImagery = L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
			attribution: 'DeQua | Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
			maxZoom: 13,
		}).addTo(mymap);
		// var Stamen_Watercolor = L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.{ext}', {
		// 	attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
		// 	subdomains: 'abcd',
		// 	minZoom: 10,
		// 	maxZoom: 16,
		// 	ext: 'jpg'
		// }).addTo(mymap);
		whichmap = "esri";
	}
	else {
		mymap.attributionControl._attributions = {};
		var OpenStreetMap_DE = L.tileLayer('https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', {
		maxZoom: 20,
		zoomControl: false,
		attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
		}).addTo(mymap);
		whichmap = "osm";
	}
	console.log("to " + whichmap)
}

function locateUser(map, marker, circle) {
	map.locate({setView: false, watch: false}) /* This will return map so you can do chaining */
		.on('locationfound', function(e){
				marker = L.marker([e.latitude, e.longitude]).bindPopup('Your are here :)');
				circle = L.circle([e.latitude, e.longitude], e.accuracy/2, {
						weight: 1,
						color: '#add8e6',
						fillColor: '#add8e6',
						fillOpacity: 0.2
				});
				map.addLayer(marker);
				map.addLayer(circle);
		})
	 .on('locationerror', function(e){
				console.log(e);
				alert("Location access denied.");
		});
}

/* Show the second search bar field - to calculate the path */
function showSecondSearchbar() {
	document.getElementById("searchbtn").style.display = "none";
	document.getElementById("add-searchfield").style.display = "none";
	document.getElementById("btn-plus").style.display = "none";
	document.getElementById("second-search-field").style.display = "inline";
	document.getElementById("calc-button").style.display = "inline";
	document.getElementById("nav_buttons").style.display = "inline";
	document.getElementById("start_from_my_location").style.display = "inline";
}

function hideSecondSearchbar() {
	document.getElementById("searchbtn").style.display = "inline";
	document.getElementById("add-searchfield").style.display = "inline";
	document.getElementById("btn-plus").style.display = "block";
	document.getElementById("second-search-field").style.display = "none";
	document.getElementById("calc-button").style.display = "none";
	document.getElementById("nav_buttons").style.display = "none";
	document.getElementById("start_from_my_location").style.display = "none";
	document.getElementById("search_field_2").value = "";
	return false;
}

function drawPreLoader() {
	console.log("set opacity..")
	document.getElementById("mapid").style.opacity = 0.3;
	console.log("visualizing div..")
	document.getElementById("loading").style.display = "inline";
	console.log("drawing preloader..")
	document.getElementById("loading_gif").src = "/static/assets/loading.gif";
	console.log("done!")
	setTimeout(console.log("now, ok"), 1000);
	return true;
}

function showSettingsWindow() {
	document.getElementById("mapid").style.opacity = 0.3;
	document.getElementById("dequa_setting_window").style.display = "inline";
}

function hideSettingsWindow() {
	document.getElementById("mapid").style.opacity = 1.0;
	document.getElementById("dequa_setting_window").style.display = "none";
}

function showResultsWindow(result_type) {
	if (window.innerWidth > 1000) {
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
	}
}

function showPossibilitiesWindow(possibilities, markerOptions, map, what_are_we_doing, searched_start, searched_end, start_found) {
	var cur_result_coords = '';
	var div ='';
	var cur_result_name = '';
	for (i = 0; i < possibilities.length; i++) {
		cur_result_name = possibilities[i].nome;
		cur_result_coords = possibilities[i].coordinate;
		div = document.createElement('div');
		div.setAttribute('class', 'possibilities_result');
		div.setAttribute('coords',cur_result_coords)
		div.coords = cur_result_coords;
		div.innerHTML = "<b>"+cur_result_name+"</b><br>"+cur_result_coords; // repr
		div.onclick = function() { goToNextStep(this, what_are_we_doing, searched_start, searched_end, start_found); };
		console.log(div);
		document.getElementById("possibilitiesFather").appendChild(div);
		L.marker([cur_result_coords[0], cur_result_coords[1]], markerOptions).addTo(map);
	}
	document.getElementById("searchbar").style.display = "none";
	if (what_are_we_doing == "address") {
		document.getElementById("cercato").innerHTML = searched_start;
	}
	if (what_are_we_doing == "choosing_start") {
		document.getElementById("cercato").innerHTML = searched_start;
	}
	if (what_are_we_doing == "choosing_end") {
		document.getElementById("cercato").innerHTML = searched_end;
	}
	document.getElementById("map_type_btn").style.display = "none";
	document.getElementById("possibilities_search").style.display = 'inline';
}

function goToNextStep(divElement, what_are_we_doing, searched_start, searched_end, start_found) {
	console.log("redirecting..");
	console.log(divElement);
	var clicked_coords = divElement.coords;
	var clicked_coords2 = divElement.attributes.coords;
	console.log("cliccato: " + clicked_coords + ", " + clicked_coords2);
	if (what_are_we_doing == "address") {
		var new_site_to_go = "/?partenza=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")&arrivo=";
		window.location = new_site_to_go;
	}
	else if (what_are_we_doing == "choosing_start") {
		console.log("starting point was chosen!")
		var new_site_to_go = "/?partenza=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")&arrivo="+searched_end;
		window.location = new_site_to_go;
	}
	else if (what_are_we_doing == "choosing_end") {
		console.log("end point was chosen!")
		console.log(start_found)

		var strt_coords = start_found.coordinate;
		var new_site_to_go = "/?partenza=LatLng("+strt_coords[0]+", "+strt_coords[1]+")&arrivo=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")";
		window.location = new_site_to_go;
	}
}

function closeResultsWindow() {
	document.getElementById("results_search").style.display = "none";
	document.getElementById("single_address").style.display = "none";
	document.getElementById("percorso").style.display = "none";
	document.getElementById("weird").style.display = "none";
}

function copyStartingPosition(address_string) {
	document.getElementById('search_field_1').value = address_string
}

function copyEndingPosition(address_string) {
	showSecondSearchbar();
	document.getElementById('search_field_2').value = address_string
}

function copyMyPositionAsStart(map) {
	map.locate({setView: false, watch: false}) /* This will return map so you can do chaining */
		.on('locationfound', function(e){
				document.getElementById('search_field_1').value = e.latlng.toString();
		})
	 .on('locationerror', function(e){
				console.log(e);
				alert("Location access denied.");
		});
}
