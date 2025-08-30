import React, { useEffect, useState } from 'react';
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
import { useHabits, useProfile, useSync } from '../hooks/useOfflineData';
import { apiClient } from '../lib/api';
import { auth } from '../lib/auth';

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
    const [habits, setHabits] = useState<Habit[]>([]);
    const [profile, setProfile] = useState<UserProfile | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const loadData = async () => {
        try {
            const [habitsResponse, profileResponse] = await Promise.all([
                apiClient.get('/habits'),
                apiClient.get('/gamification/profile'),
            ]);

            if (habitsResponse.ok) {
                setHabits(await habitsResponse.json());
            }

            if (profileResponse.ok) {
                setProfile(await profileResponse.json());
            }
        } catch (error) {
            console.error('Error loading data:', error);
            Alert.alert('Error', 'Failed to load data');
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const completeHabit = async (habitId: number) => {
        try {
            const response = await apiClient.post(`/habits/${habitId}/complete`);

            if (response.ok) {
                const result = await response.json();
                Alert.alert(
                    'Habit Completed!',
                    `+${result.xp_earned} XP${result.achievement_unlocked ? `\n🏆 ${result.achievement_unlocked.title}` : ''}`,
                    [{ text: 'OK', onPress: () => loadData() }]
                );
            } else {
                Alert.alert('Error', 'Failed to complete habit');
            }
        } catch (error) {
            console.error('Error completing habit:', error);
            Alert.alert('Error', 'Failed to complete habit');
        }
    };

    const onRefresh = () => {
        setRefreshing(true);
        loadData();
    };

    const onLogout = async () => {
        Alert.alert(
            'Logout',
            'Are you sure you want to logout?',
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Logout',
                    style: 'destructive',
                    onPress: async () => {
                        await auth.revoke();
                        navigation.reset({ index: 0, routes: [{ name: 'Login' }] });
                    },
                },
            ]
        );
    };

    useEffect(() => {
        loadData();
    }, []);

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#6366f1" />
                <Text style={styles.loadingText}>Loading...</Text>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
            {/* Profile Header */}
            {profile && (
                <View style={styles.profileCard}>
                    <View style={styles.profileHeader}>
                        <Text style={styles.profileTitle}>Level {profile.level}</Text>
                        <TouchableOpacity onPress={onLogout} style={styles.logoutButton}>
                            <Text style={styles.logoutText}>Logout</Text>
                        </TouchableOpacity>
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
                    </View>
                </View>
            )}

            {/* Habits List */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Today's Habits</Text>
                {habits.length === 0 ? (
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No habits yet!</Text>
                        <Text style={styles.emptySubtext}>Create your first habit to get started</Text>
                    </View>
                ) : (
                    habits.map((habit) => (
                        <HabitCard
                            key={habit.id}
                            habit={habit}
                            onComplete={() => completeHabit(habit.id)}
                            onPress={() => navigation.navigate('HabitDetail', { habitId: habit.id })}
                        />
                    ))
                )}
            </View>

            {/* Quick Actions */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Quick Actions</Text>
                <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => navigation.navigate('AddHabit')}
                >
                    <Text style={styles.actionButtonText}>➕ Add New Habit</Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => navigation.navigate('Analytics')}
                >
                    <Text style={styles.actionButtonText}>📊 View Analytics</Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => navigation.navigate('Achievements')}
                >
                    <Text style={styles.actionButtonText}>🏆 View Achievements</Text>
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}

interface HabitCardProps {
    habit: Habit;
    onComplete: () => void;
    onPress: () => void;
}

function HabitCard({ habit, onComplete, onPress }: HabitCardProps) {
    const getCategoryEmoji = (category: string) => {
        const emojis: { [key: string]: string } = {
            health: '💪',
            learning: '📚',
            productivity: '⚡',
            mindfulness: '🧘',
            social: '👥',
            creativity: '🎨',
            finance: '💰',
        };
        return emojis[category.toLowerCase()] || '📝';
    };

    return (
        <TouchableOpacity style={styles.habitCard} onPress={onPress}>
            <View style={styles.habitHeader}>
                <View style={styles.habitInfo}>
                    <Text style={styles.habitEmoji}>{getCategoryEmoji(habit.category)}</Text>
                    <View style={styles.habitTextContainer}>
                        <Text style={styles.habitTitle}>{habit.title}</Text>
                        <Text style={styles.habitDescription}>{habit.description}</Text>
                    </View>
                </View>
                <TouchableOpacity
                    style={[
                        styles.completeButton,
                        habit.completed_today && styles.completedButton,
                    ]}
                    onPress={(e) => {
                        e.stopPropagation();
                        onComplete();
                    }}
                    disabled={habit.completed_today}
                >
                    <Text style={styles.completeButtonText}>
                        {habit.completed_today ? '✓' : '○'}
                    </Text>
                </TouchableOpacity>
            </View>
            <View style={styles.habitStats}>
                <Text style={styles.streakText}>🔥 {habit.streak} day streak</Text>
                <Text style={styles.totalText}>
                    {habit.total_completions} total completions
                </Text>
            </View>
        </TouchableOpacity>
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
    profileCard: {
        backgroundColor: 'white',
        margin: 16,
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
    logoutButton: {
        paddingHorizontal: 12,
        paddingVertical: 6,
        backgroundColor: '#ef4444',
        borderRadius: 6,
    },
    logoutText: {
        color: 'white',
        fontSize: 14,
        fontWeight: '600',
    },
    xpBar: {
        marginBottom: 16,
    },
    xpBarBackground: {
        height: 8,
        backgroundColor: '#e2e8f0',
        borderRadius: 4,
        marginBottom: 8,
    },
    xpBarFill: {
        height: '100%',
        backgroundColor: '#6366f1',
        borderRadius: 4,
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
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1e293b',
    },
    statLabel: {
        fontSize: 12,
        color: '#64748b',
        marginTop: 4,
    },
    section: {
        marginHorizontal: 16,
        marginBottom: 24,
    },
    sectionTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 16,
    },
    emptyState: {
        backgroundColor: 'white',
        padding: 40,
        borderRadius: 12,
        alignItems: 'center',
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
    },
    habitCard: {
        backgroundColor: 'white',
        padding: 16,
        borderRadius: 12,
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
        alignItems: 'center',
        marginBottom: 12,
    },
    habitInfo: {
        flexDirection: 'row',
        flex: 1,
    },
    habitEmoji: {
        fontSize: 24,
        marginRight: 12,
    },
    habitTextContainer: {
        flex: 1,
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
    },
    completeButton: {
        width: 40,
        height: 40,
        borderRadius: 20,
        backgroundColor: '#f1f5f9',
        borderWidth: 2,
        borderColor: '#e2e8f0',
        justifyContent: 'center',
        alignItems: 'center',
    },
    completedButton: {
        backgroundColor: '#10b981',
        borderColor: '#10b981',
    },
    completeButtonText: {
        fontSize: 20,
        color: '#64748b',
    },
    habitStats: {
        flexDirection: 'row',
        justifyContent: 'space-between',
    },
    streakText: {
        fontSize: 12,
        color: '#f59e0b',
        fontWeight: '600',
    },
    totalText: {
        fontSize: 12,
        color: '#64748b',
    },
    actionButton: {
        backgroundColor: 'white',
        padding: 16,
        borderRadius: 12,
        marginBottom: 8,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 2,
    },
    actionButtonText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#1e293b',
        textAlign: 'center',
    },
});
