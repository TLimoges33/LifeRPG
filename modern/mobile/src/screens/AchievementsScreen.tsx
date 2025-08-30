import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    ScrollView,
    StyleSheet,
    ActivityIndicator,
    RefreshControl,
    TouchableOpacity,
} from 'react-native';
import { apiClient } from '../lib/api';

interface Achievement {
    id: number;
    title: string;
    description: string;
    category: string;
    unlocked: boolean;
    unlocked_at?: string;
    progress?: number;
    total_required?: number;
    rarity: 'common' | 'rare' | 'epic' | 'legendary';
}

interface AchievementCategory {
    name: string;
    achievements: Achievement[];
}

export default function AchievementsScreen() {
    const [achievements, setAchievements] = useState<Achievement[]>([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [selectedCategory, setSelectedCategory] = useState<string>('all');

    const loadAchievements = async () => {
        try {
            const response = await apiClient.get('/gamification/achievements');

            if (response.ok) {
                setAchievements(await response.json());
            }
        } catch (error) {
            console.error('Error loading achievements:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const onRefresh = () => {
        setRefreshing(true);
        loadAchievements();
    };

    useEffect(() => {
        loadAchievements();
    }, []);

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#6366f1" />
                <Text style={styles.loadingText}>Loading achievements...</Text>
            </View>
        );
    }

    const categories = ['all', ...new Set(achievements.map(a => a.category))];
    const filteredAchievements = selectedCategory === 'all'
        ? achievements
        : achievements.filter(a => a.category === selectedCategory);

    const unlockedCount = achievements.filter(a => a.unlocked).length;
    const totalCount = achievements.length;

    return (
        <View style={styles.container}>
            {/* Header Stats */}
            <View style={styles.header}>
                <View style={styles.progressContainer}>
                    <Text style={styles.progressTitle}>Achievement Progress</Text>
                    <Text style={styles.progressText}>
                        {unlockedCount} / {totalCount} unlocked
                    </Text>
                    <View style={styles.progressBar}>
                        <View
                            style={[
                                styles.progressFill,
                                { width: `${(unlockedCount / totalCount) * 100}%` },
                            ]}
                        />
                    </View>
                </View>
            </View>

            {/* Category Filter */}
            <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.categoryContainer}>
                {categories.map((category) => (
                    <TouchableOpacity
                        key={category}
                        style={[
                            styles.categoryButton,
                            selectedCategory === category && styles.categoryButtonActive,
                        ]}
                        onPress={() => setSelectedCategory(category)}
                    >
                        <Text
                            style={[
                                styles.categoryButtonText,
                                selectedCategory === category && styles.categoryButtonTextActive,
                            ]}
                        >
                            {category.charAt(0).toUpperCase() + category.slice(1)}
                        </Text>
                    </TouchableOpacity>
                ))}
            </ScrollView>

            {/* Achievements List */}
            <ScrollView
                style={styles.achievementsList}
                refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
            >
                {filteredAchievements.length === 0 ? (
                    <View style={styles.emptyState}>
                        <Text style={styles.emptyText}>No achievements found</Text>
                        <Text style={styles.emptySubtext}>Keep using LifeRPG to unlock achievements!</Text>
                    </View>
                ) : (
                    filteredAchievements.map((achievement) => (
                        <AchievementCard key={achievement.id} achievement={achievement} />
                    ))
                )}
            </ScrollView>
        </View>
    );
}

interface AchievementCardProps {
    achievement: Achievement;
}

function AchievementCard({ achievement }: AchievementCardProps) {
    const getRarityColor = (rarity: string) => {
        const colors = {
            common: '#64748b',
            rare: '#3b82f6',
            epic: '#8b5cf6',
            legendary: '#f59e0b',
        };
        return colors[rarity as keyof typeof colors] || colors.common;
    };

    const getRarityEmoji = (rarity: string) => {
        const emojis = {
            common: '🥉',
            rare: '🥈',
            epic: '🥇',
            legendary: '💎',
        };
        return emojis[rarity as keyof typeof emojis] || emojis.common;
    };

    const getCategoryEmoji = (category: string) => {
        const emojis: { [key: string]: string } = {
            habits: '✅',
            streaks: '🔥',
            experience: '⭐',
            social: '👥',
            completion: '🎯',
            consistency: '📅',
            mastery: '🏆',
        };
        return emojis[category.toLowerCase()] || '🏅';
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        });
    };

    return (
        <View style={[
            styles.achievementCard,
            !achievement.unlocked && styles.achievementCardLocked,
        ]}>
            <View style={styles.achievementHeader}>
                <View style={styles.achievementIconContainer}>
                    <Text style={styles.categoryEmoji}>{getCategoryEmoji(achievement.category)}</Text>
                    <Text style={styles.rarityEmoji}>{getRarityEmoji(achievement.rarity)}</Text>
                </View>
                <View style={styles.achievementInfo}>
                    <Text style={[
                        styles.achievementTitle,
                        !achievement.unlocked && styles.achievementTitleLocked,
                    ]}>
                        {achievement.title}
                    </Text>
                    <Text style={[
                        styles.achievementDescription,
                        !achievement.unlocked && styles.achievementDescriptionLocked,
                    ]}>
                        {achievement.description}
                    </Text>
                    <View style={styles.achievementMeta}>
                        <Text style={[
                            styles.achievementCategory,
                            { color: getRarityColor(achievement.rarity) },
                        ]}>
                            {achievement.category} • {achievement.rarity}
                        </Text>
                        {achievement.unlocked && achievement.unlocked_at && (
                            <Text style={styles.unlockedDate}>
                                Unlocked {formatDate(achievement.unlocked_at)}
                            </Text>
                        )}
                    </View>
                </View>
                <View style={styles.achievementStatus}>
                    {achievement.unlocked ? (
                        <View style={styles.unlockedBadge}>
                            <Text style={styles.unlockedText}>✓</Text>
                        </View>
                    ) : (
                        <View style={styles.lockedBadge}>
                            <Text style={styles.lockedText}>🔒</Text>
                        </View>
                    )}
                </View>
            </View>

            {/* Progress Bar for Locked Achievements */}
            {!achievement.unlocked && achievement.progress !== undefined && achievement.total_required && (
                <View style={styles.progressSection}>
                    <View style={styles.progressInfo}>
                        <Text style={styles.progressLabel}>Progress</Text>
                        <Text style={styles.progressNumbers}>
                            {achievement.progress} / {achievement.total_required}
                        </Text>
                    </View>
                    <View style={styles.progressBarContainer}>
                        <View
                            style={[
                                styles.progressBarFill,
                                {
                                    width: `${(achievement.progress / achievement.total_required) * 100}%`,
                                    backgroundColor: getRarityColor(achievement.rarity),
                                },
                            ]}
                        />
                    </View>
                </View>
            )}
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
    header: {
        backgroundColor: 'white',
        padding: 20,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    progressContainer: {
        alignItems: 'center',
    },
    progressTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 8,
    },
    progressText: {
        fontSize: 16,
        color: '#64748b',
        marginBottom: 12,
    },
    progressBar: {
        width: '100%',
        height: 8,
        backgroundColor: '#e2e8f0',
        borderRadius: 4,
    },
    progressFill: {
        height: '100%',
        backgroundColor: '#6366f1',
        borderRadius: 4,
    },
    categoryContainer: {
        backgroundColor: 'white',
        paddingHorizontal: 16,
        paddingVertical: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 2,
    },
    categoryButton: {
        paddingHorizontal: 16,
        paddingVertical: 8,
        marginRight: 8,
        backgroundColor: '#f1f5f9',
        borderRadius: 20,
    },
    categoryButtonActive: {
        backgroundColor: '#6366f1',
    },
    categoryButtonText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#64748b',
    },
    categoryButtonTextActive: {
        color: 'white',
    },
    achievementsList: {
        flex: 1,
        padding: 16,
    },
    emptyState: {
        backgroundColor: 'white',
        padding: 40,
        borderRadius: 12,
        alignItems: 'center',
        marginTop: 40,
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
    achievementCard: {
        backgroundColor: 'white',
        padding: 16,
        borderRadius: 12,
        marginBottom: 12,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.1,
        shadowRadius: 4,
        elevation: 3,
    },
    achievementCardLocked: {
        opacity: 0.7,
    },
    achievementHeader: {
        flexDirection: 'row',
        alignItems: 'flex-start',
    },
    achievementIconContainer: {
        flexDirection: 'row',
        marginRight: 12,
    },
    categoryEmoji: {
        fontSize: 24,
        marginRight: 4,
    },
    rarityEmoji: {
        fontSize: 16,
    },
    achievementInfo: {
        flex: 1,
    },
    achievementTitle: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 4,
    },
    achievementTitleLocked: {
        color: '#64748b',
    },
    achievementDescription: {
        fontSize: 14,
        color: '#64748b',
        marginBottom: 8,
        lineHeight: 20,
    },
    achievementDescriptionLocked: {
        color: '#94a3b8',
    },
    achievementMeta: {
        gap: 4,
    },
    achievementCategory: {
        fontSize: 12,
        fontWeight: '600',
        textTransform: 'capitalize',
    },
    unlockedDate: {
        fontSize: 12,
        color: '#10b981',
        fontWeight: '500',
    },
    achievementStatus: {
        marginLeft: 12,
    },
    unlockedBadge: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: '#10b981',
        justifyContent: 'center',
        alignItems: 'center',
    },
    unlockedText: {
        color: 'white',
        fontSize: 16,
        fontWeight: 'bold',
    },
    lockedBadge: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: '#e5e7eb',
        justifyContent: 'center',
        alignItems: 'center',
    },
    lockedText: {
        fontSize: 16,
    },
    progressSection: {
        marginTop: 16,
        paddingTop: 16,
        borderTopWidth: 1,
        borderTopColor: '#f1f5f9',
    },
    progressInfo: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        marginBottom: 8,
    },
    progressLabel: {
        fontSize: 14,
        color: '#64748b',
        fontWeight: '600',
    },
    progressNumbers: {
        fontSize: 14,
        color: '#1e293b',
        fontWeight: '600',
    },
    progressBarContainer: {
        height: 6,
        backgroundColor: '#f1f5f9',
        borderRadius: 3,
    },
    progressBarFill: {
        height: '100%',
        borderRadius: 3,
    },
});
