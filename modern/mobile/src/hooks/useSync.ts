import { useState, useEffect, useCallback } from 'react';
import { syncEngine } from '../lib/sync';
import { authManager } from '../lib/auth';
import { offlineDataManager, ensureInitialized } from '../lib/offlineDataManager';
import type { SyncStatus, SyncChange } from '../lib/sync';

export function useSync() {
    const [syncStatus, setSyncStatus] = useState<SyncStatus>({
        lastSync: 0,
        pendingChanges: 0,
        syncInProgress: false,
    });

    const [isAuthenticated, setIsAuthenticated] = useState(false);

    // Initialize sync status and authentication
    useEffect(() => {
        const initialize = async () => {
            await ensureInitialized();
            const status = await syncEngine.getSyncStatus();
            setSyncStatus(status);

            // Check authentication status
            try {
                const tokenInfo = await authManager.getTokenInfo();
                setIsAuthenticated(!!tokenInfo && !authManager.isTokenExpired(tokenInfo));
            } catch {
                setIsAuthenticated(false);
            }
        };

        initialize();

        // Listen for sync status updates
        const unsubscribe = syncEngine.addSyncListener(setSyncStatus);

        return unsubscribe;
    }, []);

    // Add a change to sync queue
    const addChange = useCallback(async (change: Omit<SyncChange, 'id' | 'timestamp' | 'synced'>) => {
        await syncEngine.addChange(change);
    }, []);

    // Trigger manual sync
    const sync = useCallback(async () => {
        if (!isAuthenticated) {
            throw new Error('User not authenticated');
        }
        return await syncEngine.syncChanges();
    }, [isAuthenticated]);

    // Trigger full sync
    const fullSync = useCallback(async () => {
        if (!isAuthenticated) {
            throw new Error('User not authenticated');
        }
        return await syncEngine.fullSync();
    }, [isAuthenticated]);

    // Get cached data
    const getCachedData = useCallback(async (type: string) => {
        return await syncEngine.getCachedData(type);
    }, []);

    // Check if online
    const checkOnlineStatus = useCallback(async () => {
        return await syncEngine.isOnline();
    }, []);

    const login = useCallback(async () => {
        try {
            const result = await authManager.login();
            setIsAuthenticated(true);
            return result;
        } catch (error) {
            setIsAuthenticated(false);
            throw error;
        }
    }, []);

    const logout = useCallback(async () => {
        try {
            await authManager.logout();
            setIsAuthenticated(false);
            // Clear local data on logout
            await offlineDataManager.clearUserData();
        } catch (error) {
            throw error;
        }
    }, []);

    return {
        syncStatus,
        isAuthenticated,
        addChange,
        sync,
        fullSync,
        getCachedData,
        checkOnlineStatus,
        login,
        logout,
    };
}

// Enhanced offline-first data fetching with offline data manager
export function useOfflineData<T>(
    apiEndpoint: string,
    cacheKey: string,
    fetchFunction: () => Promise<T>
) {
    const [data, setData] = useState<T | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isOffline, setIsOffline] = useState(false);
    const { getCachedData, checkOnlineStatus } = useSync();

    const loadData = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            await ensureInitialized();
            const online = await checkOnlineStatus();
            setIsOffline(!online);

            if (online) {
                // Try to fetch fresh data from API
                try {
                    const freshData = await fetchFunction();
                    setData(freshData);
                    // Cache the fresh data using database cache
                    await syncEngine.storeData(cacheKey, freshData);
                } catch (apiError) {
                    console.warn('API fetch failed, falling back to cache:', apiError);
                    // Fall back to cached data if API fails
                    const cachedData = await getCachedData(cacheKey);
                    if (cachedData) {
                        setData(cachedData);
                    } else {
                        throw apiError;
                    }
                }
            } else {
                // Use cached data when offline
                const cachedData = await getCachedData(cacheKey);
                if (cachedData) {
                    setData(cachedData);
                } else {
                    throw new Error('No cached data available offline');
                }
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Unknown error');
        } finally {
            setLoading(false);
        }
    }, [apiEndpoint, cacheKey, fetchFunction, getCachedData, checkOnlineStatus]);

    useEffect(() => {
        loadData();
    }, [loadData]);

    return {
        data,
        loading,
        error,
        isOffline,
        refetch: loadData,
    };
}
