const CACHE_NAME = "wizards-grimoire-v1.0.0";
const OFFLINE_URL = "/offline.html";
const API_CACHE_NAME = "api-cache-v1";
const SECURE_CACHE_NAME = "secure-cache-v1";

// Security configuration
const SECURITY_CONFIG = {
  // Cache security policies
  cacheSecurityHeaders: true,
  encryptSensitiveData: true,
  maxCacheAge: 24 * 60 * 60 * 1000, // 24 hours

  // CSP configuration
  contentSecurityPolicy:
    "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:; font-src 'self'; object-src 'none'; media-src 'self'; frame-src 'none';",

  // Allowed origins for API requests
  allowedOrigins: [
    "https://wizardsgrimoire.com",
    "https://api.wizardsgrimoire.com",
    "http://localhost:3000", // Development only
    "http://localhost:8000", // Development only
  ],

  // Sensitive data patterns (never cache these)
  sensitivePatterns: [
    /\/api\/.*\/auth/,
    /\/api\/.*\/login/,
    /\/api\/.*\/2fa/,
    /\/api\/.*\/token/,
    /\/api\/.*\/password/,
    /\/api\/.*\/gdpr/,
  ],

  // Cacheable patterns with encryption
  secureCachePatterns: [
    /\/api\/v1\/habits$/,
    /\/api\/v1\/user\/profile$/,
    /\/api\/v1\/analytics/,
  ],
};

// Resources to cache immediately (only non-sensitive)
const STATIC_CACHE_URLS = [
  "/",
  "/static/js/bundle.js",
  "/static/css/main.css",
  "/manifest.json",
  "/icon-192x192.png",
  "/icon-512x512.png",
  OFFLINE_URL,
];

// Simple encryption for cached sensitive data
class CacheEncryption {
  static async encrypt(data, key = "wizards-grimoire-cache-key") {
    try {
      const encoder = new TextEncoder();
      const keyData = encoder.encode(key);
      const cryptoKey = await crypto.subtle.importKey(
        "raw",
        keyData,
        { name: "AES-GCM" },
        false,
        ["encrypt"]
      );

      const iv = crypto.getRandomValues(new Uint8Array(12));
      const encodedData = encoder.encode(JSON.stringify(data));

      const encrypted = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        cryptoKey,
        encodedData
      );

      return {
        encrypted: Array.from(new Uint8Array(encrypted)),
        iv: Array.from(iv),
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error("Cache encryption failed:", error);
      return null;
    }
  }

  static async decrypt(encryptedData, key = "wizards-grimoire-cache-key") {
    try {
      const encoder = new TextEncoder();
      const decoder = new TextDecoder();
      const keyData = encoder.encode(key);

      const cryptoKey = await crypto.subtle.importKey(
        "raw",
        keyData,
        { name: "AES-GCM" },
        false,
        ["decrypt"]
      );

      const decrypted = await crypto.subtle.decrypt(
        {
          name: "AES-GCM",
          iv: new Uint8Array(encryptedData.iv),
        },
        cryptoKey,
        new Uint8Array(encryptedData.encrypted)
      );

      return JSON.parse(decoder.decode(decrypted));
    } catch (error) {
      console.error("Cache decryption failed:", error);
      return null;
    }
  }
}

// Security utilities
function isSensitiveRequest(url) {
  return SECURITY_CONFIG.sensitivePatterns.some((pattern) => pattern.test(url));
}

function isAllowedOrigin(origin) {
  return SECURITY_CONFIG.allowedOrigins.includes(origin);
}

function shouldEncryptCache(url) {
  return SECURITY_CONFIG.secureCachePatterns.some((pattern) =>
    pattern.test(url)
  );
}

function sanitizeResponse(response, url) {
  // Remove sensitive headers from cached responses
  const sanitizedHeaders = new Headers();

  // Copy safe headers only
  const safeHeaders = [
    "content-type",
    "cache-control",
    "expires",
    "last-modified",
    "etag",
  ];

  safeHeaders.forEach((header) => {
    if (response.headers.has(header)) {
      sanitizedHeaders.set(header, response.headers.get(header));
    }
  });

  // Add security headers
  sanitizedHeaders.set("X-Cached-By", "ServiceWorker");
  sanitizedHeaders.set("X-Cache-Timestamp", new Date().toISOString());

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: sanitizedHeaders,
  });
}

