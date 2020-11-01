/* Licensed under AGPLv3
/*!
* Venessia4Working Javascripts
* Copyleft 2020

*/
function initialize_html(){
  hidePreLoader();
  toggleXbuttons();
  resetColorSearchFields();
  clearAllResults();
  moveResultsToMainWindow();
  closeResultsWindow();
  removePathLayer();
  closeErrorWindow();
  addSocialButton();


  mymap.on('click', onMapClick);

  document.getElementById("search_field_1").addEventListener("change", clear_hidden_start);
  document.getElementById("search_field_2").addEventListener("change", clear_hidden_end);
  console.log("feedback sent ", feedbacksent);
  // deal with feedback sent
  switch(feedbacksent) {
    case -1:
    // error in the feedback
    document.getElementById("feedbackmessagewindow-fail").style.display = 'block';
    break;
    case 1:
    // feedback sent
    document.getElementById("feedbackmessagewindow-success").style.display = 'block';
    break;
  }
  // reset feedbacksent variable
  feedbacksent = 0;


  // function onMapClick(e) {
  //   var address_string = e.latlng.toString();
  //   popup
  //   .setLatLng(e.latlng)
  //   .setContent("<div class='text-center'>Posizione: " + address_string + "<br><button  class='btn btn-sm btn-light v4wbtn mr-3' style='font-size: 0.8em;' id='btnMapStart'>DA QUA</button><button  class='btn btn-sm btn-light v4wbtn' style='font-size: 0.8em;' id='btnMapTo'>A</button><br></div>")
  //   .openOn(mymap);
  //   document.getElementById('btnMapStart').onclick = function() { copyStartingPosition(address_string); addMarkerStart(e.latlng); popup.remove();};
  //   document.getElementById('btnMapTo').onclick = function() { copyEndingPosition(address_string); addMarkerEnd(e.latlng);popup.remove();};
  // }

  // HERE WE READ OUR JSON MESSAGE FROM PYTHON
  //var result = JSON.parse({{ results_dictionary | tojson }});
  // var dict_in_JS = {{results_dictionary | tojson}};

  console.log("dict: ",dict_in_JS);
  /**
  * NO DICTIONARY RETURNED
  **/
  if (dict_in_JS == "None") {
    hidebothXbuttons();
  }
  /**
  * ONLY TIDE LEVEL (the actual standard)
  **/
  //alert("Ahi ahi!!!\nOps... cossa xe nato :(\n"+dict_in_JS.msg)
  else if ("only_tide_level" in dict_in_JS) {
    mymap.setView([45.435, 12.333], 15);
    console.log("tutto normale, ma con l'indicazione dell'acqua alta");
    var tide_in_cm = dict_in_JS.only_tide_level;
    $('#tide_level_input').val(tide_in_cm);
  }
  /**
  * ERRORS
  **/
  else if ("error" in dict_in_JS) {
    mymap.setView([45.435, 12.333], 15);
    console.log("error: " + dict_in_JS.msg)
    document.getElementById("errorwindow-explanation").innerHTML = dict_in_JS.msg;
    var err_win = document.getElementById("errorwindow");
    var err_btn = document.getElementById("errorFbButton");
    err_win.style.display = 'block';
    if (dict_in_JS.type == 'UserError') {
      if (err_win.classList.contains("alert-dq-red")){
        err_win.classList.remove("alert-dq-red");
        err_btn.classList.remove("btn-dq-red");
      }
      err_win.classList.add("alert-dq-yellow");
      err_btn.classList.add("btn-dq-yellow");
      document.getElementById("errorTitle").innerHTML = "Non abbiamo trovato nulla!"
      document.getElementById("error-text").innerHTML = "Se pensi che non sia per questo che la ricerca non ha funzionato, lasciaci un feedback spiegandoci il problema!";
    }
    else if (dict_in_JS.type == 'DeveloperError') {
      if (err_win.classList.contains("alert-dq-yellow")) {
        err_win.classList.remove("alert-dq-yellow");
        err_btn.classList.remove("btn-dq-yellow");
      }
      err_win.classList.add("alert-dq-red");
      err_btn.classList.add("btn-dq-red");
      document.getElementById("errorTitle").innerHTML = "C'è stato un errore!"
      document.getElementById("error-text").innerHTML = "È un po' imbarazzante, ma questo è anche il motivo per cui la versione si chiama <strong>alpha</strong>!<br>Se vuoi lasciarci un feedback per darci qualche informazione in più, clicca qui:";
    }
    else {
      if (err_win.classList.contains("alert-dq-yellow")) {
        err_win.classList.remove("alert-dq-yellow");
        err_btn.classList.remove("btn-dq-yellow");
      }
      err_win.classList.add("alert-dq-red");
      err_btn.classList.add("btn-dq-red");
      document.getElementById("errorTitle").innerHTML = "C'è stato un errore!"
      document.getElementById("error-text").innerHTML = "È un po' imbarazzante, ma questo è anche il motivo per cui la versione si chiama <strong>alpha</strong>!<br>Se vuoi lasciarci un feedback per darci qualche informazione in più, clicca qui:";
    }
  }
  /**
  * A REAL DICTIONARY
  * here we do stuff!
  **/
  else {

    // Set values on feedback window
    setValuesInFeedbackWindow(dict_in_JS);

    var modus_operandi = dict_in_JS.modus_operandi;
    console.log("siamo in modus_operandi: " + modus_operandi);
    var geo_type = dict_in_JS.partenza[0].geotype;
    console.log("geo_type in questo caso = " + geo_type);
    // we switch with modus_operandi
    // modus == 0 --> indirizzo, o nulla?
    // modus == 1 --> strada tra A e B
    console.log("Setting up results window!")
    showResultsWindow(dict_in_JS);
    setSidebarTitle(dict_in_JS);
    switch(modus_operandi) {
      case 0:
      // here all the stuff we can do when only one address is searched
      // NEW VERSION with geo_type
      // geo_type == -2 --> pagina senza ricerca
      // geo_type == -1 --> trovato nulla, pazienza
      // geo_type == 0 --> marker, un punto solo
      // geo_type == 1 --> poligono
      // e facile aggiungere geo_type se vogliamo piu avanti
      console.log("shown a single address result")
      var name_location = dict_in_JS.params_research.da;
      document.getElementById('search_field_1').value = name_location;
      if (name_location.length > 0) {
        nowitstimetoshowtheX('search_field_1_x');
      }
      // if we have the coordinate, we should keep it!
      if (dict_in_JS.start_type == 'unique') {
        document.getElementById('hidden_start_coord').value = dict_in_JS.partenza[0].coordinate;
      }

      switch(geo_type) {
        case -2:
        // do nothing - pagina senza ricerca_ind
        mymap.setView([45.43, 12.33], 15);
        break;
        case -1: // in realta per ora non serve a nulla
        // code block
        alert('non abbiamo trovato nulla! Sicuro di aver scritto giusto? Riprova');
        break;
        case 0:
        // coordinate
        var coords_location = dict_in_JS.partenza[0].coordinate;
        var cur_result_name = dict_in_JS.partenza[0].nome;
        var cur_result_description = dict_in_JS.partenza[0].descrizione;
        // TODO: usare funzione addMarkerLocation in map_objects.js
        addMarkerLocation(coords_location, cur_result_name, cur_result_description);
        // marker_location = L.marker(coords_location, markerOptions);
        // // Popup se uno clicca sul marker
        // marker_location.bindPopup("<div class='text-center'><b>"+cur_result_name+"</b><br>"+cur_result_description);
        // // aggiungi il marker sulla mappa
        // marker_location.addTo(mymap);
        var group = new L.featureGroup([marker_location]);
        mymap.fitBounds(group.getBounds());
        //mymap.setView([{{start_coordx}}, {{start_coordy}}], 18);
        break;
        case 1:
        // DISEGNA POLIGONO
        var polygonOptions = {

          title: "Evidenziato " + name_location,
          clickable: true,
          // si alza all'hover - non va :(
          riseOnHover: true
        }
        // var polygon = L.polygon([
        // 		dict_in_JS.partenza[0].shape
        // ], polygonOptions).addTo(mymap);
        // var group = new L.featureGroup([polygon
        console.log("geojson: "+ dict_in_JS.partenza[0].geojson);
        // Per qualche motivo dice che il geojson è fatto male
        polygon = L.geoJSON(dict_in_JS.partenza[0].geojson);
        polygon.addTo(mymap);
        mymap.fitBounds(polygon.getBounds());
        //mymap.setView([{{start_coordx}}, {{start_coordy}}], 17);
        break;
        default:
        // do nothing
        console.log("caso default. strano. guarda nello switch che valore ha geo_type");
        break;
      }
      break;
      // MODUS OPERANDI == 1 --> PERCORSO DA A a B
      case 1:
      // geo type is not used
      console.log("also the search should be ready");
      showSecondSearchbar();
      var nome_partenza = dict_in_JS.params_research.da
      document.getElementById('search_field_1').value = nome_partenza;
      if (nome_partenza.length > 0) {
        nowitstimetoshowtheX('search_field_1_x');
      }
      // if we have the coordinate, we should keep it!
      if (dict_in_JS.params_research.start_coord.length > 0) {
        document.getElementById('hidden_start_coord').value = dict_in_JS.params_research.start_coord;
      }
      var nome_arrivo = dict_in_JS.params_research.a
      document.getElementById('search_field_2').value = nome_arrivo;
      if (nome_arrivo.length > 0) {
        nowitstimetoshowtheX('search_field_2_x');
      }
      // if we have the coordinate, we should keep it!
      if (dict_in_JS.params_research.end_coord.length > 0) {
        document.getElementById('hidden_end_coord').value = dict_in_JS.params_research.end_coord;
      }
      else if (dict_in_JS.end_type == 'unique' && dict_in_JS.arrivo[0].coordinate.lenght > 0) {
        document.getElementById('hidden_end_coord').value = dict_in_JS.arrivo[0].coordinate;
      }
      else {
        console.log("[modus 1]: seems like we are not using end_coord! is this correct?")
      }
      console.log("checking the boxes");
      checkTheBoxesThatNeedToBeChecked(dict_in_JS);
      console.log("done checking the boxes");
      console.log("drawing the streets!")

      // here all the stuff when we have path from A to B
      //var punto_di_partenza = L.point(stop_coordx, stop_coordy);
      //var prj = L.Projection.Mercator.unproject(pointM);
      addMarkerStart(dict_in_JS.partenza[0].coordinate);
      addMarkerEnd(dict_in_JS.arrivo[0].coordinate);
      // the pahts: they are more than one
      var street = dict_in_JS.path;
      // var group = new L.featureGroup([marker_partenza, marker_arrivo]);
      //console.log("steets: " + streets);
      path_shapes = street.shape_list;
      //var linestrings = L.geoJSON(path_shapes, {'style':stile});
      // var linestrings = L.geoJSON(path_shapes, {
      //   filter: function(feature) {
      //     // draw only lines!
      //     return feature.geometry.type == "LineString";
      //   },
      //   style: function(feature) {
      //     switch (feature.properties.street_type) {
      //       case 'canale': return {color: "#0000ff"};
      //       case 'ponte':  return {color: "#ffff00"};
      //       case 'calle':  return {color: "#ff0000"};
      //     }
      //   }
      // }).addTo(mymap);
      addPathLines(path_shapes);
      // linestrings.addTo(group);
      if (is_touch_device){
        mymap.fitBounds(pathGroup.getBounds(), {paddingTopLeft: [10, 200], paddingBottomRight: [20,10]});
      }
      else{
	       mymap.fitBounds(pathGroup.getBounds(), {paddingTopLeft: [300, 10], paddingBottomRight: [10,10]});
      }
      // javascript way to call a method in the for loop
      //streets.forEach(drawStreet());
      //alert('YET TO BE DONE');
      break;
      // MODUS OPERANDI == 2 --> Non siamo sicuri della soluzione
      case 2:
      // Disable click on the map
      mymap.off('click');

      console.log("Setting up possiblities window!")
      var allTheThingsWeKnow = findWhatWeKnow()

      var possibilities = allTheThingsWeKnow.possibilities;
      var what_we_know = allTheThingsWeKnow.what_we_know;
      var start_found = allTheThingsWeKnow.start_found;
      var end_found = allTheThingsWeKnow.end_found;
      var tmp_start = allTheThingsWeKnow.tmp_start;
      var tmp_end = allTheThingsWeKnow.tmp_end;

      console.log("We send this to js: ",markerOptions)
      // showPossibilitiesWindow(possibilities, markerOptions, mymap, what_we_know, tmp_start, tmp_end, start_found, end_found);
      showPossibilitiesWindow(possibilities, markerOptions, mymap, what_we_know, tmp_start, tmp_end, start_found);

      // sbagliamo a scrivere sulle barre! Da correggere in showPossibilitiesWindow
      // o ancora meglio separare possibilities window dallo scrivere sulle barre
      var nome_partenza = dict_in_JS.params_research.da;
      document.getElementById("search_field_1").value = nome_partenza;
      var nome_arrivo = dict_in_JS.params_research.a;
      document.getElementById("search_field_2").value = nome_arrivo;


      //document.getElementById('search_field_1').value = nome_partenza;
      //keep coordinates
      // if we have the start coordinate, we should keep it!
      if (dict_in_JS.params_research.start_coord.length > 0) {
        document.getElementById('hidden_start_coord').value = dict_in_JS.params_research.start_coord;
      }
      // if we have the end coordinate, we should keep it!
      if (dict_in_JS.params_research.end_coord.length > 0) {
        document.getElementById('hidden_end_coord').value = dict_in_JS.params_research.end_coord;
      }
      //possibilitiesLayer.addTo(mymap);
      mymap.fitBounds(possibilitiesLayer.getBounds());
      /*$(document).ready(function(){
      $(".owl-carousel").owlCarousel();
    });*/
    console.log("done here");
    break;
    break; // final default break
  }//closing switch modus_operandi
  var activeCard = '';
}
}

