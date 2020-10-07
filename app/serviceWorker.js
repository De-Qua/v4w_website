const staticDequa = "app_cache";

self.addEventListener("install", installEvent => {
    console.log('[ServiceWorker] installing...');
    installEvent.waitUntil(
      caches.open(staticDequa).then(function(cache) {
	      fetch("/files_to_cache", {method:'GET'}).then(function(ftc_response){
		  return ftc_response.json()
	      }).then(function(ftc_json){
		      console.log("[ServiceWorker] output from files_to_cache", ftc_json)
		      cache_prom=cache.addAll(ftc_json).then(function(res) {
			  console.log("[ServiceWorker] cached ",caches.keys().length);
			  return res
		      })
	      })
      })
    ) 
})

// non ho trovato l'evidenza che stia rimuovendo la vecchia cache (anche se ho verificato che sia attiva correttamente
self.addEventListener('activate', (evt) => {
  console.log('[ServiceWorker] Activate');
  evt.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== staticDequa) {
          console.log('[ServiceWorker] Removing old cache', key);
          return caches.delete(key);
        }
      }));
    })
  );
  self.clients.claim();
});

//offline page, esempio testato!
//self.addEventListener('fetch', (evt) => {
//  if (evt.request.mode !== 'navigate') {
//    return;
//  }
//    evt.respondWith(fetch(evt.request).catch(() => {
//	console.log("intercepted fetch for ", evt.request);
//	return caches.open(staticDequa).then((cache) => {
//            return cache.match('\offline');
//      });
//    })
//  );
//});

self.addEventListener('fetch', function(event) {
    event.respondWith(
	caches.match(event.request).then(function(response) {
//	    console.log("responding to ",event.request ,"with ", response);
	    if (response){
		//console.log("returning ",response ,"found in cache");
		return response
	    } else {
		console.log("fetching ",event.request, " from the server");
		return fetch(event.request);
// if fetch returns offline error, return the offline page
//	return caches.open(staticDequa).then((cache) => {
//            return cache.match('\offline');
	    }
	})
    );
});


/* copiando i tutorial, non so servano per storare in cache tutto
"/css/dequa.css",
"/css/s.css",
"/js/app.js"
"/static/img/dequa_logo_v2.png"
 "/js/v4w/init.js",
"/js/v4w/feedback.js",
"/js/v4w/manage_user_input.js",
"/js/v4w/map_objects.js",
"/js/v4w/results_window.js",
"/js/bootstrap.min.js",
"/js/bootstrap.min.js.map",
"/js/bootstrap.bundle.min.js",
"/js/bootstrap.bundle.min.js.map",
"/js/bootstrap.bundle.js",
"/js/bootstrap.bundle.js.map",
"/js/easy-button.js",
"/js/jquery-3.5.1.min.js",
"/js/jquery.slim.min.js",
"/images/coffee1.jpg",
"/images/coffee2.jpg",
"/images/coffee3.jpg",
"/images/coffee4.jpg",
"/images/coffee5.jpg",
"/images/coffee6.jpg",
"/images/coffee7.jpg",
"/images/coffee8.jpg",
"/images/coffee9.jpg", */
