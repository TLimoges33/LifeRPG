import React, { useEffect, useState } from 'react';
import * as BackgroundFetch from 'expo-background-fetch';
import { BackgroundFetchResult } from 'expo-background-fetch';
import * as TaskManager from 'expo-task-manager';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';
import LoginScreen from './src/screens/Login';
import HomeScreen from './src/screens/Home';
import HabitsScreen from './src/screens/HabitsScreen';
import AnalyticsScreen from './src/screens/AnalyticsScreen';
import AchievementsScreen from './src/screens/AchievementsScreen';
import HabitDetailScreen from './src/screens/HabitDetailScreen';
import AddHabitScreen from './src/screens/AddHabitScreen';

export type RootStackParamList = {
    Login: undefined;
    MainTabs: undefined;
    HabitDetail: { habitId: number };
    AddHabit: undefined;
};

export type TabParamList = {
    Home: undefined;
    Habits: undefined;
    Analytics: undefined;
    Achievements: undefined;
};

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator<TabParamList>();

function TabIcon({ emoji }: { emoji: string }) {
    return <Text style={{ fontSize: 24 }}>{emoji}</Text>;
}

function MainTabs() {
    return (
        <Tab.Navigator
            screenOptions={{
                headerShown: false,
                tabBarStyle: {
                    backgroundColor: 'white',
                    borderTopWidth: 1,
                    borderTopColor: '#e5e7eb',
                    paddingTop: 8,
                    paddingBottom: 8,
                    height: 80,
                },
                tabBarActiveTintColor: '#6366f1',
                tabBarInactiveTintColor: '#64748b',
                tabBarLabelStyle: {
                    fontSize: 12,
                    fontWeight: '600',
                    marginTop: 4,
                },
            }}
        >
            <Tab.Screen
                name="Home"
                component={HomeScreen}
                options={{
                    tabBarIcon: () => <TabIcon emoji="🏠" />,
                    headerShown: true,
                    title: 'LifeRPG',
                }}
            />
            <Tab.Screen
                name="Habits"
                component={HabitsScreen}
                options={{
                    tabBarIcon: () => <TabIcon emoji="✅" />,
                    headerShown: true,
                    title: 'Habits',
                }}
            />
            <Tab.Screen
                name="Analytics"
                component={AnalyticsScreen}
                options={{
                    tabBarIcon: () => <TabIcon emoji="📊" />,
                    headerShown: true,
                    title: 'Analytics',
                }}
            />
            <Tab.Screen
                name="Achievements"
                component={AchievementsScreen}
                options={{
                    tabBarIcon: () => <TabIcon emoji="🏆" />,
                    headerShown: true,
                    title: 'Achievements',
                }}
            />
        </Tab.Navigator>
    );
}

export default function App() {
    const [initialRoute, setInitialRoute] = useState<keyof RootStackParamList>('Login');

    useEffect(() => {
        // Lazy import to avoid circular
        import('./src/lib/auth').then(async ({ getTokens, refresh }) => {
            const t = await getTokens();
            if (t?.accessToken) {
                // Attempt a refresh to ensure validity (non-blocking)
                try { await refresh(); } catch { }
                setInitialRoute('MainTabs');
            }
        });

        // Register background fetch
        const TASK = 'liferpg-sync-task';
        TaskManager.defineTask(TASK, async () => {
            try {
                const [{ auth }, { openDb, pendingChanges, clearChangesUpTo, pushChanges }] = await Promise.all([
                    import('./src/lib/auth'),
                    import('./src/lib/db'),
                ]);
                const tokens = await auth.getTokens();
                const accessToken = tokens?.accessToken;
                if (!accessToken) return BackgroundFetchResult.NoData;
                const db = openDb();
                const changes = await pendingChanges(db);
                if (changes.length === 0) return BackgroundFetchResult.NoData;
                const extra: any = (require('expo-constants').default.expoConfig?.extra) || {};
                const apiBaseUrl = extra.apiBaseUrl;
                const res = await pushChanges(apiBaseUrl, accessToken, changes);
                if (res?.applied) await clearChangesUpTo(db, changes[changes.length - 1].id);
                return BackgroundFetchResult.NewData;
            } catch {
                return BackgroundFetchResult.Failed;
            }
        });
        BackgroundFetch.registerTaskAsync(TASK, { minimumInterval: 15 * 60, stopOnTerminate: false, startOnBoot: true }).catch(() => { });
    }, []);

    return (
        <NavigationContainer>
            <Stack.Navigator
                initialRouteName={initialRoute}
                screenOptions={{
                    headerStyle: {
                        backgroundColor: '#6366f1',
                    },
                    headerTintColor: 'white',
                    headerTitleStyle: {
                        fontWeight: 'bold',
                    },
                }}
            >
                <Stack.Screen
                    name="Login"
                    component={LoginScreen}
                    options={{
                        title: 'Sign in',
                        headerShown: false,
                    }}
                />
                <Stack.Screen
                    name="MainTabs"
                    component={MainTabs}
                    options={{
                        headerShown: false,
                    }}
                />
                <Stack.Screen
                    name="HabitDetail"
                    component={HabitDetailScreen}
                    options={{
                        title: 'Habit Details',
                    }}
                />
                <Stack.Screen
                    name="AddHabit"
                    component={AddHabitScreen}
                    options={{
                        title: 'Add Habit',
                        presentation: 'modal',
                    }}
                />
            </Stack.Navigator>
        </NavigationContainer>
    );
}