var activeCard = '';

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

function searchAgain() {
  document.getElementById("trovato").style.display = "none";
  document.getElementById("searchbar").style.display = "block";
}

function goToNextStep(nextStep) {
  drawPreLoader()
  window.location = nextStep;
}

function findWhatWeKnow() {
  var possibilities = "";
  var what_we_know = "nothing";
  var start_found = "";
  var end_found = "";
  var tmp_start = dict_in_JS.searched_start;
  var tmp_end = dict_in_JS.searched_end;
  checkTheBoxesThatNeedToBeChecked(dict_in_JS);

  if ((dict_in_JS.start_type == 'multiple') && (dict_in_JS.end_type == 'multiple')){
    possibilities = dict_in_JS.partenza;
    what_we_know = "choosing_start";
  } else if ((dict_in_JS.start_type == 'unique') && (dict_in_JS.end_type == 'multiple')) {
    // scegliamo l'arrivo!
    // nome e coordinate della partenza vengono passate come dizionario (start_found)
    possibilities = dict_in_JS.arrivo;
    start_found = {nome:dict_in_JS.params_research.da, coordinate:dict_in_JS.params_research.start_coord};
    //start_found = dict_in_JS.partenza[0];
    what_we_know = "choosing_end";
    showSecondSearchbar();
  } else if ((dict_in_JS.start_type == 'multiple') && (dict_in_JS.end_type == 'unique')) {
    // scegliamo la partenza!
    // nome e coordinate dell'arrivo vengono passate come dizionario (end_found)
    possibilities = dict_in_JS.partenza;
    if (tmp_end) {
      end_found = {nome:dict_in_JS.params_research.a, coordinate:dict_in_JS.params_research.end_coord};
      //end_found = dict_in_JS.params_research.a;
      //end_found = dict_in_JS.arrivo[0];
      what_we_know = "choosing_start";
    } else {
      what_we_know = "address";
    }
  } else {
    what_we_know = "nothing";
  }

  return {
    possibilities: possibilities,
    what_we_know: what_we_know,
    start_found: start_found,
    end_found: end_found,
    tmp_start: tmp_start,
    tmp_end: tmp_end
  };
}

