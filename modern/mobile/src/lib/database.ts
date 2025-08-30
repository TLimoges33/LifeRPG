import * as SQLite from 'expo-sqlite';
import * as SecureStore from 'expo-secure-store';

export type DB = SQLite.SQLiteDatabase;

export function openDb(): DB {
    return SQLite.openDatabaseSync('liferpg.db');
}

export async function initDb(db: DB) {
    await db.execAsync(`
        PRAGMA foreign_keys = ON;
        
        -- Core user data
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            email TEXT UNIQUE,
            display_name TEXT,
            level INTEGER DEFAULT 1,
            xp INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        
        -- Habit categories
        CREATE TABLE IF NOT EXISTS categories (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            emoji TEXT,
            color TEXT,
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        
        -- Enhanced habits table
        CREATE TABLE IF NOT EXISTS habits (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            streak INTEGER DEFAULT 0,
            total_completions INTEGER DEFAULT 0,
            best_streak INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        
        -- Habit completion logs
        CREATE TABLE IF NOT EXISTS habit_completions (
            id INTEGER PRIMARY KEY,
            habit_id INTEGER NOT NULL,
            completed_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            xp_earned INTEGER DEFAULT 0,
            streak_day INTEGER DEFAULT 1,
            notes TEXT,
            FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE
        );
        
        -- Achievement system
        CREATE TABLE IF NOT EXISTS achievements (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT,
            rarity TEXT DEFAULT 'common',
            xp_reward INTEGER DEFAULT 0,
            icon TEXT,
            requirements TEXT, -- JSON string
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        
        -- User achievements
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            achievement_id INTEGER,
            unlocked_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            progress INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(achievement_id) REFERENCES achievements(id) ON DELETE CASCADE,
            UNIQUE(user_id, achievement_id)
        );
        
        -- Analytics cache
        CREATE TABLE IF NOT EXISTS analytics_cache (
            id INTEGER PRIMARY KEY,
            cache_key TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL, -- JSON string
            expires_at TEXT,
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        
        -- Sync change queue
        CREATE TABLE IF NOT EXISTS sync_changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            entity_type TEXT NOT NULL,
            entity_id INTEGER,
            data TEXT NOT NULL, -- JSON string
            timestamp TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            synced INTEGER DEFAULT 0,
            retry_count INTEGER DEFAULT 0,
            last_error TEXT
        );
        
        -- Sync metadata
        CREATE TABLE IF NOT EXISTS sync_metadata (
            id INTEGER PRIMARY KEY,
            last_sync TEXT,
            sync_version INTEGER DEFAULT 1,
            device_id TEXT
        );
        
        -- Server data cache
        CREATE TABLE IF NOT EXISTS server_cache (
            id INTEGER PRIMARY KEY,
            endpoint TEXT UNIQUE NOT NULL,
            data TEXT NOT NULL, -- JSON string
            etag TEXT,
            expires_at TEXT,
            created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        
        -- Indexes for performance
        CREATE INDEX IF NOT EXISTS idx_habit_completions_habit_id ON habit_completions(habit_id);
        CREATE INDEX IF NOT EXISTS idx_habit_completions_date ON habit_completions(completed_at);
        CREATE INDEX IF NOT EXISTS idx_sync_changes_synced ON sync_changes(synced);
        CREATE INDEX IF NOT EXISTS idx_sync_changes_timestamp ON sync_changes(timestamp);
        CREATE INDEX IF NOT EXISTS idx_analytics_cache_key ON analytics_cache(cache_key);
        CREATE INDEX IF NOT EXISTS idx_server_cache_endpoint ON server_cache(endpoint);
    `);

    // Insert default categories
    await insertDefaultCategories(db);

    // Insert default achievements
    await insertDefaultAchievements(db);

    // Initialize sync metadata
    await initSyncMetadata(db);
}

async function insertDefaultCategories(db: DB) {
    const categories = [
        { id: 'health', name: 'Health', emoji: '💪', color: '#10b981' },
        { id: 'learning', name: 'Learning', emoji: '📚', color: '#3b82f6' },
        { id: 'productivity', name: 'Productivity', emoji: '⚡', color: '#f59e0b' },
        { id: 'mindfulness', name: 'Mindfulness', emoji: '🧘', color: '#8b5cf6' },
        { id: 'social', name: 'Social', emoji: '👥', color: '#ef4444' },
        { id: 'creativity', name: 'Creativity', emoji: '🎨', color: '#ec4899' },
        { id: 'finance', name: 'Finance', emoji: '💰', color: '#059669' },
    ];

    for (const category of categories) {
        await db.runAsync(
            'INSERT OR IGNORE INTO categories (id, name, emoji, color) VALUES (?, ?, ?, ?)',
            [category.id, category.name, category.emoji, category.color]
        );
    }
}

