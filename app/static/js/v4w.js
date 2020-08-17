//import L from 'leaflet';
//import Modal from '../../templates/index';
 /*!
  * Venessia4Working Javascripts
  * Copyleft 2020
  * Licensed under AGPLv3
  */

/* Function to detect if a device is touch or not.
	All the credits to https://stackoverflow.com/questions/4817029/whats-the-best-way-to-detect-a-touch-screen-device-using-javascript/4819886#4819886
*/
function is_touch_device() {

    var prefixes = ' -webkit- -moz- -o- -ms- '.split(' ');

    var mq = function (query) {
        return window.matchMedia(query).matches;
    }

    if (('ontouchstart' in window) || window.DocumentTouch && document instanceof DocumentTouch) {
        return true;
    }

    // include the 'heartz' as a way to have a non matching MQ to help terminate the join
    // https://git.io/vznFH
    var query = ['(', prefixes.join('touch-enabled),('), 'heartz', ')'].join('');
    return mq(query);

}

var isTouchDevice = is_touch_device();
console.log("Is touch device? "+isTouchDevice);
/* Open a window visualizing a help message on how to make the correct search.
	In the window a button to close it should be available, calling closeHelpWindow().
	The actual happening is just making the element with id "helpwindow" visible.
*/
// function showHelpWindow() {
// 	hideSettingsWindow();
// 	document.getElementById("helpwindow").style.display = "block";
// 	document.getElementById("searchbar").style.display = "none";
// 	var thingstoBeHidden = document.getElementsByClassName("onlyMap");
// 	for (i = 0; i < thingstoBeHidden.length; i++) {
// 		thingstoBeHidden[i].style.display = "none";
// 	}
// }

/* Close the window visualizing a help message on how to make the correct search.
	The actual happening is just making the element with id "helpwindow" invisible.
*/
// function closeHelpWindow() {
// 	document.getElementById("mapid").style.opacity = 1.0;
// 	document.getElementById("helpwindow").style.display = "none";
// 	document.getElementById("searchbar").style.display = "block";
// 	var thingstoBeShown = document.getElementsByClassName("onlyMap");
// 	for (i = 0; i < thingstoBeShown.length; i++) {
// 		thingstoBeShown[i].style.display = "inline";
// 	}
// }

/* Open a window visualizing a help message on how to make the correct search.
	In the window a button to close it should be available, calling closeHelpWindow().
	The actual happening is just making the element with id "helpwindow" visible.
*/
// function showFeedbackWindow() {
// 	hideSettingsWindow();
// 	document.getElementById("feedbackwindow").style.display = "block";
// 	document.getElementById("searchbar").style.display = "none";
// 	var thingstoBeHidden = document.getElementsByClassName("onlyMap");
// 	for (i = 0; i < thingstoBeHidden.length; i++) {
// 		thingstoBeHidden[i].style.display = "none";
// 	}
// }

/* Close the window visualizing a help message on how to make the correct search.
	The actual happening is just making the element with id "helpwindow" invisible.
*/
// function changeFeedbackandClose() {
// 	console.log("Prima: ");
// 	console.log(feedbackjs);
// 	feedbackjs = 0;
// 	console.log("Dopo: ")
// 	console.log(feedbackjs);
// 	toggleFeedbackWindowLayout();
// 	closeFeedbackWindow();
// }
//
// function toggleFeedbackWindowLayout() {
// 	if (feedbackjs == 0) {
// 		document.getElementById("formid").style.display = "block";
// 		document.getElementById("grazieid").style.display = "none";
// 	}
// 	else if (feedbackjs == 1) {
// 		showFeedbackWindow();
// 		document.getElementById("formid").style.display = "none";
// 		document.getElementById("grazieid").style.display = "block";
// 	}
// }

