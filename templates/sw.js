const CACHE_NAME = 'suomi-master-v5.6-cache';
const urlsToCache = [
  '/map',
  '/api/map/wildlife',
  '/api/map/harvest',
  '/api/map/ev',
  '/api/map/free-shelters',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(urlsToCache))
  );
});

self.addEventListener('fetch', event => {
  event.respondWith(
    caches.match(event.request).then(response => {
      return response || fetch(event.request).catch(() => caches.match('/map'));
    })
  );
});
