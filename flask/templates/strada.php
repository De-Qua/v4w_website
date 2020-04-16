<!DOCTYPE html>
<html>
<title>Venessia4working</title>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.6.0/dist/leaflet.css"
   integrity="sha512-xwE/Az9zrjBIphAcBb3F6JVqxf46+CDLwfLMHloNu6KEQCAWi6HcDUbeOfBIptF7tcCzusKFjFw2yuvEpDL9wQ=="
   crossorigin=""/>
<!-- Make sure you put this AFTER Leaflet's CSS -->
<script src="https://unpkg.com/leaflet@1.6.0/dist/leaflet.js"
   integrity="sha512-gZwIG9x3wUXg2hdXF6+rVkLF/0Vi9U8D2Ntg4Ga5I5BZpVkVxlJWbSQtXPSiUTtC0TjtGOmxa1AJPuV0CPthew=="
   crossorigin=""></script>

<style>
	body,h1 {font-family: "Raleway", sans-serif}
	body, html {height: 100%}
	.bgimg {
		background-image: "";
		min-height: 100%;
		background-position: center;
		background-size: cover;
	}
	#mapid {
		width: 900px;
		height: 600px;
	}
</style>
<body>

<div class="bgimg w3-display-container w3-animate-opacity w3-text-white">
  <div class="w3-display-middle w3-center">

    <div id="mapid" class="w3-center map" ></div>
    <br><br>
     <form>
     <div class="w3-text">DA:<input type="text" id="da" name="partenza" style="display: inline;">A:<input type="text" id="adove" name="arrivo"></div>
     <input type="submit" value="daicheghesemo">
     </form>
     <br>
		<script>
			var mymap = L.map('mapid').setView([45.43, 12.33], 13);
			var OpenStreetMap_DE = L.tileLayer('https://{s}.tile.openstreetmap.de/tiles/osmde/{z}/{x}/{y}.png', {
			maxZoom: 18,
			attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
			}).addTo(mymap);
			var marker = L.marker([45.43, 12.33]).addTo(mymap);
		</script>
		<div class="w3-button w3-text w3-black" onclick="window.location.href='main'">Call_main</div>
		<div class="w3-button w3-text w3-black" onclick="draw_line()">Draw a random line</div>
		PHP<br>
		<div class="w3-text w3-green" id="texttochange1">QUI LA PARTENZA: <?php echo $_GET['partenza'] ?></div>
		<div class="w3-text w3-red" id="texttochange2">QUI L'ARRIVO: <?php echo $_GET['arrivo'] ?></div>
		<div class="w3-text w3-blue" id="texttochange3">QUI LA STRADA: <?php echo $_GET['strada'] ?></div>
		JS - <div class="w3-button w3-text w3-black" onclick="fill()">Clicca</div><br>
		<div class="w3-text w3-green" id="texttochange">Ricerca: </div>
		<script>
        function fill() {
            document.document.getElementById("texttochange1").style.display = "none";
            document.document.getElementById("texttochange2").style.display = "none";
            document.document.getElementById("texttochange3").style.display = "none";
            document.document.getElementById("texttochange").innerHTML = window.location.search;
        }
		function draw_pol() {
			var polygon = L.polygon([
				[45.43 + (Math.random() * 0.04 - 0.02), 12.33 + (Math.random() * 0.04 - 0.02)],
				[45.4389 + (Math.random() * 0.04 - 0.02), 12.3407 + (Math.random() * 0.04 - 0.02)],
				[45.4407 + (Math.random() * 0.04 - 0.02), 12.3313 + (Math.random() * 0.04 - 0.02)]
				]).addTo(mymap);
			}
		function draw_line() {
			var pointA = new L.LatLng(45.43 + (Math.random() * 0.05 - 0.025), 12.33 + (Math.random() * 0.05 - 0.025));
			var pointB = new L.LatLng(45.43 + (Math.random() * 0.05 - 0.025), 12.33 + (Math.random() * 0.05 - 0.025));
			var pointList = [pointA, pointB];

			var firstpolyline = new L.Polyline(pointList, {
					color: 'red',
					weight: 3,
					opacity: 0.5,
					smoothFactor: 1
			});
			firstpolyline.addTo(mymap);
		}
		var popup = L.popup();

        var pointList = [];
		function onMapClick(e) {
		    var pointList = [e.latlng];
		    popup
            .setLatLng(e.latlng)
            .setContent("Prima parte Sei andato a " + pointList.toString() + ", quando avremo le nostre fantastiche mappe ti diro anche dov'e!")
            .openOn(mymap);
		    //var pointA = new L.LatLng(45.43, 12.33);
		    if(pointList.length<1){
			    pointList.push(e.latlng);
		    } else {
		        var pointList = [e.latlng];
		    }
			var firstpolyline = new L.Polyline(pointList, {
					color: 'green',
					weight: 3,
					opacity: 0.5,
					smoothFactor: 1
				});
			firstpolyline.addTo(mymap);
		//	popup
        //.setLatLng(e.latlng)
        //.setContent("Sei andato a " + e.latlng.toString() + ", quando avremo le nostre fantastiche mappe ti diro anche dov'e!")
        //.openOn(mymap);
		}

		mymap.on('click', onMapClick);
		</script>
  </div>
</div>

</body>
</html>
