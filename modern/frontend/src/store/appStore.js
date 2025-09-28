import { create } from "zustand";
import { tokenManager } from "../utils/secureAuth";

const useAppStore = create((set, get) => ({
  // User state
  user: null,
  isAuthenticated: false,
  loading: false,

  // Habits state
  habits: [],
  habitsLoading: false,
  habitsError: null,

  // Analytics state
  analytics: null,
  analyticsLoading: false,

  // UI state
  activeTab: "overview",
  theme: "dark",

  // Actions
  setUser: (user) => {
    set({ user, isAuthenticated: !!user });
    // Don't store user data in localStorage for security
    if (!user) {
      tokenManager.clearToken();
    }
  },

  setLoading: (loading) => set({ loading }),

  logout: () => {
    tokenManager.clearToken();
    set({
      user: null,
      isAuthenticated: false,
      habits: [],
      analytics: null,
    });
  },

  setActiveTab: (activeTab) => set({ activeTab }),

  // Habit actions
  setHabits: (habits) =>
    set({ habits, habitsLoading: false, habitsError: null }),

  setHabitsLoading: (habitsLoading) => set({ habitsLoading }),

  setHabitsError: (habitsError) => set({ habitsError, habitsLoading: false }),

  addHabit: (habit) =>
    set((state) => ({
      habits: [...state.habits, habit],
    })),

  updateHabit: (habitId, updates) =>
    set((state) => ({
      habits: state.habits.map((habit) =>
        habit.id === habitId ? { ...habit, ...updates } : habit
      ),
    })),

  deleteHabit: (habitId) =>
    set((state) => ({
      habits: state.habits.filter((habit) => habit.id !== habitId),
    })),

  // Analytics actions
  setAnalytics: (analytics) => set({ analytics, analyticsLoading: false }),

  setAnalyticsLoading: (analyticsLoading) => set({ analyticsLoading }),

  // Auth actions
  login: async (credentials) => {
    set({ loading: true });
    try {
      const response = await fetch("/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(credentials),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.access_token);
        set({ user: data.user, isAuthenticated: true, loading: false });
        return { success: true };
      } else {
        const error = await response.json();
        set({ loading: false });
        return { success: false, error: error.detail || "Login failed" };
      }
    } catch (error) {
      set({ loading: false });
      return { success: false, error: "Network error" };
    }
  },

  register: async (userData) => {
    set({ loading: true });
    try {
      const response = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(userData),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem("token", data.access_token);
        set({ user: data.user, isAuthenticated: true, loading: false });
        return { success: true };
      } else {
        const error = await response.json();
        set({ loading: false });
        return { success: false, error: error.detail || "Registration failed" };
      }
    } catch (error) {
      set({ loading: false });
      return { success: false, error: "Network error" };
    }
  },

  logout: () => {
    localStorage.removeItem("token");
    set({
      user: null,
      isAuthenticated: false,
      habits: [],
      analytics: null,
    });
  },

  checkAuth: async () => {
    const token = localStorage.getItem("token");
    if (!token) {
      set({ loading: false });
      return;
    }

    try {
      const response = await fetch("/api/v1/me", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const user = await response.json();
        set({ user, isAuthenticated: true, loading: false });
      } else {
        localStorage.removeItem("token");
        set({ loading: false });
      }
    } catch (error) {
      localStorage.removeItem("token");
      set({ loading: false });
    }
  },

  // Fetch habits
  fetchHabits: async () => {
    const token = localStorage.getItem("token");
    if (!token) return;

    set({ habitsLoading: true });
    try {
      const response = await fetch("/api/v1/habits", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const habits = await response.json();
        set({ habits, habitsLoading: false, habitsError: null });
      } else {
        set({ habitsError: "Failed to fetch habits", habitsLoading: false });
      }
    } catch (error) {
      set({ habitsError: "Network error", habitsLoading: false });
    }
  },

  // Create habit
  createHabit: async (habitData) => {
    const token = localStorage.getItem("token");
    if (!token) return { success: false, error: "Not authenticated" };

    try {
      const response = await fetch("/api/v1/habits", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(habitData),
      });

      if (response.ok) {
        const habit = await response.json();
        get().addHabit(habit);
        return { success: true, habit };
      } else {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || "Failed to create habit",
        };
      }
    } catch (error) {
      return { success: false, error: "Network error" };
    }
  },

  // Mark habit complete
  markHabitComplete: async (habitId) => {
    const token = localStorage.getItem("token");
    if (!token) return { success: false, error: "Not authenticated" };

    try {
      const response = await fetch(`/api/v1/habits/${habitId}/complete`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const result = await response.json();
        // Update the habit in state with new completion data
        get().updateHabit(habitId, {
          completed_today: true,
          last_completed: new Date().toISOString(),
        });
        return { success: true, result };
      } else {
        const error = await response.json();
        return {
          success: false,
          error: error.detail || "Failed to mark complete",
        };
      }
    } catch (error) {
      return { success: false, error: "Network error" };
    }
  },
}));

export default useAppStore;
