import * as SecureStore from 'expo-secure-store';
import { apiClient } from './api';

export interface SyncChange {
    id: string;
    type: 'habit_create' | 'habit_update' | 'habit_delete' | 'habit_complete';
    entityId?: number;
    data: any;
    timestamp: number;
    synced: boolean;
}

export interface SyncStatus {
    lastSync: number;
    pendingChanges: number;
    syncInProgress: boolean;
    lastError?: string;
}

class SyncEngine {
    private syncInProgress = false;
    private syncListeners: Array<(status: SyncStatus) => void> = [];

    // Add a sync status listener
    addSyncListener(listener: (status: SyncStatus) => void) {
        this.syncListeners.push(listener);
        return () => {
            this.syncListeners = this.syncListeners.filter(l => l !== listener);
        };
    }

    // Notify all listeners of sync status changes
    private notifyListeners(status: SyncStatus) {
        this.syncListeners.forEach(listener => listener(status));
    }

    // Get current sync status
    async getSyncStatus(): Promise<SyncStatus> {
        const lastSync = await SecureStore.getItemAsync('lastSync');
        const pendingChanges = await this.getPendingChanges();

        return {
            lastSync: lastSync ? parseInt(lastSync) : 0,
            pendingChanges: pendingChanges.length,
            syncInProgress: this.syncInProgress,
        };
    }

    // Add a change to the sync queue
    async addChange(change: Omit<SyncChange, 'id' | 'timestamp' | 'synced'>): Promise<void> {
        const changeWithMetadata: SyncChange = {
            ...change,
            id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            timestamp: Date.now(),
            synced: false,
        };

        const pendingChanges = await this.getPendingChanges();
        pendingChanges.push(changeWithMetadata);

        await SecureStore.setItemAsync('pendingChanges', JSON.stringify(pendingChanges));

        // Trigger automatic sync
        this.syncChanges();
    }

    // Get all pending changes
    async getPendingChanges(): Promise<SyncChange[]> {
        try {
            const changesJson = await SecureStore.getItemAsync('pendingChanges');
            return changesJson ? JSON.parse(changesJson) : [];
        } catch (error) {
            console.error('Error getting pending changes:', error);
            return [];
        }
    }

    // Sync all pending changes to server
    async syncChanges(): Promise<boolean> {
        if (this.syncInProgress) {
            return false; // Already syncing
        }

        this.syncInProgress = true;
        this.notifyListeners(await this.getSyncStatus());

        try {
            const pendingChanges = await this.getPendingChanges();

            if (pendingChanges.length === 0) {
                this.syncInProgress = false;
                this.notifyListeners(await this.getSyncStatus());
                return true;
            }

            const syncedChanges: string[] = [];
            let hasError = false;
            let lastError: string | undefined;

            // Process changes in order
            for (const change of pendingChanges) {
                try {
                    const success = await this.syncSingleChange(change);
                    if (success) {
                        syncedChanges.push(change.id);
                    } else {
                        hasError = true;
                        break; // Stop on first failure to maintain order
                    }
                } catch (error) {
                    console.error('Error syncing change:', error);
                    lastError = error instanceof Error ? error.message : 'Unknown error';
                    hasError = true;
                    break;
                }
            }

            // Remove successfully synced changes
            if (syncedChanges.length > 0) {
                const remainingChanges = pendingChanges.filter(
                    change => !syncedChanges.includes(change.id)
                );
                await SecureStore.setItemAsync('pendingChanges', JSON.stringify(remainingChanges));
            }

            // Update last sync time if we synced everything
            if (!hasError) {
                await SecureStore.setItemAsync('lastSync', Date.now().toString());
            }

            this.syncInProgress = false;
            const status = await this.getSyncStatus();
            this.notifyListeners({
                ...status,
                ...(lastError && { lastError }),
            });

            return !hasError;
        } catch (error) {
            console.error('Sync failed:', error);
            this.syncInProgress = false;
            const status = await this.getSyncStatus();
            this.notifyListeners({
                ...status,
                lastError: error instanceof Error ? error.message : 'Sync failed',
            });
            return false;
        }
    }

