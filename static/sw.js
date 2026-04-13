const CACHE_NAME = 'clc-pwa-v3';
const STATIC_ASSETS = [
    '/',
    '/map/',
    '/offline/',
    '/static/css/base.css',
    '/static/css/pages/home.css',
    '/static/js/base.js',
    '/static/js/pages/home.js',
    '/static/js/script.js',
    '/static/img/logo.png',
    '/static/manifest.json',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap',
    'https://fonts.googleapis.com/css2?family=Public+Sans:wght@300;400;500;600;700;800;900&display=swap',
    'https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap',
];
// Install: pre-cache critical assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('[SW] Pre-caching static assets');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});
// Activate: clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});
// Intercept fetch requests
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);
    // Only handle GET requests
    if (request.method !== 'GET') return;
    // 1. Static Assets (Stale-While-Revalidate for Fonts, Cache-First for others)
    if (url.origin.includes('fonts.googleapis.com') || url.origin.includes('fonts.gstatic.com')) {
        event.respondWith(
            caches.open(CACHE_NAME).then(cache => {
                return cache.match(request).then(cachedResponse => {
                    const fetchPromise = fetch(request).then(networkResponse => {
                        cache.put(request, networkResponse.clone());
                        return networkResponse;
                    });
                    return cachedResponse || fetchPromise;
                });
            })
        );
        return;
    }
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request).then(cachedResponse => {
                if (cachedResponse) return cachedResponse;
                return fetch(request).then(networkResponse => {
                    return caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, networkResponse.clone());
                        return networkResponse;
                    });
                });
            })
        );
        return;
    }
    // 2. HTML Pages (Network-First with Cache Fallback)
    if (request.headers.get('Accept').includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then(networkResponse => {
                    // Save to cache for offline use
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                    return networkResponse;
                })
                .catch(() => {
                    // Offline fallback: try cache, then offline.html
                    return caches.match(request).then(cachedResponse => {
                        return cachedResponse || caches.match('/offline/');
                    });
                })
        );
        return;
    }
    // 3. Other requests (Network Only)
    event.respondWith(fetch(request));
});
// Push Notifications
self.addEventListener('push', function(event) {
    if (event.data) {
        let data = { title: 'CLC', body: 'Новое уведомление' };
        try {
            data = event.data.json();
        } catch (e) {
            data.body = event.data.text();
        }
        const options = {
            body: data.body,
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/icon-192x192.png',
            vibrate: [100, 50, 100],
            data: { url: data.url || '/' }
        };
        event.waitUntil(self.registration.showNotification(data.title, options));
    }
});
// Notification Click
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            const tgtUrl = event.notification.data.url;
            for (let i = 0; i < windowClients.length; i++) {
                if (windowClients[i].url === tgtUrl && 'focus' in windowClients[i]) {
                    return windowClients[i].focus();
                }
            }
            if (clients.openWindow) return clients.openWindow(tgtUrl);
        })
    );
});
