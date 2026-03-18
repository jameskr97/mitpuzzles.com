self.__WB_DISABLE_DEV_LOGS = true;

import { precacheAndRoute } from 'workbox-precaching';
import { registerRoute } from 'workbox-routing';
import { NetworkFirst, CacheFirst } from 'workbox-strategies';
import { ExpirationPlugin } from 'workbox-expiration';
import { CacheableResponsePlugin } from 'workbox-cacheable-response';

// Precache all static assets
precacheAndRoute(self.__WB_MANIFEST);

// Runtime caching strategies
registerRoute(
  /^https?:\/\/[^\/]+\/api\/puzzle\/definition\/types$/,
  new NetworkFirst({
    cacheName: 'puzzle-catalog',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 60 * 60 * 24 }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
    networkTimeoutSeconds: 3,
  })
);

registerRoute(
  /^https?:\/\/[^\/]+\/api\/puzzle\/definition\/[^\/]+$/,
  new CacheFirst({
    cacheName: 'puzzle-definitions',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 60 * 5 }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
  })
);

// Daily puzzle definitions - CacheFirst since they don't change for a given date
registerRoute(
  /^https?:\/\/[^\/]+\/api\/puzzle\/daily\/[^\/]+\/definition\/[^\/]+$/,
  new CacheFirst({
    cacheName: 'daily-definitions',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 60 * 60 * 24 }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
  })
);

// Daily puzzle status
registerRoute(
  /^https?:\/\/[^\/]+\/api\/puzzle\/daily\/today$/,
  new NetworkFirst({
    cacheName: 'daily-status',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 60 * 5 }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
    networkTimeoutSeconds: 3,
  })
);

// Daily leaderboards
registerRoute(
  /^https?:\/\/[^\/]+\/api\/puzzle\/daily\/[^\/]+\/leaderboard\/[^\/]+$/,
  new NetworkFirst({
    cacheName: 'daily-leaderboards',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 60 * 5 }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
    networkTimeoutSeconds: 3,
  })
);

registerRoute(
  /^https?:\/\/[^\/]+\/api\/puzzle\/freeplay\/leaderboard/,
  new NetworkFirst({
    cacheName: 'leaderboards',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 60 * 5 }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
    networkTimeoutSeconds: 3,
  })
);

registerRoute(
  /^https:\/\/fonts\.googleapis\.com\/.*/i,
  new CacheFirst({
    cacheName: 'google-fonts-stylesheets',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 60 * 60 * 24 * 365 }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
  })
);

registerRoute(
  /^https:\/\/fonts\.gstatic\.com\/.*/i,
  new CacheFirst({
    cacheName: 'google-fonts-webfonts',
    plugins: [
      new ExpirationPlugin({ maxAgeSeconds: 60 * 60 * 24 * 365, maxEntries: 30 }),
      new CacheableResponsePlugin({ statuses: [0, 200] }),
    ],
  })
);

// Skip waiting and claim clients
self.skipWaiting();
self.clients.claim();

// Push notification handler
console.log('[Service Worker] Push handler loaded');

self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push event received!', event);
  console.log('[Service Worker] Event data:', event.data);

  let notificationData = {
    title: 'MIT Puzzles',
    body: 'You have a new notification',
    icon: '/favicon.svg',
    badge: '/favicon.svg',
  };

  if (event.data) {
    try {
      const parsed = event.data.json();
      console.log('[Service Worker] Parsed notification data:', parsed);
      notificationData = parsed;
    } catch (e) {
      console.error('[Service Worker] Error parsing push data:', e);
    }
  }

  console.log('[Service Worker] Showing notification with:', notificationData);

  const promiseChain = self.registration.showNotification(
    notificationData.title,
    {
      body: notificationData.body,
      icon: notificationData.icon || '/favicon.svg',
      badge: notificationData.badge || '/favicon.svg',
    }
  ).then(() => {
    console.log('[Service Worker] Notification shown successfully');
  }).catch((error) => {
    console.error('[Service Worker] Error showing notification:', error);
  });

  event.waitUntil(promiseChain);
});

self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked');
  event.notification.close();

  const promiseChain = clients
    .matchAll({ type: 'window', includeUncontrolled: true })
    .then((windowClients) => {
      if (windowClients.length > 0) {
        return windowClients[0].focus();
      }
      if (clients.openWindow) {
        return clients.openWindow('/');
      }
    });

  event.waitUntil(promiseChain);
});
