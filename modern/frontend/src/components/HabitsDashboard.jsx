import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { Input } from './ui/input';
import { Textarea } from './ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './ui/dialog';
import { Plus, Target, CheckCircle, Circle, Star, Zap, Trash2, Edit, Calendar, BookOpen, Sparkles, Wand2 } from 'lucide-react';
import { useTelemetry } from '../hooks/useTelemetry.jsx';

const HabitsDashboard = () => {
    const [habits, setHabits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [editingHabit, setEditingHabit] = useState(null);
    const [formData, setFormData] = useState({
        title: '',
        notes: '',
        cadence: 'daily',
        difficulty: 1,
        xp_reward: 10
    });
    const { trackFeatureUsage, trackInteraction } = useTelemetry();

    useEffect(() => {
        fetchHabits();
        trackFeatureUsage('habits_dashboard');
    }, [trackFeatureUsage]);

    const fetchHabits = async () => {
        try {
            const response = await fetch('/api/v1/habits', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setHabits(data);
            }
        } catch (error) {
            console.error('Failed to fetch habits:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateHabit = async () => {
        try {
            const response = await fetch('/api/v1/habits', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify(formData)
            });

            if (response.ok) {
                const result = await response.json();
                await fetchHabits();
                setShowCreateDialog(false);
                setFormData({
                    title: '',
                    notes: '',
                    cadence: 'daily',
                    difficulty: 1,
                    xp_reward: 10
                });

                trackInteraction('habit_created', 'habits', formData.title);

                // Show achievement notification if any
                if (result.achievements && result.achievements.length > 0) {
                    // You could add a toast notification here
                    console.log('New achievements unlocked!', result.achievements);
                }
            }
        } catch (error) {
            console.error('Failed to create habit:', error);
        }
    };

    const handleCompleteHabit = async (habitId) => {
        try {
            const response = await fetch(`/api/v1/habits/${habitId}/complete`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const result = await response.json();
                await fetchHabits();

                trackInteraction('habit_completed', 'habits', habitId.toString());

                // Show XP gain and achievement notifications
                if (result.xp_awarded) {
                    console.log(`+${result.xp_awarded} XP earned!`);
                }

                if (result.level_up) {
                    console.log(`Level up! You're now level ${result.new_level}!`);
                }

                if (result.new_achievements && result.new_achievements.length > 0) {
                    console.log('New achievements unlocked!', result.new_achievements);
                }
            }
        } catch (error) {
            console.error('Failed to complete habit:', error);
        }
    };

    const handleDeleteHabit = async (habitId) => {
        if (!confirm('Are you sure you want to delete this habit?')) return;

        try {
            const response = await fetch(`/api/v1/habits/${habitId}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                await fetchHabits();
                trackInteraction('habit_deleted', 'habits', habitId.toString());
            }
        } catch (error) {
            console.error('Failed to delete habit:', error);
        }
    };

    const getDifficultyColor = (difficulty) => {
        switch (difficulty) {
            case 1: return 'bg-green-100 text-green-800';
            case 2: return 'bg-yellow-100 text-yellow-800';
            case 3: return 'bg-orange-100 text-orange-800';
            case 4: return 'bg-red-100 text-red-800';
            case 5: return 'bg-purple-100 text-purple-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    const getDifficultyLabel = (difficulty) => {
        const labels = {
            1: 'Cantrip',
            2: 'Minor Spell',
            3: 'Ritual',
            4: 'Major Spell',
            5: 'Ancient Magic'
        };
        return labels[difficulty] || 'Unknown';
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="animate-pulse">
                    <div className="h-8 bg-gray-200 rounded w-64 mb-4"></div>
                    <div className="grid gap-4">
                        {[1, 2, 3].map(i => (
                            <div key={i} className="h-24 bg-gray-200 rounded"></div>
                        ))}
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold text-purple-900 flex items-center space-x-2">
                        <BookOpen className="h-7 w-7 text-purple-600" />
                        <span>My Spellbook</span>
                    </h1>
                    <p className="text-purple-700">Practice your daily spells and gather mystical energy</p>
                </div>

                <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
                    <DialogTrigger asChild>
                        <Button className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700">
                            <Plus className="h-4 w-4 mr-2" />
                            Inscribe New Spell
                        </Button>
                    </DialogTrigger>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle className="text-purple-900 flex items-center space-x-2">
                                <Sparkles className="h-5 w-5 text-purple-600" />
                                <span>Inscribe New Spell</span>
                            </DialogTitle>
                        </DialogHeader>
                        <div className="space-y-4">
                            <div>
                                <label className="text-sm font-medium text-purple-800">Spell Name</label>
                                <Input
                                    value={formData.title}
                                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                                    placeholder="e.g., Morning Meditation Ritual"
                                    className="border-purple-300 focus:border-purple-500"
                                />
                            </div>

                            <div>
                                <label className="text-sm font-medium text-purple-800">Incantation Notes</label>
                                <Textarea
                                    value={formData.notes}
                                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                    placeholder="Optional notes about this magical practice"
                                    className="border-purple-300 focus:border-purple-500"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm font-medium text-purple-800">Casting Frequency</label>
                                    <Select value={formData.cadence} onValueChange={(value) => setFormData({ ...formData, cadence: value })}>
                                        <SelectTrigger className="border-purple-300 focus:border-purple-500">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="daily">Daily Practice</SelectItem>
                                            <SelectItem value="weekly">Weekly Ritual</SelectItem>
                                            <SelectItem value="monthly">Monthly Ceremony</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>

                                <div>
                                    <label className="text-sm font-medium text-purple-800">Spell Complexity</label>
                                    <Select value={formData.difficulty.toString()} onValueChange={(value) => setFormData({ ...formData, difficulty: parseInt(value) })}>
                                        <SelectTrigger className="border-purple-300 focus:border-purple-500">
                                            <SelectValue />
                                        </SelectTrigger>
                                        <SelectContent>
                                            <SelectItem value="1">1 - Cantrip</SelectItem>
                                            <SelectItem value="2">2 - Minor Spell</SelectItem>
                                            <SelectItem value="3">3 - Ritual</SelectItem>
                                            <SelectItem value="4">4 - Major Spell</SelectItem>
                                            <SelectItem value="5">5 - Ancient Magic</SelectItem>
                                        </SelectContent>
                                    </Select>
                                </div>
                            </div>

                            <div>
                                <label className="text-sm font-medium">XP Reward</label>
                                <Input
                                    type="number"
                                    value={formData.xp_reward}
                                    onChange={(e) => setFormData({ ...formData, xp_reward: parseInt(e.target.value) || 10 })}
                                    min="1"
                                    max="100"
                                />
                            </div>

                            <div className="flex justify-end space-x-2">
                                <Button variant="outline" onClick={() => setShowCreateDialog(false)} className="border-gray-300">
                                    Cancel
                                </Button>
                                <Button
                                    onClick={handleCreateHabit}
                                    disabled={!formData.title.trim()}
                                    className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
                                >
                                    <Sparkles className="h-4 w-4 mr-2" />
                                    Inscribe Spell
                                </Button>
                            </div>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>

            {habits.length === 0 ? (
                <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
                    <CardContent className="p-12 text-center">
                        <BookOpen className="h-16 w-16 text-purple-300 mx-auto mb-4" />
                        <h3 className="text-lg font-medium mb-2 text-purple-900">Your Spellbook Awaits</h3>
                        <p className="text-purple-700 mb-4">Inscribe your first spell to begin gathering mystical energy!</p>
                        <Button
                            onClick={() => setShowCreateDialog(true)}
                            className="bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700"
                        >
                            <Sparkles className="h-4 w-4 mr-2" />
                            Inscribe Your First Spell
                        </Button>
                    </CardContent>
                </Card>
            ) : (
                <div className="grid gap-4">
                    {habits.map((habit) => (
                        <Card key={habit.id} className="transition-all hover:shadow-md border-purple-200 bg-gradient-to-r from-purple-50 to-indigo-50">
                            <CardContent className="p-6">
                                <div className="flex items-center justify-between">
                                    <div className="flex-1">
                                        <div className="flex items-center space-x-3 mb-2">
                                            <BookOpen className="h-5 w-5 text-purple-600" />
                                            <h3 className="font-medium text-lg text-purple-900">{habit.title}</h3>
                                            <Badge className={getDifficultyColor(habit.difficulty)}>
                                                {getDifficultyLabel(habit.difficulty)}
                                            </Badge>
                                            <Badge variant="outline" className="flex items-center space-x-1 border-purple-300 text-purple-700">
                                                <Sparkles className="h-3 w-3" />
                                                <span>{habit.xp_reward} Energy</span>
                                            </Badge>
                                            <Badge variant="outline" className="flex items-center space-x-1 border-indigo-300 text-indigo-700">
                                                <Calendar className="h-3 w-3" />
                                                <span>{habit.cadence}</span>
                                            </Badge>
                                        </div>

                                        {habit.notes && (
                                            <p className="text-purple-700 text-sm mb-3">{habit.notes}</p>
                                        )}

                                        <div className="flex items-center space-x-4 text-sm text-purple-600">
                                            <span>Inscribed {new Date(habit.created_at).toLocaleDateString()}</span>
                                            <span>Status: {habit.status}</span>
                                        </div>
                                    </div>

                                    <div className="flex items-center space-x-2">
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleCompleteHabit(habit.id)}
                                            className="flex items-center space-x-2 border-green-300 hover:bg-green-50 text-green-700"
                                        >
                                            <Wand2 className="h-4 w-4" />
                                            <span>Cast Spell</span>
                                        </Button>

                                        <Button
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleDeleteHabit(habit.id)}
                                            className="text-red-600 hover:text-red-700 border-red-300 hover:bg-red-50"
                                        >
                                            <Trash2 className="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    ))}
                </div>
            )}
        </div>
    );
};

export default HabitsDashboard;
