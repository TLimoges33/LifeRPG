import React, { useState, useEffect } from 'react';
import useAppStore from '../store/appStore';
import ScryingPortal from './ScryingPortal';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { LoadingSpinner, LoadingCard } from './ui/loading';
import { Plus, Check, X, Edit } from 'lucide-react';

const HabitItem = ({ habit, onComplete, onEdit, onDelete }) => {
    const [isCompleting, setIsCompleting] = useState(false);

    const handleComplete = async () => {
        setIsCompleting(true);
        await onComplete(habit.id);
        setIsCompleting(false);
    };

    return (
        <div className="flex items-center justify-between p-4 bg-slate-700/30 rounded-lg border border-purple-500/20 hover:border-purple-400/40 transition-colors">
            <div className="flex items-center space-x-4">
                <div className="text-2xl">{habit.icon || '⭐'}</div>
                <div>
                    <h4 className="font-medium text-purple-200">{habit.name}</h4>
                    <p className="text-sm text-slate-400">{habit.description}</p>
                    {habit.streak > 0 && (
                        <p className="text-sm text-orange-400">🔥 {habit.streak} day streak</p>
                    )}
                </div>
            </div>
            <div className="flex items-center space-x-2">
                <Button
                    onClick={handleComplete}
                    disabled={isCompleting || habit.completed_today}
                    variant={habit.completed_today ? "secondary" : "magical"}
                    size="sm"
                >
                    {isCompleting ? (
                        <LoadingSpinner size="sm" />
                    ) : habit.completed_today ? (
                        <><Check className="w-4 h-4 mr-1" /> Done</>
                    ) : (
                        <>✨ Complete</>
                    )}
                </Button>
                <Button
                    onClick={() => onEdit(habit)}
                    variant="ghost"
                    size="sm"
                >
                    <Edit className="w-4 h-4" />
                </Button>
                <Button
                    onClick={() => onDelete(habit.id)}
                    variant="destructive"
                    size="sm"
                >
                    <X className="w-4 h-4" />
                </Button>
            </div>
        </div>
    );
};

const CreateHabitForm = ({ onSubmit, onCancel }) => {
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        icon: '',
        category: 'health'
    });

    const handleSubmit = (e) => {
        e.preventDefault();
        onSubmit(formData);
        setFormData({ name: '', description: '', icon: '', category: 'health' });
    };

    return (
        <Card>
            <CardHeader>
                <CardTitle>✨ Create New Spell</CardTitle>
            </CardHeader>
            <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-purple-300 mb-2">
                            Spell Name
                        </label>
                        <Input
                            value={formData.name}
                            onChange={(e) => setFormData(prev => ({ ...prev, name: e.target.value }))}
                            placeholder="Morning Meditation"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-purple-300 mb-2">
                            Description
                        </label>
                        <Input
                            value={formData.description}
                            onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                            placeholder="10 minutes of mindful meditation"
                        />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-purple-300 mb-2">
                                Icon
                            </label>
                            <Input
                                value={formData.icon}
                                onChange={(e) => setFormData(prev => ({ ...prev, icon: e.target.value }))}
                                placeholder="🧘‍♂️"
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-300 mb-2">
                                Category
                            </label>
                            <select
                                value={formData.category}
                                onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
                                className="flex h-10 w-full rounded-md border border-purple-500/50 bg-slate-700/50 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-purple-500"
                            >
                                <option value="health">🏃‍♂️ Health</option>
                                <option value="mind">🧠 Mind</option>
                                <option value="productivity">💼 Productivity</option>
                                <option value="creative">🎨 Creative</option>
                                <option value="social">👥 Social</option>
                                <option value="other">⭐ Other</option>
                            </select>
                        </div>
                    </div>
                    <div className="flex space-x-2">
                        <Button type="submit" variant="magical">
                            🪄 Create Spell
                        </Button>
                        <Button type="button" variant="ghost" onClick={onCancel}>
                            Cancel
                        </Button>
                    </div>
                </form>
            </CardContent>
        </Card>
    );
};

