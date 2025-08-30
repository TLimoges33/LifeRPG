import React, { useState } from 'react';

export const Dialog = ({ children, open, onOpenChange }) => {
    const [isOpen, setIsOpen] = useState(open || false);

    React.useEffect(() => {
        setIsOpen(open || false);
    }, [open]);

    const handleOpenChange = (newOpen) => {
        setIsOpen(newOpen);
        if (onOpenChange) onOpenChange(newOpen);
    };

    return (
        <div>
            {React.Children.map(children, child =>
                React.cloneElement(child, { isOpen, handleOpenChange })
            )}
            {isOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center">
                    <div
                        className="fixed inset-0 bg-black/50"
                        onClick={() => handleOpenChange(false)}
                    />
                    <div className="relative bg-white rounded-lg shadow-lg max-w-lg w-full mx-4 max-h-[90vh] overflow-auto">
                        {React.Children.toArray(children).find(child => child.type === DialogContent)}
                    </div>
                </div>
            )}
        </div>
    );
};

export const DialogTrigger = ({ children, isOpen, handleOpenChange }) => {
    return React.cloneElement(children, {
        onClick: () => handleOpenChange(true)
    });
};

export const DialogContent = ({ children, className = "", ...props }) => {
    return (
        <div className={`p-6 ${className}`} {...props}>
            {children}
        </div>
    );
};

export const DialogHeader = ({ children, className = "", ...props }) => {
    return (
        <div className={`mb-4 ${className}`} {...props}>
            {children}
        </div>
    );
};

export const DialogTitle = ({ children, className = "", ...props }) => {
    return (
        <h2 className={`text-lg font-semibold ${className}`} {...props}>
            {children}
        </h2>
    );
};
