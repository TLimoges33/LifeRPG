import React from 'react';

export const Progress = ({
    value = 0,
    className = "",
    ...props
}) => {
    return (
        <div
            className={`relative h-4 w-full overflow-hidden rounded-full bg-secondary bg-gray-200 ${className}`}
            {...props}
        >
            <div
                className="h-full w-full flex-1 bg-primary transition-all bg-blue-600"
                style={{
                    transform: `translateX(-${100 - (value || 0)}%)`
                }}
            />
        </div>
    );
};
