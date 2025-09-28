/**
 * Enhanced secure app store with data classification and encryption
 */
import { create } from "zustand";
import { tokenManager } from "../utils/secureAuth";
import {
  secureStorage,
  StateSanitizer,
  STATE_SECURITY_CONFIG,
} from "../utils/secureState";

// State schema with security classifications
const STATE_SCHEMA = {
  // User state (confidential)
  user: { classification: STATE_SECURITY_CONFIG.CONFIDENTIAL },
  isAuthenticated: { classification: STATE_SECURITY_CONFIG.INTERNAL },
  userPreferences: { classification: STATE_SECURITY_CONFIG.INTERNAL },

  // Application data (internal)
  habits: { classification: STATE_SECURITY_CONFIG.INTERNAL },
  projects: { classification: STATE_SECURITY_CONFIG.INTERNAL },
  analytics: { classification: STATE_SECURITY_CONFIG.INTERNAL },

  // UI state (public - but still limit storage)
  activeTab: { classification: STATE_SECURITY_CONFIG.PUBLIC },
  theme: { classification: STATE_SECURITY_CONFIG.PUBLIC },

  // Loading states (never persist)
  loading: { classification: STATE_SECURITY_CONFIG.RESTRICTED },
  habitsLoading: { classification: STATE_SECURITY_CONFIG.RESTRICTED },
  analyticsLoading: { classification: STATE_SECURITY_CONFIG.RESTRICTED },

  // Error states (never persist - may contain sensitive info)
  error: { classification: STATE_SECURITY_CONFIG.RESTRICTED },
  habitsError: { classification: STATE_SECURITY_CONFIG.RESTRICTED },
};

// Secure persistence middleware
const securePerist = (config) => (set, get, api) => {
  // Override set to handle secure persistence
  const secureSet = (partial, replace) => {
    const result = set(partial, replace);

    // Persist state securely after updates
    const currentState = get();
    persistSecureState(currentState);

    return result;
  };

  // Load initial state from secure storage
  loadSecureState().then((savedState) => {
    if (savedState && Object.keys(savedState).length > 0) {
      set(savedState, false);
    }
  });

  return config(secureSet, get, api);
};

// Persist state based on security classification
async function persistSecureState(state) {
  try {
    for (const [key, value] of Object.entries(state)) {
      const schema = STATE_SCHEMA[key];
      if (!schema) continue;

      const classification = schema.classification;

      // Only persist non-restricted data
      if (classification !== STATE_SECURITY_CONFIG.RESTRICTED) {
        let sanitizedValue = value;

        // Sanitize data before storage
        switch (key) {
          case "user":
            sanitizedValue = StateSanitizer.sanitizeUserData(value);
            break;
          case "habits":
            sanitizedValue = StateSanitizer.sanitizeHabits(value);
            break;
          case "analytics":
            sanitizedValue = StateSanitizer.sanitizeAnalytics(value);
            break;
        }

        secureStorage.setItem(`app_${key}`, sanitizedValue, classification);
      }
    }
  } catch (error) {
    console.error("Failed to persist secure state:", error);
  }
}

// Load state from secure storage
async function loadSecureState() {
  const savedState = {};

  try {
    for (const [key, schema] of Object.entries(STATE_SCHEMA)) {
      if (schema.classification !== STATE_SECURITY_CONFIG.RESTRICTED) {
        const value = await secureStorage.getItem(
          `app_${key}`,
          schema.classification
        );
        if (value !== null) {
          savedState[key] = value;
        }
      }
    }
  } catch (error) {
    console.error("Failed to load secure state:", error);
  }

  return savedState;
}

