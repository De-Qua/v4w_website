/* Licensed under AGPLv3
 /*!
  * Venessia4Working Javascripts
  * Copyleft 2020

  */

// GESTIONE INPUT
//
// quando l'utente scrive qualcosa (non quando ha il focus), succedono cose:
//  - la x appare
//  - il campo "segreto" viene resettato
//
// ### Cos'e il campo "segreto"? visto che il bottone e un form, ho agigunto un campo nascosto (senza prendere spazio)
// che contiene le coordinate. quando uno cerca premendo il bottone, il form viene inviato, e visto che il campo nascosto
// si chiama start_coord (e e end_coord l'altro) viene inviato esattamente come ci aspettiamo, e il python lo puo gestire
//
// ### come sappiamo quando l'utente scrive?
// usiamo il metodo oninput - sembra funzionare molto bene, o almeno, esattamente come serve a noi
// (se una persona scrive, poi clicca sulla mappa, poi di nuovo sulla barra, non viene rilanciato)
// resta da testare nei casi limiti e nel telefono, per capire se fa cose strane

// mother function:
// when user is typing we need to clear the hidden field and show the x
// is this robust enough?
// TODO: check if oninput is always called in special cases
// here also with jQuery possible --> https://stackoverflow.com/questions/13828450/html-catch-event-when-user-is-typing-into-a-text-input
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

function clear_hidden_start() {
  console.log("search_field_1 listeren triggered");
  document.getElementById("hidden_start_coord").value = '';
}
function clear_hidden_end() {
  console.log("search_field_2 listeren triggered");
  document.getElementById("hidden_end_coord").value = '';
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


// clear the text of a field (gives as input the field id!)
function clearField(field_id) {
  document.getElementById(field_id).value = '';
  console.log("cleared " + field_id + " field");
  var button_id = field_id + "_x";
  hidefornowtheX(button_id);
}
// but we want the X to show only when something was typed in!
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

/* Show the second search bar field - to calculate the path */
function showSecondSearchbar() {
	// document.getElementById("searchbtn").style.display = "none";
	document.getElementById("add-searchfield").style.display = "none";
	document.getElementById("btn-plus").style.display = "none";
	document.getElementById("second-search-field").style.display = "block";
	document.getElementById("nav_buttons").style.display = "block";
  // copia il testo della prima barra di ricerca nella secondar
  document.getElementById('search_field_2').value = document.getElementById('search_field_1').value;
  document.getElementById('search_field_1').value = '';
  document.getElementById('hidden_end_coord').value = document.getElementById('hidden_start_coord').value;
	document.getElementById('hidden_start_coord').value = '';
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
  // swap also hidden stuff
  var hidden_field_1 = document.getElementById('hidden_start_coord').value;
  document.getElementById('hidden_start_coord').value = document.getElementById('hidden_end_coord').value;
  document.getElementById('hidden_end_coord').value = hidden_field_1;
}

function copyStartingPosition(address_string) {
  document.getElementById('search_field_1').value = 'Indicatore Verde';
  document.getElementById('hidden_start_coord').value = address_string;
}

function copyEndingPosition(address_string) {
	showSecondSearchbar();
  document.getElementById('search_field_2').value = 'Indicatore Rosso';
  document.getElementById('hidden_end_coord').value = address_string;
}

function copyMyPositionAsStart(map) {
    map.locate().on('locationfound', function(e){
	marker_start.setLatLng(e.latlng);
	marker_start.addTo(mymap);
	document.getElementById('search_field_1').value = 'La Mia Posizione';
	document.getElementById('hidden_start_coord').value = e.latlng.toString();

  //loc_control.start();
		})
	 .on('locationerror', function(e){
				console.log(e);
				alert("Location access denied.");
		});
}
