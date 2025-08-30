import { useState, useEffect, useCallback } from 'react';
import { offlineDataManager, ensureInitialized } from '../lib/offlineDataManager';
import { syncEngine } from '../lib/sync';
import type { SyncStatus } from '../lib/sync';

// Enhanced sync hook with offline data manager integration
export function useSync() {
    const [syncStatus, setSyncStatus] = useState<SyncStatus>({
        lastSync: 0,
        pendingChanges: 0,
        syncInProgress: false,
    });

    useEffect(() => {
        // Initialize and get sync status
        const initSync = async () => {
            await ensureInitialized();
            const status = await syncEngine.getSyncStatus();
            setSyncStatus(status);
        };

        initSync();

        // Listen for sync status updates
        const unsubscribe = syncEngine.addSyncListener(setSyncStatus);

        return unsubscribe;
    }, []);

    const sync = useCallback(async () => {
        return await syncEngine.syncChanges();
    }, []);

    const fullSync = useCallback(async () => {
        return await syncEngine.fullSync();
    }, []);

    return {
        syncStatus,
        sync,
        fullSync,
    };
}

// Hook for habit management with offline support
export function useHabits() {
    const [habits, setHabits] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadHabits = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            await ensureInitialized();
            const habitData = await offlineDataManager.getHabits();
            setHabits(habitData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load habits');
        } finally {
            setLoading(false);
        }
    }, []);

    const createHabit = useCallback(async (habit: { title: string; description?: string; category: string }) => {
        try {
            await offlineDataManager.createHabit(habit);
            await loadHabits(); // Refresh habits
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create habit');
            throw err;
        }
    }, [loadHabits]);

    const updateHabit = useCallback(async (id: number, updates: any) => {
        try {
            await offlineDataManager.updateHabit(id, updates);
            await loadHabits(); // Refresh habits
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update habit');
            throw err;
        }
    }, [loadHabits]);

    const deleteHabit = useCallback(async (id: number) => {
        try {
            await offlineDataManager.deleteHabit(id);
            await loadHabits(); // Refresh habits
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete habit');
            throw err;
        }
    }, [loadHabits]);

    const completeHabit = useCallback(async (id: number) => {
        try {
            const result = await offlineDataManager.completeHabit(id);
            await loadHabits(); // Refresh habits
            return result;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to complete habit');
            throw err;
        }
    }, [loadHabits]);

    useEffect(() => {
        loadHabits();
    }, [loadHabits]);

    return {
        habits,
        loading,
        error,
        refetch: loadHabits,
        createHabit,
        updateHabit,
        deleteHabit,
        completeHabit,
    };
}

// Hook for analytics data with caching
export function useAnalytics() {
    const [analytics, setAnalytics] = useState<any[]>([]);
    const [overallStats, setOverallStats] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadAnalytics = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            await ensureInitialized();

            const [analyticsData, statsData] = await Promise.all([
                offlineDataManager.getHabitAnalytics(),
                offlineDataManager.getOverallStats(),
            ]);

            setAnalytics(analyticsData);
            setOverallStats(statsData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load analytics');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadAnalytics();
    }, [loadAnalytics]);

    return {
        analytics,
        overallStats,
        loading,
        error,
        refetch: loadAnalytics,
    };
}

// Hook for achievements with progress tracking
export function useAchievements() {
    const [achievements, setAchievements] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadAchievements = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            await ensureInitialized();
            const achievementData = await offlineDataManager.getAchievements();
            setAchievements(achievementData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load achievements');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadAchievements();
    }, [loadAchievements]);

    const unlockedAchievements = achievements.filter(a => a.unlocked);
    const lockedAchievements = achievements.filter(a => !a.unlocked);

    return {
        achievements,
        unlockedAchievements,
        lockedAchievements,
        loading,
        error,
        refetch: loadAchievements,
    };
}

// Hook for user profile with level progression
export function useProfile() {
    const [profile, setProfile] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadProfile = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            await ensureInitialized();
            const profileData = await offlineDataManager.getUserProfile();
            setProfile(profileData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load profile');
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadProfile();
    }, [loadProfile]);

    return {
        profile,
        loading,
        error,
        refetch: loadProfile,
    };
}

// Hook for specific habit details and history
export function useHabitDetail(habitId: number) {
    const [habit, setHabit] = useState<any>(null);
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const loadHabitDetail = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            await ensureInitialized();

            const habits = await offlineDataManager.getHabits();
            const habitData = habits.find(h => h.id === habitId);

            if (!habitData) {
                throw new Error('Habit not found');
            }

            const historyData = await offlineDataManager.getHabitHistory(habitId, 30);

            setHabit(habitData);
            setHistory(historyData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load habit details');
        } finally {
            setLoading(false);
        }
    }, [habitId]);

    const updateHabit = useCallback(async (updates: any) => {
        try {
            await offlineDataManager.updateHabit(habitId, updates);
            await loadHabitDetail(); // Refresh data
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to update habit');
            throw err;
        }
    }, [habitId, loadHabitDetail]);

    const deleteHabit = useCallback(async () => {
        try {
            await offlineDataManager.deleteHabit(habitId);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete habit');
            throw err;
        }
    }, [habitId]);

    const completeHabit = useCallback(async () => {
        try {
            const result = await offlineDataManager.completeHabit(habitId);
            await loadHabitDetail(); // Refresh data
            return result;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to complete habit');
            throw err;
        }
    }, [habitId, loadHabitDetail]);

    useEffect(() => {
        loadHabitDetail();
    }, [loadHabitDetail]);

    return {
        habit,
        history,
        loading,
        error,
        refetch: loadHabitDetail,
        updateHabit,
        deleteHabit,
        completeHabit,
    };
}

// Hook for connection status and offline awareness
export function useOfflineStatus() {
    const [isOnline, setIsOnline] = useState(true);
    const [lastSync, setLastSync] = useState<Date | null>(null);

    useEffect(() => {
        const checkConnection = async () => {
            try {
                // Simple connectivity check
                const response = await fetch('https://www.google.com/favicon.ico', {
                    mode: 'no-cors',
                    cache: 'no-cache',
                });
                setIsOnline(true);
            } catch {
                setIsOnline(false);
            }
        };

        // Check initially
        checkConnection();

        // Check every 30 seconds
        const interval = setInterval(checkConnection, 30000);

        return () => clearInterval(interval);
    }, []);

    // Listen for sync status updates
    useEffect(() => {
        const unsubscribe = syncEngine.addSyncListener((status) => {
            if (status.lastSync > 0) {
                setLastSync(new Date(status.lastSync));
            }
        });

        return unsubscribe;
    }, []);

    return {
        isOnline,
        lastSync,
    };
}

// Hook for data backup and export
export function useDataBackup() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const exportData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            await ensureInitialized();
            const data = await offlineDataManager.exportData();
            return data;
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to export data');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    const importData = useCallback(async (jsonData: string) => {
        try {
            setLoading(true);
            setError(null);
            await ensureInitialized();
            await offlineDataManager.importData(jsonData);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to import data');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        loading,
        error,
        exportData,
        importData,
    };
}

// Hook for bulk operations
export function useBulkOperations() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const bulkCreateHabits = useCallback(async (habits: Array<{ title: string; description?: string; category: string }>) => {
        try {
            setLoading(true);
            setError(null);
            await ensureInitialized();
            await offlineDataManager.bulkCreateHabits(habits);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create habits');
            throw err;
        } finally {
            setLoading(false);
        }
    }, []);

    return {
        loading,
        error,
        bulkCreateHabits,
    };
}
