import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Home, Target, BarChart3, Trophy, Settings, Shield, Zap, Puzzle, BookOpen, Sparkles, Gem, ScrollText, Plus, Search, Filter } from 'lucide-react';
import AdvancedFilterBar from './AdvancedFilterBar';
import { useAdvancedFiltering, FilterableItem } from '../hooks/useAdvancedFiltering';

// Import our dashboard components
import GamificationDashboard from './GamificationDashboard';
import HabitsDashboard from './HabitsDashboard';
import AnalyticsDashboard from './AnalyticsDashboard';
import Leaderboard from './Leaderboard';
import TelemetrySettings from './TelemetrySettings';
import AdminTelemetryDashboard from './AdminTelemetryDashboard';
import PluginAdmin from '../plugins/PluginAdmin';
import PluginExtensionContainer from '../plugins/PluginExtensions';

// Define the habit interface for filtering
interface HabitItem extends FilterableItem {
  id: string;
  title: string;
  notes?: string;
  importance: 'High' | 'Medium' | 'Low';
  difficulty: number;
  skill?: string;
  categories: string[];
  status: 'active' | 'completed' | 'paused';
  createdAt: Date;
  completedAt?: Date;
  streak: number;
  completionRate: number;
}

const MainDashboard = ({ user }) => {
    const [activeTab, setActiveTab] = useState('overview');
    const [habits, setHabits] = useState<HabitItem[]>([]);
    const [filteredHabits, setFilteredHabits] = useState<HabitItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [showAddHabit, setShowAddHabit] = useState(false);

    // Load habits data
    useEffect(() => {
        const loadHabits = async () => {
            try {
                const response = await fetch('/api/v1/habits', {
                    headers: {
                        'Authorization': `Bearer ${localStorage.getItem('token')}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    const formattedHabits: HabitItem[] = data.map(habit => ({
                        id: habit.id.toString(),
                        title: habit.title,
                        notes: habit.notes,
                        importance: habit.importance || 'Medium',
                        difficulty: habit.difficulty || 1,
                        skill: habit.skill,
                        categories: habit.labels || [],
                        status: habit.status || 'active',
                        createdAt: new Date(habit.created_at),
                        completedAt: habit.completed_at ? new Date(habit.completed_at) : undefined,
                        streak: habit.streak || 0,
                        completionRate: habit.completion_rate || 0
                    }));
                    setHabits(formattedHabits);
                }
            } catch (error) {
                console.error('Failed to load habits:', error);
            } finally {
                setLoading(false);
            }
        };

        if (user) {
            loadHabits();
        }
    }, [user]);

    // Handle habit completion
    const handleHabitComplete = async (habitId: string) => {
        try {
            const response = await fetch(`/api/v1/habits/${habitId}/complete`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const result = await response.json();

                // Update local state
                setHabits(prev => prev.map(habit =>
                    habit.id === habitId
                        ? { ...habit, streak: (habit.streak || 0) + 1 }
                        : habit
                ));

                // Trigger achievement notifications
                window.dispatchEvent(new CustomEvent('habit-completed', {
                    detail: {
                        habitName: habits.find(h => h.id === habitId)?.title || 'Unknown Habit',
                        xpAwarded: result.xp_earned || 10,
                        streakCount: (habits.find(h => h.id === habitId)?.streak || 0) + 1
                    }
                }));

                // Check for achievements
                if (result.achievement_unlocked) {
                    window.dispatchEvent(new CustomEvent('achievement-unlocked', {
                        detail: result.achievement_unlocked
                    }));
                }

                // Check for level up
                if (result.level_up) {
                    window.dispatchEvent(new CustomEvent('level-up', {
                        detail: {
                            newLevel: result.new_level,
                            xpAwarded: result.xp_earned
                        }
                    }));
                }
            }
        } catch (error) {
            console.error('Failed to complete habit:', error);
        }
    };

    const OverviewTab = () => (
        <div className="space-y-6">
            {/* Advanced Filtering System - Like AHK's powerful search */}
            <AdvancedFilterBar
                items={habits}
                onFilteredItemsChange={setFilteredHabits}
                showQuickFilters={true}
            />

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Gamification Stats - Takes 2 columns */}
                <div className="lg:col-span-2">
                    <GamificationDashboard />
                </div>

                {/* Leaderboard - Takes 1 column */}
                <div>
                    <Leaderboard />
                </div>
            </div>

            {/* Filtered Habits Display */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                            <Target className="h-5 w-5 text-purple-600" />
                            <span>Your Magical Practices</span>
                        </div>
                        <Button
                            onClick={() => setShowAddHabit(true)}
                            className="flex items-center space-x-2"
                        >
                            <Plus className="h-4 w-4" />
                            <span>Add Habit</span>
                        </Button>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    {loading ? (
                        <div className="text-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-600 mx-auto"></div>
                            <p className="text-gray-600 mt-2">Loading your magical practices...</p>
                        </div>
                    ) : filteredHabits.length === 0 ? (
                        <div className="text-center py-8">
                            <BookOpen className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                            <p className="text-gray-600 mb-4">
                                {habits.length === 0
                                    ? "Begin your magical journey by creating your first habit!"
                                    : "No habits match your current filters."
                                }
                            </p>
                            <Button onClick={() => setShowAddHabit(true)}>
                                <Plus className="h-4 w-4 mr-2" />
                                Create Your First Habit
                            </Button>
                        </div>
                    ) : (
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {filteredHabits.slice(0, 6).map((habit) => (
                                <Card key={habit.id} className="hover:shadow-md transition-shadow">
                                    <CardContent className="p-4">
                                        <div className="flex items-start justify-between mb-2">
                                            <h3 className="font-semibold text-sm truncate flex-1">
                                                {habit.title}
                                            </h3>
                                            <span className={`px-2 py-1 rounded text-xs font-medium ${
                                                habit.importance === 'High' ? 'bg-red-100 text-red-800' :
                                                habit.importance === 'Medium' ? 'bg-yellow-100 text-yellow-800' :
                                                'bg-green-100 text-green-800'
                                            }`}>
                                                {habit.importance}
                                            </span>
                                        </div>

                                        {habit.notes && (
                                            <p className="text-xs text-gray-600 mb-2 line-clamp-2">
                                                {habit.notes}
                                            </p>
                                        )}

                                        <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                                            <span>Difficulty: {habit.difficulty}/10</span>
                                            <span>Streak: {habit.streak}</span>
                                        </div>

                                        <Button
                                            onClick={() => handleHabitComplete(habit.id)}
                                            className="w-full text-xs"
                                            size="sm"
                                        >
                                            <Zap className="h-3 w-3 mr-1" />
                                            Complete Today
                                        </Button>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Plugin Dashboard Widgets */}
            <PluginExtensionContainer extensionPoint="dashboard" />

            {/* Quick Actions */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <Sparkles className="h-5 w-5 text-purple-600" />
                        <span>Quick Enchantments</span>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <Button
                            variant="outline"
                            className="h-20 flex flex-col space-y-2 border-purple-200 hover:border-purple-400 hover:bg-purple-50"
                            onClick={() => setActiveTab('habits')}
                        >
                            <Target className="h-6 w-6 text-purple-600" />
                            <span className="text-xs">Habits</span>
                        </Button>

                        <Button
                            variant="outline"
                            className="h-20 flex flex-col space-y-2 border-blue-200 hover:border-blue-400 hover:bg-blue-50"
                            onClick={() => setActiveTab('analytics')}
                        >
                            <BarChart3 className="h-6 w-6 text-blue-600" />
                            <span className="text-xs">Analytics</span>
                        </Button>

                        <Button
                            variant="outline"
                            className="h-20 flex flex-col space-y-2 border-green-200 hover:border-green-400 hover:bg-green-50"
                            onClick={() => setActiveTab('gamification')}
                        >
                            <Trophy className="h-6 w-6 text-green-600" />
                            <span className="text-xs">Achievements</span>
                        </Button>

                        <Button
                            variant="outline"
                            className="h-20 flex flex-col space-y-2 border-orange-200 hover:border-orange-400 hover:bg-orange-50"
                            onClick={() => setActiveTab('plugins')}
                        >
                            <Puzzle className="h-6 w-6 text-orange-600" />
                            <span className="text-xs">Plugins</span>
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );

    return (
        <div className="space-y-6">
            <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-6">
                    <TabsTrigger value="overview" className="flex items-center space-x-2">
                        <Home className="h-4 w-4" />
                        <span className="hidden sm:inline">Overview</span>
                    </TabsTrigger>
                    <TabsTrigger value="habits" className="flex items-center space-x-2">
                        <Target className="h-4 w-4" />
                        <span className="hidden sm:inline">Habits</span>
                    </TabsTrigger>
                    <TabsTrigger value="analytics" className="flex items-center space-x-2">
                        <BarChart3 className="h-4 w-4" />
                        <span className="hidden sm:inline">Analytics</span>
                    </TabsTrigger>
                    <TabsTrigger value="gamification" className="flex items-center space-x-2">
                        <Trophy className="h-4 w-4" />
                        <span className="hidden sm:inline">Achievements</span>
                    </TabsTrigger>
                    <TabsTrigger value="plugins" className="flex items-center space-x-2">
                        <Puzzle className="h-4 w-4" />
                        <span className="hidden sm:inline">Plugins</span>
                    </TabsTrigger>
                    <TabsTrigger value="settings" className="flex items-center space-x-2">
                        <Settings className="h-4 w-4" />
                        <span className="hidden sm:inline">Settings</span>
                    </TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-6">
                    <OverviewTab />
                </TabsContent>

                <TabsContent value="habits" className="space-y-6">
                    <HabitsDashboard />
                </TabsContent>

                <TabsContent value="analytics" className="space-y-6">
                    <AnalyticsDashboard />
                </TabsContent>

                <TabsContent value="gamification" className="space-y-6">
                    <GamificationDashboard />
                </TabsContent>

                <TabsContent value="plugins" className="space-y-6">
                    <PluginAdmin />
                </TabsContent>

                <TabsContent value="settings" className="space-y-6">
                    <div className="grid gap-6 md:grid-cols-2">
                        <TelemetrySettings />
                        {user?.is_admin && <AdminTelemetryDashboard />}
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
};

export default MainDashboard;