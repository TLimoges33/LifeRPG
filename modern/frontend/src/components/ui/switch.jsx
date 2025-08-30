import React, { useState } from 'react';

export const Switch = ({
    checked = false,
    onCheckedChange,
    disabled = false,
    className = "",
    ...props
}) => {
    const [isChecked, setIsChecked] = useState(checked);

    const handleChange = () => {
        if (disabled) return;
        const newChecked = !isChecked;
        setIsChecked(newChecked);
        if (onCheckedChange) {
            onCheckedChange(newChecked);
        }
    };

    React.useEffect(() => {
        setIsChecked(checked);
    }, [checked]);

    return (
        <button
            type="button"
            role="switch"
            aria-checked={isChecked}
            onClick={handleChange}
            disabled={disabled}
            className={`peer inline-flex h-6 w-11 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 ${isChecked
                    ? 'bg-primary bg-blue-600'
                    : 'bg-input bg-gray-200'
                } ${className}`}
            {...props}
        >
            <span
                className={`pointer-events-none block h-5 w-5 rounded-full bg-background shadow-lg ring-0 transition-transform ${isChecked ? 'translate-x-5' : 'translate-x-0'
                    } bg-white`}
            />
        </button>
    );
};
