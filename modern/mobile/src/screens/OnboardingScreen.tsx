import React, { useState } from 'react';
import {
    View,
    Text,
    ScrollView,
    StyleSheet,
    TouchableOpacity,
    Dimensions,
    Image,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';

const { width: screenWidth } = Dimensions.get('window');

const ONBOARDING_SLIDES = [
    {
        title: 'Welcome to LifeRPG',
        subtitle: 'Transform your habits into an exciting adventure',
        description: 'Turn everyday tasks into quests, earn experience points, and level up your life.',
        emoji: '🎮',
        color: '#6366f1',
    },
    {
        title: 'Build Powerful Habits',
        subtitle: 'Track your daily progress with ease',
        description: 'Create custom habits, set reminders, and watch your consistency improve over time.',
        emoji: '✅',
        color: '#10b981',
    },
    {
        title: 'Earn Rewards & Level Up',
        subtitle: 'Gamify your personal growth',
        description: 'Gain XP for completing habits, unlock achievements, and see your progress visualized.',
        emoji: '🏆',
        color: '#f59e0b',
    },
    {
        title: 'Track Your Analytics',
        subtitle: 'Understand your patterns',
        description: 'View detailed analytics, streak tracking, and insights into your habit patterns.',
        emoji: '📊',
        color: '#8b5cf6',
    },
];

export default function OnboardingScreen() {
    const navigation = useNavigation<any>();
    const [currentSlide, setCurrentSlide] = useState(0);

    const nextSlide = () => {
        if (currentSlide < ONBOARDING_SLIDES.length - 1) {
            setCurrentSlide(currentSlide + 1);
        } else {
            completeOnboarding();
        }
    };

    const prevSlide = () => {
        if (currentSlide > 0) {
            setCurrentSlide(currentSlide - 1);
        }
    };

    const completeOnboarding = () => {
        // Mark onboarding as complete and navigate to main app
        navigation.replace('MainTabs');
    };

    const skip = () => {
        completeOnboarding();
    };

    const slide = ONBOARDING_SLIDES[currentSlide];

    if (!slide) {
        return null; // Safety check
    }

    return (
        <View style={[styles.container, { backgroundColor: slide.color }]}>
            {/* Skip Button */}
            <TouchableOpacity style={styles.skipButton} onPress={skip}>
                <Text style={styles.skipText}>Skip</Text>
            </TouchableOpacity>

            {/* Slide Content */}
            <View style={styles.slideContainer}>
                <View style={styles.emojiContainer}>
                    <Text style={styles.emoji}>{slide.emoji}</Text>
                </View>

                <View style={styles.contentContainer}>
                    <Text style={styles.title}>{slide.title}</Text>
                    <Text style={styles.subtitle}>{slide.subtitle}</Text>
                    <Text style={styles.description}>{slide.description}</Text>
                </View>
            </View>

            {/* Navigation */}
            <View style={styles.navigationContainer}>
                {/* Page Indicators */}
                <View style={styles.pageIndicators}>
                    {ONBOARDING_SLIDES.map((_, index) => (
                        <View
                            key={index}
                            style={[
                                styles.pageIndicator,
                                currentSlide === index && styles.pageIndicatorActive,
                            ]}
                        />
                    ))}
                </View>

                {/* Navigation Buttons */}
                <View style={styles.buttonContainer}>
                    <TouchableOpacity
                        style={[
                            styles.navButton,
                            styles.prevButton,
                            currentSlide === 0 && styles.navButtonDisabled,
                        ]}
                        onPress={prevSlide}
                        disabled={currentSlide === 0}
                    >
                        <Text style={[styles.navButtonText, styles.prevButtonText]}>
                            Previous
                        </Text>
                    </TouchableOpacity>

                    <TouchableOpacity style={styles.navButton} onPress={nextSlide}>
                        <Text style={styles.navButtonText}>
                            {currentSlide === ONBOARDING_SLIDES.length - 1 ? 'Get Started' : 'Next'}
                        </Text>
                    </TouchableOpacity>
                </View>
            </View>
        </View>
    );
}

const styles = StyleSheet.create({
    container: {
        flex: 1,
        justifyContent: 'space-between',
    },
    skipButton: {
        position: 'absolute',
        top: 60,
        right: 20,
        zIndex: 10,
        paddingHorizontal: 16,
        paddingVertical: 8,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        borderRadius: 20,
    },
    skipText: {
        color: 'white',
        fontSize: 16,
        fontWeight: '600',
    },
    slideContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        paddingHorizontal: 40,
    },
    emojiContainer: {
        width: 120,
        height: 120,
        borderRadius: 60,
        backgroundColor: 'rgba(255, 255, 255, 0.2)',
        justifyContent: 'center',
        alignItems: 'center',
        marginBottom: 40,
    },
    emoji: {
        fontSize: 60,
    },
    contentContainer: {
        alignItems: 'center',
        maxWidth: 300,
    },
    title: {
        fontSize: 28,
        fontWeight: 'bold',
        color: 'white',
        textAlign: 'center',
        marginBottom: 16,
    },
    subtitle: {
        fontSize: 18,
        color: 'rgba(255, 255, 255, 0.9)',
        textAlign: 'center',
        marginBottom: 20,
        fontWeight: '600',
    },
    description: {
        fontSize: 16,
        color: 'rgba(255, 255, 255, 0.8)',
        textAlign: 'center',
        lineHeight: 24,
    },
    navigationContainer: {
        paddingHorizontal: 40,
        paddingBottom: 50,
    },
    pageIndicators: {
        flexDirection: 'row',
        justifyContent: 'center',
        marginBottom: 40,
    },
    pageIndicator: {
        width: 8,
        height: 8,
        borderRadius: 4,
        backgroundColor: 'rgba(255, 255, 255, 0.3)',
        marginHorizontal: 4,
    },
    pageIndicatorActive: {
        backgroundColor: 'white',
        width: 24,
    },
    buttonContainer: {
        flexDirection: 'row',
        justifyContent: 'space-between',
        gap: 16,
    },
    navButton: {
        flex: 1,
        backgroundColor: 'white',
        paddingVertical: 16,
        borderRadius: 12,
        alignItems: 'center',
    },
    prevButton: {
        backgroundColor: 'transparent',
        borderWidth: 2,
        borderColor: 'white',
    },
    navButtonDisabled: {
        opacity: 0.3,
    },
    navButtonText: {
        fontSize: 16,
        fontWeight: 'bold',
        color: '#1e293b',
    },
    prevButtonText: {
        color: 'white',
    },
});
