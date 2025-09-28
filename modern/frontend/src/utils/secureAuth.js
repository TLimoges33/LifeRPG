/**
 * Secure token storage utilities
 * Uses httpOnly cookies when possible, encrypted localStorage as fallback
 */

// Simple encryption for localStorage fallback (not cryptographically secure, but better than plaintext)
const STORAGE_KEY = "app_session_encrypted";
const ENCRYPTION_KEY = "wizards_grimoire_key_v1";

function simpleEncrypt(text) {
  if (!text) return text;
  const encoded = btoa(text);
  return encoded.split("").reverse().join("");
}

function simpleDecrypt(encrypted) {
  if (!encrypted) return encrypted;
  try {
    const reversed = encrypted.split("").reverse().join("");
    return atob(reversed);
  } catch (e) {
    console.warn("Failed to decrypt token, clearing storage");
    localStorage.removeItem(STORAGE_KEY);
    return null;
  }
}

class SecureTokenManager {
  constructor() {
    this.isSecureContext = window.isSecureContext;
    this.supportsCredentials = "credentials" in fetch;
  }

  // Try to get token from httpOnly cookie first, then encrypted localStorage
  getToken() {
    // If we're using httpOnly cookies, the server will handle authentication
    // We don't need to explicitly manage tokens in JS
    if (this.supportsCredentials) {
      return null; // Let fetch handle cookie authentication
    }

    // Fallback to encrypted localStorage for non-secure contexts
    const encrypted = localStorage.getItem(STORAGE_KEY);
    return simpleDecrypt(encrypted);
  }

  // Store token securely (only for fallback scenarios)
  setToken(token) {
    if (!token) {
      this.clearToken();
      return;
    }

    // In secure contexts, prefer httpOnly cookies (handled by server)
    if (this.supportsCredentials && this.isSecureContext) {
      // Token will be set as httpOnly cookie by server
      return;
    }

    // Fallback: encrypted localStorage
    const encrypted = simpleEncrypt(token);
    localStorage.setItem(STORAGE_KEY, encrypted);
  }

  clearToken() {
    localStorage.removeItem(STORAGE_KEY);
    // Clear any potential old unencrypted tokens
    localStorage.removeItem("token");
    localStorage.removeItem("authToken");
    localStorage.removeItem("jwt");
  }

  // Check if we have authentication (for UI state)
  hasAuth() {
    // Check for httpOnly cookie by making an authenticated request
    if (this.supportsCredentials) {
      return this.checkAuthStatus();
    }

    // Fallback: check localStorage
    return !!this.getToken();
  }

  async checkAuthStatus() {
    try {
      const response = await fetch("/api/v1/auth/me", {
        method: "GET",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
      });
      return response.ok;
    } catch (e) {
      return false;
    }
  }
}

export const tokenManager = new SecureTokenManager();

// Enhanced fetch wrapper with secure authentication
export async function secureApiCall(url, options = {}) {
  const defaultOptions = {
    credentials: "include", // Include httpOnly cookies
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  };

  // Add CSRF token if available
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    defaultOptions.headers["X-CSRF-Token"] = csrfToken;
  }

  // Fallback token for non-secure contexts
  if (!tokenManager.supportsCredentials) {
    const token = tokenManager.getToken();
    if (token) {
      defaultOptions.headers["Authorization"] = `Bearer ${token}`;
    }
  }

  const response = await fetch(url, { ...defaultOptions, ...options });

  // Handle authentication errors
  if (response.status === 401) {
    tokenManager.clearToken();
    // Trigger logout in app state
    window.dispatchEvent(new CustomEvent("auth:logout"));
  }

  return response;
}

function getCsrfToken() {
  // Get CSRF token from cookie
  const cookies = document.cookie.split(";");
  for (let cookie of cookies) {
    const [name, value] = cookie.trim().split("=");
    if (name === "csrf_token") {
      return decodeURIComponent(value);
    }
  }
  return null;
}

export default tokenManager;
