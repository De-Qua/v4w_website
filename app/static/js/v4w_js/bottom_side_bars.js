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
	all_possibilities_div.setAttribute('id', 'all_possibilities');
	if (areWeUsingBottomBar()){
		all_possibilities_div.setAttribute('class', 'scrollable-wrapper row flex-row flex-nowrap');
		all_possibilities_div.setAttribute('style', 'min-height:100%;');
	}
	for (i = 0; i < possibilities.length; i++) {
		var description_dict = possibilities[i].descrizione;
		cur_result_icon = get_icon(description_dict);
		cur_result_title = possibilities[i].nome;
		cur_result_name = possibilities[i].nome;
		cur_result_coords = possibilities[i].coordinate;
		// cur_result_description e un dizionario con tante informazioni:
		// da quello creiamo una string fatta bene
    cur_result_description = get_description_as_string(description_dict);


		card_col = document.createElement('div');
		card_col.setAttribute('class', 'card_column')
		if (areWeUsingBottomBar()){
			card_col.classList.add('col-7','col-sm-5');
		}
		card = document.createElement('div');
		card.setAttribute('class', 'card possibilities_result border border-secondary rounded');
		if (areWeUsingBottomBar()){
			card.setAttribute('style', 'height: 100%;')
		}else{
			card.classList.add('mb-1');
		}
		card.lat = cur_result_coords[0];
		card.lng = cur_result_coords[1];
    card.name = cur_result_name;
    card.description = cur_result_description

		card_header = document.createElement('div');
		card_header.setAttribute('class','card-header p-2');
		/* Versione con icona e titolo in due colonne */
		card_header.innerHTML = '<h6 class="card-title p-1 m-1 row flex-nowrap">'
														+'<div class="col-2 p-0">'
														+cur_result_icon
														+'</div>'
														+'<div class="col-10 p-0 ml-2 align-self-center">'
														+'<strong>'+cur_result_title+'</strong>'
														+'</div>'
														+'</h6>';
		/* versione con icona e titolo in un'unica stringa */
		card_header.innerHTML = '<h6 class="card-title p-1 m-1 row flex-nowrap">'
														+'<div class="col p-0 align-self-center">'
														+cur_result_icon+'&ensp;<strong>'+cur_result_title+'</strong>'
														+'</div>'
														+'</h6>';
		//card_header.onclick = function() {stopPropagation();};
		card_body = document.createElement('div');
		card_body.setAttribute('class','card-body');
		card_body.innerHTML = '<p class="card-text">'+cur_result_description+'</p>';
		if (isTouchDevice){
			card.onclick = function () {
				if (activeCard == this){
					clearHighlight(this);
					fillForm(this);
					submitForm();
					// goToNextStep(getNextStep(this, what_are_we_doing, this.name, searched_end, start_found));
				} else{
          if (activeCard != ''){
            clearHighlight(activeCard);
          }
					activeCard = this;
					showHighlight(this);
          // move the map over the coordinates
          mymap.panTo([this.lat,this.lng]);
				};
			};
		} else {
      // card.onclick = function() {fillForm(this, what_are_we_doing, searched_end, start_found); document.getElementById("form_id").submit();}
			// passare come parametro dict_in_JS (o almeno params_research)
			// card.onclick = function() {goToNextStep(getNextStep(this, what_are_we_doing, this.name, searched_end, start_found));};
			card.onclick = function() {fillForm(this); submitForm();};
			card.onmouseover = function() {showHighlight(this);};
			card.onmouseout = function() {clearHighlight(this);};
		}
		card.appendChild(card_header);
		card.appendChild(card_body);
		card_col.appendChild(card);
		all_possibilities_div.appendChild(card_col);
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
		// passare come parametro params_research (o dict_in_JS)
		var markerNextStep = getNextStep(marker.getLatLng(), what_are_we_doing, cur_result_name, searched_end, start_found)

		marker.bindPopup("<div class='text-center'><b>"+cur_result_name+"</b><br>"+cur_result_description+"<br><a href='"+markerNextStep+"' class='btn btn-sm btn-light v4wbtn' style='font-size: 0.8em;color:inherit;'>Dequa!</a></div>");

		possibilitiesLayer.addLayer(marker).addTo(map);
	}
	document.getElementById("possibilitiesFather").appendChild(all_possibilities_div);
	document.getElementById("possibilitiesFather").setAttribute("style","height:100%;")
	console.log("We are doing: "+ what_are_we_doing);
	if (what_are_we_doing == "address") {
		document.getElementById("search_field_1").value = searched_start;
		document.getElementById("search_field_1").style.backgroundColor = style.getPropertyValue("--dq-red-2");
    console.log('@showPossibilitiesWindow[address]: show X button in first search field');
    nowitstimetoshowtheX('search_field_1_x');
	} else {
		showSecondSearchbar();
		//document.getElementById("search_field_1").value = searched_start;
		//document.getElementById("search_field_2").value = searched_end;
		if (what_are_we_doing == "choosing_start") {
      document.getElementById("search_field_1").value = searched_start;
			document.getElementById("search_field_1").style.backgroundColor = style.getPropertyValue("--dq-red-2");
      document.getElementById("search_field_2").value = searched_end;
		} else if (what_are_we_doing == "choosing_end") {
      document.getElementById("search_field_1").value = start_found.nome;
      document.getElementById("search_field_2").value = searched_end;
			document.getElementById("search_field_2").style.backgroundColor = style.getPropertyValue("--dq-red-2");
		}
    console.log('@showPossibilitiesWindow[choosing_start/choosing_end]: show both X buttons');
    showbothXbuttons();
	}

	showSidebar();
}

