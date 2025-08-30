import React, { useState, useEffect } from 'react';
import {
    View,
    Text,
    ScrollView,
    StyleSheet,
    TouchableOpacity,
    Alert,
    ActivityIndicator,
    TextInput,
    Modal,
} from 'react-native';
import { useRoute, useNavigation } from '@react-navigation/native';
import { apiClient } from '../lib/api';

interface Habit {
    id: number;
    title: string;
    description: string;
    category: string;
    streak: number;
    total_completions: number;
    completed_today: boolean;
    created_at: string;
}

interface HabitHistory {
    date: string;
    completed: boolean;
}

export default function HabitDetailScreen() {
    const route = useRoute<any>();
    const navigation = useNavigation<any>();
    const { habitId } = route.params;

    const [habit, setHabit] = useState<Habit | null>(null);
    const [history, setHistory] = useState<HabitHistory[]>([]);
    const [loading, setLoading] = useState(true);
    const [editModalVisible, setEditModalVisible] = useState(false);
    const [editTitle, setEditTitle] = useState('');
    const [editDescription, setEditDescription] = useState('');
    const [editCategory, setEditCategory] = useState('');

    const loadHabitDetail = async () => {
        try {
            const [habitResponse, historyResponse] = await Promise.all([
                apiClient.get(`/habits/${habitId}`),
                apiClient.get(`/habits/${habitId}/history`),
            ]);

            if (habitResponse.ok) {
                const habitData = await habitResponse.json();
                setHabit(habitData);
                setEditTitle(habitData.title);
                setEditDescription(habitData.description);
                setEditCategory(habitData.category);
            }

            if (historyResponse.ok) {
                setHistory(await historyResponse.json());
            }
        } catch (error) {
            console.error('Error loading habit detail:', error);
            Alert.alert('Error', 'Failed to load habit details');
        } finally {
            setLoading(false);
        }
    };

    const completeHabit = async () => {
        if (!habit) return;

        try {
            const response = await apiClient.post(`/habits/${habit.id}/complete`);

            if (response.ok) {
                const result = await response.json();
                Alert.alert(
                    'Habit Completed!',
                    `+${result.xp_earned} XP${result.achievement_unlocked ? `\n🏆 ${result.achievement_unlocked.title}` : ''}`,
                    [{ text: 'OK', onPress: () => loadHabitDetail() }]
                );
            } else {
                Alert.alert('Error', 'Failed to complete habit');
            }
        } catch (error) {
            console.error('Error completing habit:', error);
            Alert.alert('Error', 'Failed to complete habit');
        }
    };

    const updateHabit = async () => {
        if (!habit) return;

        try {
            const response = await apiClient.put(`/habits/${habit.id}`, {
                title: editTitle,
                description: editDescription,
                category: editCategory,
            });

            if (response.ok) {
                setEditModalVisible(false);
                loadHabitDetail();
                Alert.alert('Success', 'Habit updated successfully');
            } else {
                Alert.alert('Error', 'Failed to update habit');
            }
        } catch (error) {
            console.error('Error updating habit:', error);
            Alert.alert('Error', 'Failed to update habit');
        }
    };

    const deleteHabit = async () => {
        if (!habit) return;

        Alert.alert(
            'Delete Habit',
            `Are you sure you want to delete "${habit.title}"? This action cannot be undone.`,
            [
                { text: 'Cancel', style: 'cancel' },
                {
                    text: 'Delete',
                    style: 'destructive',
                    onPress: async () => {
                        try {
                            const response = await apiClient.delete(`/habits/${habit.id}`);

                            if (response.ok) {
                                navigation.goBack();
                                Alert.alert('Success', 'Habit deleted successfully');
                            } else {
                                Alert.alert('Error', 'Failed to delete habit');
                            }
                        } catch (error) {
                            console.error('Error deleting habit:', error);
                            Alert.alert('Error', 'Failed to delete habit');
                        }
                    },
                },
            ]
        );
    };

    useEffect(() => {
        loadHabitDetail();
    }, [habitId]);

    if (loading) {
        return (
            <View style={styles.centerContainer}>
                <ActivityIndicator size="large" color="#6366f1" />
                <Text style={styles.loadingText}>Loading habit details...</Text>
            </View>
        );
    }

    if (!habit) {
        return (
            <View style={styles.centerContainer}>
                <Text style={styles.errorText}>Habit not found</Text>
                <TouchableOpacity
                    style={styles.backButton}
                    onPress={() => navigation.goBack()}
                >
                    <Text style={styles.backButtonText}>Go Back</Text>
                </TouchableOpacity>
            </View>
        );
    }

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

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
        });
    };

    return (
        <ScrollView style={styles.container}>
            {/* Habit Header */}
            <View style={styles.header}>
                <View style={styles.habitInfo}>
                    <Text style={styles.habitEmoji}>{getCategoryEmoji(habit.category)}</Text>
                    <View style={styles.habitTextContainer}>
                        <Text style={styles.habitTitle}>{habit.title}</Text>
                        <Text style={styles.habitDescription}>{habit.description}</Text>
                        <Text style={styles.habitCategory}>{habit.category}</Text>
                    </View>
                </View>
                <TouchableOpacity
                    style={[
                        styles.completeButton,
                        habit.completed_today && styles.completedButton,
                    ]}
                    onPress={completeHabit}
                    disabled={habit.completed_today}
                >
                    <Text style={styles.completeButtonText}>
                        {habit.completed_today ? '✓ Completed' : 'Mark Complete'}
                    </Text>
                </TouchableOpacity>
            </View>

            {/* Stats */}
            <View style={styles.statsContainer}>
                <View style={styles.statCard}>
                    <Text style={styles.statNumber}>{habit.streak}</Text>
                    <Text style={styles.statLabel}>Current Streak</Text>
                </View>
                <View style={styles.statCard}>
                    <Text style={styles.statNumber}>{habit.total_completions}</Text>
                    <Text style={styles.statLabel}>Total Completions</Text>
                </View>
                <View style={styles.statCard}>
                    <Text style={styles.statNumber}>
                        {Math.round((habit.total_completions / Math.max(1, Math.ceil((Date.now() - new Date(habit.created_at).getTime()) / (1000 * 60 * 60 * 24)))) * 100)}%
                    </Text>
                    <Text style={styles.statLabel}>Success Rate</Text>
                </View>
            </View>

            {/* History Calendar */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>History</Text>
                <View style={styles.historyGrid}>
                    {history.slice(0, 28).map((day, index) => (
                        <View
                            key={index}
                            style={[
                                styles.historyDay,
                                day.completed && styles.historyDayCompleted,
                            ]}
                        >
                            <Text style={styles.historyDayText}>
                                {new Date(day.date).getDate()}
                            </Text>
                        </View>
                    ))}
                </View>
            </View>

            {/* Actions */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Actions</Text>
                <TouchableOpacity
                    style={styles.actionButton}
                    onPress={() => setEditModalVisible(true)}
                >
                    <Text style={styles.actionButtonText}>✏️ Edit Habit</Text>
                </TouchableOpacity>
                <TouchableOpacity
                    style={[styles.actionButton, styles.deleteButton]}
                    onPress={deleteHabit}
                >
                    <Text style={[styles.actionButtonText, styles.deleteButtonText]}>
                        🗑️ Delete Habit
                    </Text>
                </TouchableOpacity>
            </View>

            {/* Edit Modal */}
            <Modal
                visible={editModalVisible}
                animationType="slide"
                presentationStyle="pageSheet"
            >
                <View style={styles.modalContainer}>
                    <View style={styles.modalHeader}>
                        <TouchableOpacity onPress={() => setEditModalVisible(false)}>
                            <Text style={styles.modalCancelText}>Cancel</Text>
                        </TouchableOpacity>
                        <Text style={styles.modalTitle}>Edit Habit</Text>
                        <TouchableOpacity onPress={updateHabit}>
                            <Text style={styles.modalSaveText}>Save</Text>
                        </TouchableOpacity>
                    </View>

                    <ScrollView style={styles.modalContent}>
                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Title</Text>
                            <TextInput
                                style={styles.textInput}
                                value={editTitle}
                                onChangeText={setEditTitle}
                                placeholder="Enter habit title"
                            />
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Description</Text>
                            <TextInput
                                style={[styles.textInput, styles.textInputMultiline]}
                                value={editDescription}
                                onChangeText={setEditDescription}
                                placeholder="Enter habit description"
                                multiline
                                numberOfLines={3}
                            />
                        </View>

                        <View style={styles.inputGroup}>
                            <Text style={styles.inputLabel}>Category</Text>
                            <TextInput
                                style={styles.textInput}
                                value={editCategory}
                                onChangeText={setEditCategory}
                                placeholder="Enter category"
                            />
                        </View>
                    </ScrollView>
                </View>
            </Modal>
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
    errorText: {
        fontSize: 18,
        color: '#ef4444',
        marginBottom: 20,
    },
    backButton: {
        backgroundColor: '#6366f1',
        paddingHorizontal: 20,
        paddingVertical: 12,
        borderRadius: 8,
    },
    backButtonText: {
        color: 'white',
        fontSize: 16,
        fontWeight: '600',
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
    habitInfo: {
        flexDirection: 'row',
        marginBottom: 20,
    },
    habitEmoji: {
        fontSize: 32,
        marginRight: 16,
    },
    habitTextContainer: {
        flex: 1,
    },
    habitTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 8,
    },
    habitDescription: {
        fontSize: 16,
        color: '#64748b',
        marginBottom: 8,
        lineHeight: 24,
    },
    habitCategory: {
        fontSize: 14,
        color: '#8b5cf6',
        fontWeight: '600',
        textTransform: 'capitalize',
    },
    completeButton: {
        backgroundColor: '#6366f1',
        paddingVertical: 12,
        paddingHorizontal: 24,
        borderRadius: 8,
        alignItems: 'center',
    },
    completedButton: {
        backgroundColor: '#10b981',
    },
    completeButtonText: {
        color: 'white',
        fontSize: 16,
        fontWeight: '600',
    },
    statsContainer: {
        flexDirection: 'row',
        padding: 16,
        gap: 12,
    },
    statCard: {
        flex: 1,
        backgroundColor: 'white',
        padding: 16,
        borderRadius: 12,
        alignItems: 'center',
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 2,
    },
    statNumber: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 4,
    },
    statLabel: {
        fontSize: 12,
        color: '#64748b',
        textAlign: 'center',
    },
    section: {
        margin: 16,
    },
    sectionTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 16,
    },
    historyGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 8,
    },
    historyDay: {
        width: 32,
        height: 32,
        borderRadius: 16,
        backgroundColor: '#f1f5f9',
        justifyContent: 'center',
        alignItems: 'center',
    },
    historyDayCompleted: {
        backgroundColor: '#10b981',
    },
    historyDayText: {
        fontSize: 12,
        color: '#64748b',
        fontWeight: '600',
    },
    actionButton: {
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
    actionButtonText: {
        fontSize: 16,
        fontWeight: '600',
        color: '#1e293b',
        textAlign: 'center',
    },
    deleteButton: {
        backgroundColor: '#fef2f2',
        borderWidth: 1,
        borderColor: '#fecaca',
    },
    deleteButtonText: {
        color: '#dc2626',
    },
    modalContainer: {
        flex: 1,
        backgroundColor: 'white',
    },
    modalHeader: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: 16,
        borderBottomWidth: 1,
        borderBottomColor: '#e5e7eb',
    },
    modalCancelText: {
        fontSize: 16,
        color: '#6b7280',
    },
    modalTitle: {
        fontSize: 18,
        fontWeight: 'bold',
        color: '#1e293b',
    },
    modalSaveText: {
        fontSize: 16,
        color: '#6366f1',
        fontWeight: '600',
    },
    modalContent: {
        flex: 1,
        padding: 16,
    },
    inputGroup: {
        marginBottom: 24,
    },
    inputLabel: {
        fontSize: 16,
        fontWeight: '600',
        color: '#1e293b',
        marginBottom: 8,
    },
    textInput: {
        borderWidth: 1,
        borderColor: '#d1d5db',
        borderRadius: 8,
        padding: 12,
        fontSize: 16,
        backgroundColor: 'white',
    },
    textInputMultiline: {
        height: 80,
        textAlignVertical: 'top',
    },
});
