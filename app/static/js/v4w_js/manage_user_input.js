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
  /* not working - ci serve?
  if (document.getElementById(field_id).backgroundColor == 'red')
  {
    console.log("restoring white background for " + field_id + " field");
    document.getElementById(field_id).backgroundColor = 'white';
  }
  */
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
  $("#add-searchfield").hide();
  $("#btn-plus").hide();
  $("#second-search-field").show();
  $("#nav_buttons").show();
}

function click_showSecondSearchbar(){
    showSecondSearchbar();
    // copia il testo della prima barra di ricerca nella secondar
    swapDirections();
    // document.getElementById('search_field_2').value = document.getElementById('search_field_1').value;
    // document.getElementById('search_field_1').value = '';
    // document.getElementById('hidden_end_coord').value = document.getElementById('hidden_start_coord').value;
    // document.getElementById('hidden_start_coord').value = '';
}

function click_hideSecondSearchbar(){
  if ($("#search_field_1").val() == "") {
    swapDirections();
  }
  deleteSecondSearchbar();
  hideSecondSearchbar();
}

function deleteSecondSearchbar() {
  // elimina contenuto seconda barra
  console.log("second bar was full, we remove " + $("#search_field_2").val());
  $("#search_field_2").val("");
  $("#hidden_end_coord").val("");

  console.log("second bar was full, we removed and now is " + $("#search_field_2").val());
}

function hideSecondSearchbar() {
	// document.getElementById("searchbtn").style.display = "block";
  $("#second-search-field").hide();
  $("#nav_buttons").hide();
  $("#add-searchfield").show();
  $("#btn-plus").show();
	// document.getElementById("start_from_my_location").style.display = "none";

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
  map.locate().once('locationfound', function(e){
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

function updateViewsAfterResizeWindow(){
  updateSidebarAfterResizeWindow();
  updateButtonsAfterResizeWindow();
}

function openHighTideAlertIfNeeded(){
  if (dict_in_JS =="None" || !("path" in dict_in_JS)) {
    console.log("this is the first access: no high tide warning");
  }
  else if ((dict_in_JS.path.tide_level_current >= 80) && (dict_in_JS.params_research.with_tide == 'off')){
  	console.log("opening high tide warning window");
    document.getElementById("current_tide_in_alert").innerHTML = dict_in_JS.path.tide_level_current;
	  document.getElementById("high_tide_window-warning").style.display = 'block';
  }
  else {
    console.log("This should never happen");
    $("#high_tide_window-warning").hide()
  }
}

function on_path_calculated_recalc(){
  if ("path" in dict_in_JS){
    $('#ricerca_ind').submit()
  }
}
