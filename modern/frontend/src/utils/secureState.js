/**
 * Secure state management utilities for client-side data
 */

// Security configuration for state management
const STATE_SECURITY_CONFIG = {
  // Data classification levels
  PUBLIC: "public",
  INTERNAL: "internal",
  CONFIDENTIAL: "confidential",
  RESTRICTED: "restricted",

  // Storage policies
  MAX_STORAGE_AGE: 15 * 60 * 1000, // 15 minutes
  ENCRYPTION_KEY_ROTATION: 24 * 60 * 60 * 1000, // 24 hours

  // Sensitive data patterns
  SENSITIVE_PATTERNS: [
    /password/i,
    /token/i,
    /secret/i,
    /key/i,
    /auth/i,
    /session/i,
    /credit/i,
    /payment/i,
    /personal/i,
  ],
};

// Data classification utility
class DataClassifier {
  static classify(key, value) {
    const keyLower = key.toLowerCase();
    const valueStr = typeof value === "string" ? value : JSON.stringify(value);

    // Check for restricted data (never store)
    if (
      STATE_SECURITY_CONFIG.SENSITIVE_PATTERNS.some(
        (pattern) => pattern.test(keyLower) || pattern.test(valueStr)
      )
    ) {
      return STATE_SECURITY_CONFIG.RESTRICTED;
    }

    // Classify based on data type and content
    if (
      keyLower.includes("user") &&
      (keyLower.includes("id") || keyLower.includes("email"))
    ) {
      return STATE_SECURITY_CONFIG.CONFIDENTIAL;
    }

    if (keyLower.includes("preference") || keyLower.includes("setting")) {
      return STATE_SECURITY_CONFIG.INTERNAL;
    }

    return STATE_SECURITY_CONFIG.PUBLIC;
  }
}

// Secure state storage with encryption
class SecureStateStorage {
  constructor() {
    this.encryptionKey = null;
    this.keyRotationInterval = null;
    this.initEncryption();
  }

  async initEncryption() {
    await this.rotateEncryptionKey();

    // Set up key rotation
    this.keyRotationInterval = setInterval(() => {
      this.rotateEncryptionKey();
    }, STATE_SECURITY_CONFIG.ENCRYPTION_KEY_ROTATION);
  }

  async rotateEncryptionKey() {
    try {
      const keyMaterial = await window.crypto.subtle.generateKey(
        { name: "AES-GCM", length: 256 },
        false,
        ["encrypt", "decrypt"]
      );
      this.encryptionKey = keyMaterial;
      console.log("State encryption key rotated");
    } catch (error) {
      console.error("Failed to rotate encryption key:", error);
    }
  }

  async encrypt(data) {
    if (!this.encryptionKey) {
      throw new Error("Encryption key not initialized");
    }

    try {
      const encoder = new TextEncoder();
      const iv = crypto.getRandomValues(new Uint8Array(12));
      const encodedData = encoder.encode(JSON.stringify(data));

      const encrypted = await crypto.subtle.encrypt(
        { name: "AES-GCM", iv: iv },
        this.encryptionKey,
        encodedData
      );

      return {
        encrypted: Array.from(new Uint8Array(encrypted)),
        iv: Array.from(iv),
        timestamp: Date.now(),
      };
    } catch (error) {
      console.error("State encryption failed:", error);
      throw error;
    }
  }

  async decrypt(encryptedData) {
    if (!this.encryptionKey) {
      throw new Error("Encryption key not initialized");
    }

    try {
      const decoder = new TextDecoder();

      const decrypted = await crypto.subtle.decrypt(
        { name: "AES-GCM", iv: new Uint8Array(encryptedData.iv) },
        this.encryptionKey,
        new Uint8Array(encryptedData.encrypted)
      );

      return JSON.parse(decoder.decode(decrypted));
    } catch (error) {
      console.error("State decryption failed:", error);
      throw error;
    }
  }

  // Store state securely based on classification
  setItem(key, value, classification = null) {
    const dataClass = classification || DataClassifier.classify(key, value);

    switch (dataClass) {
      case STATE_SECURITY_CONFIG.RESTRICTED:
        // Never store restricted data
        console.warn(`Attempted to store restricted data: ${key}`);
        return false;

      case STATE_SECURITY_CONFIG.CONFIDENTIAL:
        // Encrypt confidential data in sessionStorage
        this.encrypt({ value, timestamp: Date.now() })
          .then((encrypted) => {
            sessionStorage.setItem(`secure_${key}`, JSON.stringify(encrypted));
          })
          .catch((error) => {
            console.error(`Failed to store confidential data ${key}:`, error);
          });
        break;

      case STATE_SECURITY_CONFIG.INTERNAL:
        // Store internal data with timestamp in sessionStorage
        sessionStorage.setItem(
          key,
          JSON.stringify({
            value,
            timestamp: Date.now(),
            classification: dataClass,
          })
        );
        break;

      case STATE_SECURITY_CONFIG.PUBLIC:
        // Store public data normally
        localStorage.setItem(
          key,
          JSON.stringify({
            value,
            timestamp: Date.now(),
            classification: dataClass,
          })
        );
        break;
    }

    return true;
  }