function get_description_as_string(description_dict) {
	description_string = 'località';
	if (description_dict['modelName'] == 'Poi'){
			console.log('I m showing a Poi');
			known_type = translate_type(description_dict['type']);
			if (known_type){
				description_string = known_type + '<br><small><i>' + description_dict['address'] + '</i></small>';
			}
			else {
				description_string = '<small><i>' + description_dict['address'] + '</i></small>';
			}
	}
	else if (description_dict['modelName'] == 'Location') {
			console.log('I m showing a Location');
			description_string = description_dict['name'] + "<br>CAP " + description_dict['zipcode'];
	}
	else if (description_dict['modelName'] == 'Neighborhood') {
			description_string = 'Sestiere'+ "<br>CAP " + description_dict['zipcode'];
	}
	else if (description_dict['modelName'] == 'Area') {
			description_string = 'Zona';
	}
	else if (description_dict['modelName'] == 'Street') {
			description_string = 'Campo o Calle' + "<br>" + description_dict['neighborhood'] + ", " + description_dict['zipcode'];
	}
	return description_string;
}

function translate_type(unformatted_type){
	var string_input = String(unformatted_type);
	var descr = '';
	console.log('unformatted_type: ' + unformatted_type);
	if (string_input.includes("ferry")) {
		descr = 'Fermata del vaporetto';
	}
	else if (string_input.includes('pharmacy')) {
		descr = 'Farmacia';
	}
	else if (string_input.includes('restaurant')) {
		descr = 'Ristorante';
	}
	else if (string_input.includes('bank')) {
		descr = 'Banca';
	}
	else if (string_input.includes('bar')) {
		descr = 'Bar';
	}
	else if (string_input.includes('kebab')) {
		descr = 'Kebab';
	}
	else if (string_input.includes('pub')) {
		descr = 'Pub';
	}
	else if (string_input.includes('osteria')) {
		descr = 'Osteria';
	}
	else if (string_input.includes('ice_cream')) {
		descr = 'Gelateria';
	}
	else if (string_input.includes('cafe')) {
		descr = 'Caffè-bar';
	}
	else if (string_input.includes('place_of_worship') || string_input.includes('church')) {
		descr = 'Chiesa';
	}
	return descr;
}

