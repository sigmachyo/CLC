const CACHE_NAME = 'clc-pwa-v1';
const STATIC_ASSETS = [
    '/static/css/index.css',
    '/static/js/script.js',
    '/static/fonts/Inter.woff2',
    '/static/icons/icon-192x192.png',
    '/static/icons/icon-512x512.png',
    '/offline/',
];

// Установка: кешируем базовую статику
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            console.log('[SW] Кэширование статических файлов');
            return cache.addAll(STATIC_ASSETS);
        })
    );
    self.skipWaiting();
});

// Активация: чистим старые кеши
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cache => {
                    if (cache !== CACHE_NAME) {
                        console.log('[SW] Удаление старого кэша', cache);
                        return caches.delete(cache);
                    }
                })
            );
        })
    );
    self.clients.claim();
});

// Перехват запросов (Fetch)
self.addEventListener('fetch', event => {
    const request = event.request;
    const url = new URL(request.url);

    // Только GET запросы
    if (request.method !== 'GET') return;

    // Статика -> Cache First
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request).then(cachedResponse => {
                return cachedResponse || fetch(request).then(networkResponse => {
                    const responseClone = networkResponse.clone();
                    caches.open(CACHE_NAME).then(cache => {
                        cache.put(request, responseClone);
                    });
                    return networkResponse;
                });
            })
        );
        return;
    }

    // HTML страницы -> Network First
    if (request.headers.get('Accept').includes('text/html')) {
        event.respondWith(
            fetch(request).then(response => {
                const responseClone = response.clone();
                caches.open(CACHE_NAME).then(cache => {
                    cache.put(request, responseClone);
                });
                return response;
            }).catch(() => {
                // Если сеть недоступна, пытаемся достать из кеша текущую страницу
                return caches.match(request).then(cachedResponse => {
                    // Если страницы нет, показываем offline.html
                    return cachedResponse || caches.match('/offline/');
                });
            })
        );
        return;
    }

    // Остальное -> Network Only
    event.respondWith(fetch(request));
});

// Перехват Push-уведомлений
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
            badge: '/static/icons/badge-96x96.png',
            vibrate: [100, 50, 100],
            data: {
                url: data.url || '/'
            }
        };

        event.waitUntil(
            self.registration.showNotification(data.title, options)
        );
    }
});

// Перехват клика по уведомлению
self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(windowClients => {
            const tgtUrl = event.notification.data.url;
            for (var i = 0; i < windowClients.length; i++) {
                var client = windowClients[i];
                if (client.url === tgtUrl && 'focus' in client) {
                    return client.focus();
                }
            }
            if (clients.openWindow) {
                return clients.openWindow(tgtUrl);
            }
        })
    );
});
