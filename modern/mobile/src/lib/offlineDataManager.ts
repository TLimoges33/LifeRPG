import { openDb, initDb, type DB } from './database';
import { syncEngine } from './sync';
import * as db from './database';

interface OfflineDataManager {
    init(): Promise<void>;
    getHabits(): Promise<any[]>;
    createHabit(habit: { title: string; description?: string; category: string }): Promise<number>;
    updateHabit(id: number, updates: any): Promise<void>;
    deleteHabit(id: number): Promise<void>;
    completeHabit(id: number): Promise<{ xpEarned: number; achievementUnlocked?: any }>;
    getHabitAnalytics(): Promise<any[]>;
    getOverallStats(): Promise<any>;
    getAchievements(): Promise<any[]>;
    getUserProfile(): Promise<any>;
    sync(): Promise<void>;
}

class OfflineDataManagerImpl implements OfflineDataManager {
    private database: DB | null = null;

    async init(): Promise<void> {
        this.database = openDb();
        await initDb(this.database);

        // Initialize user if not exists
        const user = await db.queryOne(this.database, 'SELECT * FROM users WHERE id = 1', []);
        if (!user) {
            await db.exec(this.database,
                'INSERT INTO users (id, email, display_name, level, xp) VALUES (1, ?, ?, 1, 0)',
                ['user@example.com', 'LifeRPG User']
            );
        }
    }

    private getDb(): DB {
        if (!this.database) {
            throw new Error('Database not initialized. Call init() first.');
        }
        return this.database;
    }

    async getHabits(): Promise<any[]> {
        const database = this.getDb();

        // Try to get from cache first
        const cached = await db.getCacheData(database, 'habits');
        if (cached) {
            return cached;
        }

        // Get from local database
        const habits = await db.query(database, `
      SELECT 
        h.*,
        CASE 
          WHEN hc.completed_at IS NOT NULL AND date(hc.completed_at) = date('now') 
          THEN 1 ELSE 0 
        END as completed_today
      FROM habits h
      LEFT JOIN (
        SELECT DISTINCT habit_id, completed_at
        FROM habit_completions 
        WHERE date(completed_at) = date('now')
      ) hc ON h.id = hc.habit_id
      ORDER BY h.created_at DESC
    `);

        // Cache for 5 minutes
        await db.setCacheData(database, 'habits', habits, new Date(Date.now() + 5 * 60 * 1000));

        return habits;
    }

    async createHabit(habit: { title: string; description?: string; category: string }): Promise<number> {
        const database = this.getDb();
        const habitId = await db.createHabit(database, habit);

        // Clear cache
        await this.clearCache('habits');

        // Trigger sync
        syncEngine.syncChanges().catch(console.error);

        return habitId as number;
    }

    async updateHabit(id: number, updates: any): Promise<void> {
        const database = this.getDb();
        await db.updateHabit(database, id, updates);

        // Clear cache
        await this.clearCache('habits');

        // Trigger sync
        syncEngine.syncChanges().catch(console.error);
    }

    async deleteHabit(id: number): Promise<void> {
        const database = this.getDb();
        await db.deleteHabit(database, id);

        // Clear cache
        await this.clearCache('habits');

        // Trigger sync
        syncEngine.syncChanges().catch(console.error);
    }

    async completeHabit(id: number): Promise<{ xpEarned: number; achievementUnlocked?: any }> {
        const database = this.getDb();
        const result = await db.completeHabit(database, id);

        // Clear relevant caches
        await this.clearCache('habits');
        await this.clearCache('analytics');
        await this.clearCache('profile');
        await this.clearCache('achievements');

        // Trigger sync
        syncEngine.syncChanges().catch(console.error);

        return result;
    }

    async getHabitAnalytics(): Promise<any[]> {
        const database = this.getDb();

        // Try cache first
        const cached = await db.getCacheData(database, 'analytics');
        if (cached) {
            return cached;
        }

        const analytics = await db.getHabitAnalytics(database);

        // Cache for 10 minutes
        await db.setCacheData(database, 'analytics', analytics, new Date(Date.now() + 10 * 60 * 1000));

        return analytics;
    }

