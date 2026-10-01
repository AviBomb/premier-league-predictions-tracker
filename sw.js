// Offline support for the public dashboard. Network first, so live data always wins;
// the cache is only a fallback when the phone has no connection.
const CACHE = 'pl-hub-v1';
const SHELL_PAGES = new Set(['', 'index.html', 'dashboard.html', 'manifest.webmanifest']);

self.addEventListener('install', () => self.skipWaiting());

self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(keys => Promise.all(keys.filter(key => key !== CACHE).map(key => caches.delete(key))))
            .then(() => self.clients.claim())
    );
});

function cacheable(url) {
    if (url.origin !== self.location.origin) return false;
    const rel = url.pathname.slice(new URL(self.registration.scope).pathname.length);
    return SHELL_PAGES.has(rel) || rel.startsWith('assets/') || rel.startsWith('data/site/');
}

self.addEventListener('fetch', event => {
    const request = event.request;
    if (request.method !== 'GET') return;
    const url = new URL(request.url);
    if (!cacheable(url)) return;
    // Keyed without the query string: ?v=<build> changes every run and would grow the cache forever.
    const key = url.origin + url.pathname;
    event.respondWith(
        fetch(request)
            .then(response => {
                if (response.ok) {
                    const copy = response.clone();
                    event.waitUntil(caches.open(CACHE).then(cache => cache.put(key, copy)));
                }
                return response;
            })
            .catch(async () => (await caches.match(key)) || Response.error())
    );
});