//runned by submit
function drawPreLoader() {
  // Set opacity
  document.getElementById("mapid").style.opacity = 0.3;
  // draw loading
  document.getElementById("loading").style.display = "inline";
  // disable buttons
  disableAllInputs();
  // console.log("drawing preloader..")
  //document.getElementById("loading_gif").src = "/static/assets/loading.gif";
  console.log("done!")
  // setTimeout(console.log("now, ok"), 1000);
  return true;
}

function hidePreLoader() {
  // hide loading
  $("#loading").hide();
  // show map
  $("#mapid").fadeTo("fast", 1);
  // enable buttons
  enableAllInputs();
}

function disableAllInputs() {
  $(':button').prop('disabled', true);
  $("input[type=checkbox]").attr("disabled", true);
}
function enableAllInputs() {
  $(':button').prop('disabled', false);
  $("input[type=checkbox][class!=disabled]").removeAttr("disabled");
}

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
  else {
    document.getElementById("walk_setting").checked = false;
  }
  if (checkBoxesDict.with_tide == "on") {
    $("#tide_level").show();
  }
  else {
    $("#tide_level").hide();
  }
}

function resetColorSearchFields() {
  $("#search_field_1").css("background-color","#fff")
  $("#search_field_2").css("background-color","#fff")
}

function closeErrorWindow() {
  $("#errorwindow").hide();
}
