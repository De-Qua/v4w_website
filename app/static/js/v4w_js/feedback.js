/* Licensed under AGPLv3
 /*!
  * Venessia4Working Javascripts
  * Copyleft 2020

  */



function closeFeedbackWindow() {
	document.getElementById("mapid").style.opacity = 1.0;
	document.getElementById("feedbackwindow").style.display = "none";
	document.getElementById("searchbar").style.display = "block";
	var thingstoBeShown = document.getElementsByClassName("onlyMap");
	for (i = 0; i < thingstoBeShown.length; i++) {
		thingstoBeShown[i].style.display = "inline";
	}
}

function clearFeedbackWindow() {
	$('#searched_string').val('');
	$('#found_string').val('');
	$('#searched_start').val('');
	$('#searched_end').val('');
	$('#found_start').val('');
	$('#found_end').val('');
	$('#hidden_start_coord_fb').val('');
	$('#hidden_end_coord_fb').val('');

}

function hideSearchFoundFeedbackWindow() {
	$('#form-search-address').hide();
	$('#form-found-address').hide();
	$('#form-search-path').hide();
	$('#form-found-path').hide();
}

function setValuesInFeedbackWindow(JSdict) {
	// clear and hide all the fields of the research
	clearFeedbackWindow();
	hideSearchFoundFeedbackWindow();
	// in any case, we set the start and end_coords (worst case they are "")
	// we copy the values from the hidden fields for the search
	// the field with "_fb" are inside the feedback form, so they will be sent
	// along with the feedback form, I hope
	console.log("copying hidden field to the feedback hidden field");
	$('#hidden_start_coord_fb').val($('#hidden_start_coord').val());
	$('#hidden_end_coord_fb').val($('#hidden_end_coord').val());

	if (JSdict == "None" || !("partenza" in JSdict)){
    return
  } else if ("error" in JSdict) {
		// we have only the first search field
		if (!$('#search_field_2').val()) {
			$('#form-search-address').show();
			$('#searched_string').val($('#search_field_1').val());
		} else {
			$('#form-search-path').show();
			$('#searched_start').val($('#search_field_1').val());
			$('#searched_end').val($('#search_field_2').val());
		}
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
			$('#form-search-address').show();
			$('#form-found-address').show();
      // write values
			$('#searched_string').val(JSdict.searched_start);
			$("#found_string").val(all_found_start.join("; "));

    } else if (JSdict.modus_operandi==1 || JSdict.modus_operandi==2){
      // show div
			$('#form-search-path').show();
			$('#form-found-path').show();
			// write values
			$('#searched_start').val(JSdict.searched_start);
			$('#searched_end').val(JSdict.searched_end);
			$('#found_start').val(all_found_start.join("; "));
			$('#found_end').val(all_found_end.join("; "));

    } else {
      // do nothing
      return
    }
  }
}


function closeErrorAndShowFeedbackNew() {
	console.log("closing error window");
	// chiudi la di errore
	document.getElementById('errorwindow').style.display = 'none';
	console.log("setting window to show: true using jQuery");
	// apri la finestra di setting
	$('#settingsWindow').modal({
		show: true
	});
	showFeedbackWindowNew();
}
function showFeedbackWindowNew() {
	console.log("opening feedback window");
	document.getElementById("settings-general").style.display = 'none';
	document.getElementById("settings-feedback").style.display = 'block';
	// Dropdown choices:
	// (0, 'Oggetto non specificato')
	// (1, 'Indirizzo sbagliato')
	// (2, 'Strada sbagliata')
	// (3, 'Problemi di grafica')
	// (4, 'Proposta di miglioramento')
	// (5, 'Altro')
	document.getElementById("category").selectedIndex = 0;
	// we copy the hidden_coords
	console.log("@showFeedbackWindowNew: copying hidden field to the feedback hidden field");
	$('#hidden_start_coord_fb').val($('#hidden_start_coord').val());
	$('#hidden_end_coord_fb').val($('#hidden_end_coord').val());
}

function closeFeedbackWindowNew() {
	document.getElementById("settings-feedback").style.display = 'none';
}
