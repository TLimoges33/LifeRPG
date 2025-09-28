const CACHE_NAME = "liferpg-v1.0.0";
const OFFLINE_URL = "/offline.html";
const API_CACHE_NAME = "api-cache-v1";

// Resources to cache immediately
const STATIC_CACHE_URLS = [
  "/",
  "/static/js/bundle.js",
  "/static/css/main.css",
  "/manifest.json",
  "/icon-72x72.png",
  "/icon-96x96.png",
  "/icon-128x128.png",
  "/icon-144x144.png",
  "/icon-152x152.png",
  "/icon-192x192.png",
  "/icon-384x384.png",
  "/icon-512x512.png",
  OFFLINE_URL,
];

// API endpoints to cache
const API_CACHE_PATTERNS = [
  /\/api\/v1\/habits$/,
  /\/api\/v1\/habits\/today$/,
  /\/api\/v1\/user\/profile$/,
  /\/api\/v1\/analytics/,
  /\/api\/v1\/gamification/,
];

// Install event - cache static resources
self.addEventListener("install", (event) => {
  console.log("Service Worker: Installing...");

  event.waitUntil(
    (async () => {
      try {
        const cache = await caches.open(CACHE_NAME);
        console.log("Service Worker: Caching static resources");
        await cache.addAll(STATIC_CACHE_URLS);

        // Force activation of the new service worker
        await self.skipWaiting();
      } catch (error) {
        console.error(
          "Service Worker: Failed to cache static resources",
          error
        );
      }
    })()
  );
});

// Activate event - clean up old caches
self.addEventListener("activate", (event) => {
  console.log("Service Worker: Activating...");

  event.waitUntil(
    (async () => {
      try {
        const cacheNames = await caches.keys();
        await Promise.all(
          cacheNames
            .filter(
              (cacheName) =>
                cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME
            )
            .map((cacheName) => {
              console.log("Service Worker: Deleting old cache", cacheName);
              return caches.delete(cacheName);
            })
        );

        // Take control of all clients
        await self.clients.claim();
      } catch (error) {
        console.error("Service Worker: Failed to activate", error);
      }
    })()
  );
});

// Fetch event - serve cached content when offline
self.addEventListener("fetch", (event) => {
  // Skip non-GET requests for modification requests
  const url = new URL(event.request.url);

  // Skip chrome-extension requests
  if (event.request.url.startsWith("chrome-extension://")) return;

  event.respondWith(
    (async () => {
      try {
        // Handle API requests
        if (url.pathname.startsWith("/api/")) {
          return await handleApiRequest(event.request);
        }

        // Handle navigation requests
        if (event.request.mode === "navigate") {
          return await handleNavigationRequest(event.request);
        }

        // Handle static resource requests
        return await handleStaticRequest(event.request);
      } catch (error) {
        console.error("Service Worker: Fetch error", error);
        return await handleFallback(event.request);
      }
    })()
  );
});

// Handle API requests with cache-first strategy for GET requests
async function handleApiRequest(request) {
  const url = new URL(request.url);
  const shouldCache = API_CACHE_PATTERNS.some((pattern) =>
    pattern.test(url.pathname)
  );

  if (shouldCache && request.method === "GET") {
    try {
      // Try cache first for API requests
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        // Return cached response and update in background
        updateApiCache(request);
        return cachedResponse;
      }

      // Fetch from network and cache
      const response = await fetch(request);
      if (response.ok) {
        const cache = await caches.open(API_CACHE_NAME);
        cache.put(request, response.clone());
      }
      return response;
    } catch (error) {
      // Return cached version if network fails
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        return cachedResponse;
      }
      throw error;
    }
  }

  // For non-cached API requests, try network first
  try {
    const response = await fetch(request);

    // If it's a POST/PUT/DELETE request that modifies data, store it for sync
    if (["POST", "PUT", "DELETE"].includes(request.method)) {
      await storeOfflineAction(request);
    }

    return response;
  } catch (error) {
    // Store the action for later sync
    if (["POST", "PUT", "DELETE"].includes(request.method)) {
      await storeOfflineAction(request);
      return new Response(JSON.stringify({ success: true, offline: true }), {
        headers: { "Content-Type": "application/json" },
      });
    }
    throw error;
  }
}

// Handle navigation requests
async function handleNavigationRequest(request) {
  try {
    const response = await fetch(request);
    return response;
  } catch (error) {
    // Return cached version or offline page
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }

    const offlineResponse = await caches.match(OFFLINE_URL);
    return offlineResponse || new Response("Offline", { status: 200 });
  }
}

// Handle static resource requests
async function handleStaticRequest(request) {
  // Try cache first for static resources
  const cachedResponse = await caches.match(request);
  if (cachedResponse) {
    return cachedResponse;
  }

  // If not in cache, fetch from network
  try {
    const response = await fetch(request);

    // Cache successful responses
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    throw error;
  }
}

