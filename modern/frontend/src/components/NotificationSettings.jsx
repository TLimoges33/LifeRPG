import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { LoadingSpinner } from './ui/loading';
import { useNotifications } from '../hooks/useNotifications';
import { Bell, BellOff, Clock, Smartphone, Mail, Settings } from 'lucide-react';

const NotificationSettings = () => {
    const {
        permission,
        isSupported,
        requestPermission,
        subscribeToPush,
        unsubscribeFromPush,
        scheduleNotification
    } = useNotifications();

    const [settings, setSettings] = useState({
        dailyReminders: true,
        reminderTime: '09:00',
        weeklyReports: true,
        achievementAlerts: true,
        friendActivity: true,
        pushNotifications: false,
        emailNotifications: true
    });

    const [loading, setLoading] = useState(false);
    const [testNotification, setTestNotification] = useState(false);

    useEffect(() => {
        loadNotificationSettings();
    }, []);

    const loadNotificationSettings = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/v1/user/notification-settings', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setSettings(prev => ({ ...prev, ...data }));
            }
        } catch (error) {
            console.error('Failed to load notification settings:', error);
        }
    };

    const saveNotificationSettings = async (newSettings) => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/v1/user/notification-settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(newSettings)
            });

            if (response.ok) {
                setSettings(newSettings);
            }
        } catch (error) {
            console.error('Failed to save notification settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const handlePushNotificationToggle = async () => {
        if (!settings.pushNotifications) {
            // Enable push notifications
            const granted = await requestPermission();
            if (granted) {
                await subscribeToPush();
                await saveNotificationSettings({
                    ...settings,
                    pushNotifications: true
                });
            }
        } else {
            // Disable push notifications
            await unsubscribeFromPush();
            await saveNotificationSettings({
                ...settings,
                pushNotifications: false
            });
        }
    };

    const handleTestNotification = async () => {
        setTestNotification(true);
        try {
            if (isSupported && permission === 'granted') {
                await scheduleNotification(
                    '🧙‍♂️ Test Spell Alert!',
                    'This is a test notification from your magical grimoire!',
                    new Date(Date.now() + 1000) // 1 second from now
                );
            } else {
                // Fallback to browser notification
                new Notification('🧙‍♂️ Test Spell Alert!', {
                    body: 'This is a test notification from your magical grimoire!',
                    icon: '/icon-192x192.png'
                });
            }
        } catch (error) {
            console.error('Failed to send test notification:', error);
        } finally {
            setTimeout(() => setTestNotification(false), 2000);
        }
    };

    const ToggleSwitch = ({ checked, onChange, disabled = false }) => (
        <button
            onClick={() => !disabled && onChange(!checked)}
            disabled={disabled}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${checked ? 'bg-purple-600' : 'bg-gray-600'
                } ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}`}
        >
            <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${checked ? 'translate-x-6' : 'translate-x-1'
                    }`}
            />
        </button>
    );

    return (
        <div className="space-y-6">
            <div className="text-center">
                <h2 className="text-3xl font-bold text-purple-300 mb-4">
                    🔔 Notification Enchantments
                </h2>
                <p className="text-gray-300">
                    Configure how your grimoire communicates with you
                </p>
            </div>

            {/* Push Notification Status */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Smartphone className="w-5 h-5" />
                        Push Notifications
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {!isSupported ? (
                        <div className="bg-yellow-900/50 border border-yellow-500 text-yellow-200 px-4 py-3 rounded">
                            Push notifications are not supported in this browser.
                        </div>
                    ) : permission === 'denied' ? (
                        <div className="bg-red-900/50 border border-red-500 text-red-200 px-4 py-3 rounded">
                            Notifications are blocked. Please enable them in your browser settings.
                        </div>
                    ) : (
                        <div className="flex items-center justify-between">
                            <div>
                                <h4 className="font-medium text-purple-200">Enable Push Notifications</h4>
                                <p className="text-sm text-slate-400">
                                    Get reminders and updates even when the app is closed
                                </p>
                            </div>
                            <ToggleSwitch
                                checked={settings.pushNotifications}
                                onChange={handlePushNotificationToggle}
                                disabled={loading}
                            />
                        </div>
                    )}

                    {permission === 'granted' && (
                        <Button
                            onClick={handleTestNotification}
                            disabled={testNotification}
                            variant="outline"
                            className="w-full"
                        >
                            {testNotification ? (
                                <>
                                    <LoadingSpinner size="sm" className="mr-2" />
                                    Casting Test Spell...
                                </>
                            ) : (
                                <>
                                    <Bell className="w-4 h-4 mr-2" />
                                    Test Notification
                                </>
                            )}
                        </Button>
                    )}
                </CardContent>
            </Card>

            {/* Notification Preferences */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Settings className="w-5 h-5" />
                        Notification Preferences
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    {/* Daily Reminders */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Daily Spell Reminders</h4>
                            <p className="text-sm text-slate-400">
                                Get reminded to practice your daily habits
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={settings.dailyReminders}
                            onChange={(checked) => saveNotificationSettings({
                                ...settings,
                                dailyReminders: checked
                            })}
                            disabled={loading}
                        />
                    </div>

                    {/* Reminder Time */}
                    {settings.dailyReminders && (
                        <div className="ml-6 flex items-center gap-4">
                            <Clock className="w-4 h-4 text-slate-400" />
                            <div>
                                <label className="block text-sm text-purple-300 mb-1">Reminder Time</label>
                                <Input
                                    type="time"
                                    value={settings.reminderTime}
                                    onChange={(e) => saveNotificationSettings({
                                        ...settings,
                                        reminderTime: e.target.value
                                    })}
                                    className="w-32"
                                />
                            </div>
                        </div>
                    )}

                    {/* Weekly Reports */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Weekly Progress Reports</h4>
                            <p className="text-sm text-slate-400">
                                Receive a summary of your weekly magical progress
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={settings.weeklyReports}
                            onChange={(checked) => saveNotificationSettings({
                                ...settings,
                                weeklyReports: checked
                            })}
                            disabled={loading}
                        />
                    </div>

                    {/* Achievement Alerts */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Achievement Alerts</h4>
                            <p className="text-sm text-slate-400">
                                Get notified when you unlock new achievements
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={settings.achievementAlerts}
                            onChange={(checked) => saveNotificationSettings({
                                ...settings,
                                achievementAlerts: checked
                            })}
                            disabled={loading}
                        />
                    </div>

                    {/* Friend Activity */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Friend Activity</h4>
                            <p className="text-sm text-slate-400">
                                Get updates when friends complete challenges
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={settings.friendActivity}
                            onChange={(checked) => saveNotificationSettings({
                                ...settings,
                                friendActivity: checked
                            })}
                            disabled={loading}
                        />
                    </div>

                    {/* Email Notifications */}
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Email Notifications</h4>
                            <p className="text-sm text-slate-400">
                                Receive important updates via email
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={settings.emailNotifications}
                            onChange={(checked) => saveNotificationSettings({
                                ...settings,
                                emailNotifications: checked
                            })}
                            disabled={loading}
                        />
                    </div>
                </CardContent>
            </Card>

            {/* Notification Schedule */}
            <Card>
                <CardHeader>
                    <CardTitle>📅 Notification Schedule</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-center">
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <div className="text-2xl mb-2">🌅</div>
                            <h4 className="font-medium text-purple-200">Morning Boost</h4>
                            <p className="text-sm text-slate-400">Start your magical day</p>
                            <p className="text-xs text-purple-300 mt-1">{settings.reminderTime}</p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <div className="text-2xl mb-2">📊</div>
                            <h4 className="font-medium text-purple-200">Weekly Report</h4>
                            <p className="text-sm text-slate-400">Every Monday</p>
                            <p className="text-xs text-purple-300 mt-1">9:00 AM</p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <div className="text-2xl mb-2">🏆</div>
                            <h4 className="font-medium text-purple-200">Achievements</h4>
                            <p className="text-sm text-slate-400">Real-time</p>
                            <p className="text-xs text-purple-300 mt-1">Instant</p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default NotificationSettings;
