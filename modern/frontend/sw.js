// Minimal service worker (cache-first for shell)
const CACHE = 'liferpg-shell-v1'
self.addEventListener('install', (e) => {
    e.waitUntil(
        caches.open(CACHE).then((cache) => cache.addAll(['/', '/index.html']))
    )
})
self.addEventListener('fetch', (e) => {
    e.respondWith(
        caches.match(e.request).then((r) => r || fetch(e.request))
    )
})
