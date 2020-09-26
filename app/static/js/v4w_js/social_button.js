
function addSocialButton(mymap) {
  console.log("launching dynamic script for social button");
  console.log("dynamic scripts are async by default --> https://javascript.info/script-async-defer");
  let script = document.createElement('script');
  script.src = "/static/js/v4w_js/add2any_smaller.js";
  document.body.append(script); // (*)
  console.log("now checking the social button situation!");
  //console.log(document.getElementById("social_button"));
  if (window.location.search && document.getElementById("social_button") == null ) {
    console.log("adding button for search:" + window.location.search);
    var stringaButton1 = '<div style="padding:0px !important" id="social_button" class="a2a_dd" href="https://www.addtoany.com/share"><svg width="1em" height="1em" viewBox="0 0 16 16" class="bi bi-share-fill" fill="currentColor" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" d="M11 2.5a2.5 2.5 0 1 1 .603 1.628l-6.718 3.12a2.499 2.499 0 0 1 0 1.504l6.718 3.12a2.5 2.5 0 1 1-.488.876l-6.718-3.12a2.5 2.5 0 1 1 0-3.256l6.718-3.12A2.5 2.5 0 0 1 11 2.5z"/></svg></div>';
    L.easyButton(stringaButton1, function(btn) {
      window.location.href="https://www.addtoany.com/share";
    }, {
      position: 'bottomright'
    }).addTo(mymap);
  }
  else {
    console.log("social button is already there!");
  }
}