    async getOverallStats(): Promise<any> {
        const database = this.getDb();

        // Try cache first
        const cached = await db.getCacheData(database, 'stats');
        if (cached) {
            return cached;
        }

        const stats = await db.getOverallStats(database);

        // Cache for 10 minutes
        await db.setCacheData(database, 'stats', stats, new Date(Date.now() + 10 * 60 * 1000));

        return stats;
    }

    async getAchievements(): Promise<any[]> {
        const database = this.getDb();

        // Try cache first
        const cached = await db.getCacheData(database, 'achievements');
        if (cached) {
            return cached;
        }

        const achievements = await db.query(database, `
      SELECT 
        a.*,
        CASE WHEN ua.id IS NOT NULL THEN 1 ELSE 0 END as unlocked,
        ua.unlocked_at,
        COALESCE(ua.progress, 0) as progress
      FROM achievements a
      LEFT JOIN user_achievements ua ON a.id = ua.achievement_id AND ua.user_id = 1
      ORDER BY unlocked DESC, a.rarity DESC, a.created_at ASC
    `);

        // Cache for 10 minutes
        await db.setCacheData(database, 'achievements', achievements, new Date(Date.now() + 10 * 60 * 1000));

        return achievements;
    }

    async getUserProfile(): Promise<any> {
        const database = this.getDb();

        // Try cache first
        const cached = await db.getCacheData(database, 'profile');
        if (cached) {
            return cached;
        }

        const user = await db.queryOne(database, 'SELECT * FROM users WHERE id = 1', []);
        if (!user) {
            throw new Error('User not found');
        }

        // Calculate level progression
        const xpToNextLevel = this.calculateXpToNextLevel(user.level);
        const currentLevelXp = this.calculateXpForLevel(user.level);
        const nextLevelXp = this.calculateXpForLevel(user.level + 1);

        const profile = {
            ...user,
            xp_to_next_level: xpToNextLevel,
            current_level_xp: currentLevelXp,
            next_level_xp: nextLevelXp,
            level_progress: Math.max(0, (user.xp - currentLevelXp) / (nextLevelXp - currentLevelXp))
        };

        // Cache for 5 minutes
        await db.setCacheData(database, 'profile', profile, new Date(Date.now() + 5 * 60 * 1000));

        return profile;
    }

    private calculateXpForLevel(level: number): number {
        // Exponential XP curve: level 1 = 0, level 2 = 100, level 3 = 250, etc.
        return Math.floor(100 * Math.pow(level - 1, 1.5));
    }

    private calculateXpToNextLevel(currentLevel: number): number {
        const currentLevelXp = this.calculateXpForLevel(currentLevel);
        const nextLevelXp = this.calculateXpForLevel(currentLevel + 1);
        return nextLevelXp - currentLevelXp;
    }

    async sync(): Promise<void> {
        await syncEngine.syncChanges();
    }

    private async clearCache(pattern: string): Promise<void> {
        const database = this.getDb();
        if (pattern === 'all') {
            await db.exec(database, 'DELETE FROM analytics_cache', []);
        } else {
            await db.exec(database, 'DELETE FROM analytics_cache WHERE cache_key LIKE ?', [`%${pattern}%`]);
        }
    }

    // Bulk operations for better performance
    async bulkCreateHabits(habits: Array<{ title: string; description?: string; category: string }>): Promise<void> {
        const database = this.getDb();

        for (const habit of habits) {
            await db.createHabit(database, habit);
        }

        await this.clearCache('habits');
        syncEngine.syncChanges().catch(console.error);
    }

    // Analytics helpers
    async getHabitHistory(habitId: number, days: number = 30): Promise<any[]> {
        const database = this.getDb();

        const history = await db.query(database, `
      WITH RECURSIVE date_series(date) AS (
        SELECT date('now', '-${days - 1} days')
        UNION ALL
        SELECT date(date, '+1 day')
        FROM date_series
        WHERE date < date('now')
      )
      SELECT 
        ds.date,
        CASE WHEN hc.id IS NOT NULL THEN 1 ELSE 0 END as completed
      FROM date_series ds
      LEFT JOIN habit_completions hc ON ds.date = date(hc.completed_at) AND hc.habit_id = ?
      ORDER BY ds.date ASC
    `, [habitId]);

        return history;
    }

