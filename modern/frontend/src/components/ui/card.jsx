import React from 'react';
import { cn } from '../../lib/utils';

export const Card = ({ children, className = "", ...props }) => (
    <div className={cn(
        "bg-slate-800/50 backdrop-blur-sm border border-purple-500/30 rounded-lg shadow-lg hover:shadow-xl transition-all duration-300 hover:border-purple-400/50",
        className
    )} {...props}>
        {children}
    </div>
);

export const CardHeader = ({ children, className = "", ...props }) => (
    <div className={cn("p-6 pb-0", className)} {...props}>
        {children}
    </div>
);

export const CardTitle = ({ children, className = "", ...props }) => (
    <h3 className={cn(
        "text-lg font-semibold leading-none tracking-tight text-purple-300",
        className
    )} {...props}>
        {children}
    </h3>
);

export const CardContent = ({ children, className = "", ...props }) => (
    <div className={cn("p-6 pt-0 text-slate-200", className)} {...props}>
        {children}
    </div>
);

export const CardDescription = ({ children, className = "", ...props }) => (
    <p className={cn("text-sm text-slate-400", className)} {...props}>
        {children}
    </p>
);

export const CardFooter = ({ children, className = "", ...props }) => (
    <div className={cn("flex items-center p-6 pt-0", className)} {...props}>
        {children}
    </div>
);
