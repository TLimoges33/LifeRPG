import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Switch } from './ui/switch';
import { Badge } from './ui/badge';
import { Shield, Activity, Eye, BarChart } from 'lucide-react';

const TelemetrySettings = () => {
    const [consent, setConsent] = useState(false);
    const [globalEnabled, setGlobalEnabled] = useState(false);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    // Load current consent status
    useEffect(() => {
        fetchConsentStatus();
    }, []);

    const fetchConsentStatus = async () => {
        try {
            const response = await fetch('/api/v1/telemetry/consent', {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setConsent(data.consent);
                setGlobalEnabled(data.enabled_globally);
            }
        } catch (error) {
            console.error('Failed to fetch telemetry consent:', error);
        } finally {
            setLoading(false);
        }
    };

    const updateConsent = async (newConsent) => {
        setSaving(true);
        try {
            const response = await fetch('/api/v1/telemetry/consent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                },
                body: JSON.stringify({ consent: newConsent })
            });

            if (response.ok) {
                setConsent(newConsent);
            }
        } catch (error) {
            console.error('Failed to update telemetry consent:', error);
        } finally {
            setSaving(false);
        }
    };

    if (loading) {
        return (
            <Card>
                <CardContent className="p-6">
                    <div className="flex items-center space-x-2">
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-gray-900"></div>
                        <span>Loading telemetry settings...</span>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                    <Shield className="h-5 w-5" />
                    <span>Privacy & Telemetry</span>
                </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <div className="space-y-1">
                            <label className="text-sm font-medium">
                                Anonymous Usage Analytics
                            </label>
                            <p className="text-sm text-gray-600">
                                Help improve LifeRPG by sharing anonymous usage patterns
                            </p>
                        </div>
                        <Switch
                            checked={consent && globalEnabled}
                            onCheckedChange={updateConsent}
                            disabled={!globalEnabled || saving}
                        />
                    </div>

                    {!globalEnabled && (
                        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                            <p className="text-sm text-yellow-800">
                                <Shield className="h-4 w-4 inline mr-1" />
                                Telemetry is disabled globally by the administrator.
                            </p>
                        </div>
                    )}

                    {consent && globalEnabled && (
                        <div className="p-3 bg-green-50 border border-green-200 rounded-md">
                            <p className="text-sm text-green-800">
                                <Eye className="h-4 w-4 inline mr-1" />
                                Anonymous telemetry is enabled. Thank you for helping improve LifeRPG!
                            </p>
                        </div>
                    )}
                </div>

                <div className="space-y-3">
                    <h4 className="text-sm font-medium">What we collect:</h4>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="flex items-center space-x-2">
                            <Activity className="h-4 w-4 text-blue-500" />
                            <span className="text-sm">Feature usage patterns</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <BarChart className="h-4 w-4 text-blue-500" />
                            <span className="text-sm">Performance metrics</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Badge variant="outline" className="text-xs">Anonymous</Badge>
                            <span className="text-sm">No personal information</span>
                        </div>
                        <div className="flex items-center space-x-2">
                            <Badge variant="outline" className="text-xs">Optional</Badge>
                            <span className="text-sm">Can be disabled anytime</span>
                        </div>
                    </div>
                </div>

                <div className="pt-4 border-t">
                    <p className="text-xs text-gray-500">
                        All telemetry data is anonymous and used solely to improve the application.
                        No personal information, habit names, or content is ever collected.
                    </p>
                </div>
            </CardContent>
        </Card>
    );
};

export default TelemetrySettings;
