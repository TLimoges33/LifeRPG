import React, { useCallback } from 'react';

// Custom hook for telemetry events
export const useTelemetry = () => {
    const recordEvent = useCallback(async (eventName, properties = null) => {
        try {
            const token = localStorage.getItem('token');
            if (!token) return false;

            const response = await fetch('/api/v1/telemetry/event', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    event_name: eventName,
                    properties
                })
            });

            return response.ok;
        } catch (error) {
            console.warn('Telemetry event failed:', error);
            return false;
        }
    }, []);

    // Convenience methods for common events
    const trackFeatureUsage = useCallback((feature, duration = null) => {
        return recordEvent('feature_used', {
            feature_used: feature,
            ...(duration && { duration })
        });
    }, [recordEvent]);

    const trackError = useCallback((errorType, context = null) => {
        return recordEvent('error_occurred', {
            error_type: errorType,
            ...(context && { context })
        });
    }, [recordEvent]);

    const trackNavigation = useCallback((page) => {
        return recordEvent('page_view', {
            page
        });
    }, [recordEvent]);

    const trackInteraction = useCallback((action, category = null, label = null) => {
        return recordEvent('user_interaction', {
            action,
            ...(category && { category }),
            ...(label && { label })
        });
    }, [recordEvent]);

    return {
        recordEvent,
        trackFeatureUsage,
        trackError,
        trackNavigation,
        trackInteraction
    };
};

// Higher-order component to automatically track page views
export const withTelemetry = (WrappedComponent, pageName) => {
    return function TelemetryWrappedComponent(props) {
        const { trackNavigation } = useTelemetry();

        React.useEffect(() => {
            trackNavigation(pageName);
        }, [trackNavigation]);

        return <WrappedComponent {...props} />;
    };
};
