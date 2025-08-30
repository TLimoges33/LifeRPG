import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { LoadingSpinner } from './ui/loading';
import { Users, UserPlus, Trophy, Flame, Star, Crown } from 'lucide-react';

const FriendCard = ({ friend, currentUser }) => {
    const [isLoading, setIsLoading] = useState(false);

    return (
        <Card className="relative overflow-hidden">
            <div className="absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl from-purple-500/20 to-transparent"></div>
            <CardContent className="p-4">
                <div className="flex items-center space-x-4">
                    <div className="relative">
                        <div className="w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-lg">
                            {friend.name?.charAt(0)?.toUpperCase() || '?'}
                        </div>
                        {friend.isOnline && (
                            <div className="absolute bottom-0 right-0 w-3 h-3 bg-green-400 rounded-full border-2 border-slate-800"></div>
                        )}
                    </div>

                    <div className="flex-1">
                        <h4 className="font-medium text-purple-200">{friend.name}</h4>
                        <div className="flex items-center space-x-4 text-sm text-slate-400">
                            <span className="flex items-center">
                                <Trophy className="w-3 h-3 mr-1" />
                                Level {friend.level || 1}
                            </span>
                            <span className="flex items-center">
                                <Flame className="w-3 h-3 mr-1" />
                                {friend.currentStreak || 0} day streak
                            </span>
                        </div>
                        <div className="text-xs text-purple-300 mt-1">
                            {friend.completedToday || 0} spells cast today
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="text-lg font-bold text-yellow-400">
                            {friend.totalXP || 0}
                        </div>
                        <div className="text-xs text-slate-400">XP</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

const LeaderboardItem = ({ user, rank, isCurrentUser }) => {
    const getRankIcon = (rank) => {
        switch (rank) {
            case 1: return <Crown className="w-5 h-5 text-yellow-400" />;
            case 2: return <Trophy className="w-5 h-5 text-gray-400" />;
            case 3: return <Trophy className="w-5 h-5 text-amber-600" />;
            default: return <span className="text-slate-400 font-bold">{rank}</span>;
        }
    };

    return (
        <Card className={`${isCurrentUser ? 'border-purple-400 bg-purple-500/10' : ''}`}>
            <CardContent className="p-4">
                <div className="flex items-center space-x-4">
                    <div className="flex items-center justify-center w-8">
                        {getRankIcon(rank)}
                    </div>

                    <div className="w-10 h-10 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold">
                        {user.name?.charAt(0)?.toUpperCase() || '?'}
                    </div>

                    <div className="flex-1">
                        <h4 className={`font-medium ${isCurrentUser ? 'text-purple-200' : 'text-slate-200'}`}>
                            {user.name} {isCurrentUser && '(You)'}
                        </h4>
                        <div className="flex items-center space-x-3 text-sm text-slate-400">
                            <span>Level {user.level || 1}</span>
                            <span>🔥 {user.currentStreak || 0}</span>
                            <span>✨ {user.completedThisWeek || 0} this week</span>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="text-lg font-bold text-yellow-400">
                            {user.totalXP || 0}
                        </div>
                        <div className="text-xs text-slate-400">XP</div>
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

const AddFriendModal = ({ isOpen, onClose, onAddFriend }) => {
    const [searchQuery, setSearchQuery] = useState('');
    const [searchResults, setSearchResults] = useState([]);
    const [isSearching, setIsSearching] = useState(false);

    const handleSearch = async () => {
        if (!searchQuery.trim()) return;

        setIsSearching(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch(`/api/v1/social/search?q=${encodeURIComponent(searchQuery)}`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const results = await response.json();
                setSearchResults(results);
            }
        } catch (error) {
            console.error('Search failed:', error);
        } finally {
            setIsSearching(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
            <Card className="w-full max-w-md">
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <UserPlus className="w-5 h-5" />
                        Add Wizard Friend
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex space-x-2">
                        <Input
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Search by username or email..."
                            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                        />
                        <Button onClick={handleSearch} disabled={isSearching}>
                            {isSearching ? <LoadingSpinner size="sm" /> : 'Search'}
                        </Button>
                    </div>

                    <div className="space-y-2 max-h-64 overflow-y-auto">
                        {searchResults.map(user => (
                            <div key={user.id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                                <div className="flex items-center space-x-3">
                                    <div className="w-8 h-8 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center text-white font-bold text-sm">
                                        {user.name?.charAt(0)?.toUpperCase() || '?'}
                                    </div>
                                    <div>
                                        <div className="font-medium text-purple-200">{user.name}</div>
                                        <div className="text-sm text-slate-400">Level {user.level || 1}</div>
                                    </div>
                                </div>
                                <Button
                                    onClick={() => onAddFriend(user.id)}
                                    variant="magical"
                                    size="sm"
                                >
                                    Add
                                </Button>
                            </div>
                        ))}
                    </div>

                    <div className="flex justify-end space-x-2">
                        <Button variant="ghost" onClick={onClose}>Cancel</Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

const SocialFeatures = () => {
    const [friends, setFriends] = useState([]);
    const [leaderboard, setLeaderboard] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('friends');
    const [showAddFriend, setShowAddFriend] = useState(false);

    useEffect(() => {
        fetchSocialData();
    }, []);

    const fetchSocialData = async () => {
        try {
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            const [friendsResponse, leaderboardResponse] = await Promise.all([
                fetch('/api/v1/social/friends', { headers }),
                fetch('/api/v1/social/leaderboard', { headers })
            ]);

            if (friendsResponse.ok) {
                const friendsData = await friendsResponse.json();
                setFriends(friendsData);
            }

            if (leaderboardResponse.ok) {
                const leaderboardData = await leaderboardResponse.json();
                setLeaderboard(leaderboardData);
            }
        } catch (error) {
            console.error('Failed to fetch social data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleAddFriend = async (userId) => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/v1/social/friends', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ userId })
            });

            if (response.ok) {
                setShowAddFriend(false);
                fetchSocialData(); // Refresh data
            }
        } catch (error) {
            console.error('Failed to add friend:', error);
        }
    };

    if (loading) {
        return (
            <div className="text-center py-12">
                <LoadingSpinner size="lg" />
                <p className="text-slate-400 mt-4">Loading magical community...</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Tab Navigation */}
            <div className="flex space-x-4">
                <Button
                    variant={activeTab === 'friends' ? 'default' : 'ghost'}
                    onClick={() => setActiveTab('friends')}
                    className="flex items-center gap-2"
                >
                    <Users className="w-4 h-4" />
                    Friends ({friends.length})
                </Button>
                <Button
                    variant={activeTab === 'leaderboard' ? 'default' : 'ghost'}
                    onClick={() => setActiveTab('leaderboard')}
                    className="flex items-center gap-2"
                >
                    <Trophy className="w-4 h-4" />
                    Leaderboard
                </Button>
            </div>

            {/* Friends Tab */}
            {activeTab === 'friends' && (
                <div className="space-y-4">
                    <div className="flex justify-between items-center">
                        <h3 className="text-xl font-bold text-purple-300">Wizard Friends</h3>
                        <Button
                            onClick={() => setShowAddFriend(true)}
                            variant="magical"
                            className="flex items-center gap-2"
                        >
                            <UserPlus className="w-4 h-4" />
                            Add Friend
                        </Button>
                    </div>

                    {friends.length === 0 ? (
                        <Card>
                            <CardContent className="p-8 text-center">
                                <Users className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                                <h4 className="text-lg font-medium text-purple-300 mb-2">No Friends Yet</h4>
                                <p className="text-slate-400 mb-4">Connect with other wizards to share your magical journey!</p>
                                <Button onClick={() => setShowAddFriend(true)} variant="magical">
                                    Find Wizard Friends
                                </Button>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="grid gap-4">
                            {friends.map(friend => (
                                <FriendCard key={friend.id} friend={friend} />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Leaderboard Tab */}
            {activeTab === 'leaderboard' && (
                <div className="space-y-4">
                    <h3 className="text-xl font-bold text-purple-300">🏆 Hall of Fame</h3>

                    {leaderboard.length === 0 ? (
                        <Card>
                            <CardContent className="p-8 text-center">
                                <Trophy className="w-12 h-12 text-slate-400 mx-auto mb-4" />
                                <h4 className="text-lg font-medium text-purple-300 mb-2">Leaderboard Empty</h4>
                                <p className="text-slate-400">Keep practicing spells to climb the rankings!</p>
                            </CardContent>
                        </Card>
                    ) : (
                        <div className="space-y-3">
                            {leaderboard.map((user, index) => (
                                <LeaderboardItem
                                    key={user.id}
                                    user={user}
                                    rank={index + 1}
                                    isCurrentUser={user.isCurrentUser}
                                />
                            ))}
                        </div>
                    )}
                </div>
            )}

            {/* Add Friend Modal */}
            <AddFriendModal
                isOpen={showAddFriend}
                onClose={() => setShowAddFriend(false)}
                onAddFriend={handleAddFriend}
            />
        </div>
    );
};

export default SocialFeatures;