function closeFeedbackWindow() {
	document.getElementById("mapid").style.opacity = 1.0;
	document.getElementById("feedbackwindow").style.display = "none";
	document.getElementById("searchbar").style.display = "block";
	var thingstoBeShown = document.getElementsByClassName("onlyMap");
	for (i = 0; i < thingstoBeShown.length; i++) {
		thingstoBeShown[i].style.display = "inline";
	}
}

function setValuesInFeedbackWindow(JSdict) {
  if (JSdict == "None"){
    return
  } else if ("error" in JSdict){
    return
  } else {
    // values we found
    var all_found_start = [];
    for (found_start of JSdict.partenza){
      all_found_start.push(found_start.nome);
    };
    var all_found_end = [];
    for (found_end of JSdict.arrivo){
      all_found_end.push(found_end.nome);
    };

    // determine what to show
    if(JSdict.modus_operandi==0 || (JSdict.modus_operandi==2 && JSdict.arrivo == "no_end")) {
      // show div
      document.getElementById("form-search-address").style.display = "flex";
      document.getElementById("form-found-address").style.display = "flex";
      // write values
      document.getElementById("searched_string").value = JSdict.searched_start;
      document.getElementById("found_string").value = all_found_start.join("; ");
    } else if (JSdict.modus_operandi==1 || JSdict.modus_operandi==2){
      // show div
      document.getElementById("found_start").value = all_found_start.join("; ");
      document.getElementById("found_end").value = all_found_end.join("; ");
      document.getElementById("form-search-path").style.display = "flex";
      document.getElementById("form-found-path").style.display = "flex";
      // write values
      document.getElementById("searched_start").value = JSdict.searched_start;
      document.getElementById("searched_end").value = JSdict.searched_end;
      document.getElementById("found_start").value = all_found_start.join("; ");
      document.getElementById("found_end").value = all_found_end.join("; ");
    } else {
      // do nothing
      return
    }
  }
}

function searchAgain() {
    document.getElementById("trovato").style.display = "none";
	document.getElementById("searchbar").style.display = "block";
}

function changeMap(currentMap) {
	console.log("changing map.. from " + currentMap)
	if (currentMap == "OpenStreetMap") {
		whichmap = "ESRIMap";
	} else if (currentMap == 'ESRIMap') {
		whichmap = "OpenStreetMap";
	} else {
		whichmap = "OpenStreetMap";
	}

	mymap.removeLayer(baseMaps[currentMap]);
	baseMaps[whichmap].addTo(mymap);

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
	// document.getElementById("searchbtn").style.display = "none";
	document.getElementById("add-searchfield").style.display = "none";
	document.getElementById("btn-plus").style.display = "none";
	document.getElementById("second-search-field").style.display = "block";
	document.getElementById("nav_buttons").style.display = "block";
	// document.getElementById("start_from_my_location").style.display = "block";
}

function hideSecondSearchbar() {
	// document.getElementById("searchbtn").style.display = "block";
	document.getElementById("add-searchfield").style.display = "block";
	document.getElementById("btn-plus").style.display = "block";
	document.getElementById("second-search-field").style.display = "none";
	document.getElementById("nav_buttons").style.display = "none";
	// document.getElementById("start_from_my_location").style.display = "none";
	document.getElementById("search_field_2").value = "";
	return false;
}

function swapDirections() {
  var field_1 = document.getElementById('search_field_1').value;
  document.getElementById('search_field_1').value = document.getElementById('search_field_2').value;
  document.getElementById('search_field_2').value = field_1;
}