async function insertDefaultAchievements(db: DB) {
    const achievements = [
        {
            title: 'First Steps',
            description: 'Complete your first habit',
            category: 'habits',
            rarity: 'common',
            xp_reward: 50,
            icon: '🎯',
            requirements: JSON.stringify({ type: 'habit_completions', count: 1 })
        },
        {
            title: 'Streak Starter',
            description: 'Maintain a 7-day streak',
            category: 'streaks',
            rarity: 'rare',
            xp_reward: 200,
            icon: '🔥',
            requirements: JSON.stringify({ type: 'streak_length', count: 7 })
        },
        {
            title: 'Consistency King',
            description: 'Maintain a 30-day streak',
            category: 'streaks',
            rarity: 'epic',
            xp_reward: 1000,
            icon: '👑',
            requirements: JSON.stringify({ type: 'streak_length', count: 30 })
        },
        {
            title: 'Centurion',
            description: 'Complete 100 habits',
            category: 'completion',
            rarity: 'epic',
            xp_reward: 800,
            icon: '💯',
            requirements: JSON.stringify({ type: 'total_completions', count: 100 })
        },
        {
            title: 'Dedicated',
            description: 'Use LifeRPG for 30 days',
            category: 'consistency',
            rarity: 'rare',
            xp_reward: 300,
            icon: '📅',
            requirements: JSON.stringify({ type: 'days_active', count: 30 })
        }
    ];

    for (const achievement of achievements) {
        await db.runAsync(
            'INSERT OR IGNORE INTO achievements (title, description, category, rarity, xp_reward, icon, requirements) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [achievement.title, achievement.description, achievement.category, achievement.rarity, achievement.xp_reward, achievement.icon, achievement.requirements]
        );
    }
}

async function initSyncMetadata(db: DB) {
    const deviceId = await SecureStore.getItemAsync('device_id') || generateDeviceId();
    await SecureStore.setItemAsync('device_id', deviceId);

    await db.runAsync(
        'INSERT OR IGNORE INTO sync_metadata (id, device_id) VALUES (1, ?)',
        [deviceId]
    );
}

function generateDeviceId(): string {
    return 'device_' + Math.random().toString(36).substr(2, 9) + '_' + Date.now().toString(36);
}

// Enhanced database operations
export async function exec(db: DB, sql: string, params: any[] = []): Promise<void> {
    await db.runAsync(sql, params);
}

export async function query<T = any>(db: DB, sql: string, params: any[] = []): Promise<T[]> {
    const rows = await db.getAllAsync<T>(sql, params);
    return rows as T[];
}

export async function queryOne<T = any>(db: DB, sql: string, params: any[] = []): Promise<T | null> {
    const rows = await query<T>(db, sql, params);
    return rows.length > 0 ? (rows[0] ?? null) : null;
}

// Habit operations
export async function createHabit(db: DB, habit: { title: string; description?: string; category: string }) {
    const result = await db.runAsync(
        'INSERT INTO habits (title, description, category) VALUES (?, ?, ?)',
        [habit.title, habit.description || '', habit.category]
    );

    // Add to sync queue
    await addSyncChange(db, 'habit_create', 'habit', result.lastInsertRowId!, habit);

    return result.lastInsertRowId;
}

export async function updateHabit(db: DB, id: number, updates: Partial<{ title: string; description: string; category: string }>) {
    const setClause = Object.keys(updates).map(key => `${key} = ?`).join(', ');
    const values = Object.values(updates);

    await db.runAsync(
        `UPDATE habits SET ${setClause}, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = ?`,
        [...values, id]
    );

    // Add to sync queue
    await addSyncChange(db, 'habit_update', 'habit', id, { id, ...updates });
}

export async function deleteHabit(db: DB, id: number) {
    await db.runAsync('DELETE FROM habits WHERE id = ?', [id]);

    // Add to sync queue
    await addSyncChange(db, 'habit_delete', 'habit', id, { id });
}

