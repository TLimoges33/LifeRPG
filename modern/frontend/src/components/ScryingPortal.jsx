import React, { useState, useEffect } from 'react';
import {
    LineChart, Line, AreaChart, Area, BarChart, Bar, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { format, subDays, startOfWeek, endOfWeek, eachDayOfInterval } from 'date-fns';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { LoadingSpinner } from './ui/loading';
import { Calendar, TrendingUp, Target, Award } from 'lucide-react';

const COLORS = ['#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#3b82f6', '#ef4444'];

const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-slate-800 border border-purple-500 rounded-lg p-3 shadow-xl">
                <p className="text-purple-300 font-medium">{label}</p>
                {payload.map((entry, index) => (
                    <p key={index} style={{ color: entry.color }} className="text-sm">
                        {`${entry.dataKey}: ${entry.value}`}
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const ProgressChart = ({ habits }) => {
    const [timeRange, setTimeRange] = useState('week');

    const generateProgressData = () => {
        const days = timeRange === 'week' ? 7 : timeRange === 'month' ? 30 : 365;
        const startDate = subDays(new Date(), days - 1);

        return eachDayOfInterval({ start: startDate, end: new Date() }).map(date => {
            const dayString = format(date, 'yyyy-MM-dd');
            const completed = Math.floor(Math.random() * habits.length);
            const total = habits.length;

            return {
                date: format(date, timeRange === 'week' ? 'EEE' : 'MM/dd'),
                completed,
                total,
                percentage: total > 0 ? Math.round((completed / total) * 100) : 0
            };
        });
    };

    const data = generateProgressData();

    return (
        <Card>
            <CardHeader>
                <div className="flex justify-between items-center">
                    <CardTitle className="flex items-center gap-2">
                        <TrendingUp className="w-5 h-5" />
                        Magical Progress
                    </CardTitle>
                    <div className="flex gap-2">
                        {['week', 'month', 'year'].map(range => (
                            <Button
                                key={range}
                                variant={timeRange === range ? 'default' : 'outline'}
                                size="sm"
                                onClick={() => setTimeRange(range)}
                            >
                                {range.charAt(0).toUpperCase() + range.slice(1)}
                            </Button>
                        ))}
                    </div>
                </div>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <AreaChart data={data}>
                        <defs>
                            <linearGradient id="progressGradient" x1="0" y1="0" x2="0" y2="1">
                                <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8} />
                                <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1} />
                            </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="date" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip content={<CustomTooltip />} />
                        <Area
                            type="monotone"
                            dataKey="percentage"
                            stroke="#8b5cf6"
                            fillOpacity={1}
                            fill="url(#progressGradient)"
                        />
                    </AreaChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
};

const HabitCompletionChart = ({ habits }) => {
    const data = habits.map(habit => ({
        name: habit.name,
        completed: habit.streak || 0,
        target: 30,
        icon: habit.icon || '⭐'
    }));

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Target className="w-5 h-5" />
                    Spell Mastery
                </CardTitle>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                        <XAxis dataKey="name" stroke="#9ca3af" />
                        <YAxis stroke="#9ca3af" />
                        <Tooltip content={<CustomTooltip />} />
                        <Bar dataKey="completed" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                        <Bar dataKey="target" fill="#374151" radius={[4, 4, 0, 0]} opacity={0.3} />
                    </BarChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
};

const CategoryDistribution = ({ habits }) => {
    const categoryData = habits.reduce((acc, habit) => {
        const category = habit.category || 'other';
        acc[category] = (acc[category] || 0) + 1;
        return acc;
    }, {});

    const data = Object.entries(categoryData).map(([category, count]) => ({
        name: category.charAt(0).toUpperCase() + category.slice(1),
        value: count,
        percentage: Math.round((count / habits.length) * 100)
    }));

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Award className="w-5 h-5" />
                    Spell Schools
                </CardTitle>
            </CardHeader>
            <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percentage }) => `${name} ${percentage}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                        >
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                </ResponsiveContainer>
            </CardContent>
        </Card>
    );
};

const StreakHeatmap = ({ habits }) => {
    const generateHeatmapData = () => {
        const weeks = [];
        const startDate = subDays(new Date(), 364);

        for (let week = 0; week < 52; week++) {
            const weekStart = startOfWeek(subDays(startDate, -week * 7));
            const weekEnd = endOfWeek(weekStart);

            const days = eachDayOfInterval({ start: weekStart, end: weekEnd }).map(date => {
                const intensity = Math.floor(Math.random() * 5);
                return {
                    date: format(date, 'yyyy-MM-dd'),
                    day: format(date, 'EEE'),
                    intensity,
                    completed: intensity * 2
                };
            });

            weeks.push({ week, days });
        }

        return weeks;
    };

    const heatmapData = generateHeatmapData();

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Calendar className="w-5 h-5" />
                    Mystical Activity
                </CardTitle>
            </CardHeader>
            <CardContent>
                <div className="grid grid-cols-12 gap-1 text-xs">
                    {heatmapData.slice(-12).map((week, weekIndex) => (
                        <div key={weekIndex} className="space-y-1">
                            {week.days.map((day, dayIndex) => (
                                <div
                                    key={dayIndex}
                                    className={`w-3 h-3 rounded-sm ${day.intensity === 0 ? 'bg-slate-700' :
                                            day.intensity === 1 ? 'bg-purple-900' :
                                                day.intensity === 2 ? 'bg-purple-700' :
                                                    day.intensity === 3 ? 'bg-purple-500' :
                                                        'bg-purple-300'
                                        }`}
                                    title={`${day.date}: ${day.completed} habits completed`}
                                />
                            ))}
                        </div>
                    ))}
                </div>
                <div className="flex justify-between items-center mt-4 text-sm text-slate-400">
                    <span>Less Magical</span>
                    <div className="flex gap-1">
                        {[0, 1, 2, 3, 4].map(level => (
                            <div
                                key={level}
                                className={`w-3 h-3 rounded-sm ${level === 0 ? 'bg-slate-700' :
                                        level === 1 ? 'bg-purple-900' :
                                            level === 2 ? 'bg-purple-700' :
                                                level === 3 ? 'bg-purple-500' :
                                                    'bg-purple-300'
                                    }`}
                            />
                        ))}
                    </div>
                    <span>More Magical</span>
                </div>
            </CardContent>
        </Card>
    );
};

const ScryingPortal = ({ habits, loading }) => {
    if (loading) {
        return (
            <div className="space-y-6">
                <div className="text-center">
                    <LoadingSpinner size="lg" />
                    <p className="text-slate-400 mt-4">Peering into the crystal ball...</p>
                </div>
            </div>
        );
    }

    if (habits.length === 0) {
        return (
            <div className="text-center py-12">
                <div className="text-6xl mb-4">🔮</div>
                <h3 className="text-xl font-semibold text-purple-300 mb-2">The Crystal Ball is Cloudy</h3>
                <p className="text-slate-400">Start practicing spells to reveal mystical insights!</p>
            </div>
        );
    }

    const stats = {
        totalHabits: habits.length,
        completedToday: habits.filter(h => h.completed_today).length,
        longestStreak: Math.max(...habits.map(h => h.streak || 0), 0),
        averageStreak: Math.round(habits.reduce((sum, h) => sum + (h.streak || 0), 0) / habits.length)
    };

    return (
        <div className="space-y-6">
            {/* Magical Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="magical-hover">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-purple-400">{stats.totalHabits}</div>
                        <div className="text-sm text-slate-400">Active Spells</div>
                        <div className="text-xs text-purple-300 mt-1">📜 In your grimoire</div>
                    </CardContent>
                </Card>
                <Card className="magical-hover">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-green-400">{stats.completedToday}</div>
                        <div className="text-sm text-slate-400">Cast Today</div>
                        <div className="text-xs text-green-300 mt-1">✨ Magical energy flowing</div>
                    </CardContent>
                </Card>
                <Card className="magical-hover">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-orange-400">{stats.longestStreak}</div>
                        <div className="text-sm text-slate-400">Longest Streak</div>
                        <div className="text-xs text-orange-300 mt-1">🔥 Most powerful enchantment</div>
                    </CardContent>
                </Card>
                <Card className="magical-hover">
                    <CardContent className="p-4">
                        <div className="text-2xl font-bold text-blue-400">{stats.averageStreak}</div>
                        <div className="text-sm text-slate-400">Average Streak</div>
                        <div className="text-xs text-blue-300 mt-1">⚡ Consistency magic</div>
                    </CardContent>
                </Card>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ProgressChart habits={habits} />
                <HabitCompletionChart habits={habits} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <CategoryDistribution habits={habits} />
                <StreakHeatmap habits={habits} />
            </div>
        </div>
    );
};

export default ScryingPortal;
