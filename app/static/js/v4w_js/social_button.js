
function addSocialButton() {
  console.log("launching dynamic script for social button");
  console.log("dynamic scripts are async by default --> https://javascript.info/script-async-defer");
  let script = document.createElement('script');
  script.src = "/static/js/v4w_js/add2any_smaller.js";
  document.body.append(script); // (*)
  console.log("now checking the social button situation!");
  //console.log(document.getElementById("social_button"));
  searched_something = window.location.search != "";
  empty_search = dict_in_JS == "None";
  error_window = dict_in_JS.error == true;
  // button_not_created = document.getElementById("social_button") == null;

  if (searched_something && !empty_search && !error_window) {
    console.log("adding button for search:" + window.location.search);
    social_button.addTo(mymap);
  }
  else {
    console.log("remove social button!");
    social_button.remove();
  }
}
