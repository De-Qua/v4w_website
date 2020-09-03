/* Licensed under AGPLv3
/*!
* Venessia4Working Javascripts
* Copyleft 2020

*/

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
      // card.onclick = function() {fillForm(this, what_are_we_doing, searched_end, start_found); document.getElementById("form_id").submit();}
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