export async function completeHabit(db: DB, habitId: number): Promise<{ xpEarned: number; achievementUnlocked?: any }> {
    const habit = await queryOne(db, 'SELECT * FROM habits WHERE id = ?', [habitId]);
    if (!habit) throw new Error('Habit not found');

    // Check if already completed today
    const today = new Date().toISOString().split('T')[0];
    const completionToday = await queryOne(db,
        'SELECT id FROM habit_completions WHERE habit_id = ? AND date(completed_at) = ?',
        [habitId, today]
    );

    if (completionToday) {
        throw new Error('Habit already completed today');
    }

    // Calculate XP based on streak
    const newStreak = habit.streak + 1;
    const baseXP = 10;
    const streakBonus = Math.floor(newStreak / 7) * 5; // +5 XP for every week of streak
    const xpEarned = baseXP + streakBonus;

    // Update habit
    await db.runAsync(
        'UPDATE habits SET streak = ?, total_completions = total_completions + 1, best_streak = MAX(best_streak, ?), updated_at = strftime(\'%Y-%m-%dT%H:%M:%fZ\',\'now\') WHERE id = ?',
        [newStreak, newStreak, habitId]
    );

    // Record completion
    await db.runAsync(
        'INSERT INTO habit_completions (habit_id, xp_earned, streak_day) VALUES (?, ?, ?)',
        [habitId, xpEarned, newStreak]
    );

    // Update user XP
    await db.runAsync(
        'UPDATE users SET xp = xp + ? WHERE id = 1',
        [xpEarned]
    );

    // Check for achievements
    const achievementUnlocked = await checkAchievements(db, 1);

    // Add to sync queue
    await addSyncChange(db, 'habit_complete', 'habit_completion', null, {
        habitId,
        completedAt: new Date().toISOString(),
        xpEarned,
        streakDay: newStreak
    });

    return { xpEarned, achievementUnlocked };
}

// Achievement checking
async function checkAchievements(db: DB, userId: number): Promise<any> {
    const achievements = await query(db, 'SELECT * FROM achievements WHERE id NOT IN (SELECT achievement_id FROM user_achievements WHERE user_id = ?)', [userId]);

    for (const achievement of achievements) {
        const requirements = JSON.parse(achievement.requirements);
        const isUnlocked = await checkAchievementRequirement(db, userId, requirements);

        if (isUnlocked) {
            // Unlock achievement
            await db.runAsync(
                'INSERT INTO user_achievements (user_id, achievement_id) VALUES (?, ?)',
                [userId, achievement.id]
            );

            // Award XP
            await db.runAsync(
                'UPDATE users SET xp = xp + ? WHERE id = ?',
                [achievement.xp_reward, userId]
            );

            return achievement;
        }
    }

    return null;
}

async function checkAchievementRequirement(db: DB, userId: number, requirements: any): Promise<boolean> {
    switch (requirements.type) {
        case 'habit_completions':
            const completions = await queryOne(db, 'SELECT COUNT(*) as count FROM habit_completions', []);
            return (completions?.count || 0) >= requirements.count;

        case 'streak_length':
            const maxStreak = await queryOne(db, 'SELECT MAX(streak) as max_streak FROM habits', []);
            return (maxStreak?.max_streak || 0) >= requirements.count;

        case 'total_completions':
            const totalCompletions = await queryOne(db, 'SELECT SUM(total_completions) as total FROM habits', []);
            return (totalCompletions?.total || 0) >= requirements.count;

        default:
            return false;
    }
}

// Sync operations
export async function addSyncChange(db: DB, type: string, entityType: string, entityId: number | null, data: any) {
    await db.runAsync(
        'INSERT INTO sync_changes (type, entity_type, entity_id, data) VALUES (?, ?, ?, ?)',
        [type, entityType, entityId, JSON.stringify(data)]
    );
}

export async function getPendingChanges(db: DB) {
    return query(db, 'SELECT * FROM sync_changes WHERE synced = 0 ORDER BY timestamp ASC');
}

export async function markChangesSynced(db: DB, changeIds: number[]) {
    if (changeIds.length === 0) return;
    const placeholders = changeIds.map(() => '?').join(',');
    await db.runAsync(`UPDATE sync_changes SET synced = 1 WHERE id IN (${placeholders})`, changeIds);
}

export async function updateSyncMetadata(db: DB, lastSync: string) {
    await db.runAsync(
        'UPDATE sync_metadata SET last_sync = ? WHERE id = 1',
        [lastSync]
    );
}

// Cache operations
export async function setCacheData(db: DB, key: string, data: any, expiresAt?: Date) {
    const expiresAtStr = expiresAt ? expiresAt.toISOString() : null;
    await db.runAsync(
        'INSERT OR REPLACE INTO analytics_cache (cache_key, data, expires_at) VALUES (?, ?, ?)',
        [key, JSON.stringify(data), expiresAtStr]
    );
}