function drawPreLoader() {
	console.log("set opacity..")
	document.getElementById("mapid").style.opacity = 0.3;
	console.log("visualizing div..")
	document.getElementById("loading").style.display = "inline";
	// console.log("drawing preloader..")
	//document.getElementById("loading_gif").src = "/static/assets/loading.gif";
	console.log("done!")
	// setTimeout(console.log("now, ok"), 1000);
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

var activeCard = '';
/* show possibilities window / differnet mobile and desktop */
function showPossibilitiesWindow(possibilities, markerOptions, map, what_are_we_doing, searched_start, searched_end, start_found) {
	var cur_result_coords = '';
	var div ='';
	var cur_result_name = '';
  var cur_result_description = '';
	all_possibilities_div = document.createElement('div');
	if (areWeUsingBottomBar()){
		all_possibilities_div.setAttribute('class', 'scrollable-wrapper row flex-row flex-nowrap');
	}
	for (i = 0; i < possibilities.length; i++) {
		cur_result_name = possibilities[i].nome;
		cur_result_coords = possibilities[i].coordinate;
    cur_result_description = possibilities[i].descrizione;
		card = document.createElement('div');
		if (areWeUsingBottomBar()){
			card.setAttribute('class', 'card possibilities_result col-6');
		}else{
			card.setAttribute('class', 'card possibilities_result');
		}
		card.lat = cur_result_coords[0];
		card.lng = cur_result_coords[1];
    card.name = cur_result_name;
    card.description = cur_result_description;

		card_header = document.createElement('div');
		card_header.setAttribute('class','card-header');
		card_header.innerHTML = '<div class="row">'
														+'<div class="col-12 align-self-center"><h6 class="card-title"><strong>'+cur_result_name+'</strong></h6></div>'
														//+'<div class="col-1 align-self-center " style="z-index: 10"><button class="btn btn-sm btn-light v4wbtn pull-right" onclick="showResultLocation()"><i class="fa fa-map-marker"></i></button></div>'
														+'</div>';
		//card_header.onclick = function() {stopPropagation();};
		card_body = document.createElement('div');
		card_body.setAttribute('class','card-body');
		card_body.innerHTML = '<h6 class="card-subtitle text-muted">Descrizione:</h6>'
													+ '<p class="card-text">'+cur_result_description+'</p>';
		if (isTouchDevice){
			card.onclick = function () {
				if (activeCard == this){
					clearHighlight(this);
					goToNextStep(getNextStep(this, what_are_we_doing, this.name, searched_end, start_found));
				} else{
          if (activeCard != ''){
            clearHighlight(activeCard);
          }
					activeCard = this;
					showHighlight(this);
          // move the map over the coordinates
          mymap.panTo([this.lat,this.lng])
				};
			};
		} else {
			card.onclick = function() {goToNextStep(getNextStep(this, what_are_we_doing, this.name, searched_end, start_found));};
			card.onmouseover = function() {showHighlight(this)};
			card.onmouseout = function() {clearHighlight(this);};
		}
		card.appendChild(card_header)
		card.appendChild(card_body)
		all_possibilities_div.appendChild(card);
		// div = document.createElement('div');
		// div.setAttribute('class', 'possibilities_result');
		// //div.setAttribute('class', '');
		// //dev.setAttribute('class', 'card');
		// div.setAttribute('coords',cur_result_coords)
		// div.coords = cur_result_coords;
		// div.innerHTML = "<b>"+cur_result_name+"</b><br>"+cur_result_coords; // repr
		// div.onclick = function() { goToNextStep(this, what_are_we_doing, searched_start, searched_end, start_found); };
		// console.log(div);
		console.log("for this div we searched "+searched_end);
		//document.getElementById("possibilitiesFather").appendChild(div);
		var curMarkerOptions = markerOptions;
		curMarkerOptions["title"] = cur_result_name;
		var marker = L.marker([cur_result_coords[0], cur_result_coords[1]],curMarkerOptions);

		// markerPopup.setLatLng([cur_result_coords[0], cur_result_coords[1]]);
		var markerNextStep = getNextStep(marker.getLatLng(), what_are_we_doing, cur_result_name, searched_end, start_found)

		marker.bindPopup("<div class='text-center'><b>"+cur_result_name+"</b><br>"+cur_result_description+"<br><a href='"+markerNextStep+"' class='btn btn-sm btn-light v4wbtn' style='font-size: 0.8em;color:inherit;'>Dequa!</a></div>");

		possibilitiesLayer.addLayer(marker).addTo(map);
	}
	document.getElementById("possibilitiesFather").appendChild(all_possibilities_div);
	console.log("We are doing: "+ what_are_we_doing);
	if (what_are_we_doing == "address") {
		document.getElementById("search_field_1").value = searched_start;
		document.getElementById("search_field_1").style.backgroundColor = "#f44";
    console.log('@showPossibilitiesWindow[address]: show X button in first search field');
    nowitstimetoshowtheX('search_field_1_x');
	} else {
		showSecondSearchbar();
		//document.getElementById("search_field_1").value = searched_start;
		//document.getElementById("search_field_2").value = searched_end;
		if (what_are_we_doing == "choosing_start") {
      document.getElementById("search_field_1").value = searched_start;
			document.getElementById("search_field_1").style.backgroundColor = "#f44";
      document.getElementById("search_field_2").value = searched_end;
		} else if (what_are_we_doing == "choosing_end") {
      document.getElementById("search_field_1").value = start_found.nome;
      document.getElementById("search_field_2").value = searched_end;
			document.getElementById("search_field_2").style.backgroundColor = "#f44";
		}
    console.log('@showPossibilitiesWindow[choosing_start/choosing_end]: show both X buttons');
    showbothXbuttons();
	}

	showSidebar();
}

// mette la spunta
function checkTheBoxesThatNeedToBeChecked(dict_in_JS) {
  var checkBoxesDict = dict_in_JS.params_research;

  if (checkBoxesDict.by_boat == "on") {
    document.getElementById("boat_setting").checked = true;
  }
  if (checkBoxesDict.less_bridges == "on") {
    document.getElementById("less_bridges_setting").checked = true;
  }
  if (checkBoxesDict.walking == "on") {
    document.getElementById("walk_setting").checked = true;
  }
}

function retrieveBoxesSituationAsAString() {
  var by_boat_checked = document.getElementById("boat_setting").checked ? "&boat=on" : "&boat=off";
  var less_bridges_checked = document.getElementById("walk_setting").checked ? "&lazy=on" : "&lazy=off";
  return by_boat_checked + less_bridges_checked;
}

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
		new_site_to_go = "/?partenza="+escape(strt_name).replace(/%20/g, "+")+"&start_coord=LatLng("+strt_coords[0]+", "+strt_coords[1]+")&arrivo="+escape(cur_result_name).replace(/%20/g, "+")+"&end_coord=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")"+stringBoxes;
    // document.getElementById("search_field_1").value = strt_name
    // document.getElementById("start_coord").value = "LatLng("+strt_coords[0]+", "+strt_coords[1]+")";
    // document.getElementById("search_field_2").value = cur_result_name
    // document.getElementById("end_coord").value = "LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")";
  }
	return new_site_to_go;
}