// Install event - cache static resources securely
self.addEventListener("install", (event) => {
  console.log("Secure Service Worker: Installing...");

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
  console.log("Secure Service Worker: Activating...");

  event.waitUntil(
    (async () => {
      try {
        const cacheNames = await caches.keys();

        // Delete old caches
        await Promise.all(
          cacheNames.map(async (cacheName) => {
            if (
              cacheName !== CACHE_NAME &&
              cacheName !== API_CACHE_NAME &&
              cacheName !== SECURE_CACHE_NAME
            ) {
              console.log("Service Worker: Deleting old cache", cacheName);
              await caches.delete(cacheName);
            }
          })
        );

        // Take control of all clients
        await self.clients.claim();
      } catch (error) {
        console.error("Service Worker: Activation failed", error);
      }
    })()
  );
});

// Fetch event - secure request handling
self.addEventListener("fetch", (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Security checks
  if (!isAllowedOrigin(url.origin) && url.origin !== self.location.origin) {
    console.warn(
      "Service Worker: Blocked request to unauthorized origin",
      url.origin
    );
    return;
  }

  // Never cache sensitive requests
  if (isSensitiveRequest(url.pathname)) {
    console.log(
      "Service Worker: Bypassing cache for sensitive request",
      url.pathname
    );
    event.respondWith(fetch(request));
    return;
  }

  event.respondWith(
    (async () => {
      try {
        // Try cache first for static resources
        if (request.method === "GET") {
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            // Check cache age
            const cacheTimestamp =
              cachedResponse.headers.get("X-Cache-Timestamp");
            if (cacheTimestamp) {
              const age = Date.now() - new Date(cacheTimestamp).getTime();
              if (age > SECURITY_CONFIG.maxCacheAge) {
                console.log(
                  "Service Worker: Cache expired, fetching fresh",
                  url.pathname
                );
                // Cache expired, fetch fresh
              } else {
                console.log("Service Worker: Serving from cache", url.pathname);
                return cachedResponse;
              }
            } else {
              return cachedResponse;
            }
          }
        }

        // Fetch from network
        const response = await fetch(request);

        // Cache successful GET responses
        if (request.method === "GET" && response.status === 200) {
          try {
            const cache = await caches.open(
              shouldEncryptCache(url.pathname) ? SECURE_CACHE_NAME : CACHE_NAME
            );

            // Sanitize response before caching
            const sanitizedResponse = sanitizeResponse(
              response.clone(),
              url.pathname
            );

            // For secure endpoints, encrypt the data
            if (
              shouldEncryptCache(url.pathname) &&
              SECURITY_CONFIG.encryptSensitiveData
            ) {
              const responseData = await response.clone().json();
              const encryptedData = await CacheEncryption.encrypt(responseData);

              if (encryptedData) {
                const encryptedResponse = new Response(
                  JSON.stringify({
                    encrypted: true,
                    data: encryptedData,
                  }),
                  {
                    headers: sanitizedResponse.headers,
                  }
                );
                await cache.put(request, encryptedResponse);
              }
            } else {
              await cache.put(request, sanitizedResponse);
            }
          } catch (cacheError) {
            console.warn(
              "Service Worker: Failed to cache response",
              cacheError
            );
          }
        }

        return response;
      } catch (error) {
        console.error("Service Worker: Fetch failed", error);

        // Return offline page for navigation requests
        if (request.mode === "navigate") {
          const offlineResponse = await caches.match(OFFLINE_URL);
          if (offlineResponse) {
            return offlineResponse;
          }
        }

        // Return basic error response
        return new Response(
          JSON.stringify({
            error: "Network error",
            message: "Unable to fetch resource",
            offline: true,
          }),
          {
            status: 503,
            headers: {
              "Content-Type": "application/json",
              "X-Error-Source": "ServiceWorker",
            },
          }
        );
      }
    })()
  );
});

// Message handling for cache management
self.addEventListener("message", (event) => {
  if (event.data && event.data.type) {
    switch (event.data.type) {
      case "CLEAR_CACHE":
        clearCache();
        break;
      case "CLEAR_SENSITIVE_CACHE":
        clearSensitiveCache();
        break;
      case "UPDATE_SECURITY_CONFIG":
        // In a real implementation, validate and update security config
        console.log("Service Worker: Security config update requested");
        break;
    }
  }
});

async function clearCache() {
  try {
    const cacheNames = await caches.keys();
    await Promise.all(cacheNames.map((name) => caches.delete(name)));
    console.log("Service Worker: All caches cleared");
  } catch (error) {
    console.error("Service Worker: Failed to clear cache", error);
  }
}

async function clearSensitiveCache() {
  try {
    await caches.delete(SECURE_CACHE_NAME);
    console.log("Service Worker: Sensitive cache cleared");
  } catch (error) {
    console.error("Service Worker: Failed to clear sensitive cache", error);
  }
}
