import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Calendar } from 'recharts';
import { TrendingUp, Calendar as CalendarIcon, BarChart3, Flame, RefreshCw } from 'lucide-react';
import { useTelemetry } from '../hooks/useTelemetry.jsx';

const AnalyticsDashboard = () => {
    const [heatmapData, setHeatmapData] = useState([]);
    const [trendsData, setTrendsData] = useState([]);
    const [breakdownData, setBreakdownData] = useState([]);
    const [insights, setInsights] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('heatmap');
    const [timeframe, setTimeframe] = useState('30');
    const { trackFeatureUsage } = useTelemetry();

    useEffect(() => {
        fetchAnalyticsData();
    }, [timeframe]);

    useEffect(() => {
        // Track feature usage when tab changes
        trackFeatureUsage(`analytics_${activeTab}`);
    }, [activeTab, trackFeatureUsage]);

    const fetchAnalyticsData = async () => {
        setLoading(true);
        try {
            const token = localStorage.getItem('token');
            const headers = { 'Authorization': `Bearer ${token}` };

            // Fetch all analytics data
            const [heatmapRes, trendsRes, breakdownRes, insightsRes] = await Promise.all([
                fetch(`/api/v1/analytics/heatmap?days=${timeframe}`, { headers }),
                fetch(`/api/v1/analytics/trends?days=${timeframe}`, { headers }),
                fetch(`/api/v1/analytics/breakdown?days=${timeframe}`, { headers }),
                fetch('/api/v1/analytics/insights', { headers })
            ]);

            if (heatmapRes.ok) {
                const heatmap = await heatmapRes.json();
                setHeatmapData(heatmap.data || []);
            }

            if (trendsRes.ok) {
                const trends = await trendsRes.json();
                setTrendsData(trends.data || []);
            }

            if (breakdownRes.ok) {
                const breakdown = await breakdownRes.json();
                setBreakdownData(breakdown.habits || []);
            }

            if (insightsRes.ok) {
                const insightsData = await insightsRes.json();
                setInsights(insightsData.insights || []);
            }
        } catch (error) {
            console.error('Failed to fetch analytics data:', error);
        } finally {
            setLoading(false);
        }
    };

    const HeatmapView = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                    <CalendarIcon className="h-5 w-5" />
                    <span>Completion Heatmap</span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                {heatmapData.length > 0 ? (
                    <div className="space-y-4">
                        <div className="grid grid-cols-7 gap-1 text-xs text-center font-medium text-gray-600">
                            <div>Sun</div>
                            <div>Mon</div>
                            <div>Tue</div>
                            <div>Wed</div>
                            <div>Thu</div>
                            <div>Fri</div>
                            <div>Sat</div>
                        </div>
                        <div className="grid grid-cols-7 gap-1">
                            {heatmapData.map((day, index) => {
                                const intensity = Math.min(day.completions / 5, 1); // Max out at 5 completions
                                const bgIntensity = Math.round(intensity * 4); // 0-4 scale

                                return (
                                    <div
                                        key={index}
                                        className={`h-8 w-8 rounded text-xs flex items-center justify-center transition-all hover:scale-110 cursor-pointer ${bgIntensity === 0 ? 'bg-gray-100' :
                                                bgIntensity === 1 ? 'bg-green-100 text-green-800' :
                                                    bgIntensity === 2 ? 'bg-green-300 text-green-900' :
                                                        bgIntensity === 3 ? 'bg-green-500 text-white' :
                                                            'bg-green-700 text-white'
                                            }`}
                                        title={`${day.date}: ${day.completions} completions`}
                                    >
                                        {day.completions > 0 ? day.completions : ''}
                                    </div>
                                );
                            })}
                        </div>
                        <div className="flex items-center space-x-2 text-xs text-gray-600">
                            <span>Less</span>
                            <div className="flex space-x-1">
                                <div className="h-3 w-3 bg-gray-100 rounded"></div>
                                <div className="h-3 w-3 bg-green-100 rounded"></div>
                                <div className="h-3 w-3 bg-green-300 rounded"></div>
                                <div className="h-3 w-3 bg-green-500 rounded"></div>
                                <div className="h-3 w-3 bg-green-700 rounded"></div>
                            </div>
                            <span>More</span>
                        </div>
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        <CalendarIcon className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p>No completion data available</p>
                    </div>
                )}
            </CardContent>
        </Card>
    );

    const TrendsView = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                    <TrendingUp className="h-5 w-5" />
                    <span>Completion Trends</span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                {trendsData.length > 0 ? (
                    <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trendsData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="date"
                                    tickFormatter={(date) => new Date(date).toLocaleDateString()}
                                />
                                <YAxis />
                                <Tooltip
                                    labelFormatter={(date) => new Date(date).toLocaleDateString()}
                                    formatter={(value) => [value, 'Completions']}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="completions"
                                    stroke="#8884d8"
                                    strokeWidth={2}
                                    dot={{ fill: '#8884d8' }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        <TrendingUp className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p>No trend data available</p>
                    </div>
                )}
            </CardContent>
        </Card>
    );

    const BreakdownView = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                    <BarChart3 className="h-5 w-5" />
                    <span>Habit Breakdown</span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                {breakdownData.length > 0 ? (
                    <div className="h-80">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={breakdownData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis
                                    dataKey="title"
                                    angle={-45}
                                    textAnchor="end"
                                    height={80}
                                    fontSize={12}
                                />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="completions" fill="#82ca9d" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        <BarChart3 className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p>No habit data available</p>
                    </div>
                )}
            </CardContent>
        </Card>
    );

    const InsightsView = () => (
        <Card>
            <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                    <Flame className="h-5 w-5" />
                    <span>Performance Insights</span>
                </CardTitle>
            </CardHeader>
            <CardContent>
                {insights.length > 0 ? (
                    <div className="space-y-4">
                        {insights.map((insight, index) => (
                            <div key={index} className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                                <h4 className="font-medium text-blue-900 mb-2">{insight.title}</h4>
                                <p className="text-blue-800">{insight.description}</p>
                                {insight.suggestion && (
                                    <p className="text-sm text-blue-600 mt-2">
                                        💡 <strong>Suggestion:</strong> {insight.suggestion}
                                    </p>
                                )}
                            </div>
                        ))}
                    </div>
                ) : (
                    <div className="text-center py-8 text-gray-500">
                        <Flame className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                        <p>Complete more habits to get personalized insights!</p>
                    </div>
                )}
            </CardContent>
        </Card>
    );

    if (loading) {
        return (
            <div className="space-y-6">
                <div className="animate-pulse">
                    <div className="h-8 bg-gray-200 rounded w-64 mb-4"></div>
                    <div className="h-64 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold">Analytics Dashboard</h1>
                    <p className="text-gray-600">Track your habit completion patterns and insights</p>
                </div>

                <div className="flex items-center space-x-3">
                    <Select value={timeframe} onValueChange={setTimeframe}>
                        <SelectTrigger className="w-32">
                            <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                            <SelectItem value="7">Last 7 days</SelectItem>
                            <SelectItem value="30">Last 30 days</SelectItem>
                            <SelectItem value="90">Last 90 days</SelectItem>
                            <SelectItem value="365">Last year</SelectItem>
                        </SelectContent>
                    </Select>

                    <Button variant="outline" size="sm" onClick={fetchAnalyticsData}>
                        <RefreshCw className="h-4 w-4 mr-2" />
                        Refresh
                    </Button>
                </div>
            </div>

            {/* Tab Navigation */}
            <div className="flex space-x-1 border-b">
                {[
                    { key: 'heatmap', label: 'Heatmap', icon: CalendarIcon },
                    { key: 'trends', label: 'Trends', icon: TrendingUp },
                    { key: 'breakdown', label: 'Breakdown', icon: BarChart3 },
                    { key: 'insights', label: 'Insights', icon: Flame }
                ].map(({ key, label, icon: Icon }) => (
                    <button
                        key={key}
                        onClick={() => setActiveTab(key)}
                        className={`flex items-center space-x-2 px-4 py-2 border-b-2 transition-colors ${activeTab === key
                                ? 'border-blue-500 text-blue-600'
                                : 'border-transparent text-gray-600 hover:text-gray-900'
                            }`}
                    >
                        <Icon className="h-4 w-4" />
                        <span>{label}</span>
                    </button>
                ))}
            </div>

            {/* Tab Content */}
            {activeTab === 'heatmap' && <HeatmapView />}
            {activeTab === 'trends' && <TrendsView />}
            {activeTab === 'breakdown' && <BreakdownView />}
            {activeTab === 'insights' && <InsightsView />}
        </div>
    );
};

export default AnalyticsDashboard;
