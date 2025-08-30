import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Trophy, Medal, Award, Crown, Zap, RefreshCw } from 'lucide-react';

const Leaderboard = () => {
    const [leaderboard, setLeaderboard] = useState([]);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);

    useEffect(() => {
        fetchLeaderboard();
    }, []);

    const fetchLeaderboard = async () => {
        setLoading(true);
        try {
            const response = await fetch('/api/v1/gamification/leaderboard', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setLeaderboard(data);
            }
        } catch (error) {
            console.error('Failed to fetch leaderboard:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleRefresh = () => {
        setRefreshing(true);
        fetchLeaderboard();
    };

    const getRankIcon = (rank) => {
        switch (rank) {
            case 1:
                return <Crown className="h-6 w-6 text-yellow-500" />;
            case 2:
                return <Medal className="h-6 w-6 text-gray-400" />;
            case 3:
                return <Award className="h-6 w-6 text-amber-600" />;
            default:
                return <Trophy className="h-5 w-5 text-gray-400" />;
        }
    };

    const getRankColor = (rank) => {
        switch (rank) {
            case 1:
                return 'bg-gradient-to-r from-yellow-400 to-yellow-600 text-white';
            case 2:
                return 'bg-gradient-to-r from-gray-300 to-gray-500 text-white';
            case 3:
                return 'bg-gradient-to-r from-amber-400 to-amber-600 text-white';
            default:
                return 'bg-white border';
        }
    };

    if (loading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center space-x-2">
                        <Trophy className="h-5 w-5" />
                        <span>Leaderboard</span>
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="space-y-3">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className="animate-pulse">
                                <div className="h-16 bg-gray-200 rounded-lg"></div>
                            </div>
                        ))}
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <div className="flex items-center justify-between">
                    <CardTitle className="flex items-center space-x-2">
                        <Trophy className="h-5 w-5" />
                        <span>Leaderboard</span>
                    </CardTitle>
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRefresh}
                        disabled={refreshing}
                    >
                        <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>
            </CardHeader>
            <CardContent>
                {leaderboard.length === 0 ? (
                    <div className="text-center py-8 text-gray-500">
                        <Trophy className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p>No players on the leaderboard yet</p>
                        <p className="text-sm">Complete some habits to get started!</p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {leaderboard.map((player, index) => (
                            <div
                                key={index}
                                className={`p-4 rounded-lg transition-all hover:scale-105 ${getRankColor(player.rank)}`}
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center space-x-4">
                                        <div className="flex items-center justify-center w-10 h-10">
                                            {player.rank <= 3 ? (
                                                getRankIcon(player.rank)
                                            ) : (
                                                <div className="flex items-center justify-center w-8 h-8 bg-gray-100 rounded-full text-gray-600 font-bold">
                                                    {player.rank}
                                                </div>
                                            )}
                                        </div>

                                        <div>
                                            <h4 className={`font-medium ${player.rank <= 3 ? 'text-white' : 'text-gray-900'}`}>
                                                {player.display_name}
                                            </h4>
                                            <p className={`text-sm ${player.rank <= 3 ? 'text-white/80' : 'text-gray-600'}`}>
                                                Level {player.level}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="text-right">
                                        <div className={`flex items-center space-x-1 ${player.rank <= 3 ? 'text-white' : 'text-gray-700'}`}>
                                            <Zap className="h-4 w-4" />
                                            <span className="font-bold">
                                                {player.total_xp.toLocaleString()}
                                            </span>
                                        </div>
                                        <p className={`text-xs ${player.rank <= 3 ? 'text-white/80' : 'text-gray-500'}`}>
                                            Total XP
                                        </p>
                                    </div>
                                </div>

                                {player.rank <= 3 && (
                                    <div className="mt-3 pt-3 border-t border-white/20">
                                        <div className="flex items-center justify-center space-x-2">
                                            {player.rank === 1 && (
                                                <Badge variant="outline" className="border-white text-white bg-white/20">
                                                    🏆 Champion
                                                </Badge>
                                            )}
                                            {player.rank === 2 && (
                                                <Badge variant="outline" className="border-white text-white bg-white/20">
                                                    🥈 Runner-up
                                                </Badge>
                                            )}
                                            {player.rank === 3 && (
                                                <Badge variant="outline" className="border-white text-white bg-white/20">
                                                    🥉 Third Place
                                                </Badge>
                                            )}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}

                {leaderboard.length > 0 && (
                    <div className="mt-6 pt-4 border-t text-center">
                        <p className="text-sm text-gray-500">
                            Rankings update in real-time based on total XP earned
                        </p>
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

export default Leaderboard;
