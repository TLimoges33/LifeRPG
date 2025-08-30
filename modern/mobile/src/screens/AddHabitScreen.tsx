import React, { useState } from 'react';
import {
    View,
    Text,
    ScrollView,
    StyleSheet,
    TextInput,
    TouchableOpacity,
    Alert,
    ActivityIndicator,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { apiClient } from '../lib/api';

const CATEGORIES = [
    { name: 'Health', emoji: '💪', color: '#10b981' },
    { name: 'Learning', emoji: '📚', color: '#3b82f6' },
    { name: 'Productivity', emoji: '⚡', color: '#f59e0b' },
    { name: 'Mindfulness', emoji: '🧘', color: '#8b5cf6' },
    { name: 'Social', emoji: '👥', color: '#ef4444' },
    { name: 'Creativity', emoji: '🎨', color: '#ec4899' },
    { name: 'Finance', emoji: '💰', color: '#059669' },
];

const HABIT_TEMPLATES = [
    {
        title: 'Drink 8 glasses of water',
        description: 'Stay hydrated throughout the day',
        category: 'health',
    },
    {
        title: 'Read for 30 minutes',
        description: 'Read books, articles, or educational content',
        category: 'learning',
    },
    {
        title: 'Exercise for 30 minutes',
        description: 'Any form of physical activity',
        category: 'health',
    },
    {
        title: 'Meditate for 10 minutes',
        description: 'Practice mindfulness and meditation',
        category: 'mindfulness',
    },
    {
        title: 'Write in journal',
        description: 'Reflect on your day and thoughts',
        category: 'creativity',
    },
    {
        title: 'Learn a new word',
        description: 'Expand your vocabulary daily',
        category: 'learning',
    },
];

export default function AddHabitScreen() {
    const navigation = useNavigation<any>();
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [selectedCategory, setSelectedCategory] = useState('');
    const [loading, setLoading] = useState(false);

    const createHabit = async () => {
        if (!title.trim()) {
            Alert.alert('Error', 'Please enter a habit title');
            return;
        }

        if (!selectedCategory) {
            Alert.alert('Error', 'Please select a category');
            return;
        }

        setLoading(true);

        try {
            const response = await apiClient.post('/habits', {
                title: title.trim(),
                description: description.trim(),
                category: selectedCategory.toLowerCase(),
            });

            if (response.ok) {
                navigation.goBack();
                Alert.alert('Success', 'Habit created successfully!');
            } else {
                const error = await response.json();
                Alert.alert('Error', error.detail || 'Failed to create habit');
            }
        } catch (error) {
            console.error('Error creating habit:', error);
            Alert.alert('Error', 'Failed to create habit');
        } finally {
            setLoading(false);
        }
    };

    const useTemplate = (template: typeof HABIT_TEMPLATES[0]) => {
        setTitle(template.title);
        setDescription(template.description);
        setSelectedCategory(template.category);
    };

    return (
        <ScrollView style={styles.container}>
            <View style={styles.header}>
                <Text style={styles.headerTitle}>Create New Habit</Text>
                <Text style={styles.headerSubtitle}>
                    Build a new positive habit to improve your life
                </Text>
            </View>

            {/* Habit Templates */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Quick Templates</Text>
                <Text style={styles.sectionSubtitle}>
                    Get started quickly with these popular habits
                </Text>
                <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.templatesContainer}>
                    {HABIT_TEMPLATES.map((template, index) => (
                        <TouchableOpacity
                            key={index}
                            style={styles.templateCard}
                            onPress={() => useTemplate(template)}
                        >
                            <Text style={styles.templateTitle}>{template.title}</Text>
                            <Text style={styles.templateDescription} numberOfLines={2}>
                                {template.description}
                            </Text>
                            <Text style={styles.templateCategory}>
                                {template.category.charAt(0).toUpperCase() + template.category.slice(1)}
                            </Text>
                        </TouchableOpacity>
                    ))}
                </ScrollView>
            </View>

            {/* Custom Habit Form */}
            <View style={styles.section}>
                <Text style={styles.sectionTitle}>Custom Habit</Text>

                <View style={styles.inputGroup}>
                    <Text style={styles.inputLabel}>Habit Title *</Text>
                    <TextInput
                        style={styles.textInput}
                        value={title}
                        onChangeText={setTitle}
                        placeholder="e.g., Drink 8 glasses of water"
                        maxLength={100}
                    />
                    <Text style={styles.characterCount}>{title.length}/100</Text>
                </View>

                <View style={styles.inputGroup}>
                    <Text style={styles.inputLabel}>Description</Text>
                    <TextInput
                        style={[styles.textInput, styles.textInputMultiline]}
                        value={description}
                        onChangeText={setDescription}
                        placeholder="Describe your habit and why it's important to you"
                        multiline
                        numberOfLines={3}
                        maxLength={500}
                    />
                    <Text style={styles.characterCount}>{description.length}/500</Text>
                </View>

                <View style={styles.inputGroup}>
                    <Text style={styles.inputLabel}>Category *</Text>
                    <View style={styles.categoriesGrid}>
                        {CATEGORIES.map((category) => (
                            <TouchableOpacity
                                key={category.name}
                                style={[
                                    styles.categoryButton,
                                    selectedCategory === category.name.toLowerCase() && {
                                        backgroundColor: category.color,
                                        borderColor: category.color,
                                    },
                                ]}
                                onPress={() => setSelectedCategory(category.name.toLowerCase())}
                            >
                                <Text style={styles.categoryEmoji}>{category.emoji}</Text>
                                <Text
                                    style={[
                                        styles.categoryText,
                                        selectedCategory === category.name.toLowerCase() && styles.categoryTextSelected,
                                    ]}
                                >
                                    {category.name}
                                </Text>
                            </TouchableOpacity>
                        ))}
                    </View>
                </View>

                <TouchableOpacity
                    style={[styles.createButton, loading && styles.createButtonDisabled]}
                    onPress={createHabit}
                    disabled={loading}
                >
                    {loading ? (
                        <ActivityIndicator color="white" />
                    ) : (
                        <Text style={styles.createButtonText}>Create Habit</Text>
                    )}
                </TouchableOpacity>
            </View>
        </ScrollView>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        backgroundColor: '#f8fafc',
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
    headerTitle: {
        fontSize: 24,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 8,
    },
    headerSubtitle: {
        fontSize: 16,
        color: '#64748b',
    },
    section: {
        margin: 16,
    },
    sectionTitle: {
        fontSize: 20,
        fontWeight: 'bold',
        color: '#1e293b',
        marginBottom: 8,
    },
    sectionSubtitle: {
        fontSize: 14,
        color: '#64748b',
        marginBottom: 16,
    },
    templatesContainer: {
        marginBottom: 8,
    },
    templateCard: {
        backgroundColor: 'white',
        padding: 16,
        borderRadius: 12,
        marginRight: 12,
        width: 200,
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 1 },
        shadowOpacity: 0.05,
        shadowRadius: 2,
        elevation: 2,
    },
    templateTitle: {
        fontSize: 16,
        fontWeight: '600',
        color: '#1e293b',
        marginBottom: 8,
    },
    templateDescription: {
        fontSize: 14,
        color: '#64748b',
        marginBottom: 8,
        lineHeight: 20,
    },
    templateCategory: {
        fontSize: 12,
        color: '#8b5cf6',
        fontWeight: '600',
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
    characterCount: {
        fontSize: 12,
        color: '#9ca3af',
        textAlign: 'right',
        marginTop: 4,
    },
    categoriesGrid: {
        flexDirection: 'row',
        flexWrap: 'wrap',
        gap: 12,
    },
    categoryButton: {
        flexDirection: 'row',
        alignItems: 'center',
        backgroundColor: 'white',
        paddingVertical: 12,
        paddingHorizontal: 16,
        borderRadius: 12,
        borderWidth: 2,
        borderColor: '#e5e7eb',
        minWidth: 120,
    },
    categoryEmoji: {
        fontSize: 20,
        marginRight: 8,
    },
    categoryText: {
        fontSize: 14,
        fontWeight: '600',
        color: '#64748b',
    },
    categoryTextSelected: {
        color: 'white',
    },
    createButton: {
        backgroundColor: '#6366f1',
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
        marginTop: 16,
    },
    createButtonDisabled: {
        opacity: 0.6,
    },
    createButtonText: {
        color: 'white',
        fontSize: 18,
        fontWeight: 'bold',
    },
});
