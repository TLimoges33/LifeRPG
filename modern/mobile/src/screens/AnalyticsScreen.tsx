import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    ScrollView,
    StyleSheet,
    Dimensions,
    ActivityIndicator,
    RefreshControl,
} from 'react-native';
import { apiClient } from '../lib/api';

const { width: screenWidth } = Dimensions.get('window');

interface HabitAnalytics {
    title: string;
    category: string;
    streak: number;
    total_completions: number;
    completion_rate: number;
    weekly_completions: number[];
}

interface OverallStats {
    total_habits: number;
    active_streaks: number;
    longest_streak: number;
    total_xp: number;
    level: number;
    achievements_count: number;
}

export default function AnalyticsScreen() {
    const [habitAnalytics, setHabitAnalytics] = useState<HabitAnalytics[]>([]);
    const [overallStats, setOverallStats] = useState<OverallStats | null>(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    const loadAnalytics = async () => {
        try {
            const [habitsResponse, statsResponse] = await Promise.all([
                apiClient.get('/analytics/habits'),
                apiClient.get('/analytics/overview'),
            ]);

            if (habitsResponse.ok) {
                setHabitAnalytics(await habitsResponse.json());
            }

            if (statsResponse.ok) {
                setOverallStats(await statsResponse.json());
            }
        } catch (error) {
            console.error('Error loading analytics:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = () => {
        setRefreshing(true);
        loadAnalytics();
    };

    useEffect(() => {
        loadAnalytics();
    }, []);

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#6366f1" />
                <Text style={styles.loadingText}>Loading analytics...</Text>
            </View>
        );
    }

    return (
        <ScrollView
            style={styles.container}
            refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        >
            {/* Overall Stats */}
            {overallStats && (
                <View style={styles.section}>
                    <Text style={styles.sectionTitle}>Overview</Text>
                    <View style={styles.statsGrid}>
                        <StatCard
                            title="Total Habits"
                            value={overallStats.total_habits.toString()}
                            icon="📋"
                            color="#3b82f6"
                        />
                        <StatCard
                            title="Active Streaks"
                            value={overallStats.active_streaks.toString()}
                            icon="🔥"
                            color="#f59e0b"
                        />
                        <StatCard
                            title="Longest Streak"
                            value={`${overallStats.longest_streak} days`}
                            icon="🏆"
                            color="#10b981"
                        />
                        <StatCard
                            title="Level"
                            value={overallStats.level.toString()}
                            icon="⭐"
                            color="#8b5cf6"
                        />
                        <StatCard
                            title="Total XP"
                            value={overallStats.total_xp.toLocaleString()}
                            icon="💎"
                            color="#06b6d4"
                        />
                        <StatCard
                            title="Achievements"
                            value={overallStats.achievements_count.toString()}
                            icon="🎖️"
                            color="#ef4444"
                        />
                    </View>
                </View>
            )}

            {/* Habit Analytics */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Habit Performance</Text>
                {habitAnalytics.length === 0 ? (
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No habit data available</Text>
                        <Text style={styles.emptySubtext}>Start tracking habits to see analytics</Text>
                    </View>
                ) : (
                    habitAnalytics.map((habit, index) => (
                        <HabitAnalyticsCard key={index} habit={habit} />
                    ))
                )}
            </View>
        </ScrollView>
    );
}

interface StatCardProps {
    title: string;
    value: string;
    icon: string;
    color: string;
}

function StatCard({ title, value, icon, color }: StatCardProps) {
    return (
        <View style={[styles.statCard, { borderLeftColor: color }]}>
            <View style={styles.statHeader}>
                <Text style={styles.statIcon}>{icon}</Text>
                <Text style={styles.statTitle}>{title}</Text>
            </View>
            <Text style={[styles.statValue, { color }]}>{value}</Text>
        </View>
    );
}

interface HabitAnalyticsCardProps {
    habit: HabitAnalytics;
}

function HabitAnalyticsCard({ habit }: HabitAnalyticsCardProps) {
    const getCompletionColor = (rate: number) => {
        if (rate >= 80) return '#10b981';
        if (rate >= 60) return '#f59e0b';
        return '#ef4444';
    };

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
        <View style={styles.habitCard}>
            <View style={styles.habitHeader}>
                <View style={styles.habitInfo}>
                    <Text style={styles.habitEmoji}>{getCategoryEmoji(habit.category)}</Text>
                    <View style={styles.habitTextContainer}>
                        <Text style={styles.habitTitle}>{habit.title}</Text>
                        <Text style={styles.habitCategory}>{habit.category}</Text>
                    </View>
                </View>
                <View style={styles.completionBadge}>
                    <Text style={[styles.completionRate, { color: getCompletionColor(habit.completion_rate) }]}>
                        {habit.completion_rate.toFixed(1)}%
                    </Text>
                </View>
            </View>

            <View style={styles.metricsRow}>
                <View style={styles.metric}>
                    <Text style={styles.metricValue}>{habit.streak}</Text>
                    <Text style={styles.metricLabel}>Current Streak</Text>
                </View>
                <View style={styles.metric}>
                    <Text style={styles.metricValue}>{habit.total_completions}</Text>
                    <Text style={styles.metricLabel}>Total Completions</Text>
                </View>
            </View>

            {/* Weekly Chart */}
            <View style={styles.chartContainer}>
                <Text style={styles.chartTitle}>Last 7 Days</Text>
                <View style={styles.chart}>
                    {habit.weekly_completions.map((count, index) => {
                        const maxCount = Math.max(...habit.weekly_completions, 1);
                        const height = (count / maxCount) * 40;
                        return (
                            <View key={index} style={styles.chartBarContainer}>
                                <View
                                    style={[
                                        styles.chartBar,
                                        {
                                            height: height,
                                            backgroundColor: count > 0 ? '#10b981' : '#e5e7eb',
                                        },
                                    ]}
                                />
                                <Text style={styles.chartDayLabel}>
                                    {['S', 'M', 'T', 'W', 'T', 'F', 'S'][index]}
                                </Text>
                            </View>
                        );
                    })}
                </View>
            </View>
        </View>
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
    statsGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 12,
    },
    statCard: {
        backgroundColor: 'white',
        padding: 16,
        borderRadius: 12,
        borderLeftWidth: 4,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
        width: (screenWidth - 44) / 2,
    },
    statHeader: {
        flexDirection: 'row',
        alignItems: 'center',
        marginBottom: 8,
    },
    statIcon: {
        fontSize: 20,
        marginRight: 8,
    },
    statTitle: {
        fontSize: 12,
        color: '#64748b',
        fontWeight: '600',
        flex: 1,
    },
    statValue: {
        fontSize: 24,
        fontWeight: 'bold',
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
        marginBottom: 16,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    habitHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
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
    habitCategory: {
        fontSize: 12,
        color: '#64748b',
        textTransform: 'capitalize',
    },
    completionBadge: {
        backgroundColor: '#f1f5f9',
        paddingHorizontal: 12,
        paddingVertical: 6,
        borderRadius: 20,
    },
    completionRate: {
        fontSize: 14,
        fontWeight: 'bold',
    },
    metricsRow: {
        flexDirection: 'row',
        justifyContent: 'space-around',
        marginBottom: 16,
        paddingVertical: 12,
        backgroundColor: '#f8fafc',
        borderRadius: 8,
    },
    metric: {
        alignItems: 'center',
    },
    metricValue: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1e293b',
    },
    metricLabel: {
        fontSize: 12,
        color: '#64748b',
        marginTop: 4,
    },
    chartContainer: {
        marginTop: 8,
    },
    chartTitle: {
        fontSize: 14,
        fontWeight: '600',
        color: '#64748b',
        marginBottom: 12,
    },
    chart: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'flex-end',
        height: 60,
    },
    chartBarContainer: {
        alignItems: 'center',
        flex: 1,
    },
    chartBar: {
        width: 20,
        borderRadius: 4,
        marginBottom: 8,
    },
    chartDayLabel: {
        fontSize: 12,
        color: '#64748b',
    },
});
