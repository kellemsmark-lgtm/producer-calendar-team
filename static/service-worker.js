const CACHE_NAME = 'producer-calendar-static-v1-8-dark-mode-handoff-verified';
const STATIC_ASSETS = [
  '/static/styles.css',
  '/static/app.js',
  '/static/manifest.webmanifest',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/static/icons/apple-touch-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(STATIC_ASSETS)).catch(() => undefined));
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.map(key => key === CACHE_NAME ? undefined : caches.delete(key)))));
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/exports/') || url.pathname.startsWith('/share/') || url.pathname === '/' || url.pathname === '/login' || event.request.method !== 'GET') {
    return;
  }
  if (url.pathname.startsWith('/static/')) {
    // Network first so UX-test changes reach iPhone/iPad Home Screen installs
    // quickly. Cached assets are only a fallback for offline/poor-network use.
    event.respondWith(
      fetch(event.request, { cache: 'no-store' })
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy)).catch(() => undefined);
          return response;
        })
        .catch(() => caches.match(event.request))
    );
  }
});
