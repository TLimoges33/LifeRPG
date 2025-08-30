import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Progress } from './ui/progress';
import { Trophy, Star, Zap, Target, Award, Sparkles, Crown, BookOpen, ScrollText, Gem } from 'lucide-react';

const GamificationDashboard = () => {
    const [stats, setStats] = useState(null);
    const [achievements, setAchievements] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchGamificationData();
    }, []);

    const fetchGamificationData = async () => {
        try {
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            // Fetch user stats
            const statsResponse = await fetch('/api/v1/gamification/stats', { headers });
            const achievementsResponse = await fetch('/api/v1/gamification/achievements', { headers });

            if (statsResponse.ok && achievementsResponse.ok) {
                const statsData = await statsResponse.json();
                const achievementsData = await achievementsResponse.json();

                setStats(statsData);
                setAchievements(achievementsData);
            }
        } catch (error) {
            console.error('Failed to fetch gamification data:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="animate-pulse">
                    <div className="h-32 bg-gray-200 rounded-lg mb-4"></div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="h-24 bg-gray-200 rounded-lg"></div>
                        <div className="h-24 bg-gray-200 rounded-lg"></div>
                    </div>
                </div>
            </div>
        );
    }

    if (!stats) {
        return (
            <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
                <CardContent className="p-6 text-center">
                    <Crown className="h-12 w-12 text-purple-400 mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2 text-purple-900">Your Journey Awaits</h3>
                    <p className="text-purple-700">Practice some spells to begin gathering mystical energy!</p>
                </CardContent>
            </Card>
        );
    }

    const xpProgress = stats.current_level < 100 ?
        (stats.xp_progress / stats.xp_needed) * 100 : 100;

    return (
        <div className="space-y-6">
            {/* Level and XP Card */}
            <Card className="bg-gradient-to-r from-purple-600 via-indigo-600 to-purple-700 text-white border-2 border-gold-400 shadow-xl">
                <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-4">
                        <div>
                            <h2 className="text-2xl font-bold flex items-center space-x-2">
                                <Crown className="h-8 w-8 text-yellow-300" />
                                <span>Wizard Level {stats.current_level}</span>
                            </h2>
                            <p className="text-purple-100">
                                {stats.total_xp.toLocaleString()} Mystical Energy Gathered
                            </p>
                        </div>
                        <div className="text-right">
                            <Sparkles className="h-8 w-8 text-yellow-300 mx-auto mb-2" />
                            <Badge variant="secondary" className="bg-white/20 text-white">
                                {stats.current_level < 100 ? `${stats.xp_progress}/${stats.xp_needed} Energy` : 'Archmage Achieved!'}
                            </Badge>
                        </div>
                    </div>

                    {stats.current_level < 100 && (
                        <div className="space-y-2">
                            <div className="flex justify-between text-sm text-purple-100">
                                <span>Advancement to Level {stats.current_level + 1}</span>
                                <span>{Math.round(xpProgress)}%</span>
                            </div>
                            <Progress value={xpProgress} className="bg-white/20" />
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
                    <CardContent className="p-4 text-center">
                        <BookOpen className="h-8 w-8 text-purple-500 mx-auto mb-2" />
                        <p className="text-2xl font-bold text-purple-900">{stats.total_habits}</p>
                        <p className="text-sm text-purple-700">Spells in Grimoire</p>
                    </CardContent>
                </Card>

                <Card className="border-green-200 bg-gradient-to-br from-green-50 to-emerald-50">
                    <CardContent className="p-4 text-center">
                        <Sparkles className="h-8 w-8 text-green-500 mx-auto mb-2" />
                        <p className="text-2xl font-bold text-green-900">{stats.active_habits}</p>
                        <p className="text-sm text-green-700">Active Spells</p>
                    </CardContent>
                </Card>

                <Card className="border-yellow-200 bg-gradient-to-br from-yellow-50 to-amber-50">
                    <CardContent className="p-4 text-center">
                        <Trophy className="h-8 w-8 text-yellow-500 mx-auto mb-2" />
                        <p className="text-2xl font-bold text-yellow-900">{stats.current_streak}</p>
                        <p className="text-sm text-yellow-700">Spell Mastery Streak</p>
                    </CardContent>
                </Card>

                <Card className="border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50">
                    <CardContent className="p-4 text-center">
                        <ScrollText className="h-8 w-8 text-indigo-500 mx-auto mb-2" />
                        <p className="text-2xl font-bold text-indigo-900">{stats.total_completions}</p>
                        <p className="text-sm text-indigo-700">Spells Cast</p>
                    </CardContent>
                </Card>
            </div>

            {/* Achievements */}
            <Card className="border-purple-200 bg-gradient-to-br from-purple-50 to-indigo-50">
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2 text-purple-900">
                        <Award className="h-5 w-5 text-purple-600" />
                        <span>Mystical Enchantments</span>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {achievements.map((achievement) => (
                            <div
                                key={achievement.key}
                                className={`p-4 rounded-lg border-2 transition-all ${achievement.earned
                                    ? 'border-gold-400 bg-gradient-to-br from-yellow-50 to-amber-50 shadow-lg'
                                    : 'border-gray-300 bg-gray-100'
                                    }`}
                            >
                                <div className="flex items-center space-x-3">
                                    <div className="text-2xl">
                                        {achievement.earned ? achievement.definition.icon : '�'}
                                    </div>
                                    <div className="flex-1">
                                        <h4 className={`font-medium ${achievement.earned ? 'text-amber-800' : 'text-gray-600'
                                            }`}>
                                            {achievement.definition.name}
                                        </h4>
                                        <p className={`text-sm ${achievement.earned ? 'text-amber-700' : 'text-gray-500'
                                            }`}>
                                            {achievement.definition.description}
                                        </p>
                                        {achievement.definition.xp_reward > 0 && (
                                            <Badge variant="outline" className="mt-2 border-purple-300 text-purple-700">
                                                +{achievement.definition.xp_reward} XP
                                            </Badge>
                                        )}
                                    </div>
                                </div>
                                {achievement.earned && achievement.earned_at && (
                                    <p className="text-xs text-green-500 mt-2">
                                        Earned {new Date(achievement.earned_at).toLocaleDateString()}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default GamificationDashboard;
