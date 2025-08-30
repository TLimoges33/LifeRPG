import React from 'react';
import { cn } from '../../lib/utils';

export const Button = ({
    children,
    variant = "default",
    size = "default",
    className = "",
    disabled = false,
    ...props
}) => {
    const baseClasses = "inline-flex items-center justify-center rounded-md text-sm font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-purple-500 focus-visible:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";

    const variants = {
        default: "bg-gradient-to-r from-purple-600 to-purple-700 text-white hover:from-purple-700 hover:to-purple-800 shadow-lg hover:shadow-xl",
        outline: "border border-purple-500 bg-transparent hover:bg-purple-500/10 text-purple-300 hover:text-purple-100",
        ghost: "hover:bg-purple-500/10 hover:text-purple-300 text-slate-300",
        destructive: "bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 shadow-lg",
        magical: "bg-gradient-to-r from-purple-500 via-pink-500 to-purple-600 text-white hover:from-purple-600 hover:via-pink-600 hover:to-purple-700 shadow-lg hover:shadow-2xl transform hover:scale-105",
        secondary: "bg-slate-700 text-slate-100 hover:bg-slate-600"
    };

    const sizes = {
        default: "h-10 py-2 px-4",
        sm: "h-9 px-3 rounded-md",
        lg: "h-11 px-8 rounded-md",
        icon: "h-10 w-10"
    };

    return (
        <button
            className={cn(baseClasses, variants[variant], sizes[size], className)}
            disabled={disabled}
            {...props}
        >
            {children}
        </button>
    );
};