// dalla descrizione del nome scegliamo un'icona appropriata
function get_icon(description_dict){
	console.log('choosing icon for a result of the type: ' + description_dict['modelName']);
	icon = '<i class="fa fa-map-marker" aria-hidden="true"></i>'; // il default marker
	/*if (description_dict['modelName'] == 'Location') {
		icon = '<i class="fa fa-map-pin" aria-hidden="true"></i>';
	}*/
	if (description_dict['modelName'] == 'Street') {
		icon = '<i class="fa fa-road" aria-hidden="true"></i>';
	}
	else if ((description_dict['modelName'] == 'Area') || (description_dict['modelName'] == 'Neighborhood')) {
		icon = '<i class="fa fa-map-o" aria-hidden="true"></i>';
	}
	else if (description_dict['modelName'] == 'Poi') {
		var descr = translate_type(description_dict['type'][0]);
		console.log('choosing icon for ' + descr);
		if (descr == 'Fermata del vaporetto') {
			icon = '<svg width="21" height="23" viewBox="0 0 21 23" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M11.0013 2.64151V3.64151H9.00132V2.64151H11.0013ZM10.0013 9.75151L15.3813 11.5215L17.7713 12.3015L16.6513 16.2715C16.1113 15.9715 15.7113 15.5615 15.5113 15.3315L14.0013 13.6015L12.4913 15.3215C12.1513 15.7215 11.2113 16.6415 10.0013 16.6415C8.79132 16.6415 7.85133 15.7215 7.51133 15.3215L6.00133 13.6015L4.49132 15.3215C4.29133 15.5515 3.89132 15.9515 3.35132 16.2515L2.22132 12.2915L4.62133 11.5015L10.0013 9.75151ZM13.0013 0.64151H7.00133V3.64151H4.00133C2.90133 3.64151 2.00132 4.54151 2.00132 5.64151V10.2615L0.711325 10.6815C0.583079 10.7209 0.463997 10.7855 0.361074 10.8716C0.25815 10.9576 0.173459 11.0634 0.111975 11.1826C0.0504916 11.3019 0.0134544 11.4322 0.00303922 11.5659C-0.00737601 11.6997 0.00904062 11.8342 0.0513249 11.9615L1.95133 18.6415H2.00132C3.60133 18.6415 5.02133 17.7615 6.00133 16.6415C6.98133 17.7615 8.40132 18.6415 10.0013 18.6415C11.6013 18.6415 13.0213 17.7615 14.0013 16.6415C14.9813 17.7615 16.4013 18.6415 18.0013 18.6415H18.0513L19.9413 11.9615C20.0213 11.7015 20.0013 11.4215 19.8813 11.1815C19.7613 10.9415 19.5413 10.7615 19.2813 10.6815L18.0013 10.2615V5.64151C18.0013 4.54151 17.1013 3.64151 16.0013 3.64151H13.0013V0.64151ZM4.00133 9.61151V5.64151H16.0013V9.61151L10.0013 7.64151L4.00133 9.61151ZM14.0013 19.3215C12.7813 20.1715 11.3913 20.6015 10.0013 20.6015C8.61132 20.6015 7.22132 20.1715 6.00133 19.3215C4.78133 20.1715 3.39132 20.6415 2.00132 20.6415H0.00132499V22.6415H2.00132C3.38132 22.6415 4.74133 22.2915 6.00133 21.6515C7.26132 22.2915 8.63132 22.6215 10.0013 22.6215C11.3713 22.6215 12.7413 22.3015 14.0013 21.6515C15.2613 22.3015 16.6213 22.6415 18.0013 22.6415H20.0013V20.6415H18.0013C16.6113 20.6415 15.2213 20.1715 14.0013 19.3215Z" fill="#4A4A4A"/></svg>';
		}
		else if (descr == 'Farmacia') {
			icon = '<i class="fa fa-plus" aria-hidden="true"></i>';
		}
		else if (descr == 'Ristorante') {
			icon = '<i class="fas fa-utensils"></i>'; // ristorante
		}
		else if (descr == 'Pizzeria') {
			icon = '<i class="fas fa-pizza-slice"></i>'; //pizzeria
		}
		else if (descr == 'Gelateria') {
			icon = '<i class="fa fa-cutlery" aria-hidden="true"></i>';
		}
		else if (descr == 'Bar') {
			icon = '<i class="fa fa-beer" aria-hidden="true"></i>';
		}
		else if (descr == 'Negozio') {
			icon = '<i class="fas fa-shopping-bag"></i>'; //negozio
		}
		else if (descr == 'Caffè-bar') {
			icon = '<i class="fa fa-coffee" aria-hidden="true"></i>';
		}
		else if (descr == 'Chiesa') {
			icon = '<i class="fa fa-home" aria-hidden="true"></i>';
		}
	}

	return icon
}