const MainDashboard = ({ user, onLogout }) => {
    const {
        activeTab, setActiveTab,
        habits, habitsLoading,
        fetchHabits, createHabit, markHabitComplete
    } = useAppStore();

    const [showCreateForm, setShowCreateForm] = useState(false);

    useEffect(() => {
        fetchHabits();
    }, [fetchHabits]);

    const handleCreateHabit = async (habitData) => {
        const result = await createHabit(habitData);
        if (result.success) {
            setShowCreateForm(false);
        }
    };

    const handleCompleteHabit = async (habitId) => {
        await markHabitComplete(habitId);
    };

    const handleEditHabit = (habit) => {
        // TODO: Implement edit functionality
        console.log('Edit habit:', habit);
    };

    const handleDeleteHabit = (habitId) => {
        // TODO: Implement delete functionality
        console.log('Delete habit:', habitId);
    };

    // Calculate stats
    const completedToday = habits.filter(h => h.completed_today).length;
    const totalHabits = habits.length;
    const longestStreak = Math.max(...habits.map(h => h.streak || 0), 0);

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            {/* Header */}
            <header className="bg-slate-800/50 backdrop-blur-sm border-b border-purple-500">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex justify-between items-center py-4">
                        <div className="flex items-center space-x-4">
                            <div className="text-3xl">🧙‍♂️</div>
                            <div>
                                <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400">
                                    The Wizard's Grimoire
                                </h1>
                                <p className="text-purple-300">
                                    Welcome, {user?.name || user?.email || 'Wizard'}
                                </p>
                            </div>
                        </div>
                        <Button onClick={onLogout} variant="destructive">
                            🚪 Leave Sanctum
                        </Button>
                    </div>
                </div>
            </header>

            {/* Navigation */}
            <nav className="bg-slate-800/30 backdrop-blur-sm border-b border-purple-500/50">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    <div className="flex space-x-8 py-4">
                        {[
                            { id: 'overview', label: '🏠 Overview', icon: '🏠' },
                            { id: 'spells', label: '📜 Spell Practice', icon: '📜' },
                            { id: 'scrying', label: '🔮 Scrying Portal', icon: '🔮' },
                            { id: 'hall', label: '🏆 Hall of Fame', icon: '🏆' },
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id)}
                                className={`px-4 py-2 rounded-lg transition-colors ${activeTab === tab.id
                                        ? 'bg-purple-600 text-white'
                                        : 'text-purple-300 hover:text-white hover:bg-purple-600/50'
                                    }`}
                            >
                                {tab.label}
                            </button>
                        ))}
                    </div>
                </div>
            </nav>

            {/* Main Content */}
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
                {activeTab === 'overview' && (
                    <div className="space-y-6">
                        <div className="text-center">
                            <h2 className="text-3xl font-bold text-purple-300 mb-4">
                                ✨ Magical Dashboard ✨
                            </h2>
                            <p className="text-gray-300">
                                Your enchanted realm of habit tracking and personal growth
                            </p>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            <Card>
                                <CardHeader>
                                    <CardTitle>📜 Today's Progress</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-purple-400 mb-2">
                                        {completedToday}/{totalHabits}
                                    </div>
                                    <div className="text-gray-300">Spells Completed</div>
                                    <div className="w-full bg-slate-700 rounded-full h-2 mt-3">
                                        <div
                                            className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full"
                                            style={{ width: `${totalHabits > 0 ? (completedToday / totalHabits) * 100 : 0}%` }}
                                        />
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>🔥 Longest Streak</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-orange-400 mb-2">{longestStreak}</div>
                                    <div className="text-gray-300">Days</div>
                                    <div className="text-sm text-green-400 mt-2">Keep the magic alive!</div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>⭐ Total Habits</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-yellow-400 mb-2">{totalHabits}</div>
                                    <div className="text-gray-300">Active Spells</div>
                                    <Button
                                        onClick={() => setShowCreateForm(true)}
                                        variant="outline"
                                        size="sm"
                                        className="mt-2 w-full"
                                    >
                                        <Plus className="w-4 h-4 mr-1" /> Add New
                                    </Button>
                                </CardContent>
                            </Card>
                        </div>

                        {/* Today's Habits Preview */}
                        <Card>
                            <CardHeader>
                                <CardTitle>📜 Today's Spell Practice</CardTitle>
                            </CardHeader>
                            <CardContent>
                                {habitsLoading ? (
                                    <div className="space-y-4">
                                        {[1, 2, 3].map(i => <LoadingCard key={i} />)}
                                    </div>
                                ) : habits.length === 0 ? (
                                    <div className="text-center py-8">
                                        <div className="text-6xl mb-4">📜</div>
                                        <p className="text-slate-400 mb-4">No spells in your grimoire yet!</p>
                                        <Button onClick={() => setShowCreateForm(true)} variant="magical">
                                            <Plus className="w-4 h-4 mr-2" /> Create Your First Spell
                                        </Button>
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {habits.slice(0, 5).map((habit) => (
                                            <HabitItem
                                                key={habit.id}
                                                habit={habit}
                                                onComplete={handleCompleteHabit}
                                                onEdit={handleEditHabit}
                                                onDelete={handleDeleteHabit}
                                            />
                                        ))}
                                        {habits.length > 5 && (
                                            <Button
                                                onClick={() => setActiveTab('spells')}
                                                variant="outline"
                                                className="w-full"
                                            >
                                                View All {habits.length} Spells
                                            </Button>
                                        )}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                )}

                {activeTab === 'spells' && (
                    <div className="space-y-6">
                        <div className="flex justify-between items-center">
                            <div>
                                <h2 className="text-3xl font-bold text-purple-300">📜 Spell Practice</h2>
                                <p className="text-gray-300">Master your daily habits and unlock new magical abilities</p>
                            </div>
                            <Button onClick={() => setShowCreateForm(true)} variant="magical">
                                <Plus className="w-4 h-4 mr-2" /> New Spell
                            </Button>
                        </div>

                        {showCreateForm && (
                            <CreateHabitForm
                                onSubmit={handleCreateHabit}
                                onCancel={() => setShowCreateForm(false)}
                            />
                        )}

                        {habitsLoading ? (
                            <div className="grid gap-4">
                                {[1, 2, 3, 4].map(i => <LoadingCard key={i} />)}
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {habits.map((habit) => (
                                    <HabitItem
                                        key={habit.id}
                                        habit={habit}
                                        onComplete={handleCompleteHabit}
                                        onEdit={handleEditHabit}
                                        onDelete={handleDeleteHabit}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                )}

                {activeTab === 'scrying' && (
                    <div className="space-y-6">
                        <div className="text-center">
                            <h2 className="text-3xl font-bold text-purple-300 mb-4">
                                🔮 Scrying Portal
                            </h2>
                            <p className="text-gray-300 mb-8">
                                Peer into the mystical patterns of your progress
                            </p>
                        </div>
                        <ScryingPortal habits={habits} loading={habitsLoading} />
                    </div>
                )}

                {activeTab === 'hall' && (
                    <div className="text-center">
                        <h2 className="text-3xl font-bold text-purple-300 mb-4">
                            🏆 Hall of Fame
                        </h2>
                        <p className="text-gray-300 mb-8">
                            Celebrate your greatest magical achievements
                        </p>
                        <Card className="max-w-2xl mx-auto">
                            <CardContent>
                                <div className="text-6xl mb-4">🏆</div>
                                <p className="text-gray-300">
                                    The trophy room is being prepared...
                                    <br />
                                    Achievements system coming soon!
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                )}
            </main>
        </div>
    );
};

export default MainDashboard;
