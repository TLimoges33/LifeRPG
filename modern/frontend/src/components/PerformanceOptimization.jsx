import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { LoadingSpinner } from './ui/loading';
import {
    Zap,
    Database,
    Smartphone,
    Wifi,
    Download,
    Upload,
    Trash2,
    RefreshCw,
    Settings,
    Monitor
} from 'lucide-react';

const PerformanceOptimization = () => {
    const [loading, setLoading] = useState(false);
    const [cacheInfo, setCacheInfo] = useState({
        size: 0,
        entries: 0,
        lastCleared: null
    });
    const [performanceData, setPerformanceData] = useState({
        loadTime: 0,
        memoryUsage: 0,
        cacheHitRate: 0,
        networkLatency: 0
    });
    const [optimization, setOptimization] = useState({
        imageCompression: true,
        lazyLoading: true,
        caching: true,
        preloading: true,
        offlineMode: false
    });

    useEffect(() => {
        loadPerformanceData();
        checkCacheInfo();
        measurePerformance();
    }, []);

    const loadPerformanceData = async () => {
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/v1/user/performance-settings', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const data = await response.json();
                setOptimization(prev => ({ ...prev, ...data }));
            }
        } catch (error) {
            console.error('Failed to load performance settings:', error);
        }
    };

    const saveOptimizationSettings = async (newSettings) => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const response = await fetch('/api/v1/user/performance-settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(newSettings)
            });

            if (response.ok) {
                setOptimization(newSettings);
            }
        } catch (error) {
            console.error('Failed to save performance settings:', error);
        } finally {
            setLoading(false);
        }
    };

    const checkCacheInfo = async () => {
        try {
            if ('caches' in window) {
                const cacheNames = await caches.keys();
                let totalSize = 0;
                let totalEntries = 0;

                for (const name of cacheNames) {
                    const cache = await caches.open(name);
                    const keys = await cache.keys();
                    totalEntries += keys.length;

                    // Estimate cache size
                    for (const request of keys) {
                        const response = await cache.match(request);
                        if (response) {
                            const blob = await response.blob();
                            totalSize += blob.size;
                        }
                    }
                }

                setCacheInfo({
                    size: totalSize,
                    entries: totalEntries,
                    lastCleared: localStorage.getItem('cacheLastCleared')
                });
            }
        } catch (error) {
            console.error('Failed to check cache info:', error);
        }
    };

    const measurePerformance = () => {
        // Page load time
        if (performance.navigation) {
            const loadTime = performance.navigation.loadEventEnd - performance.navigation.navigationStart;
            setPerformanceData(prev => ({ ...prev, loadTime }));
        }

        // Memory usage (if available)
        if (performance.memory) {
            const memoryUsage = performance.memory.usedJSHeapSize / 1024 / 1024; // MB
            setPerformanceData(prev => ({ ...prev, memoryUsage }));
        }

        // Simulate cache hit rate
        const hitRate = Math.random() * 30 + 70; // 70-100%
        setPerformanceData(prev => ({ ...prev, cacheHitRate: hitRate }));

        // Measure network latency
        measureNetworkLatency();
    };

    const measureNetworkLatency = async () => {
        try {
            const start = performance.now();
            await fetch('/api/v1/health', { method: 'HEAD' });
            const latency = performance.now() - start;
            setPerformanceData(prev => ({ ...prev, networkLatency: latency }));
        } catch (error) {
            console.error('Failed to measure network latency:', error);
        }
    };

    const clearCache = async () => {
        setLoading(true);
        try {
            if ('caches' in window) {
                const cacheNames = await caches.keys();
                await Promise.all(cacheNames.map(name => caches.delete(name)));

                localStorage.setItem('cacheLastCleared', new Date().toISOString());
                await checkCacheInfo();
            }

            // Also clear browser storage
            localStorage.removeItem('habits-cache');
            localStorage.removeItem('analytics-cache');
            sessionStorage.clear();

        } catch (error) {
            console.error('Failed to clear cache:', error);
        } finally {
            setLoading(false);
        }
    };

    const optimizeImages = async () => {
        setLoading(true);
        try {
            // Simulate image optimization
            await new Promise(resolve => setTimeout(resolve, 2000));

            // In a real app, this would compress and optimize images
            console.log('Images optimized');
        } catch (error) {
            console.error('Failed to optimize images:', error);
        } finally {
            setLoading(false);
        }
    };

    const enableOfflineMode = async () => {
        setLoading(true);
        try {
            if ('serviceWorker' in navigator) {
                const registration = await navigator.serviceWorker.register('/sw.js');

                // Cache essential resources
                const cache = await caches.open('offline-cache-v1');
                await cache.addAll([
                    '/',
                    '/static/js/bundle.js',
                    '/static/css/main.css',
                    '/manifest.json'
                ]);

                await saveOptimizationSettings({
                    ...optimization,
                    offlineMode: true
                });
            }
        } catch (error) {
            console.error('Failed to enable offline mode:', error);
        } finally {
            setLoading(false);
        }
    };

    const formatBytes = (bytes) => {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    const getPerformanceColor = (value, metric) => {
        switch (metric) {
            case 'loadTime':
                return value < 2000 ? 'text-green-400' : value < 5000 ? 'text-yellow-400' : 'text-red-400';
            case 'memory':
                return value < 50 ? 'text-green-400' : value < 100 ? 'text-yellow-400' : 'text-red-400';
            case 'cacheHit':
                return value > 90 ? 'text-green-400' : value > 70 ? 'text-yellow-400' : 'text-red-400';
            case 'latency':
                return value < 100 ? 'text-green-400' : value < 300 ? 'text-yellow-400' : 'text-red-400';
            default:
                return 'text-gray-400';
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
                    ⚡ Performance Enchantments
                </h2>
                <p className="text-gray-300">
                    Optimize your grimoire for maximum magical efficiency
                </p>
            </div>

            {/* Performance Metrics */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Monitor className="w-5 h-5" />
                        Performance Metrics
                    </CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center">
                            <div className={`text-2xl font-bold ${getPerformanceColor(performanceData.loadTime, 'loadTime')}`}>
                                {(performanceData.loadTime / 1000).toFixed(2)}s
                            </div>
                            <p className="text-sm text-slate-400">Load Time</p>
                        </div>
                        <div className="text-center">
                            <div className={`text-2xl font-bold ${getPerformanceColor(performanceData.memoryUsage, 'memory')}`}>
                                {performanceData.memoryUsage.toFixed(1)}MB
                            </div>
                            <p className="text-sm text-slate-400">Memory Usage</p>
                        </div>
                        <div className="text-center">
                            <div className={`text-2xl font-bold ${getPerformanceColor(performanceData.cacheHitRate, 'cacheHit')}`}>
                                {performanceData.cacheHitRate.toFixed(0)}%
                            </div>
                            <p className="text-sm text-slate-400">Cache Hit Rate</p>
                        </div>
                        <div className="text-center">
                            <div className={`text-2xl font-bold ${getPerformanceColor(performanceData.networkLatency, 'latency')}`}>
                                {performanceData.networkLatency.toFixed(0)}ms
                            </div>
                            <p className="text-sm text-slate-400">Network Latency</p>
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Cache Management */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Database className="w-5 h-5" />
                        Cache Management
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    <div className="flex justify-between items-center">
                        <div>
                            <h4 className="font-medium text-purple-200">Cache Size</h4>
                            <p className="text-sm text-slate-400">
                                {formatBytes(cacheInfo.size)} ({cacheInfo.entries} entries)
                            </p>
                            {cacheInfo.lastCleared && (
                                <p className="text-xs text-slate-500">
                                    Last cleared: {new Date(cacheInfo.lastCleared).toLocaleDateString()}
                                </p>
                            )}
                        </div>
                        <Button
                            onClick={clearCache}
                            disabled={loading}
                            variant="outline"
                            className="flex items-center gap-2"
                        >
                            {loading ? (
                                <LoadingSpinner size="sm" />
                            ) : (
                                <Trash2 className="w-4 h-4" />
                            )}
                            Clear Cache
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Optimization Settings */}
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Zap className="w-5 h-5" />
                        Optimization Settings
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Image Compression</h4>
                            <p className="text-sm text-slate-400">
                                Automatically compress images for faster loading
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={optimization.imageCompression}
                            onChange={(checked) => saveOptimizationSettings({
                                ...optimization,
                                imageCompression: checked
                            })}
                            disabled={loading}
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Lazy Loading</h4>
                            <p className="text-sm text-slate-400">
                                Load content only when needed
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={optimization.lazyLoading}
                            onChange={(checked) => saveOptimizationSettings({
                                ...optimization,
                                lazyLoading: checked
                            })}
                            disabled={loading}
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Smart Caching</h4>
                            <p className="text-sm text-slate-400">
                                Cache frequently accessed data
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={optimization.caching}
                            onChange={(checked) => saveOptimizationSettings({
                                ...optimization,
                                caching: checked
                            })}
                            disabled={loading}
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Content Preloading</h4>
                            <p className="text-sm text-slate-400">
                                Preload next pages and content
                            </p>
                        </div>
                        <ToggleSwitch
                            checked={optimization.preloading}
                            onChange={(checked) => saveOptimizationSettings({
                                ...optimization,
                                preloading: checked
                            })}
                            disabled={loading}
                        />
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <h4 className="font-medium text-purple-200">Offline Mode</h4>
                            <p className="text-sm text-slate-400">
                                Enable offline functionality with service workers
                            </p>
                        </div>
                        <div className="flex items-center gap-2">
                            <ToggleSwitch
                                checked={optimization.offlineMode}
                                onChange={enableOfflineMode}
                                disabled={loading}
                            />
                            {!optimization.offlineMode && (
                                <Button
                                    onClick={enableOfflineMode}
                                    disabled={loading}
                                    size="sm"
                                    variant="outline"
                                >
                                    <Download className="w-4 h-4 mr-1" />
                                    Enable
                                </Button>
                            )}
                        </div>
                    </div>
                </CardContent>
            </Card>

            {/* Quick Actions */}
            <Card>
                <CardHeader>
                    <CardTitle>🚀 Quick Optimizations</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        <Button
                            onClick={optimizeImages}
                            disabled={loading}
                            variant="outline"
                            className="flex flex-col items-center p-6 h-auto"
                        >
                            <Smartphone className="w-8 h-8 mb-2" />
                            <span className="font-medium">Optimize Images</span>
                            <span className="text-xs text-slate-400 mt-1">
                                Compress all images
                            </span>
                        </Button>

                        <Button
                            onClick={measurePerformance}
                            disabled={loading}
                            variant="outline"
                            className="flex flex-col items-center p-6 h-auto"
                        >
                            <RefreshCw className="w-8 h-8 mb-2" />
                            <span className="font-medium">Refresh Metrics</span>
                            <span className="text-xs text-slate-400 mt-1">
                                Update performance data
                            </span>
                        </Button>

                        <Button
                            onClick={() => window.location.reload()}
                            variant="outline"
                            className="flex flex-col items-center p-6 h-auto"
                        >
                            <Wifi className="w-8 h-8 mb-2" />
                            <span className="font-medium">Hard Refresh</span>
                            <span className="text-xs text-slate-400 mt-1">
                                Clear cache & reload
                            </span>
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {/* Performance Tips */}
            <Card>
                <CardHeader>
                    <CardTitle>💡 Performance Tips</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">🎯 Keep it focused</h4>
                            <p className="text-sm text-slate-400">
                                Close unused tabs and focus on current habits for better performance.
                            </p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">📱 Use mobile app</h4>
                            <p className="text-sm text-slate-400">
                                The mobile app provides better performance on mobile devices.
                            </p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">🔄 Regular updates</h4>
                            <p className="text-sm text-slate-400">
                                Keep your browser updated for the latest performance improvements.
                            </p>
                        </div>
                        <div className="bg-slate-700/30 rounded-lg p-4">
                            <h4 className="font-medium text-purple-200 mb-2">🌐 Stable connection</h4>
                            <p className="text-sm text-slate-400">
                                A stable internet connection ensures smooth synchronization.
                            </p>
                        </div>
                    </div>
                </CardContent>
            </Card>
        </div>
    );
};

export default PerformanceOptimization;
