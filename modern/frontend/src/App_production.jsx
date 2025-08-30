import React, { useEffect } from 'react';
import useAppStore from './store/appStore';
import MainDashboard from './components/MainDashboard_production';
import ErrorBoundary from './components/ui/error-boundary';
import { FullPageLoader } from './components/ui/loading';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';

const LoginForm = () => {
    const { login, register, loading } = useAppStore();
    const [isRegistering, setIsRegistering] = React.useState(false);
    const [formData, setFormData] = React.useState({
        email: '',
        password: '',
        name: ''
    });
    const [error, setError] = React.useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');

        const result = isRegistering
            ? await register(formData)
            : await login({ email: formData.email, password: formData.password });

        if (!result.success) {
            setError(result.error);
        }
    };

    const handleInputChange = (e) => {
        setFormData(prev => ({
            ...prev,
            [e.target.name]: e.target.value
        }));
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
            <Card className="w-full max-w-md">
                <CardHeader className="text-center space-y-4">
                    <div className="text-6xl">🧙‍♂️</div>
                    <CardTitle className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
                        The Wizard's Grimoire
                    </CardTitle>
                    <p className="text-slate-400">
                        {isRegistering ? 'Join the Magical Order' : 'Enter the Sanctum'}
                    </p>
                </CardHeader>
                <CardContent>
                    <form onSubmit={handleSubmit} className="space-y-4">
                        {isRegistering && (
                            <div>
                                <label className="block text-sm font-medium text-purple-300 mb-2">
                                    Wizard Name
                                </label>
                                <Input
                                    name="name"
                                    type="text"
                                    value={formData.name}
                                    onChange={handleInputChange}
                                    placeholder="Enter your wizard name"
                                    required
                                />
                            </div>
                        )}
                        <div>
                            <label className="block text-sm font-medium text-purple-300 mb-2">
                                Mystical Email
                            </label>
                            <Input
                                name="email"
                                type="email"
                                value={formData.email}
                                onChange={handleInputChange}
                                placeholder="wizard@grimoire.com"
                                required
                            />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-purple-300 mb-2">
                                Secret Incantation
                            </label>
                            <Input
                                name="password"
                                type="password"
                                value={formData.password}
                                onChange={handleInputChange}
                                placeholder="Enter your secret password"
                                required
                            />
                        </div>

                        {error && (
                            <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded">
                                {error}
                            </div>
                        )}

                        <Button
                            type="submit"
                            variant="magical"
                            className="w-full"
                            disabled={loading}
                        >
                            {loading ? (
                                <span className="flex items-center justify-center">
                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2" />
                                    Casting Spell...
                                </span>
                            ) : (
                                `🪄 ${isRegistering ? 'Join Order' : 'Enter Sanctum'}`
                            )}
                        </Button>

                        <Button
                            type="button"
                            variant="ghost"
                            className="w-full"
                            onClick={() => setIsRegistering(!isRegistering)}
                        >
                            {isRegistering
                                ? 'Already a wizard? Enter here'
                                : 'New to magic? Join the order'
                            }
                        </Button>
                    </form>
                </CardContent>
            </Card>
        </div>
    );
};

const App = () => {
    const { user, isAuthenticated, loading, checkAuth, logout } = useAppStore();

    useEffect(() => {
        checkAuth();
    }, [checkAuth]);

    if (loading) {
        return <FullPageLoader />;
    }

    return (
        <ErrorBoundary>
            {isAuthenticated && user ? (
                <MainDashboard user={user} onLogout={logout} />
            ) : (
                <LoginForm />
            )}
        </ErrorBoundary>
    );
};

export default App;
