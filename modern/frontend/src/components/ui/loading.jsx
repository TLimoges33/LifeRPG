import React from 'react';

export const LoadingSpinner = ({ size = "default", className = "" }) => {
    const sizeClasses = {
        sm: "w-4 h-4",
        default: "w-6 h-6",
        lg: "w-8 h-8",
        xl: "w-12 h-12"
    };

    return (
        <div className={`animate-spin rounded-full border-2 border-purple-200 border-t-purple-600 ${sizeClasses[size]} ${className}`} />
    );
};

export const LoadingSkeleton = ({ className = "" }) => (
    <div className={`animate-pulse space-y-4 ${className}`}>
        <div className="h-4 bg-slate-700 rounded w-3/4"></div>
        <div className="h-4 bg-slate-700 rounded w-1/2"></div>
        <div className="h-4 bg-slate-700 rounded w-5/6"></div>
    </div>
);

export const LoadingCard = () => (
    <div className="bg-slate-800/50 border border-purple-500/30 rounded-lg p-6 animate-pulse">
        <div className="h-6 bg-slate-700 rounded mb-4 w-1/2"></div>
        <div className="space-y-3">
            <div className="h-4 bg-slate-700 rounded"></div>
            <div className="h-4 bg-slate-700 rounded w-3/4"></div>
            <div className="h-4 bg-slate-700 rounded w-1/2"></div>
        </div>
    </div>
);

export const FullPageLoader = () => (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
        <div className="text-center">
            <div className="text-6xl mb-4">🧙‍♂️</div>
            <LoadingSpinner size="xl" className="mx-auto mb-4" />
            <h2 className="text-2xl font-bold text-purple-300 mb-2">
                Channeling Magical Energies...
            </h2>
            <p className="text-slate-400">
                The wizard's grimoire is awakening
            </p>
        </div>
    </div>
);
