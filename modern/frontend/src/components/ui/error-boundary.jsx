import React from 'react';
import { Button } from './button';
import { Card, CardHeader, CardTitle, CardContent } from './card';

class ErrorBoundary extends React.Component {
    constructor(props) {
        super(props);
        this.state = { hasError: false, error: null, errorInfo: null };
    }

    static getDerivedStateFromError(error) {
        return { hasError: true };
    }

    componentDidCatch(error, errorInfo) {
        this.setState({
            error: error,
            errorInfo: errorInfo
        });

        // Log error to monitoring service
        console.error('ErrorBoundary caught an error:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            return (
                <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
                    <Card className="max-w-lg w-full">
                        <CardHeader className="text-center">
                            <div className="text-6xl mb-4">🧙‍♂️💥</div>
                            <CardTitle className="text-red-400 text-2xl">
                                Magical Spell Backfired!
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="text-center">
                            <p className="text-slate-300 mb-4">
                                Something went wrong with the enchantment. The magical energies have been disrupted.
                            </p>
                            <p className="text-slate-400 text-sm mb-6">
                                {this.state.error && this.state.error.toString()}
                            </p>
                            <div className="space-y-2">
                                <Button
                                    onClick={() => window.location.reload()}
                                    variant="magical"
                                    className="w-full"
                                >
                                    🔄 Recast Spell
                                </Button>
                                <Button
                                    onClick={() => this.setState({ hasError: false })}
                                    variant="outline"
                                    className="w-full"
                                >
                                    ✨ Try Again
                                </Button>
                            </div>
                        </CardContent>
                    </Card>
                </div>
            );
        }

        return this.props.children;
    }
}

export const ErrorFallback = ({ error, resetError }) => (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center p-4">
        <Card className="max-w-lg w-full">
            <CardHeader className="text-center">
                <div className="text-6xl mb-4">🧙‍♂️⚠️</div>
                <CardTitle className="text-yellow-400 text-2xl">
                    Spell Interrupted
                </CardTitle>
            </CardHeader>
            <CardContent className="text-center">
                <p className="text-slate-300 mb-4">
                    The magical process encountered an unexpected error.
                </p>
                <p className="text-slate-400 text-sm mb-6">
                    {error?.message || 'Unknown magical disturbance'}
                </p>
                <Button
                    onClick={resetError}
                    variant="magical"
                    className="w-full"
                >
                    🪄 Restore Order
                </Button>
            </CardContent>
        </Card>
    </div>
);

export default ErrorBoundary;
