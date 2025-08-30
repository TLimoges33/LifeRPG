import { useEffect, useState } from 'react';

// Custom hook for managing push notifications
export const useNotifications = () => {
    const [permission, setPermission] = useState(Notification.permission);
    const [subscription, setSubscription] = useState(null);
    const [isSupported, setIsSupported] = useState(false);

    useEffect(() => {
        // Check if notifications are supported
        setIsSupported('Notification' in window && 'serviceWorker' in navigator);
    }, []);

    const requestPermission = async () => {
        if (!isSupported) return false;

        try {
            const result = await Notification.requestPermission();
            setPermission(result);
            return result === 'granted';
        } catch (error) {
            console.error('Error requesting notification permission:', error);
            return false;
        }
    };

    const subscribeToPush = async () => {
        if (!isSupported || permission !== 'granted') return null;

        try {
            const registration = await navigator.serviceWorker.ready;

            // Check if already subscribed
            const existingSubscription = await registration.pushManager.getSubscription();
            if (existingSubscription) {
                setSubscription(existingSubscription);
                return existingSubscription;
            }

            // Create new subscription
            const newSubscription = await registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array(process.env.REACT_APP_VAPID_PUBLIC_KEY || '')
            });

            setSubscription(newSubscription);

            // Send subscription to backend
            await sendSubscriptionToBackend(newSubscription);

            return newSubscription;
        } catch (error) {
            console.error('Error subscribing to push notifications:', error);
            return null;
        }
    };

    const unsubscribeFromPush = async () => {
        if (!subscription) return;

        try {
            await subscription.unsubscribe();
            setSubscription(null);

            // Remove subscription from backend
            await removeSubscriptionFromBackend(subscription);
        } catch (error) {
            console.error('Error unsubscribing from push notifications:', error);
        }
    };

    const scheduleNotification = async (title, body, scheduledTime) => {
        if (!isSupported || permission !== 'granted') return;

        try {
            const registration = await navigator.serviceWorker.ready;

            // Calculate delay
            const delay = new Date(scheduledTime).getTime() - Date.now();

            if (delay > 0) {
                setTimeout(() => {
                    registration.showNotification(title, {
                        body,
                        icon: '/icon-192x192.png',
                        badge: '/icon-72x72.png',
                        vibrate: [100, 50, 100],
                        tag: 'habit-reminder',
                        renotify: true,
                        actions: [
                            {
                                action: 'complete',
                                title: '✅ Mark Complete'
                            },
                            {
                                action: 'snooze',
                                title: '⏰ Remind Later'
                            }
                        ]
                    });
                }, delay);
            }
        } catch (error) {
            console.error('Error scheduling notification:', error);
        }
    };

    return {
        permission,
        subscription,
        isSupported,
        requestPermission,
        subscribeToPush,
        unsubscribeFromPush,
        scheduleNotification
    };
};

// Helper function to convert VAPID key
function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }

    return outputArray;
}

// Send subscription to backend
async function sendSubscriptionToBackend(subscription) {
    try {
        const token = localStorage.getItem('token');
        await fetch('/api/v1/notifications/subscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });
    } catch (error) {
        console.error('Error sending subscription to backend:', error);
    }
}

// Remove subscription from backend
async function removeSubscriptionFromBackend(subscription) {
    try {
        const token = localStorage.getItem('token');
        await fetch('/api/v1/notifications/unsubscribe', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                subscription: subscription.toJSON()
            })
        });
    } catch (error) {
        console.error('Error removing subscription from backend:', error);
    }
}