  async getItem(key, classification = null) {
    const dataClass = classification || STATE_SECURITY_CONFIG.CONFIDENTIAL; // Assume confidential if unknown

    try {
      let stored;

      if (dataClass === STATE_SECURITY_CONFIG.CONFIDENTIAL) {
        // Try to get encrypted data
        stored = sessionStorage.getItem(`secure_${key}`);
        if (stored) {
          const encryptedData = JSON.parse(stored);
          const decrypted = await this.decrypt(encryptedData);

          // Check expiration
          if (
            Date.now() - decrypted.timestamp >
            STATE_SECURITY_CONFIG.MAX_STORAGE_AGE
          ) {
            this.removeItem(key, dataClass);
            return null;
          }

          return decrypted.value;
        }
      } else {
        // Get regular data
        stored = sessionStorage.getItem(key) || localStorage.getItem(key);
        if (stored) {
          const data = JSON.parse(stored);

          // Check expiration for internal data
          if (dataClass === STATE_SECURITY_CONFIG.INTERNAL) {
            if (
              Date.now() - data.timestamp >
              STATE_SECURITY_CONFIG.MAX_STORAGE_AGE
            ) {
              this.removeItem(key, dataClass);
              return null;
            }
          }

          return data.value;
        }
      }

      return null;
    } catch (error) {
      console.error(`Failed to retrieve data ${key}:`, error);
      this.removeItem(key, dataClass); // Clean up corrupted data
      return null;
    }
  }

  removeItem(key, classification = null) {
    const dataClass = classification || STATE_SECURITY_CONFIG.CONFIDENTIAL;

    if (dataClass === STATE_SECURITY_CONFIG.CONFIDENTIAL) {
      sessionStorage.removeItem(`secure_${key}`);
    }

    sessionStorage.removeItem(key);
    localStorage.removeItem(key);
  }

  // Clear all stored state
  clearAll() {
    const sessionKeys = Object.keys(sessionStorage);
    const localKeys = Object.keys(localStorage);

    sessionKeys.forEach((key) => {
      if (key.startsWith("secure_")) {
        sessionStorage.removeItem(key);
      }
    });

    [...sessionKeys, ...localKeys].forEach((key) => {
      if (
        key.includes("app_") ||
        key.includes("user_") ||
        key.includes("habit_")
      ) {
        sessionStorage.removeItem(key);
        localStorage.removeItem(key);
      }
    });

    console.log("All application state cleared");
  }

  // Cleanup expired data
  cleanup() {
    const now = Date.now();

    [sessionStorage, localStorage].forEach((storage) => {
      const keys = Object.keys(storage);

      keys.forEach((key) => {
        try {
          const item = storage.getItem(key);
          if (item) {
            const data = JSON.parse(item);
            if (
              data.timestamp &&
              now - data.timestamp > STATE_SECURITY_CONFIG.MAX_STORAGE_AGE
            ) {
              storage.removeItem(key);
            }
          }
        } catch (error) {
          // Remove corrupted items
          storage.removeItem(key);
        }
      });
    });
  }

  destroy() {
    if (this.keyRotationInterval) {
      clearInterval(this.keyRotationInterval);
    }
    this.clearAll();
  }
}

// State sanitization utilities
class StateSanitizer {
  static sanitizeUserData(userData) {
    if (!userData || typeof userData !== "object") {
      return null;
    }

    // Remove sensitive fields
    const sanitized = { ...userData };
    const sensitiveFields = [
      "password",
      "passwordHash",
      "salt",
      "totpSecret",
      "backupCodes",
      "privateKey",
      "creditCard",
      "ssn",
      "personalId",
    ];

    sensitiveFields.forEach((field) => {
      delete sanitized[field];
    });

    // Limit stored user data
    return {
      id: sanitized.id,
      email: sanitized.email,
      displayName: sanitized.displayName,
      role: sanitized.role,
      preferences: sanitized.preferences,
      lastLogin: Date.now(),
    };
  }

  static sanitizeHabits(habits) {
    if (!Array.isArray(habits)) {
      return [];
    }

    return habits.map((habit) => ({
      id: habit.id,
      title: habit.title,
      description: habit.description,
      category: habit.category,
      difficulty: habit.difficulty,
      progress: habit.progress,
      lastUpdate: Date.now(),
    }));
  }

  static sanitizeAnalytics(analytics) {
    if (!analytics || typeof analytics !== "object") {
      return null;
    }

    // Remove any personally identifiable analytics
    const sanitized = { ...analytics };
    delete sanitized.userId;
    delete sanitized.userAgent;
    delete sanitized.ipAddress;
    delete sanitized.deviceId;

    return sanitized;
  }
}

// Global secure storage instance
const secureStorage = new SecureStateStorage();

// Set up periodic cleanup
setInterval(() => {
  secureStorage.cleanup();
}, 5 * 60 * 1000); // Every 5 minutes

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  secureStorage.cleanup();
});

export {
  SecureStateStorage,
  DataClassifier,
  StateSanitizer,
  secureStorage,
  STATE_SECURITY_CONFIG,
};