export async function getCacheData(db: DB, key: string): Promise<any | null> {
    const cached = await queryOne(db,
        'SELECT data, expires_at FROM analytics_cache WHERE cache_key = ?',
        [key]
    );

    if (!cached) return null;

    // Check expiration
    if (cached.expires_at && new Date(cached.expires_at) < new Date()) {
        await db.runAsync('DELETE FROM analytics_cache WHERE cache_key = ?', [key]);
        return null;
    }

    return JSON.parse(cached.data);
}

// Server cache operations
export async function setServerCache(db: DB, endpoint: string, data: any, etag?: string, expiresAt?: Date) {
    const expiresAtStr = expiresAt ? expiresAt.toISOString() : null;
    await db.runAsync(
        'INSERT OR REPLACE INTO server_cache (endpoint, data, etag, expires_at) VALUES (?, ?, ?, ?)',
        [endpoint, JSON.stringify(data), etag || null, expiresAtStr]
    );
}

export async function getServerCache(db: DB, endpoint: string): Promise<{ data: any; etag?: string } | null> {
    const cached = await queryOne(db,
        'SELECT data, etag, expires_at FROM server_cache WHERE endpoint = ?',
        [endpoint]
    );

    if (!cached) return null;

    // Check expiration
    if (cached.expires_at && new Date(cached.expires_at) < new Date()) {
        await db.runAsync('DELETE FROM server_cache WHERE endpoint = ?', [endpoint]);
        return null;
    }

    return {
        data: JSON.parse(cached.data),
        etag: cached.etag
    };
}

// Analytics operations
export async function getHabitAnalytics(db: DB) {
    const habits = await query(db, `
        SELECT 
            h.*,
            COALESCE(hc.completion_rate, 0) as completion_rate,
            COALESCE(hc.weekly_completions, '[]') as weekly_completions
        FROM habits h
        LEFT JOIN (
            SELECT 
                habit_id,
                COUNT(*) * 100.0 / 
                (CASE WHEN COUNT(*) = 0 THEN 1 ELSE 
                    (julianday('now') - julianday(MIN(completed_at))) + 1 
                END) as completion_rate,
                json_group_array(
                    CASE WHEN date(completed_at) >= date('now', '-7 days') 
                    THEN 1 ELSE 0 END
                ) as weekly_completions
            FROM habit_completions 
            GROUP BY habit_id
        ) hc ON h.id = hc.habit_id
        ORDER BY h.created_at DESC
    `);

    return habits.map(habit => ({
        ...habit,
        weekly_completions: JSON.parse(habit.weekly_completions || '[]')
    }));
}

export async function getOverallStats(db: DB) {
    const stats = await queryOne(db, `
        SELECT 
            (SELECT COUNT(*) FROM habits) as total_habits,
            (SELECT COUNT(*) FROM habits WHERE streak > 0) as active_streaks,
            (SELECT MAX(best_streak) FROM habits) as longest_streak,
            (SELECT COALESCE(xp, 0) FROM users WHERE id = 1) as total_xp,
            (SELECT COALESCE(level, 1) FROM users WHERE id = 1) as level,
            (SELECT COUNT(*) FROM user_achievements WHERE user_id = 1) as achievements_count
    `);

    return stats;
}

// Sync helpers for backward compatibility
export async function enqueueChange(db: DB, entity: string, entityId: string, action: 'upsert' | 'delete', payload: any) {
    await addSyncChange(db, action, entity, parseInt(entityId), payload);
}

export async function pendingChanges(db: DB) {
    return getPendingChanges(db);
}

export async function clearChangesUpTo(db: DB, lastId: number) {
    await db.runAsync('DELETE FROM sync_changes WHERE id <= ?', [lastId]);
}

// API sync functions
export async function pullSince(apiBaseUrl: string, accessToken: string, sinceIso?: string) {
    const url = new URL('/sync/pull', apiBaseUrl);
    if (sinceIso) url.searchParams.set('since', sinceIso);
    const res = await fetch(url, { headers: { Authorization: `Bearer ${accessToken}` } });
    if (!res.ok) throw new Error(`Pull failed: ${res.status}`);
    return res.json();
}

export async function pushChanges(apiBaseUrl: string, accessToken: string, changes: any[]) {
    const res = await fetch(new URL('/sync/push', apiBaseUrl), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${accessToken}` },
        body: JSON.stringify({ changes }),
    });
    if (!res.ok) throw new Error(`Push failed: ${res.status}`);
    return res.json();
}