    async getStreakHistory(): Promise<any> {
        const database = this.getDb();

        const streaks = await db.query(database, `
      SELECT 
        h.title,
        h.category,
        h.streak as current_streak,
        h.best_streak,
        COUNT(hc.id) as total_completions,
        MAX(hc.completed_at) as last_completion
      FROM habits h
      LEFT JOIN habit_completions hc ON h.id = hc.habit_id
      GROUP BY h.id
      ORDER BY h.streak DESC, h.best_streak DESC
    `);

        return streaks;
    }

    // Clear all user data (for logout)
    async clearUserData(): Promise<void> {
        const database = this.getDb();

        await db.exec(database, `
      DELETE FROM habits;
      DELETE FROM habit_completions;
      DELETE FROM achievements;
      DELETE FROM analytics_cache;
      DELETE FROM sync_metadata;
      DELETE FROM sync_queue;
      UPDATE users SET 
        username = NULL,
        email = NULL,
        avatar_url = NULL,
        xp = 0,
        level = 1,
        total_habits_completed = 0,
        current_streak = 0,
        longest_streak = 0;
    `, []);
    }

    // Backup and restore
    async exportData(): Promise<string> {
        const database = this.getDb();

        const data = {
            users: await db.query(database, 'SELECT * FROM users', []),
            habits: await db.query(database, 'SELECT * FROM habits', []),
            completions: await db.query(database, 'SELECT * FROM habit_completions', []),
            achievements: await db.query(database, 'SELECT * FROM user_achievements', []),
            exportedAt: new Date().toISOString()
        };

        return JSON.stringify(data, null, 2);
    }

    async importData(jsonData: string): Promise<void> {
        const database = this.getDb();
        const data = JSON.parse(jsonData);

        // Clear existing data (be careful!)
        await db.exec(database, 'DELETE FROM habit_completions', []);
        await db.exec(database, 'DELETE FROM user_achievements', []);
        await db.exec(database, 'DELETE FROM habits', []);
        await db.exec(database, 'DELETE FROM users WHERE id > 1', []);

        // Import data
        for (const user of data.users || []) {
            await db.exec(database,
                'INSERT OR REPLACE INTO users (id, email, display_name, level, xp, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                [user.id, user.email, user.display_name, user.level, user.xp, user.created_at, user.updated_at]
            );
        }

        for (const habit of data.habits || []) {
            await db.exec(database,
                'INSERT INTO habits (id, title, description, category, streak, total_completions, best_streak, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)',
                [habit.id, habit.title, habit.description, habit.category, habit.streak, habit.total_completions, habit.best_streak, habit.created_at, habit.updated_at]
            );
        }

        for (const completion of data.completions || []) {
            await db.exec(database,
                'INSERT INTO habit_completions (id, habit_id, completed_at, xp_earned, streak_day, notes) VALUES (?, ?, ?, ?, ?, ?)',
                [completion.id, completion.habit_id, completion.completed_at, completion.xp_earned, completion.streak_day, completion.notes]
            );
        }

        for (const achievement of data.achievements || []) {
            await db.exec(database,
                'INSERT INTO user_achievements (id, user_id, achievement_id, unlocked_at, progress) VALUES (?, ?, ?, ?, ?)',
                [achievement.id, achievement.user_id, achievement.achievement_id, achievement.unlocked_at, achievement.progress]
            );
        }

        // Clear all caches
        await this.clearCache('all');
    }
}

// Create singleton instance
export const offlineDataManager = new OfflineDataManagerImpl();

// Initialize on first import
let initialized = false;
export async function ensureInitialized() {
    if (!initialized) {
        await offlineDataManager.init();
        initialized = true;
    }
}
