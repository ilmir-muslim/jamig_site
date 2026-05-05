// static/service-worker.js

const CACHE_NAME = 'jamig-reader-v2';
const ASSETS_TO_CACHE = [
    '/static/css/reader.css',
    '/static/js/reader.js',
    '/static/css/style.css',
    '/static/css/studio.css',    // если понадобится в офлайне
    // можно добавить другие важные ресурсы
];

// Установка: кэшируем статику
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(ASSETS_TO_CACHE))
            .then(() => self.skipWaiting())
    );
});

// Активация: удаляем старые кэши
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys.filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

// Стратегия: для HTML‑страниц (читалка) – Network First,
// для статики – Cache First
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Страницы читалки – пытаемся загрузить с сервера, при ошибке отдаём кэш
    if (event.request.mode === 'navigate' && url.pathname.includes('/texts/')) {
        event.respondWith(
            fetch(event.request)
                .then(response => {
                    // Кэшируем свежую копию страницы
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache =>
                        cache.put(event.request, clone)
                    );
                    return response;
                })
                .catch(() =>
                    caches.match(event.request)
                )
        );
        return;
    }

    // Статические ресурсы – сначала кэш, потом сеть
    if (ASSETS_TO_CACHE.some(asset => url.pathname.endsWith(asset.replace('/static/', '')))) {
        event.respondWith(
            caches.match(event.request)
                .then(cached => cached || fetch(event.request))
        );
        return;
    }

    // Остальное – обычный запрос (не мешаем)
    event.respondWith(fetch(event.request));
});