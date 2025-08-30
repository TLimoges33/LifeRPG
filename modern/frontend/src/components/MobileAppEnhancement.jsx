import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { LoadingSpinner } from './ui/loading';
import {
    Smartphone,
    Download,
    Share,
    Home,
    Wifi,
    WifiOff,
    Sync,
    Settings,
    Monitor,
    Tablet
} from 'lucide-react';

const MobileAppEnhancement = () => {
    const [installPrompt, setInstallPrompt] = useState(null);
    const [isInstalled, setIsInstalled] = useState(false);
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const [syncStatus, setSyncStatus] = useState('idle');
    const [offlineData, setOfflineData] = useState({
        habits: 0,
        pendingSync: 0,
        lastSync: null
    });
    const [deviceInfo, setDeviceInfo] = useState({
        type: 'desktop',
        os: 'unknown',
        browser: 'unknown'
    });

    useEffect(() => {
        detectDevice();
        checkInstallation();
        setupNetworkListeners();
        loadOfflineData();
        setupInstallPrompt();
    }, []);

    const detectDevice = () => {
        const userAgent = navigator.userAgent;
        const isMobile = /iPhone|iPad|iPod|Android/i.test(userAgent);
        const isTablet = /iPad|Android(?=.*Mobile)/i.test(userAgent);

        let os = 'unknown';
        if (/iPhone|iPad|iPod/i.test(userAgent)) os = 'iOS';
        else if (/Android/i.test(userAgent)) os = 'Android';
        else if (/Windows/i.test(userAgent)) os = 'Windows';
        else if (/Mac/i.test(userAgent)) os = 'macOS';
        else if (/Linux/i.test(userAgent)) os = 'Linux';

        let browser = 'unknown';
        if (/Chrome/i.test(userAgent)) browser = 'Chrome';
        else if (/Firefox/i.test(userAgent)) browser = 'Firefox';
        else if (/Safari/i.test(userAgent) && !/Chrome/i.test(userAgent)) browser = 'Safari';
        else if (/Edge/i.test(userAgent)) browser = 'Edge';

        setDeviceInfo({
            type: isTablet ? 'tablet' : isMobile ? 'mobile' : 'desktop',
            os,
            browser
        });
    };

    const checkInstallation = () => {
        // Check if app is running in standalone mode (installed as PWA)
        const isStandalone = window.matchMedia('(display-mode: standalone)').matches ||
            window.navigator.standalone ||
            document.referrer.includes('android-app://');

        setIsInstalled(isStandalone);
    };

    const setupNetworkListeners = () => {
        const handleOnline = () => {
            setIsOnline(true);
            syncOfflineData();
        };

        const handleOffline = () => {
            setIsOnline(false);
        };

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    };

    const setupInstallPrompt = () => {
        const handleBeforeInstallPrompt = (e) => {
            e.preventDefault();
            setInstallPrompt(e);
        };

        window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);

        return () => {
            window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
        };
    };

    const loadOfflineData = () => {
        const cachedHabits = localStorage.getItem('offline-habits');
        const pendingSync = localStorage.getItem('pending-sync-items');
        const lastSync = localStorage.getItem('last-sync-time');

        setOfflineData({
            habits: cachedHabits ? JSON.parse(cachedHabits).length : 0,
            pendingSync: pendingSync ? JSON.parse(pendingSync).length : 0,
            lastSync: lastSync ? new Date(lastSync) : null
        });
    };

    const installApp = async () => {
        if (installPrompt) {
            installPrompt.prompt();
            const result = await installPrompt.userChoice;

            if (result.outcome === 'accepted') {
                setIsInstalled(true);
                setInstallPrompt(null);
            }
        }
    };

    const shareApp = async () => {
        if (navigator.share) {
            try {
                await navigator.share({
                    title: "The Wizard's Grimoire",
                    text: 'Track your magical habits and build powerful routines!',
                    url: window.location.origin
                });
            } catch (error) {
                console.error('Error sharing:', error);
            }
        } else {
            // Fallback to clipboard
            navigator.clipboard.writeText(window.location.origin);
            alert('Link copied to clipboard!');
        }
    };

    const syncOfflineData = async () => {
        if (!isOnline) return;

        setSyncStatus('syncing');

        try {
            const pendingSyncItems = localStorage.getItem('pending-sync-items');
            if (pendingSyncItems) {
                const items = JSON.parse(pendingSyncItems);
                const token = localStorage.getItem('token');

                for (const item of items) {
                    await fetch(`/api/v1/habits/${item.habitId}/complete`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Authorization': `Bearer ${token}`
                        },
                        body: JSON.stringify(item.data)
                    });
                }

                localStorage.removeItem('pending-sync-items');
                localStorage.setItem('last-sync-time', new Date().toISOString());
                loadOfflineData();
            }

            setSyncStatus('success');
            setTimeout(() => setSyncStatus('idle'), 2000);
        } catch (error) {
            console.error('Sync failed:', error);
            setSyncStatus('error');
            setTimeout(() => setSyncStatus('idle'), 2000);
        }
    };

    const addToHomeScreen = () => {
        // iOS specific instructions
        if (deviceInfo.os === 'iOS') {
            alert('To add to home screen:\n1. Tap the Share button\n2. Select "Add to Home Screen"\n3. Tap "Add"');
        } else {
            // Android/Other
            installApp();
        }
    };

    const getSyncStatusIcon = () => {
        switch (syncStatus) {
            case 'syncing':
                return <LoadingSpinner size="sm" className="animate-spin" />;
            case 'success':
                return <Sync className="w-4 h-4 text-green-400" />;
            case 'error':
                return <Sync className="w-4 h-4 text-red-400" />;
            default:
                return <Sync className="w-4 h-4" />;
        }
    };

    const getDeviceIcon = () => {
        switch (deviceInfo.type) {
            case 'mobile':
                return <Smartphone className="w-5 h-5" />;
            case 'tablet':
                return <Tablet className="w-5 h-5" />;
            default:
                return <Monitor className="w-5 h-5" />;
        }
    };

    return (
        <div className="space-y-6">
            <div className="text-center">
                <h2 className="text-3xl font-bold text-purple-300 mb-4">
                    📱 Mobile Grimoire
                </h2>
                <p className="text-gray-300">
                    Enhanced mobile experience for your magical journey
                </p>
            </div>

            {/* Device Information */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        {getDeviceIcon()}
                        Device Information
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                        <div>
                            <div className="text-lg font-semibold text-purple-300">
                                {deviceInfo.type.charAt(0).toUpperCase() + deviceInfo.type.slice(1)}
                            </div>
                            <p className="text-sm text-slate-400">Device Type</p>
                        </div>
                        <div>
                            <div className="text-lg font-semibold text-purple-300">{deviceInfo.os}</div>
                            <p className="text-sm text-slate-400">Operating System</p>
                        </div>
                        <div>
                            <div className="text-lg font-semibold text-purple-300">{deviceInfo.browser}</div>
                            <p className="text-sm text-slate-400">Browser</p>
                        </div>
                        <div>
                            <div className={`text-lg font-semibold ${isInstalled ? 'text-green-400' : 'text-orange-400'}`}>
                                {isInstalled ? 'Installed' : 'Web App'}
                            </div>
                            <p className="text-sm text-slate-400">Status</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Installation */}
            {!isInstalled && (
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Download className="w-5 h-5" />
                            Install Mobile App
                        </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="text-center">
                            <div className="text-6xl mb-4">📲</div>
                            <h3 className="text-xl font-semibold text-purple-200 mb-2">
                                Install The Wizard's Grimoire
                            </h3>
                            <p className="text-slate-400 mb-6">
                                Get the full app experience with offline support, push notifications, and home screen access.
                            </p>

                            <div className="flex flex-col sm:flex-row gap-3 justify-center">
                                {installPrompt ? (
                                    <Button onClick={installApp} className="flex items-center gap-2">
                                        <Download className="w-4 h-4" />
                                        Install App
                                    </Button>
                                ) : (
                                    <Button onClick={addToHomeScreen} className="flex items-center gap-2">
                                        <Home className="w-4 h-4" />
                                        Add to Home Screen
                                    </Button>
                                )}

                                <Button onClick={shareApp} variant="outline" className="flex items-center gap-2">
                                    <Share className="w-4 h-4" />
                                    Share App
                                </Button>
                            </div>
                        </div>

                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">✨ App Benefits</h4>
                            <ul className="text-sm text-slate-400 space-y-1">
                                <li>• Works offline for uninterrupted habit tracking</li>
                                <li>• Push notifications for habit reminders</li>
                                <li>• Faster loading and smoother animations</li>
                                <li>• Home screen icon for quick access</li>
                                <li>• Native app-like experience</li>
                            </ul>
                        </div>
                    </CardContent>
                </Card>
            )}

            {/* Offline Support */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        {isOnline ? <Wifi className="w-5 h-5" /> : <WifiOff className="w-5 h-5" />}
                        Offline Support
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className={`font-medium ${isOnline ? 'text-green-400' : 'text-orange-400'}`}>
                                {isOnline ? 'Online' : 'Offline Mode'}
                            </h4>
                            <p className="text-sm text-slate-400">
                                {isOnline
                                    ? 'All features available, data syncing automatically'
                                    : 'Core features available, data will sync when online'
                                }
                            </p>
                        </div>
                        <Button
                            onClick={syncOfflineData}
                            disabled={!isOnline || syncStatus === 'syncing'}
                            variant="outline"
                            className="flex items-center gap-2"
                        >
                            {getSyncStatusIcon()}
                            Sync
                        </Button>
                    </div>

                    <div className="grid grid-cols-3 gap-4 text-center">
                        <div className="bg-slate-700/30 rounded-lg p-3">
                            <div className="text-lg font-semibold text-purple-300">{offlineData.habits}</div>
                            <p className="text-xs text-slate-400">Cached Habits</p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-3">
                            <div className="text-lg font-semibold text-orange-300">{offlineData.pendingSync}</div>
                            <p className="text-xs text-slate-400">Pending Sync</p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-3">
                            <div className="text-lg font-semibold text-green-300">
                                {offlineData.lastSync ? '✓' : '—'}
                            </div>
                            <p className="text-xs text-slate-400">Last Sync</p>
                        </div>
                    </div>

                    {offlineData.lastSync && (
                        <p className="text-xs text-slate-500 text-center">
                            Last synced: {offlineData.lastSync.toLocaleString()}
                        </p>
                    )}
                </CardContent>
            </Card>

            {/* Mobile Features */}
            <Card>
                <CardHeader>
                    <CardTitle>📲 Mobile Features</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">🔔 Push Notifications</h4>
                            <p className="text-sm text-slate-400">
                                Get reminded about your habits even when the app is closed.
                            </p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">📴 Offline Mode</h4>
                            <p className="text-sm text-slate-400">
                                Track habits without internet connection, sync when online.
                            </p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">🎨 Native UI</h4>
                            <p className="text-sm text-slate-400">
                                App-like interface optimized for touch interactions.
                            </p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">⚡ Fast Loading</h4>
                            <p className="text-sm text-slate-400">
                                Cached resources for instant app startup.
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Installation Instructions */}
            {!isInstalled && (
                <Card>
                    <CardHeader>
                        <CardTitle>📋 Installation Guide</CardTitle>
                    </CardHeader>
                    <CardContent>
                        {deviceInfo.os === 'iOS' ? (
                            <div className="space-y-3">
                                <h4 className="font-medium text-purple-200">For iPhone/iPad (Safari):</h4>
                                <ol className="text-sm text-slate-400 space-y-2 list-decimal list-inside">
                                    <li>Open this page in Safari browser</li>
                                    <li>Tap the Share button (square with arrow up)</li>
                                    <li>Scroll down and tap "Add to Home Screen"</li>
                                    <li>Customize the name if desired</li>
                                    <li>Tap "Add" to install</li>
                                </ol>
                            </div>
                        ) : deviceInfo.os === 'Android' ? (
                            <div className="space-y-3">
                                <h4 className="font-medium text-purple-200">For Android (Chrome):</h4>
                                <ol className="text-sm text-slate-400 space-y-2 list-decimal list-inside">
                                    <li>Look for the "Install app" popup at the bottom</li>
                                    <li>Or tap the menu (three dots) → "Add to Home screen"</li>
                                    <li>Tap "Install" to add to your home screen</li>
                                    <li>The app will behave like a native Android app</li>
                                </ol>
                            </div>
                        ) : (
                            <div className="space-y-3">
                                <h4 className="font-medium text-purple-200">For Desktop:</h4>
                                <ol className="text-sm text-slate-400 space-y-2 list-decimal list-inside">
                                    <li>Look for the install icon in your browser's address bar</li>
                                    <li>Or go to browser menu → "Install The Wizard's Grimoire"</li>
                                    <li>The app will be added to your desktop/dock</li>
                                    <li>Launch it like any other desktop application</li>
                                </ol>
                            </div>
                        )}
                    </CardContent>
                </Card>
            )}
        </div>
    );
};

export default MobileAppEnhancement;