function goToNextStep(nextStep) {
  drawPreLoader()
	window.location = nextStep;
  // document.getElementById("ricerca_ind").submit()
}
// function goToNextStep(divElement, what_are_we_doing, searched_start, searched_end, start_found) {
// 	console.log("redirecting..");
// 	console.log(divElement);
// 	var clicked_coords = [divElement.lat, divElement.lng];
// 	//var clicked_coords2 = divElement.attributes.coords;
// 	console.log("cercato"+searched_end);
// 	console.log("what are we doing:"+what_are_we_doing);
// 	//console.log("cliccato: " + clicked_coords + ", " + clicked_coords2);
// 	if (what_are_we_doing == "choosing_start" || what_are_we_doing == "address") {
// 		console.log("starting point was chosen!")
// 		var new_site_to_go = "/?partenza=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")&arrivo="+searched_end+"#dequa";
// 		window.location = new_site_to_go;
// 	}
// 	else if (what_are_we_doing == "choosing_end") {
// 		console.log("end point was chosen!")
// 		console.log("start"+start_found)
//
// 		var strt_coords = start_found.coordinate;
// 		var new_site_to_go = "/?partenza=LatLng("+strt_coords[0]+", "+strt_coords[1]+")&arrivo=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")";
// 		window.location = new_site_to_go;
// 	}
// }

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

