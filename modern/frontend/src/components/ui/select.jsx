import React, { useState } from 'react';

export const Select = ({ children, value, onValueChange, ...props }) => {
    return (
        <div className="relative">
            {React.cloneElement(children, { value, onValueChange })}
        </div>
    );
};

export const SelectTrigger = ({ children, className = "", ...props }) => {
    return (
        <button
            className={`flex h-10 w-full items-center justify-between rounded-md border border-input bg-transparent px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 border-gray-300 ${className}`}
            {...props}
        >
            {children}
            <svg
                className="h-4 w-4 opacity-50"
                xmlns="http://www.w3.org/2000/svg"
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
            >
                <polyline points="6,9 12,15 18,9" />
            </svg>
        </button>
    );
};

export const SelectValue = ({ placeholder, value }) => {
    return <span>{value || placeholder}</span>;
};

export const SelectContent = ({ children, value, onValueChange }) => {
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="relative">
            <div
                className="absolute top-1 z-50 min-w-[8rem] overflow-hidden rounded-md border bg-popover p-1 text-popover-foreground shadow-md animate-in fade-in-80 bg-white border-gray-200"
                style={{ display: isOpen ? 'block' : 'none' }}
            >
                {React.Children.map(children, child =>
                    React.cloneElement(child, { onValueChange, setIsOpen })
                )}
            </div>
        </div>
    );
};

export const SelectItem = ({ value, children, onValueChange, setIsOpen }) => {
    const handleClick = () => {
        if (onValueChange) onValueChange(value);
        if (setIsOpen) setIsOpen(false);
    };

    return (
        <div
            className="relative flex w-full cursor-default select-none items-center rounded-sm py-1.5 pl-8 pr-2 text-sm outline-none focus:bg-accent focus:text-accent-foreground hover:bg-gray-100 cursor-pointer"
            onClick={handleClick}
        >
            {children}
        </div>
    );
};
