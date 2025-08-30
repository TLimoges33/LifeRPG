import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Home, Target, BarChart3, Trophy, Settings, Shield, Zap, Puzzle, BookOpen, Sparkles, Gem, ScrollText } from 'lucide-react';

// Import our dashboard components
import GamificationDashboard from './GamificationDashboard';
import HabitsDashboard from './HabitsDashboard';
import AnalyticsDashboard from './AnalyticsDashboard';
import Leaderboard from './Leaderboard';
import TelemetrySettings from './TelemetrySettings';
import AdminTelemetryDashboard from './AdminTelemetryDashboard';
import PluginAdmin from '../plugins/PluginAdmin';
import PluginExtensionContainer from '../plugins/PluginExtensions';

const MainDashboard = ({ user }) => {
    const [activeTab, setActiveTab] = useState('overview');

    const OverviewTab = () => (
        <div className="space-y-6">
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
                            <BookOpen className="h-6 w-6 text-purple-600" />
                            <span>Spell Practice</span>
                        </Button>

                        <Button
                            variant="outline"
                            className="h-20 flex flex-col space-y-2 border-purple-200 hover:border-purple-400 hover:bg-purple-50"
                            onClick={() => setActiveTab('analytics')}
                        >
                            <Gem className="h-6 w-6 text-indigo-600" />
                            <span>Scrying</span>
                        </Button>

                        <Button
                            variant="outline"
                            className="h-20 flex flex-col space-y-2 border-purple-200 hover:border-purple-400 hover:bg-purple-50"
                            onClick={() => setActiveTab('leaderboard')}
                        >
                            <Trophy className="h-6 w-6 text-yellow-600" />
                            <span>Hall of Fame</span>
                        </Button>

                        <Button
                            variant="outline"
                            className="h-20 flex flex-col space-y-2 border-purple-200 hover:border-purple-400 hover:bg-purple-50"
                            onClick={() => setActiveTab('settings')}
                        >
                            <Settings className="h-6 w-6 text-gray-600" />
                            <span>Sanctum</span>
                        </Button>
                    </div>
                </CardContent>
            </Card>
        </div>
    );

    const SettingsTab = () => (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold mb-2 text-purple-900">Sanctum Settings</h2>
                <p className="text-purple-700">Manage your arcane preferences and mystical configurations</p>
            </div>

            <TelemetrySettings />

            {user?.role === 'admin' && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center space-x-2">
                            <Shield className="h-5 w-5 text-red-600" />
                            <span>Archmage Panel</span>
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <Button
                            variant="outline"
                            onClick={() => setActiveTab('admin')}
                            className="border-red-200 hover:border-red-400 hover:bg-red-50"
                        >
                            Access Archmage Dashboard
                        </Button>
                    </CardContent>
                </Card>
            )}
        </div>
    );

    return (
        <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-100">
            <div className="max-w-7xl mx-auto px-4 py-8">
                <div className="mb-8">
                    <h1 className="text-3xl font-bold text-purple-900">
                        Welcome back, {user?.display_name || user?.email || 'Apprentice Wizard'}! 🧙‍♂️
                    </h1>
                    <p className="text-purple-700 mt-2">
                        Practice your daily spells, gather mystical energy, and unlock powerful enchantments
                    </p>
                </div>

                <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
                    <TabsList className="grid w-full grid-cols-2 md:grid-cols-7 bg-white shadow-lg border-purple-200">
                        <TabsTrigger value="overview" className="flex items-center space-x-2 data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700">
                            <Home className="h-4 w-4" />
                            <span>Sanctum</span>
                        </TabsTrigger>
                        <TabsTrigger value="habits" className="flex items-center space-x-2 data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700">
                            <BookOpen className="h-4 w-4" />
                            <span>Spells</span>
                        </TabsTrigger>
                        <TabsTrigger value="analytics" className="flex items-center space-x-2 data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700">
                            <Gem className="h-4 w-4" />
                            <span>Scrying</span>
                        </TabsTrigger>
                        <TabsTrigger value="leaderboard" className="flex items-center space-x-2 data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700">
                            <Trophy className="h-4 w-4" />
                            <span>Hall of Fame</span>
                        </TabsTrigger>
                        <TabsTrigger value="plugins" className="flex items-center space-x-2 data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700">
                            <ScrollText className="h-4 w-4" />
                            <span>Artifacts</span>
                        </TabsTrigger>
                        <TabsTrigger value="settings" className="flex items-center space-x-2 data-[state=active]:bg-purple-100 data-[state=active]:text-purple-700">
                            <Settings className="h-4 w-4" />
                            <span>Settings</span>
                        </TabsTrigger>
                        {user?.role === 'admin' && (
                            <TabsTrigger value="admin" className="flex items-center space-x-2 data-[state=active]:bg-red-100 data-[state=active]:text-red-700">
                                <Shield className="h-4 w-4" />
                                <span>Archmage</span>
                            </TabsTrigger>
                        )}
                    </TabsList>

                    <TabsContent value="overview">
                        <OverviewTab />
                    </TabsContent>

                    <TabsContent value="habits">
                        <HabitsDashboard />
                    </TabsContent>

                    <TabsContent value="analytics">
                        <AnalyticsDashboard />
                    </TabsContent>

                    <TabsContent value="leaderboard">
                        <div className="max-w-2xl mx-auto">
                            <Leaderboard />
                        </div>
                    </TabsContent>

                    <TabsContent value="plugins">
                        <PluginAdmin />
                    </TabsContent>

                    <TabsContent value="settings">
                        <SettingsTab />
                    </TabsContent>

                    {user?.role === 'admin' && (
                        <TabsContent value="admin">
                            <AdminTelemetryDashboard />
                        </TabsContent>
                    )}
                </Tabs>
            </div>
        </div>
    );
};

export default MainDashboard;
