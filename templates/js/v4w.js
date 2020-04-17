/*!
  * Venessia4Working Javascripts
  * Copyright 2020
  * Licensed under MIT
  */

	/* Open a window visualizing a help message on how to make the correct search.
		In the window a button to close it should be available, calling closeHelpWindow().
		The actual happening is just making the element with id "helpwindow" visible.
	*/
	function showHelpWindow() {
		document.getElementById("helpwindow").style.display = "block";
		document.getElementById("searchbar").style.display = "none";
		var thingstoBeHidden = document.getElementsByClass("onlyMap");
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
		var thingstoBeShown = document.getElementsByClass("onlyMap");
		for (i = 0; i < thingstoBeShown.length; i++) {
			thingstoBeShown[i].style.display = "inline";
		}
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