// Create secure app store
const useSecureAppStore = create(
  securePerist((set, get) => ({
    // User state
    user: null,
    isAuthenticated: false,
    userPreferences: {},

    // Application data
    habits: [],
    projects: [],
    analytics: null,

    // UI state
    activeTab: "overview",
    theme: "dark",

    // Loading states (not persisted)
    loading: false,
    habitsLoading: false,
    analyticsLoading: false,

    // Error states (not persisted)
    error: null,
    habitsError: null,

    // Secure actions
    setUser: (user) => {
      const sanitizedUser = StateSanitizer.sanitizeUserData(user);
      set({
        user: sanitizedUser,
        isAuthenticated: !!user,
      });

      if (!user) {
        tokenManager.clearToken();
        // Clear all user-related state
        get().clearUserData();
      }
    },

    setUserPreferences: (preferences) => {
      // Sanitize preferences to remove any sensitive data
      const sanitizedPreferences = {
        theme: preferences.theme,
        language: preferences.language,
        notifications: preferences.notifications,
        privacy: {
          analytics: preferences.privacy?.analytics || false,
          marketing: preferences.privacy?.marketing || false,
        },
      };

      set({ userPreferences: sanitizedPreferences });
    },

    setHabits: (habits) => {
      const sanitizedHabits = StateSanitizer.sanitizeHabits(habits);
      set({
        habits: sanitizedHabits,
        habitsLoading: false,
        habitsError: null,
      });
    },

    setAnalytics: (analytics) => {
      const sanitizedAnalytics = StateSanitizer.sanitizeAnalytics(analytics);
      set({
        analytics: sanitizedAnalytics,
        analyticsLoading: false,
      });
    },

    setTheme: (theme) => {
      // Validate theme value
      const validThemes = ["light", "dark", "auto"];
      if (validThemes.includes(theme)) {
        set({ theme });
      }
    },

    setActiveTab: (tab) => {
      // Validate tab value to prevent XSS
      const validTabs = [
        "overview",
        "habits",
        "projects",
        "analytics",
        "settings",
      ];
      if (validTabs.includes(tab)) {
        set({ activeTab: tab });
      }
    },

    // Loading state actions
    setLoading: (loading) => set({ loading }),
    setHabitsLoading: (loading) => set({ habitsLoading: loading }),
    setAnalyticsLoading: (loading) => set({ analyticsLoading: loading }),

    // Error state actions
    setError: (error) => {
      console.error("App error:", error);
      set({ error: error?.message || "An error occurred" });
    },
    setHabitsError: (error) => {
      console.error("Habits error:", error);
      set({ habitsError: error?.message || "Failed to load habits" });
    },

    // Utility actions
    clearErrors: () =>
      set({
        error: null,
        habitsError: null,
      }),

    clearUserData: () => {
      // Clear all user-related data
      set({
        user: null,
        isAuthenticated: false,
        userPreferences: {},
        habits: [],
        projects: [],
        analytics: null,
      });

      // Clear from secure storage
      secureStorage.clearAll();
    },

    // Emergency state reset
    resetState: () => {
      secureStorage.clearAll();
      set({
        user: null,
        isAuthenticated: false,
        userPreferences: {},
        habits: [],
        projects: [],
        analytics: null,
        activeTab: "overview",
        theme: "dark",
        loading: false,
        habitsLoading: false,
        analyticsLoading: false,
        error: null,
        habitsError: null,
      });
    },

    // State validation
    validateState: () => {
      const state = get();
      const issues = [];

      // Check for data consistency
      if (state.isAuthenticated && !state.user) {
        issues.push("Authenticated but no user data");
      }

      if (state.user && !state.isAuthenticated) {
        issues.push("User data present but not authenticated");
      }

      // Check for stale data
      const maxAge = 60 * 60 * 1000; // 1 hour
      if (state.user && state.user.lastLogin) {
        if (Date.now() - state.user.lastLogin > maxAge) {
          issues.push("User session may be stale");
        }
      }

      if (issues.length > 0) {
        console.warn("State validation issues:", issues);
        return false;
      }

      return true;
    },
  }))
);

// State monitoring and cleanup
let stateMonitorInterval;

// Start state monitoring
function startStateMonitoring() {
  stateMonitorInterval = setInterval(() => {
    const store = useSecureAppStore.getState();

    // Validate state periodically
    if (!store.validateState()) {
      console.warn("State validation failed, considering cleanup");
    }

    // Auto-cleanup old data
    secureStorage.cleanup();
  }, 5 * 60 * 1000); // Every 5 minutes
}

// Stop state monitoring
function stopStateMonitoring() {
  if (stateMonitorInterval) {
    clearInterval(stateMonitorInterval);
    stateMonitorInterval = null;
  }
}

// Initialize monitoring
startStateMonitoring();

// Cleanup on page unload
window.addEventListener("beforeunload", () => {
  stopStateMonitoring();
  secureStorage.cleanup();
});

// Development helpers
if (process.env.NODE_ENV === "development") {
  window.debugSecureStore = {
    getState: () => useSecureAppStore.getState(),
    clearAll: () => useSecureAppStore.getState().resetState(),
    validateState: () => useSecureAppStore.getState().validateState(),
    getStoredData: async () => {
      const data = {};
      for (const key of Object.keys(STATE_SCHEMA)) {
        data[key] = await secureStorage.getItem(`app_${key}`);
      }
      return data;
    },
  };
}

export default useSecureAppStore;