function fillForm(element) {
	console.log("I fill the form with :");
	console.log(element);
	var what_are_we_doing = findWhatWeKnow().what_we_know;
	if (what_are_we_doing == "choosing_start" || what_are_we_doing == "address") {
		$("#search_field_1").val(element.name);
		$("#hidden_start_coord").val(""+element.lat+","+element.lng);
	} else if ( what_are_we_doing == "choosing_end") {
		$("#search_field_2").val(element.name);
		$("#hidden_end_coord").val(""+element.lat+","+element.lng);
	}
	return;
}

function submitForm() {
	$('#ricerca_ind').submit();
	return true
}

function getNextStep(element, what_are_we_doing, cur_result_name, searched_end, start_found) {
	var clicked_coords = [element.lat, element.lng];
	var new_site_to_go = "";
  var stringBoxes = retrieveBoxesSituationAsAString();
	// check if there was an already selected end
	var end_coord = dict_in_JS.params_research.end_coord;
	if (what_are_we_doing == "choosing_start" || what_are_we_doing == "address") {
		new_site_to_go = "/?partenza="+encodeURI(cur_result_name).replace(/%20/g, "+")+"&start_coord=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")&arrivo="+encodeURI(searched_end).replace(/%20/g, "+")+"&end_coord="+end_coord+stringBoxes;
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
		new_site_to_go = "/?partenza="+encodeURI(strt_name).replace(/%20/g, "+")+"&start_coord="+encodeURI(strt_coords)+")&arrivo="+encodeURI(cur_result_name).replace(/%20/g, "+")+"&end_coord=LatLng("+clicked_coords[0]+", "+clicked_coords[1]+")"+stringBoxes;
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
	if ((window.innerWidth < 812) && (window.innerWidth <= window.innerHeight)){
		return true;
	} else{
		return false;
	}
}

function clearAllResults() {
	removeSidebar();
	removePossibilitiesLayer();
	removePathLayer();
	removeMarkerLocation();
}

function removeSidebar(){
  $("#possibilitiesFather").empty();
	hideSidebar();
	$("#show-sidebar").hide();
}

function removePossibilitiesLayer(){
	highlight.clearLayers();
	possibilitiesLayer.eachLayer(function(layer) {
		possibilitiesLayer.removeLayer(layer);
	});
	try{
		mymap.removeLayer(polygon);
	} catch(e){
		console.log("no polygon");
	};
}

function removePathLayer(){
	pathLines.clearLayers();
	pathGroup.eachLayer(function(layer) {
		mymap.removeLayer(layer);
	});
}

function removeMarkerLocation(){
	try{
		mymap.removeLayer(marker_location);
	} catch(e){
		console.log("no marker of single location")
	};
}

function isSidebarEmpty(){
	possibilities_in_sidebar = $("#possibilitiesFather")[0].childElementCount > 0;
	res_land_in_sidebar = $("#percorso_terra").css('display') != 'none';
	res_water_in_sidebar = $("#percorso_acqua").css('display') != 'none';
	res_address_in_sidebar = $("#single_address").css('display') != 'none';
	return !(possibilities_in_sidebar || res_land_in_sidebar || res_water_in_sidebar || res_address_in_sidebar)
}



function updateSidebarAfterResizeWindow() {
	if (!isSidebarEmpty()) {
		if (is_keyboard){
			console.log("nascondo la sidebar");
			hideSidebar();
			console.log("nascondo il bottone");
			document.getElementById("show-sidebar").style.display = 'none';
		} else {
			console.log("Nell'else");
			document.getElementById("show-sidebar").style.display = 'block';
			// showSidebar();
		}
	}
	console.log("View aggiornata!")
}

function changePositionSidebar() {
	// It is bottombar but it is still on the side
	if (!isSidebarEmpty()){
		if ($("#sidebar").css('display') != 'none') {
			showSidebar();
		} else {
			hideSidebar();
		}
	}
	console.log("change position of sidebar")
	if (is_bottom_bar) {
		$("#all_possibilities").addClass('scrollable-wrapper row flex-row flex-nowrap');
		$("#all_possibilities").css('minHeight','100%');
		$(".card_column").addClass('col-7 col-sm-5');
		$(".possibilities_result").removeClass('mb-1').css('height','100%');

	} else { // Is is sidebar but is is still on the bottom
		$("#all_possibilities").removeClass('scrollable-wrapper row flex-row flex-nowrap');
		$("#all_possibilities").css('minHeight','');
		$(".card_column").removeClass('col-7 col-sm-5');
		$(".possibilities_result").addClass('mb-1').css('height','');
	}
}
