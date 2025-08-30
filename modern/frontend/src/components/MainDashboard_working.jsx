import React, { useState } from 'react';

// Simple inline components to avoid import issues
const Card = ({ children, className = "", ...props }) => (
    <div className={`bg-slate-800 border border-purple-500 rounded-lg shadow-lg ${className}`} {...props}>
        {children}
    </div>
);

const CardHeader = ({ children, className = "", ...props }) => (
    <div className={`p-6 pb-0 ${className}`} {...props}>
        {children}
    </div>
);

const CardTitle = ({ children, className = "", ...props }) => (
    <h3 className={`text-xl font-semibold text-purple-300 ${className}`} {...props}>
        {children}
    </h3>
);

const CardContent = ({ children, className = "", ...props }) => (
    <div className={`p-6 pt-0 ${className}`} {...props}>
        {children}
    </div>
);

const Button = ({ children, className = "", onClick, ...props }) => (
    <button
        className={`px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors ${className}`}
        onClick={onClick}
        {...props}
    >
        {children}
    </button>
);

const MainDashboard = ({ user, onLogout }) => {
    const [activeTab, setActiveTab] = useState('overview');

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
                                    Welcome, {user?.email || 'Wizard'}
                                </p>
                            </div>
                        </div>
                        <Button onClick={onLogout} className="bg-red-600 hover:bg-red-700">
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
                                    <CardTitle>🧙‍♂️ Wizard Level</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-purple-400 mb-2">Level 5</div>
                                    <div className="text-gray-300">Apprentice Mage</div>
                                    <div className="w-full bg-slate-700 rounded-full h-2 mt-3">
                                        <div className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full" style={{ width: '65%' }}></div>
                                    </div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>⚡ Mystical Energy</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-yellow-400 mb-2">850</div>
                                    <div className="text-gray-300">Experience Points</div>
                                    <div className="text-sm text-purple-300 mt-2">+50 today</div>
                                </CardContent>
                            </Card>

                            <Card>
                                <CardHeader>
                                    <CardTitle>🔥 Spell Streak</CardTitle>
                                </CardHeader>
                                <CardContent>
                                    <div className="text-3xl font-bold text-orange-400 mb-2">12</div>
                                    <div className="text-gray-300">Days</div>
                                    <div className="text-sm text-green-400 mt-2">Keep it up!</div>
                                </CardContent>
                            </Card>
                        </div>

                        <Card>
                            <CardHeader>
                                <CardTitle>📜 Today's Spell Practice</CardTitle>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-4">
                                    {[
                                        { name: 'Morning Meditation', completed: true, icon: '🧘‍♂️' },
                                        { name: 'Physical Training', completed: true, icon: '💪' },
                                        { name: 'Study Ancient Texts', completed: false, icon: '📚' },
                                        { name: 'Evening Reflection', completed: false, icon: '🌙' },
                                    ].map((habit, index) => (
                                        <div key={index} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                                            <div className="flex items-center space-x-3">
                                                <div className="text-2xl">{habit.icon}</div>
                                                <span className={habit.completed ? 'text-green-400' : 'text-gray-300'}>
                                                    {habit.name}
                                                </span>
                                            </div>
                                            <div className={`w-6 h-6 rounded-full border-2 ${habit.completed
                                                    ? 'bg-green-500 border-green-500'
                                                    : 'border-gray-500'
                                                }`}>
                                                {habit.completed && <div className="text-white text-center text-sm">✓</div>}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {activeTab === 'spells' && (
                    <div className="text-center">
                        <h2 className="text-3xl font-bold text-purple-300 mb-4">
                            📜 Spell Practice
                        </h2>
                        <p className="text-gray-300 mb-8">
                            Master your daily habits and unlock new magical abilities
                        </p>
                        <Card className="max-w-2xl mx-auto">
                            <CardContent>
                                <div className="text-6xl mb-4">🔮</div>
                                <p className="text-gray-300">
                                    This mystical realm is still being enchanted...
                                    <br />
                                    Check back soon for powerful habit tracking spells!
                                </p>
                            </CardContent>
                        </Card>
                    </div>
                )}

                {activeTab === 'scrying' && (
                    <div className="text-center">
                        <h2 className="text-3xl font-bold text-purple-300 mb-4">
                            🔮 Scrying Portal
                        </h2>
                        <p className="text-gray-300 mb-8">
                            Peer into the mystical patterns of your progress
                        </p>
                        <Card className="max-w-2xl mx-auto">
                            <CardContent>
                                <div className="text-6xl mb-4">📊</div>
                                <p className="text-gray-300">
                                    The crystal ball is cloudy right now...
                                    <br />
                                    Analytics magic is being prepared!
                                </p>
                            </CardContent>
                        </Card>
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
                                    The trophy room is being polished...
                                    <br />
                                    Your achievements will be displayed here soon!
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
