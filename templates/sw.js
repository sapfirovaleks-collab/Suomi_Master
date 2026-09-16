self.addEventListener("install", e=>{self.skipWaiting(); e.waitUntil(caches.open("suomi-v5-6").then(c=>c.addAll(["/map","/manifest.json"])))});
self.addEventListener("activate", e=>{e.waitUntil(clients.claim())});
self.addEventListener("fetch", e=>{e.respondWith(fetch(e.request).catch(()=>caches.match(e.request).then(r=>r || caches.match("/map"))))});
