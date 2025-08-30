import React, { useState, useEffect } from 'react';
import MainDashboard from './components/MainDashboard_working';

// Simple inline components instead of importing UI components
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

const Input = ({ className = "", ...props }) => (
    <input
        className={`w-full px-3 py-2 bg-slate-700 border border-purple-500 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 ${className}`}
        {...props}
    />
);

const App = () => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);
    const [loginForm, setLoginForm] = useState({ email: '', password: '' });
    const [registering, setRegistering] = useState(false);

    useEffect(() => {
        checkAuth();
    }, []);

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
        }
        setLoading(false);
    };

    const handleLogin = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch('/api/v1/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(loginForm),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                setUser(data.user);
            } else {
                const error = await response.json();
                alert(error.detail || 'Login failed');
            }
        } catch (error) {
            console.error('Login failed:', error);
            alert('Login failed. Please try again.');
        }
    };

    const handleRegister = async (e) => {
        e.preventDefault();

        try {
            const response = await fetch('/api/v1/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(loginForm),
            });

            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('token', data.access_token);
                setUser(data.user);
            } else {
                const error = await response.json();
                alert(error.detail || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration failed:', error);
            alert('Registration failed. Please try again.');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('token');
        setUser(null);
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
                <div className="text-center">
                    <div className="text-6xl mb-4">🔮</div>
                    <div className="text-xl text-purple-300">Consulting the ancient scrolls...</div>
                </div>
            </div>
        );
    }

    if (user) {
        return <MainDashboard user={user} onLogout={handleLogout} />;
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <div className="text-6xl mb-4">🧙‍♂️</div>
                    <h1 className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 mb-2">
                        The Wizard's Grimoire
                    </h1>
                    <p className="text-purple-300">Enter the mystical realm of habit tracking</p>
                </div>

                <Card className="backdrop-blur-sm bg-slate-800/50">
                    <CardHeader>
                        <CardTitle className="text-center">
                            {registering ? 'Join the Magical Order' : 'Enter the Sanctum'}
                        </CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={registering ? handleRegister : handleLogin} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-purple-300 mb-2">
                                    📧 Mystical Email
                                </label>
                                <Input
                                    type="email"
                                    placeholder="wizard@grimoire.magic"
                                    value={loginForm.email}
                                    onChange={(e) => setLoginForm({ ...loginForm, email: e.target.value })}
                                    required
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-purple-300 mb-2">
                                    🔐 Secret Incantation
                                </label>
                                <Input
                                    type="password"
                                    placeholder="Enter your magical password"
                                    value={loginForm.password}
                                    onChange={(e) => setLoginForm({ ...loginForm, password: e.target.value })}
                                    required
                                />
                            </div>
                            <Button type="submit" className="w-full">
                                {registering ? '🌟 Begin Journey' : '✨ Enter Sanctum'}
                            </Button>
                        </form>

                        <div className="mt-4 text-center">
                            <button
                                type="button"
                                onClick={() => setRegistering(!registering)}
                                className="text-purple-400 hover:text-purple-300 underline"
                            >
                                {registering
                                    ? 'Already have a grimoire? Sign in'
                                    : 'New to magic? Create a grimoire'
                                }
                            </button>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
};

export default App;