    // Sync a single change to the server
    private async syncSingleChange(change: SyncChange): Promise<boolean> {
        try {
            let response: Response;

            switch (change.type) {
                case 'habit_create':
                    response = await apiClient.post('/habits', change.data);
                    break;

                case 'habit_update':
                    response = await apiClient.put(`/habits/${change.entityId}`, change.data);
                    break;

                case 'habit_delete':
                    response = await apiClient.delete(`/habits/${change.entityId}`);
                    break;

                case 'habit_complete':
                    response = await apiClient.post(`/habits/${change.entityId}/complete`, change.data);
                    break;

                default:
                    console.warn('Unknown change type:', change.type);
                    return false;
            }

            return response.ok;
        } catch (error) {
            console.error('Error syncing single change:', error);
            return false;
        }
    }

    // Force a full sync from server (download all data)
    async fullSync(): Promise<boolean> {
        if (this.syncInProgress) {
            return false;
        }

        this.syncInProgress = true;
        this.notifyListeners(await this.getSyncStatus());

        try {
            // First upload any pending changes
            await this.syncChanges();

            // Then download fresh data from server
            const response = await apiClient.get('/sync/full');

            if (response.ok) {
                const serverData = await response.json();

                // Store server data locally
                await this.storeServerData(serverData);

                await SecureStore.setItemAsync('lastSync', Date.now().toString());

                this.syncInProgress = false;
                this.notifyListeners(await this.getSyncStatus());
                return true;
            } else {
                throw new Error('Failed to fetch server data');
            }
        } catch (error) {
            console.error('Full sync failed:', error);
            this.syncInProgress = false;
            const status = await this.getSyncStatus();
            this.notifyListeners({
                ...status,
                lastError: error instanceof Error ? error.message : 'Full sync failed',
            });
            return false;
        }
    }

    // Store server data locally (public method)
    async storeData(key: string, data: any): Promise<void> {
        try {
            await SecureStore.setItemAsync(`cached${key}`, JSON.stringify(data));
        } catch (error) {
            console.error('Error storing data:', error);
            throw error;
        }
    }

    // Store server data locally
    private async storeServerData(serverData: any): Promise<void> {
        try {
            // Store habits
            if (serverData.habits) {
                await SecureStore.setItemAsync('cachedHabits', JSON.stringify(serverData.habits));
            }

            // Store profile data
            if (serverData.profile) {
                await SecureStore.setItemAsync('cachedProfile', JSON.stringify(serverData.profile));
            }

            // Store achievements
            if (serverData.achievements) {
                await SecureStore.setItemAsync('cachedAchievements', JSON.stringify(serverData.achievements));
            }

            // Store analytics
            if (serverData.analytics) {
                await SecureStore.setItemAsync('cachedAnalytics', JSON.stringify(serverData.analytics));
            }
        } catch (error) {
            console.error('Error storing server data:', error);
            throw error;
        }
    }

    // Get cached data for offline use
    async getCachedData(type: string): Promise<any> {
        try {
            const data = await SecureStore.getItemAsync(`cached${type}`);
            return data ? JSON.parse(data) : null;
        } catch (error) {
            console.error('Error getting cached data:', error);
            return null;
        }
    }

    // Clear all sync data (useful for logout)
    async clearSyncData(): Promise<void> {
        try {
            await Promise.all([
                SecureStore.deleteItemAsync('pendingChanges'),
                SecureStore.deleteItemAsync('lastSync'),
                SecureStore.deleteItemAsync('cachedHabits'),
                SecureStore.deleteItemAsync('cachedProfile'),
                SecureStore.deleteItemAsync('cachedAchievements'),
                SecureStore.deleteItemAsync('cachedAnalytics'),
            ]);
        } catch (error) {
            console.error('Error clearing sync data:', error);
        }
    }

    // Check if device is online
    async isOnline(): Promise<boolean> {
        try {
            const response = await fetch('https://www.google.com/favicon.ico', {
                method: 'HEAD',
                mode: 'no-cors',
            });
            return true;
        } catch {
            return false;
        }
    }

    // Auto-sync with exponential backoff
    async autoSync(): Promise<void> {
        const maxRetries = 3;
        let retryCount = 0;
        let delay = 1000; // Start with 1 second

        while (retryCount < maxRetries) {
            const online = await this.isOnline();

            if (!online) {
                console.log('Device is offline, skipping sync');
                return;
            }

            const success = await this.syncChanges();

            if (success) {
                return; // Success, exit
            }

            retryCount++;

            if (retryCount < maxRetries) {
                console.log(`Sync failed, retrying in ${delay}ms (attempt ${retryCount}/${maxRetries})`);
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2; // Exponential backoff
            }
        }

        console.log('Auto-sync failed after maximum retries');
    }
}

export const syncEngine = new SyncEngine();
