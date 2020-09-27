const staticDequa = "app";
const assets = [
    "/static/js/bootleaf.js",
    "/static/js/easy-button.js",
    "/static/js/v4w_js/init.js",
    "/idee"
  ];

self.addEventListener("install", installEvent => {
    console.log('[ServiceWorker] installing...');
    installEvent.waitUntil(
      caches.open(staticDequa).then(
        function(cache) {
          console.log("[ServiceWorker] cached ");
		return cache.addAll(assets)
    })
  )
})

// self.addEventListener('fetch', (evt) => {
//   console.log('[ServiceWorker] fetching...');
//   return ("/static/js/v4w_js/init.js");
//   evt.respondWith(fetch(evt.request).catch(() => {
//     console.log("a");
//     return caches.open(staticDequa).then((cache) => {
//       console.log("b");
//       return cache.match("/static/js/v4w_js/init.js");
//     });
//   })
//   );
// });

// codelabs
self.addEventListener('fetch', event => {
  console.log('Fetch intercepted for:', event.request.url);
  console.log('event.request: ' +  (event.request));
  console.log('caches.match: ' +  caches.match(event.request));
  if (event.request.url=="http://127.0.0.1:5000/info") {
    console.log("richiesta pagina info!");
    event.respondWith("/idee");
  }
  else {
    console.log("richiesta che non è la pagina info, ma " + event.request.url);
    event.respondWith(caches.match(event.request)
      .then(cachedResponse => {
          if (cachedResponse) {
            return cachedResponse;
          }
          return fetch(event.request);
        })
      );
    }
});

//offline cookbook
// self.addEventListener('fetch', function(event) {
//   event.respondWith(
//     caches.open('app').then(function(cache) {
//       return cache.match(event.request).then(function (response) {
//         return response || fetch(event.request).then(function(response) {
//           cache.put(event.request, response.clone());
//           return response;
//         });
//       });
//     })
//   );
// });

//
// self.addEventListener("fetch", fetchEvent => {
//   fetchEvent.respondWith(
//     caches.match(fetchEvent.request).then(res => {
//       return res || fetch(fetchEvent.request)
//     })
//   )
// })

self.addEventListener('activate', activateEvent => {
  console.log('[ServiceWorker] Activate');
  activateEvent.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(keyList.map((key) => {
        if (key !== assets) {
          console.log('[ServiceWorker] Removing old cache...', key);
          return caches.delete(key);
        }
      }));
    })
  );
  self.clients.claim();
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
