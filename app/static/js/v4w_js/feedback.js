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
