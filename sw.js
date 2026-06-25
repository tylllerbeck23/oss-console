/* OSS Console service worker — offline app shell.
   Network-first for the app HTML (so it never serves a stale build), cache-first
   for libraries and already-viewed map tiles (so the chart works offline at sea). */
const C = 'oss-v39';
const SHELL = [
  './', './app.html',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js',
  'https://unpkg.com/leaflet.heat@0.2.0/dist/leaflet-heat.js',
];

self.addEventListener('install', e => {
  // do NOT skipWaiting here — the page shows an "Update now" banner and the
  // user activates the new version on demand (no surprise reloads mid-task).
  e.waitUntil(caches.open(C).then(c => c.addAll(SHELL).catch(() => {})));
});
self.addEventListener('activate', e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== C).map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
self.addEventListener('message', e => { if (e.data && e.data.type === 'SKIP_WAITING') self.skipWaiting(); });
self.addEventListener('fetch', e => {
  const r = e.request;
  if (r.method !== 'GET') return;
  const url = new URL(r.url);

  // any page navigation (app.html, index.html, demo.html): network-first,
  // cache under its OWN url, fall back to its cache (or the app) when offline
  if (r.mode === 'navigate' || /\.html$/.test(url.pathname)) {
    e.respondWith(
      fetch(r).then(res => { const cp = res.clone(); caches.open(C).then(c => c.put(r, cp)); return res; })
              .catch(() => caches.match(r).then(m => m || caches.match('./app.html')))
    );
    return;
  }
  // everything else: cache-first, fill cache from network (libs + viewed tiles)
  e.respondWith(
    caches.match(r).then(m => m || fetch(r).then(res => {
      if (res.ok && (url.origin === location.origin || /unpkg|jsdelivr|arcgisonline|fonts\.googleapis|fonts\.gstatic/.test(url.host))) {
        const cp = res.clone(); caches.open(C).then(c => c.put(r, cp));
      }
      return res;
    }).catch(() => m))
  );
});
