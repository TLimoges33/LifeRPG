import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, Users, Eye, TrendingUp, RefreshCw } from 'lucide-react';

const AdminTelemetryDashboard = () => {
    const [stats, setStats] = useState(null);
    const [loading, setLoading] = useState(true);
    const [refreshing, setRefreshing] = useState(false);
    const [timeframe, setTimeframe] = useState('30');

    useEffect(() => {
        fetchTelemetryStats();
    }, [timeframe]);

    const fetchTelemetryStats = async () => {
        setLoading(true);
        try {
            const response = await fetch(`/api/v1/admin/telemetry/stats?days=${timeframe}`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('token')}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                setStats(data);
            }
        } catch (error) {
            console.error('Failed to fetch telemetry stats:', error);
        } finally {
            setLoading(false);
            setRefreshing(false);
        }
    };

    const handleRefresh = () => {
        setRefreshing(true);
        fetchTelemetryStats();
    };

    if (loading && !stats) {
        return (
            <div className="p-6">
                <div className="flex items-center space-x-2 mb-6">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-gray-900"></div>
                    <span>Loading telemetry dashboard...</span>
                </div>
            </div>
        );
    }

    if (!stats) {
        return (
            <div className="p-6">
                <Card>
                    <CardContent className="p-6 text-center">
                        <Eye className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                        <h3 className="text-lg font-medium mb-2">No Telemetry Data</h3>
                        <p className="text-gray-600">No telemetry data available for the selected period.</p>
                    </CardContent>
                </Card>
            </div>
        );
    }

    // Prepare chart data
    const eventChartData = Object.entries(stats.events_by_type).map(([name, count]) => ({
        name: name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        count
    }));

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

    return (
        <div className="p-6 space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-bold flex items-center space-x-2">
                        <Activity className="h-6 w-6" />
                        <span>Telemetry Dashboard</span>
                    </h1>
                    <p className="text-gray-600">Anonymous usage analytics and insights</p>
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
                        </SelectContent>
                    </Select>

                    <Button
                        variant="outline"
                        size="sm"
                        onClick={handleRefresh}
                        disabled={refreshing}
                    >
                        <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
                        Refresh
                    </Button>
                </div>
            </div>

            {/* Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center space-x-2">
                            <Activity className="h-8 w-8 text-blue-500" />
                            <div>
                                <p className="text-2xl font-bold">{stats.total_events.toLocaleString()}</p>
                                <p className="text-sm text-gray-600">Total Events</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center space-x-2">
                            <Users className="h-8 w-8 text-green-500" />
                            <div>
                                <p className="text-2xl font-bold">{stats.unique_users.toLocaleString()}</p>
                                <p className="text-sm text-gray-600">Active Users</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center space-x-2">
                            <TrendingUp className="h-8 w-8 text-purple-500" />
                            <div>
                                <p className="text-2xl font-bold">
                                    {stats.total_events > 0 ? Math.round(stats.total_events / stats.unique_users) : 0}
                                </p>
                                <p className="text-sm text-gray-600">Events per User</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="p-6">
                        <div className="flex items-center space-x-2">
                            <Eye className="h-8 w-8 text-orange-500" />
                            <div>
                                <p className="text-2xl font-bold">{stats.telemetry_enabled ? 'Enabled' : 'Disabled'}</p>
                                <p className="text-sm text-gray-600">Global Status</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Event Types Bar Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Event Types</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={eventChartData}>
                                    <CartesianGrid strokeDasharray="3 3" />
                                    <XAxis
                                        dataKey="name"
                                        angle={-45}
                                        textAnchor="end"
                                        height={80}
                                        fontSize={12}
                                    />
                                    <YAxis />
                                    <Tooltip />
                                    <Bar dataKey="count" fill="#8884d8" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>

                {/* Event Distribution Pie Chart */}
                <Card>
                    <CardHeader>
                        <CardTitle>Event Distribution</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <div className="h-80">
                            <ResponsiveContainer width="100%" height="100%">
                                <PieChart>
                                    <Pie
                                        data={eventChartData}
                                        cx="50%"
                                        cy="50%"
                                        labelLine={false}
                                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                        outerRadius={80}
                                        fill="#8884d8"
                                        dataKey="count"
                                    >
                                        {eventChartData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                        ))}
                                    </Pie>
                                    <Tooltip />
                                </PieChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Event Details Table */}
            <Card>
                <CardHeader>
                    <CardTitle>Event Breakdown</CardTitle>
                </CardHeader>
                <CardContent>
                    <div className="overflow-x-auto">
                        <table className="w-full text-sm">
                            <thead>
                                <tr className="border-b">
                                    <th className="text-left p-2">Event Type</th>
                                    <th className="text-right p-2">Count</th>
                                    <th className="text-right p-2">Percentage</th>
                                </tr>
                            </thead>
                            <tbody>
                                {Object.entries(stats.events_by_type)
                                    .sort(([, a], [, b]) => b - a)
                                    .map(([eventType, count]) => (
                                        <tr key={eventType} className="border-b">
                                            <td className="p-2 font-medium">
                                                {eventType.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                            </td>
                                            <td className="p-2 text-right">{count.toLocaleString()}</td>
                                            <td className="p-2 text-right">
                                                {((count / stats.total_events) * 100).toFixed(1)}%
                                            </td>
                                        </tr>
                                    ))
                                }
                            </tbody>
                        </table>
                    </div>
                </CardContent>
            </Card>

            <div className="text-sm text-gray-500 border-t pt-4">
                <p>
                    📊 Data period: Last {timeframe} days •
                    Last updated: {new Date().toLocaleString()} •
                    All data is anonymous and aggregated
                </p>
            </div>
        </div>
    );
};

export default AdminTelemetryDashboard;
