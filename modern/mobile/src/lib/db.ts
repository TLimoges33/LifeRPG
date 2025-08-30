import * as SQLite from 'expo-sqlite';

export type DB = SQLite.SQLiteDatabase;

export function openDb(): DB {
    return SQLite.openDatabaseSync('liferpg.db');
}

export async function initDb(db: DB) {
    await db.execAsync(`
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT,
            display_name TEXT
        );
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            name TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS habits (
            id TEXT PRIMARY KEY,
            project_id TEXT,
            name TEXT,
            streak INTEGER DEFAULT 0,
            updated_at TEXT,
            FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS logs (
            id TEXT PRIMARY KEY,
            habit_id TEXT,
            ts TEXT,
            delta INTEGER,
            note TEXT,
            FOREIGN KEY(habit_id) REFERENCES habits(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS changes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity TEXT NOT NULL,
            entity_id TEXT NOT NULL,
            action TEXT NOT NULL,
            payload TEXT NOT NULL,
            ts TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE INDEX IF NOT EXISTS idx_changes_ts ON changes(ts);
    `);
}

export async function exec(db: DB, sql: string, params: any[] = []): Promise<void> {
    await db.runAsync(sql, params);
}

export async function query<T = any>(db: DB, sql: string, params: any[] = []): Promise<T[]> {
    const rows = await db.getAllAsync<T>(sql, params);
    return rows as T[];
}

// Simple sync placeholders
export async function enqueueChange(db: DB, entity: string, entityId: string, action: 'upsert' | 'delete', payload: any) {
    await exec(db, 'INSERT INTO changes(entity, entity_id, action, payload) VALUES (?, ?, ?, ?)', [entity, entityId, action, JSON.stringify(payload)]);
}

export async function pendingChanges(db: DB) {
    return query(db, 'SELECT * FROM changes ORDER BY id ASC');
}

export async function clearChangesUpTo(db: DB, lastId: number) {
    await exec(db, 'DELETE FROM changes WHERE id <= ?', [lastId]);
}

// Very minimal pull/push examples
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
