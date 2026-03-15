// AgriLink Service Worker v1.0
const CACHE_NAME = 'agrilink-v3';

// Pages/assets to cache for offline use
const STATIC_ASSETS = [
  '/home/',
  '/static/manifest.json',
  '/offline/',
];

// ✅ Install Event — Cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing AgriLink Service Worker...');
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Caching static assets');
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// ✅ Activate Event — Clean old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating AgriLink Service Worker...');
  event.waitUntil(
    caches.keys().then((cacheNames) =>
      Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      )
    )
  );
  self.clients.claim();
});

// ✅ Fetch Event — Network first, fallback to cache
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests and Chrome extension requests
  if (event.request.method !== 'GET') return;
  if (event.request.url.startsWith('chrome-extension://')) return;

  // Skip POST/API calls (login, register, orders)
  const url = new URL(event.request.url);
  const skipPaths = ['/farmer_login/', '/retailer_login/', '/driver/login/',
                     '/farmer_register/', '/retailer_register/', '/driver/register/',
                     '/admin/'];
  if (skipPaths.some(path => url.pathname.startsWith(path))) return;

  event.respondWith(
    fetch(event.request)
      .then((networkResponse) => {
        // Cache successful GET responses
        if (networkResponse && networkResponse.status === 200) {
          const cloned = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(event.request, cloned);
          });
        }
        return networkResponse;
      })
      .catch(() => {
        // Offline fallback — serve from cache
        return caches.match(event.request).then((cachedResponse) => {
          if (cachedResponse) return cachedResponse;
          // If page not cached, show offline page
          if (event.request.destination === 'document') {
            return caches.match('/offline/');
          }
        });
      })
  );
});

// ✅ Push Notifications (future use)
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'AgriLink 🌾';
  const options = {
    body: data.body || 'You have a new update!',
    icon: '/static/images/icon-192x192.png',
    badge: '/static/images/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: { url: data.url || '/home/' },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

// ✅ Notification Click
self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/home/')
  );
});