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
	if (currentMap == "osm") {
		mymap.attributionControl._attributions = {};
		var Stamen_Watercolor = L.tileLayer('https://stamen-tiles-{s}.a.ssl.fastly.net/watercolor/{z}/{x}/{y}.{ext}', {
			attribution: 'Map tiles by <a href="http://stamen.com">Stamen Design</a>, <a href="http://creativecommons.org/licenses/by/3.0">CC BY 3.0</a> &mdash; Map data &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
			subdomains: 'abcd',
			minZoom: 1,
			maxZoom: 16,
			ext: 'jpg'
		}).addTo(mymap);
		whichmap = "water";
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
}

function hideSecondSearchbar() {
	document.getElementById("searchbtn").style.display = "inline";
	document.getElementById("add-searchfield").style.display = "inline";
	document.getElementById("btn-plus").style.display = "block";
	document.getElementById("second-search-field").style.display = "none";
	document.getElementById("calc-button").style.display = "none";
	document.getElementById("nav_buttons").style.display = "none";
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