// Fallback handler
async function handleFallback(request) {
  if (request.mode === "navigate") {
    const offlineResponse = await caches.match(OFFLINE_URL);
    return offlineResponse || new Response("Offline", { status: 200 });
  }

  return new Response("Resource not available offline", { status: 503 });
}

// Update API cache in background
async function updateApiCache(request) {
  try {
    const response = await fetch(request);
    if (response.ok) {
      const cache = await caches.open(API_CACHE_NAME);
      await cache.put(request, response);
    }
  } catch (error) {
    console.log("Background update failed:", error);
  }
}

// Store offline actions for later sync
async function storeOfflineAction(request) {
  try {
    const action = {
      url: request.url,
      method: request.method,
      headers: Object.fromEntries(request.headers.entries()),
      body: await request.text(),
      timestamp: Date.now(),
    };

    const existingActions = await getStoredActions();
    existingActions.push(action);

    // Store in IndexedDB or localStorage fallback
    const storage = await getOfflineStorage();
    await storage.setItem("offline-actions", JSON.stringify(existingActions));
  } catch (error) {
    console.error("Failed to store offline action:", error);
  }
}

// Get stored offline actions
async function getStoredActions() {
  try {
    const storage = await getOfflineStorage();
    const actions = await storage.getItem("offline-actions");
    return actions ? JSON.parse(actions) : [];
  } catch (error) {
    console.error("Failed to get stored actions:", error);
    return [];
  }
}

// Simple storage abstraction
async function getOfflineStorage() {
  // Try to use IndexedDB, fallback to cache storage
  return {
    async getItem(key) {
      const cache = await caches.open("offline-storage");
      const response = await cache.match(`/${key}`);
      return response ? await response.text() : null;
    },

    async setItem(key, value) {
      const cache = await caches.open("offline-storage");
      await cache.put(`/${key}`, new Response(value));
    },
  };
}

// Background sync event
self.addEventListener("sync", (event) => {
  if (event.tag === "background-sync") {
    event.waitUntil(syncOfflineActions());
  }
});

// Sync offline actions when back online
async function syncOfflineActions() {
  try {
    const actions = await getStoredActions();
    const successfulSyncs = [];

    for (const action of actions) {
      try {
        const request = new Request(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body || undefined,
        });

        const response = await fetch(request);

        if (response.ok) {
          successfulSyncs.push(action);
        }
      } catch (error) {
        console.error("Failed to sync action:", error);
      }
    }

    // Remove successfully synced actions
    if (successfulSyncs.length > 0) {
      const remainingActions = actions.filter(
        (action) => !successfulSyncs.includes(action)
      );

      const storage = await getOfflineStorage();
      await storage.setItem(
        "offline-actions",
        JSON.stringify(remainingActions)
      );
    }
  } catch (error) {
    console.error("Background sync failed:", error);
  }
}

// Push notification event
self.addEventListener("push", (event) => {
  if (!event.data) return;

  try {
    const data = event.data.json();

    const options = {
      body: data.body || "Time to practice your magical habits!",
      icon: "/icon-192x192.png",
      badge: "/icon-72x72.png",
      image: data.image,
      vibrate: [200, 100, 200],
      data: {
        url: data.url || "/",
        action: data.action || "open",
      },
      actions: [
        {
          action: "complete",
          title: "✓ Mark Complete",
          icon: "/icon-72x72.png",
        },
        {
          action: "view",
          title: "👁 View Details",
          icon: "/icon-72x72.png",
        },
      ],
      requireInteraction: true,
      tag: data.tag || "habit-reminder",
    };

    event.waitUntil(
      self.registration.showNotification(
        data.title || "🧙‍♂️ Grimoire Reminder",
        options
      )
    );
  } catch (error) {
    console.error("Push notification error:", error);
  }
});

// Notification click event
self.addEventListener("notificationclick", (event) => {
  event.notification.close();

  const action = event.action;
  const data = event.notification.data;

  if (action === "complete") {
    // Handle habit completion
    event.waitUntil(handleHabitCompletion(data));
  } else {
    // Open the app
    event.waitUntil(clients.openWindow(data.url || "/"));
  }
});

// Handle habit completion from notification
async function handleHabitCompletion(data) {
  try {
    if (data.habitId) {
      // Store completion for sync
      await storeOfflineAction(
        new Request(`/api/v1/habits/${data.habitId}/complete`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ completedAt: new Date().toISOString() }),
        })
      );

      // Show success notification
      await self.registration.showNotification("✅ Habit Completed!", {
        body: "Great job! Your progress has been recorded.",
        icon: "/icon-192x192.png",
        tag: "completion-success",
      });
    }
  } catch (error) {
    console.error("Failed to complete habit:", error);
  }
}

console.log("Service Worker: Loaded");
