const staticDequa = "app";
const assets = [
    "/static/js/bootleaf.js",
    "/static/js/easy-button.js",
    "/static/js/v4w_js/init.js",
    "/idee",
    "/offline", 
    "/"
  ];

self.addEventListener("install", installEvent => {
    console.log('[ServiceWorker] installing...');
    installEvent.waitUntil(
      caches.open(staticDequa).then(
        function(cache) {
	    cache_prom=cache.addAll(assets).then((res)=>{
		console.log("[ServiceWorker] cached ");
		return res
	    })
	    return cache_prom 
	})
    )
})

// offline page, esempio testato!
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
	    console.log("responding with ", response);
	    return response || fetch(event.request);
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
