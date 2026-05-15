const CACHE_NAME = 'clc-pwa-v5';
const STATIC_ASSETS = [
    '/',
    '/offline/',
    '/static/css/base.css',
    '/static/css/pages/home.css',
    '/static/js/base.js',
    '/static/js/index.js',
    '/static/img/logo.png',
    '/static/manifest.json',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('[SW] Pre-caching static assets');
            return Promise.allSettled(
                STATIC_ASSETS.map(url =>
                    cache.add(url).catch(err => console.warn('[SW] Failed to cache:', url, err))
                )
            );
        })
    );
    self.skipWaiting();
});

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

self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);

    if (request.method !== 'GET') return;

    if (url.pathname.startsWith('/admin/') || url.pathname.startsWith('/api/')) return;

    if (url.origin.includes('fonts.googleapis.com') || url.origin.includes('fonts.gstatic.com')) {
        event.respondWith(
            caches.open(CACHE_NAME).then(cache => {
                return cache.match(request).then(cachedResponse => {
                    const fetchPromise = fetch(request).then(networkResponse => {
                        if (networkResponse && networkResponse.status === 200) {
                            cache.put(request, networkResponse.clone());
                        }
                        return networkResponse;
                    }).catch(() => null);
                    
                    return cachedResponse || fetchPromise.then(res => {
                        return res || new Response('', {status: 503, statusText: 'Service Unavailable'});
                    });
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
                    if (networkResponse && networkResponse.status === 200) {
                        return caches.open(CACHE_NAME).then(cache => {
                            cache.put(request, networkResponse.clone());
                            return networkResponse;
                        });
                    }
                    return networkResponse;
                }).catch(() => {
                    return new Response('', {status: 503, statusText: 'Service Unavailable'});
                });
            })
        );
        return;
    }

    const acceptHeader = request.headers.get('Accept') || '';
    if (acceptHeader.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then(networkResponse => {
                    if (networkResponse && networkResponse.status === 200) {
                        const responseClone = networkResponse.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(request, responseClone));
                    }
                    return networkResponse;
                })
                .catch(() => {
                    return caches.match(request).then(cachedResponse => {
                        return cachedResponse || caches.match('/offline/').then(offlineRes => {
                            return offlineRes || new Response('Offline', {status: 503, statusText: 'Service Unavailable'});
                        });
                    });
                })
        );
        return;
    }

    event.respondWith(
        fetch(request).catch(() => {
            return caches.match(request).then(cachedResponse => {
                return cachedResponse || new Response('', {status: 503, statusText: 'Service Unavailable'});
            });
        })
    );
});

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
