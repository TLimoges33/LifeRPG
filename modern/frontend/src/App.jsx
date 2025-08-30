import React, { useState, useEffect } from 'react';
import MainDashboard from './components/MainDashboard';
import ScryingPortal from './components/ScryingPortal';
import SocialFeatures from './components/SocialFeatures';
import NotificationSettings from './components/NotificationSettings';
import PerformanceOptimization from './components/PerformanceOptimization';
import MobileAppEnhancement from './components/MobileAppEnhancement';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { User, Lock, Mail, BarChart3, Users, Settings, Zap, Smartphone, Home } from 'lucide-react';

const App = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loginForm, setLoginForm] = useState({ email: '', password: '' });
    const [registering, setRegistering] = useState(false);
    const [currentView, setCurrentView] = useState('dashboard');

    useEffect(() => {
        checkAuth();
        registerServiceWorker();
    }, []);

    const registerServiceWorker = async () => {
        if ('serviceWorker' in navigator) {
            try {
                const registration = await navigator.serviceWorker.register('/sw.js');
                console.log('Service Worker registered:', registration);
            } catch (error) {
                console.error('Service Worker registration failed:', error);
            }
        }
    };

    const checkAuth = async () => {
        const token = localStorage.getItem('token');
        if (!token) {
            setLoading(false);
            return;
        }

        try {
            const response = await fetch('/api/v1/me', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const userData = await response.json();
                setUser(userData);
            } else {
                localStorage.removeItem('token');
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            localStorage.removeItem('token');
        } finally {
            setLoading(false);
        }
    };

    const handleLogin = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(loginForm)
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.token);
                setUser(data.user);
            } else {
                const error = await response.json();
                alert(error.detail || 'Login failed');
            }
        } catch (error) {
            console.error('Login failed:', error);
            alert('Login failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();
        setLoading(true);

        try {
            const response = await fetch('/api/v1/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...loginForm,
                    display_name: loginForm.email.split('@')[0] // Simple display name
                })
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.token);
                setUser(data.user);
            } else {
                const error = await response.json();
                alert(error.detail || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration failed:', error);
            alert('Registration failed. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading...</p>
                </div>
            </div>
        );
    }

    if (!user) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center px-4">
                <Card className="w-full max-w-md bg-gradient-to-b from-purple-100 to-blue-50 border-2 border-gold-400 shadow-2xl">
                    <CardHeader className="text-center">
                        <div className="w-16 h-16 bg-gradient-to-br from-purple-600 to-indigo-600 rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
                            <span className="text-2xl">🔮</span>
                        </div>
                        <CardTitle className="text-2xl text-purple-900">
                            {registering ? 'Join the Academy' : 'Welcome to The Wizard\'s Grimoire'}
                        </CardTitle>
                        <p className="text-purple-700 mt-2">
                            {registering
                                ? 'Begin your magical journey and master daily spells'
                                : 'Enter your sanctum to practice spells and unlock mystical powers'
                            }
                        </p>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={registering ? handleRegister : handleLogin} className="space-y-4">
                            <div>
                                <label className="text-sm font-medium text-purple-800">Mystic Email</label>
                                <div className="relative">
                                    <Mail className="absolute left-3 top-3 h-4 w-4 text-purple-500" />
                                    <Input
                                        type="email"
                                        placeholder="Enter your mystical contact"
                                        value={loginForm.email}
                                        onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                                        className="pl-10 border-purple-300 focus:border-purple-500"
                                        required
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="text-sm font-medium text-purple-800">Arcane Password</label>
                                <div className="relative">
                                    <Lock className="absolute left-3 top-3 h-4 w-4 text-purple-500" />
                                    <Input
                                        type="password"
                                        placeholder="Speak the secret incantation"
                                        value={loginForm.password}
                                        onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                                        className="pl-10 border-purple-300 focus:border-purple-500"
                                        required
                                    />
                                </div>
                            </div>

                            <Button
                                type="submit"
                                className="w-full bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white shadow-lg"
                                disabled={loading}
                            >
                                {loading ? 'Summoning...' : registering ? 'Begin Journey' : 'Enter Sanctum'}
                            </Button>
                        </form>

                        <div className="mt-6 text-center">
                            <button
                                type="button"
                                onClick={() => setRegistering(!registering)}
                                className="text-purple-600 hover:text-purple-700 text-sm font-medium"
                            >
                                {registering
                                    ? 'Already initiated? Enter your sanctum'
                                    : "New to magic? Join the Academy"
                                }
                            </button>
                        </div>

                        {!registering && (
                            <div className="mt-4 text-center">
                                <p className="text-xs text-purple-600">
                                    🧙‍♂️ Demo: Use any incantation to create a practice realm
                                </p>
                            </div>
                        )}
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Navigation component
    const Navigation = () => (
        <div className="bg-slate-800 border-b border-purple-500/30 p-4 mb-6">
            <div className="flex flex-wrap gap-2">
                <Button
                    onClick={() => setCurrentView('dashboard')}
                    variant={currentView === 'dashboard' ? 'default' : 'outline'}
                    className="flex items-center gap-2"
                >
                    <Home className="w-4 h-4" />
                    Dashboard
                </Button>
                <Button
                    onClick={() => setCurrentView('analytics')}
                    variant={currentView === 'analytics' ? 'default' : 'outline'}
                    className="flex items-center gap-2"
                >
                    <BarChart3 className="w-4 h-4" />
                    Analytics
                </Button>
                <Button
                    onClick={() => setCurrentView('social')}
                    variant={currentView === 'social' ? 'default' : 'outline'}
                    className="flex items-center gap-2"
                >
                    <Users className="w-4 h-4" />
                    Social
                </Button>
                <Button
                    onClick={() => setCurrentView('notifications')}
                    variant={currentView === 'notifications' ? 'default' : 'outline'}
                    className="flex items-center gap-2"
                >
                    <Settings className="w-4 h-4" />
                    Notifications
                </Button>
                <Button
                    onClick={() => setCurrentView('performance')}
                    variant={currentView === 'performance' ? 'default' : 'outline'}
                    className="flex items-center gap-2"
                >
                    <Zap className="w-4 h-4" />
                    Performance
                </Button>
                <Button
                    onClick={() => setCurrentView('mobile')}
                    variant={currentView === 'mobile' ? 'default' : 'outline'}
                    className="flex items-center gap-2"
                >
                    <Smartphone className="w-4 h-4" />
                    Mobile
                </Button>
            </div>
        </div>
    );

    // Render current view
    const renderCurrentView = () => {
        switch (currentView) {
            case 'analytics':
                return <ScryingPortal />;
            case 'social':
                return <SocialFeatures />;
            case 'notifications':
                return <NotificationSettings />;
            case 'performance':
                return <PerformanceOptimization />;
            case 'mobile':
                return <MobileAppEnhancement />;
            default:
                return <MainDashboard user={user} onLogout={handleLogout} />;
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
            <Navigation />
            <div className="container mx-auto px-4">
                {renderCurrentView()}
            </div>
        </div>
    );
};

export default App;
