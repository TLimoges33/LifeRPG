import React, { useState } from 'react';
import {
    View,
    Text,
    ScrollView,
    StyleSheet,
    TouchableOpacity,
    Alert,
    RefreshControl,
    ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useHabits, useProfile, useOfflineStatus } from '../hooks/useOfflineData';
import { useSync } from '../hooks/useSync';

interface Habit {
    id: number;
    title: string;
    description: string;
    category: string;
    streak: number;
    total_completions: number;
    completed_today: boolean;
}

interface UserProfile {
    level: number;
    xp: number;
    xp_to_next_level: number;
    total_achievements: number;
    current_streaks: number;
}

export default function HabitsScreen() {
    const navigation = useNavigation<any>();
    const { habits, loading, error, refetch, completeHabit, createHabit } = useHabits();
    const { profile, refetch: refetchProfile } = useProfile();
    const { sync, syncStatus, isAuthenticated, login, logout } = useSync();
    const { isOnline, lastSync } = useOfflineStatus();
    const [refreshing, setRefreshing] = useState(false);

    const onRefresh = async () => {
        setRefreshing(true);
        try {
            if (isAuthenticated && isOnline) {
                await sync();
            }
            await Promise.all([refetch(), refetchProfile()]);
        } catch (error) {
            console.error('Refresh failed:', error);
        } finally {
            setRefreshing(false);
        }
    };

    const handleCompleteHabit = async (habitId: number) => {
        try {
            const result = await completeHabit(habitId);

            if (result.achievementUnlocked) {
                Alert.alert(
                    '🏆 Achievement Unlocked!',
                    result.achievementUnlocked.title,
                    [{ text: 'Awesome!', style: 'default' }]
                );
            }
        } catch (error) {
            Alert.alert('Error', 'Failed to complete habit');
        }
    };

    const handleAddHabit = () => {
        Alert.prompt(
            'Add New Habit',
            'Enter habit title',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Add',
                    onPress: async (title) => {
                        if (title?.trim()) {
                            try {
                                await createHabit({
                                    title: title.trim(),
                                    description: '',
                                    category: 'health'
                                });
                            } catch (error) {
                                Alert.alert('Error', 'Failed to create habit');
                            }
                        }
                    }
                }
            ],
            'plain-text'
        );
    };

    const handleLogin = async () => {
        try {
            await login();
        } catch (error) {
            Alert.alert('Login Failed', 'Please try again');
        }
    };

    const handleLogout = async () => {
        Alert.alert(
            'Logout',
            'Are you sure you want to logout?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Logout',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            await logout();
                            navigation.reset({
                                index: 0,
                                routes: [{ name: 'Login' as never }],
                            });
                        } catch (error) {
                            console.error('Logout failed:', error);
                        }
                    }
                }
            ]
        );
    };

    if (loading && habits.length === 0) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#6366f1" />
                <Text style={styles.loadingText}>Loading your habits...</Text>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
            {/* Connection Status */}
            <View style={[styles.statusBar, { backgroundColor: isOnline ? '#10b981' : '#f59e0b' }]}>
                <Text style={styles.statusText}>
                    {isOnline ? '🌐 Online' : '📱 Offline'}
                    {lastSync && ` • Last sync: ${lastSync.toLocaleTimeString()}`}
                </Text>
                {syncStatus.pendingChanges > 0 && (
                    <Text style={styles.statusText}>
                        {syncStatus.pendingChanges} changes pending
                    </Text>
                )}
            </View>

            {/* Profile Header */}
            {profile && (
                <View style={styles.profileCard}>
                    <View style={styles.profileHeader}>
                        <Text style={styles.profileTitle}>Level {profile.level}</Text>
                        <View style={styles.headerButtons}>
                            {!isAuthenticated && (
                                <TouchableOpacity onPress={handleLogin} style={styles.loginButton}>
                                    <Text style={styles.loginText}>Login</Text>
                                </TouchableOpacity>
                            )}
                            {isAuthenticated && (
                                <TouchableOpacity onPress={handleLogout} style={styles.logoutButton}>
                                    <Text style={styles.logoutText}>Logout</Text>
                                </TouchableOpacity>
                            )}
                        </View>
                    </View>
                    <View style={styles.xpBar}>
                        <View style={styles.xpBarBackground}>
                            <View
                                style={[
                                    styles.xpBarFill,
                                    {
                                        width: `${((profile.xp_to_next_level - (profile.xp % profile.xp_to_next_level)) / profile.xp_to_next_level) * 100}%`,
                                    },
                                ]}
                            />
                        </View>
                        <Text style={styles.xpText}>
                            {profile.xp} XP ({profile.xp_to_next_level - (profile.xp % profile.xp_to_next_level)} to next level)
                        </Text>
                    </View>
                    <View style={styles.statsRow}>
                        <View style={styles.statItem}>
                            <Text style={styles.statNumber}>{profile.total_achievements}</Text>
                            <Text style={styles.statLabel}>Achievements</Text>
                        </View>
                        <View style={styles.statItem}>
                            <Text style={styles.statNumber}>{profile.current_streaks}</Text>
                            <Text style={styles.statLabel}>Active Streaks</Text>
                        </View>
                        <View style={styles.statItem}>
                            <Text style={styles.statNumber}>{habits.length}</Text>
                            <Text style={styles.statLabel}>Total Habits</Text>
                        </View>
                    </View>
                </View>
            )}

            {/* Error Message */}
            {error && (
                <View style={styles.errorCard}>
                    <Text style={styles.errorText}>⚠️ {error}</Text>
                    <TouchableOpacity onPress={refetch} style={styles.retryButton}>
                        <Text style={styles.retryText}>Retry</Text>
                    </TouchableOpacity>
                </View>
            )}

            {/* Add Habit Button */}
            <TouchableOpacity style={styles.addButton} onPress={handleAddHabit}>
                <Text style={styles.addButtonText}>+ Add New Habit</Text>
            </TouchableOpacity>

            {/* Habits List */}
            <View style={styles.habitsContainer}>
                <Text style={styles.sectionTitle}>Your Habits</Text>

                {habits.length === 0 ? (
                    <View style={styles.emptyContainer}>
                        <Text style={styles.emptyText}>No habits yet</Text>
                        <Text style={styles.emptySubtext}>Add your first habit to get started!</Text>
                    </View>
                ) : (
                    habits.map((habit) => (
                        <View key={habit.id} style={styles.habitCard}>
                            <View style={styles.habitHeader}>
                                <View style={styles.habitInfo}>
                                    <Text style={styles.habitTitle}>{habit.title}</Text>
                                    {habit.description ? (
                                        <Text style={styles.habitDescription}>{habit.description}</Text>
                                    ) : null}
                                    <Text style={styles.habitCategory}>{habit.category}</Text>
                                </View>
                                <View style={styles.habitStats}>
                                    <Text style={styles.streakText}>🔥 {habit.streak}</Text>
                                    <Text style={styles.completionsText}>
                                        {habit.total_completions} total
                                    </Text>
                                </View>
                            </View>

                            <View style={styles.habitActions}>
                                <TouchableOpacity
                                    style={[
                                        styles.completeButton,
                                        habit.completed_today && styles.completedButton,
                                    ]}
                                    onPress={() => handleCompleteHabit(habit.id)}
                                    disabled={habit.completed_today}
                                >
                                    <Text
                                        style={[
                                            styles.completeButtonText,
                                            habit.completed_today && styles.completedButtonText,
                                        ]}
                                    >
                                        {habit.completed_today ? '✓ Completed' : 'Complete'}
                                    </Text>
                                </TouchableOpacity>

                                <TouchableOpacity
                                    style={styles.detailsButton}
                                    onPress={() => navigation.navigate('HabitDetail', { habitId: habit.id })}
                                >
                                    <Text style={styles.detailsButtonText}>Details</Text>
                                </TouchableOpacity>
                            </View>
                        </View>
                    ))
                )}
            </View>

            {/* Bottom Navigation Placeholder */}
            <View style={styles.bottomSpacer} />
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f8fafc',
    },
    centerContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#f8fafc',
    },
    loadingText: {
        marginTop: 16,
        fontSize: 16,
        color: '#64748b',
    },
    statusBar: {
        padding: 8,
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    statusText: {
        color: 'white',
        fontSize: 12,
        fontWeight: '500',
    },
    profileCard: {
        backgroundColor: 'white',
        margin: 16,
        marginBottom: 8,
        padding: 20,
        borderRadius: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    profileHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
    },
    profileTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1e293b',
    },
    headerButtons: {
        flexDirection: 'row',
        gap: 8,
    },
    loginButton: {
        backgroundColor: '#6366f1',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 6,
    },
    loginText: {
        color: 'white',
        fontWeight: '600',
        fontSize: 14,
    },
    logoutButton: {
        backgroundColor: '#ef4444',
        paddingHorizontal: 16,
        paddingVertical: 8,
        borderRadius: 6,
    },
    logoutText: {
        color: 'white',
        fontWeight: '600',
        fontSize: 14,
    },
    xpBar: {
        marginBottom: 16,
    },
    xpBarBackground: {
        height: 8,
        backgroundColor: '#e2e8f0',
        borderRadius: 4,
        overflow: 'hidden',
        marginBottom: 8,
    },
    xpBarFill: {
        height: '100%',
        backgroundColor: '#6366f1',
    },
    xpText: {
        fontSize: 14,
        color: '#64748b',
        textAlign: 'center',
    },
    statsRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
    },
    statItem: {
        alignItems: 'center',
    },
    statNumber: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1e293b',
    },
    statLabel: {
        fontSize: 12,
        color: '#64748b',
        marginTop: 4,
    },
    errorCard: {
        backgroundColor: '#fef2f2',
        margin: 16,
        marginBottom: 8,
        padding: 16,
        borderRadius: 8,
        borderLeftWidth: 4,
        borderLeftColor: '#ef4444',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
    },
    errorText: {
        color: '#dc2626',
        fontSize: 14,
        flex: 1,
    },
    retryButton: {
        backgroundColor: '#ef4444',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 4,
    },
    retryText: {
        color: 'white',
        fontSize: 12,
        fontWeight: '600',
    },
    addButton: {
        backgroundColor: '#6366f1',
        margin: 16,
        marginBottom: 8,
        padding: 16,
        borderRadius: 8,
        alignItems: 'center',
    },
    addButtonText: {
        color: 'white',
        fontSize: 16,
        fontWeight: '600',
    },
    habitsContainer: {
        margin: 16,
        marginTop: 8,
    },
    sectionTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 16,
    },
    emptyContainer: {
        alignItems: 'center',
        padding: 32,
    },
    emptyText: {
        fontSize: 18,
        fontWeight: '600',
        color: '#64748b',
        marginBottom: 8,
    },
    emptySubtext: {
        fontSize: 14,
        color: '#94a3b8',
        textAlign: 'center',
    },
    habitCard: {
        backgroundColor: 'white',
        padding: 16,
        borderRadius: 8,
        marginBottom: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 2,
    },
    habitHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 12,
    },
    habitInfo: {
        flex: 1,
        marginRight: 12,
    },
    habitTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#1e293b',
        marginBottom: 4,
    },
    habitDescription: {
        fontSize: 14,
        color: '#64748b',
        marginBottom: 4,
    },
    habitCategory: {
        fontSize: 12,
        color: '#6366f1',
        textTransform: 'uppercase',
        fontWeight: '500',
    },
    habitStats: {
        alignItems: 'flex-end',
    },
    streakText: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#ea580c',
        marginBottom: 4,
    },
    completionsText: {
        fontSize: 12,
        color: '#64748b',
    },
    habitActions: {
        flexDirection: 'row',
        gap: 8,
    },
    completeButton: {
        backgroundColor: '#10b981',
        flex: 1,
        padding: 12,
        borderRadius: 6,
        alignItems: 'center',
    },
    completedButton: {
        backgroundColor: '#e2e8f0',
    },
    completeButtonText: {
        color: 'white',
        fontWeight: '600',
        fontSize: 14,
    },
    completedButtonText: {
        color: '#64748b',
    },
    detailsButton: {
        backgroundColor: '#f1f5f9',
        paddingHorizontal: 16,
        paddingVertical: 12,
        borderRadius: 6,
        alignItems: 'center',
    },
    detailsButtonText: {
        color: '#6366f1',
        fontWeight: '600',
        fontSize: 14,
    },
    bottomSpacer: {
        height: 100,
    },
});