function copyStartingPosition(address_string) {
	document.getElementById('search_field_1').value = address_string
}

function copyEndingPosition(address_string) {
	showSecondSearchbar();
	document.getElementById('search_field_2').value = address_string
}

function addMarkerStart(latlng) {
  marker_start.setLatLng(latlng);
  marker_start.addTo(mymap);
}

function addMarkerEnd(latlng) {
  marker_end.setLatLng(latlng);
  marker_end.addTo(mymap);
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

function animateSidebar() {
  $("#sidebar").animate({
    width: "toggle"
  }, 350, function() {
    document.getElementById("mapid").invalidateSize();
  });
}

function hideSidebar(){
	document.getElementById("sidebar").style.display = 'none';
	document.getElementById("show-sidebar").style.display = 'block';
	restoreMapForBottomBar();
	mymap.invalidateSize();
}

function showSidebar(){
	document.getElementById("sidebar").style.display = 'block';
	document.getElementById("show-sidebar").style.display = 'none';
	shrinkMapForBottomBar();
	mymap.invalidateSize();
	//animateSidebar();
}

function shrinkMapForBottomBar(){
	if (areWeUsingBottomBar()){
		console.log("Let's shrink the map size");
		document.getElementById("mapcontainer").classList.add('shrinkedMapForBottomBar');
	}
}

function restoreMapForBottomBar(){
	if (areWeUsingBottomBar()){
		console.log("Let's restore the map size");
		document.getElementById("mapcontainer").classList.remove("shrinkedMapForBottomBar")
	}
}

function areWeUsingBottomBar(){
	if ((window.innerWidth < 812) && (window.innerWidth < window.innerHeight)){
		return true;
	} else{
		return false;
	}
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

// mother function:
// when user is typing we need to clear the hidden field and show the x
// is this robust enough?
// TODO: check if oninput is always called in special cases
function useristypingin(field_id) {
  console.log("user is typing in " + field_id);
  var button_id = field_id + "_x";
  clearhiddeninput(field_id);
  nowitstimetoshowtheX(button_id);
}

function clearhiddeninput(field_id) {
  console.log("clearing hidden field for " + field_id);
  if (field_id == 'search_field_1') {
    document.getElementById('hidden_start_coord').value='';
    console.log('cleared hidden start');
  }
  if (field_id == 'search_field_2') {
    document.getElementById('hidden_end_coord').value='';
    console.log('cleared hidden end');
  }
  console.log('finished, if no print of start or end, nothing happened!')
}

// clear the text of a field (gives as input the field id!)
function clearField(field_id) {
  document.getElementById(field_id).value = '';
  console.log("cleared " + field_id + " field");
  var button_id = field_id + "_x";
  hidefornowtheX(button_id);
}
// but we want the X to show only when something was typed in!
// here also with jQuery possible --> https://stackoverflow.com/questions/13828450/html-catch-event-when-user-is-typing-into-a-text-input
function nowitstimetoshowtheX(button_id) {
  document.getElementById(button_id).style.display = "inline";
  console.log("showing " + button_id + " button");
}
function hidefornowtheX(button_id) {
  document.getElementById(button_id).style.display = "none";
  console.log("hiding " + button_id + " button");
}
function hidebothXbuttons() {
  hidefornowtheX('search_field_1_x');
  hidefornowtheX('search_field_2_x');
}
function showbothXbuttons() {
  nowitstimetoshowtheX('search_field_1_x');
  nowitstimetoshowtheX('search_field_2_x');
}
function toggleXbuttons() {
  if (document.getElementById('search_field_1').value.length > 0) {
    nowitstimetoshowtheX('search_field_1_x');
  }
  else {
    hidefornowtheX('search_field_1_x');
  }
  if (document.getElementById('search_field_2').value.length > 0) {
    nowitstimetoshowtheX('search_field_2_x');
  }
  else {
    hidefornowtheX('search_field_2_x');
  }
}
