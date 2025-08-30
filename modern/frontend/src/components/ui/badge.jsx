import React from 'react';

export const Badge = ({
    children,
    variant = "default",
    className = "",
    ...props
}) => {
    const baseClasses = "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2";

    const variants = {
        default: "border-transparent bg-primary text-primary-foreground hover:bg-primary/80 bg-blue-600 text-white",
        secondary: "border-transparent bg-secondary text-secondary-foreground hover:bg-secondary/80 bg-gray-100 text-gray-900",
        destructive: "border-transparent bg-destructive text-destructive-foreground hover:bg-destructive/80 bg-red-600 text-white",
        outline: "text-foreground border-gray-300"
    };

    return (
        <div className={`${baseClasses} ${variants[variant]} ${className}`} {...props}>
            {children}
        </div>
    );
};
