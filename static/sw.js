// Service Worker для KCLC Красноярск
// Версия кэша - обновляйте при изменении файлов
const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `kclc-cache-${CACHE_VERSION}`;

// Файлы для кэширования (основные ресурсы)
const STATIC_FILES = [
    '/',
    '/static/css/base.css',
    '/static/js/base.js',
    '/static/js/pwa-install.js',
    '/static/manifest.json',
    '/static/icons/favicon.ico',
    '/static/icons/favicon-32x32.png',
    '/static/icons/favicon-16x16.png',
    '/static/icons/apple-touch-icon.png',
    '/static/img/logo.png',
    '/offline/',
];

// URL-адреса API, которые НЕ кэшируем
const EXCLUDED_URLS = [
    '/api/',
    '/admin/',
    '/media/',
];

// Устанавливаем Service Worker
self.addEventListener('install', (event) => {
    console.log('[SW] Установка Service Worker', CACHE_VERSION);
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Кэширование статических файлов');
                return cache.addAll(STATIC_FILES);
            })
            .then(() => {
                console.log('[SW] Установка завершена');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Ошибка при установке:', error);
            })
    );
});

// Активируем Service Worker
self.addEventListener('activate', (event) => {
    console.log('[SW] Активация Service Worker', CACHE_VERSION);
    
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((name) => {
                            // Удаляем старые кэши
                            return name !== CACHE_NAME;
                        })
                        .map((name) => {
                            console.log('[SW] Удаление старого кэша:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Активация завершена');
                return self.clients.claim();
            })
            .catch((error) => {
                console.error('[SW] Ошибка при активации:', error);
            })
    );
});

// Перехватываем запросы
self.addEventListener('fetch', (event) => {
    const requestUrl = event.request.url;
    
    // Проверяем, нужно ли кэшировать этот запрос
    const shouldCache = !EXCLUDED_URLS.some((url) => requestUrl.includes(url));
    
    if (!shouldCache) {
        // API-запросы и админку не кэшируем
        return;
    }
    
    event.respondWith(
        caches.match(event.request)
            .then((cachedResponse) => {
                // Если есть в кэше - возвращаем
                if (cachedResponse) {
                    // Обновляем кэш в фоне (stale-while-revalidate)
                    fetch(event.request)
                        .then((networkResponse) => {
                            if (networkResponse && networkResponse.status === 200) {
                                caches.open(CACHE_NAME)
                                    .then((cache) => {
                                        cache.put(event.request, networkResponse.clone());
                                    });
                            }
                        })
                        .catch(() => {
                            // Ошибка сети - используем кэш
                        });
                    
                    return cachedResponse;
                }
                
                // Если нет в кэше - запрашиваем из сети
                return fetch(event.request)
                    .then((networkResponse) => {
                        // Если ответ успешный - сохраняем в кэш
                        if (networkResponse && networkResponse.status === 200) {
                            const responseClone = networkResponse.clone();
                            caches.open(CACHE_NAME)
                                .then((cache) => {
                                    cache.put(event.request, responseClone);
                                })
                                .catch((error) => {
                                    console.warn('[SW] Не удалось сохранить в кэш:', error);
                                });
                        }
                        return networkResponse;
                    })
                    .catch((error) => {
                        console.warn('[SW] Ошибка при запросе:', error);
                        
                        // Если запрос на HTML-страницу - показываем offline.html
                        const acceptHeader = event.request.headers.get('Accept') || '';
                        if (acceptHeader.includes('text/html')) {
                            return caches.match('/offline/');
                        }
                        
                        // Для остальных - возвращаем ошибку
                        return new Response('Офлайн-режим', {
                            status: 503,
                            statusText: 'Service Unavailable',
                        });
                    });
            })
    );
});

// Обработка push-уведомлений
self.addEventListener('push', (event) => {
    console.log('[SW] Получено push-уведомление');
    
    let data = {
        title: 'KCLC Красноярск',
        body: 'Новое уведомление',
        url: '/',
        icon: '/static/icons/apple-touch-icon.png',
        badge: '/static/icons/favicon-32x32.png',
    };
    
    try {
        if (event.data) {
            data = event.data.json();
        }
    } catch (e) {
        // Если пришла строка
        try {
            const parsed = JSON.parse(event.data.text());
            data = { ...data, ...parsed };
        } catch (e2) {
            // Если не JSON, используем как тело
            data.body = event.data.text();
        }
    }
    
    const options = {
        body: data.body,
        icon: data.icon || '/static/icons/apple-touch-icon.png',
        badge: data.badge || '/static/icons/favicon-32x32.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/',
        },
        actions: [
            {
                action: 'open',
                title: 'Открыть',
            },
            {
                action: 'close',
                title: 'Закрыть',
            },
        ],
    };
    
    event.waitUntil(
        self.registration.showNotification(data.title, options)
    );
});

// Обработка кликов по уведомлениям
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Клик по уведомлению');
    
    event.notification.close();
    
    const url = event.notification.data?.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window' })
            .then((clientList) => {
                // Если уже есть открытое окно - переключаемся на него
                for (const client of clientList) {
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }
                // Иначе открываем новое окно
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});