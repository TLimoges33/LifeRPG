import React, { useState, useEffect, useMemo, useCallback } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { LoadingSpinner } from "./ui/loading";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  AreaChart,
  Area,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  HeatMap,
  ScatterChart,
  Scatter,
} from "recharts";
import {
  Calendar,
  TrendingUp,
  Award,
  Target,
  Clock,
  BarChart3,
  PieChart as PieChartIcon,
  Activity,
  Filter,
  Download,
  RefreshCw,
  Zap,
} from "lucide-react";

const COLORS = {
  primary: "#8B5CF6",
  secondary: "#06B6D4",
  success: "#10B981",
  warning: "#F59E0B",
  error: "#EF4444",
  info: "#3B82F6",
};

const CHART_COLORS = [
  "#8B5CF6",
  "#06B6D4",
  "#10B981",
  "#F59E0B",
  "#EF4444",
  "#3B82F6",
  "#8B5A2B",
  "#EC4899",
];

// Advanced Analytics Dashboard Component
const AdvancedAnalyticsDashboard = ({ userId }) => {
  const [analyticsData, setAnalyticsData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState("30d");
  const [selectedMetrics, setSelectedMetrics] = useState([
    "completion_rate",
    "streaks",
    "categories",
    "difficulty",
  ]);
  const [refreshing, setRefreshing] = useState(false);

  // Fetch analytics data
  const fetchAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem("token");
      const response = await fetch(
        `/api/v1/analytics/advanced?time_range=${timeRange}&metrics=${selectedMetrics.join(
          ","
        )}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setAnalyticsData(data);
      } else {
        throw new Error("Failed to fetch analytics data");
      }
    } catch (error) {
      console.error("Analytics fetch error:", error);
      setError(error.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [timeRange, selectedMetrics]);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  const handleRefresh = useCallback(async () => {
    setRefreshing(true);
    await fetchAnalytics();
  }, [fetchAnalytics]);

  // Export analytics data
  const exportData = useCallback(
    async (format = "json") => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch(
          `/api/v1/analytics/export?format=${format}&time_range=${timeRange}`,
          {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.ok) {
          const blob = await response.blob();
          const url = window.URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `habit-analytics-${timeRange}.${format}`;
          a.click();
          window.URL.revokeObjectURL(url);
        }
      } catch (error) {
        console.error("Export error:", error);
      }
    },
    [timeRange]
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
        <span className="ml-2">Loading analytics dashboard...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-red-500 mb-2">⚠️ Error loading analytics</div>
          <p className="text-gray-600">{error}</p>
          <Button onClick={handleRefresh} className="mt-4">
            <RefreshCw className="h-4 w-4 mr-2" />
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header with controls */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                📊 Advanced Analytics
              </h2>
              <p className="text-gray-600">
                Deep insights into your habit patterns and progress
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Button
                onClick={handleRefresh}
                variant="outline"
                size="sm"
                disabled={refreshing}
              >
                <RefreshCw
                  className={`h-4 w-4 mr-2 ${refreshing ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
              <Button
                onClick={() => exportData("csv")}
                variant="outline"
                size="sm"
              >
                <Download className="h-4 w-4 mr-2" />
                Export CSV
              </Button>
            </div>
          </div>

          {/* Time range and metric filters */}
          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2">
              <Calendar className="h-4 w-4" />
              <select
                value={timeRange}
                onChange={(e) => setTimeRange(e.target.value)}
                className="px-3 py-1 border rounded-md text-sm"
              >
                <option value="7d">Last 7 days</option>
                <option value="30d">Last 30 days</option>
                <option value="90d">Last 90 days</option>
                <option value="1y">Last year</option>
                <option value="all">All time</option>
              </select>
            </div>

            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4" />
              <span className="text-sm">Metrics:</span>
              {[
                { key: "completion_rate", label: "Completion" },
                { key: "streaks", label: "Streaks" },
                { key: "categories", label: "Categories" },
                { key: "difficulty", label: "Difficulty" },
              ].map((metric) => (
                <label key={metric.key} className="flex items-center text-sm">
                  <input
                    type="checkbox"
                    checked={selectedMetrics.includes(metric.key)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedMetrics([...selectedMetrics, metric.key]);
                      } else {
                        setSelectedMetrics(
                          selectedMetrics.filter((m) => m !== metric.key)
                        );
                      }
                    }}
                    className="mr-1"
                  />
                  {metric.label}
                </label>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Performance Indicators */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <MetricCard
          title="Overall Progress"
          value={`${
            analyticsData?.kpis?.overall_completion_rate?.toFixed(1) || 0
          }%`}
          change={analyticsData?.kpis?.completion_rate_change}
          icon={<TrendingUp className="h-5 w-5" />}
          color="success"
        />
        <MetricCard
          title="Active Streaks"
          value={analyticsData?.kpis?.active_streaks || 0}
          change={analyticsData?.kpis?.streak_change}
          icon={<Zap className="h-5 w-5" />}
          color="warning"
        />
        <MetricCard
          title="Achievements"
          value={analyticsData?.kpis?.total_achievements || 0}
          change={analyticsData?.kpis?.achievement_change}
          icon={<Award className="h-5 w-5" />}
          color="primary"
        />
        <MetricCard
          title="Categories Active"
          value={analyticsData?.kpis?.active_categories || 0}
          change={analyticsData?.kpis?.category_change}
          icon={<Target className="h-5 w-5" />}
          color="info"
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Completion Rate Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Completion Rate Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={analyticsData?.completion_trend || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line
                  type="monotone"
                  dataKey="completion_rate"
                  stroke={COLORS.primary}
                  strokeWidth={2}
                  dot={{ fill: COLORS.primary, strokeWidth: 2, r: 4 }}
                />
                <Line
                  type="monotone"
                  dataKey="target_rate"
                  stroke={COLORS.secondary}
                  strokeDasharray="5 5"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Habit Category Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <PieChartIcon className="h-5 w-5 mr-2" />
              Habit Categories
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={analyticsData?.category_distribution || []}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) =>
                    `${name} ${(percent * 100).toFixed(0)}%`
                  }
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="count"
                >
                  {(analyticsData?.category_distribution || []).map(
                    (entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={CHART_COLORS[index % CHART_COLORS.length]}
                      />
                    )
                  )}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Weekly Activity Heatmap */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Activity className="h-5 w-5 mr-2" />
              Weekly Activity Pattern
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {(analyticsData?.weekly_heatmap || []).map((week, weekIndex) => (
                <div key={weekIndex} className="flex space-x-1">
                  {week.map((day, dayIndex) => (
                    <div
                      key={dayIndex}
                      className="w-4 h-4 rounded-sm"
                      style={{
                        backgroundColor:
                          day.intensity > 0
                            ? `rgba(139, 92, 246, ${day.intensity})`
                            : "#f3f4f6",
                      }}
                      title={`${day.date}: ${day.completions} completions`}
                    />
                  ))}
                </div>
              ))}
              <div className="flex items-center justify-between text-xs text-gray-500 mt-2">
                <span>Less</span>
                <div className="flex space-x-1">
                  {[0, 0.25, 0.5, 0.75, 1].map((intensity) => (
                    <div
                      key={intensity}
                      className="w-3 h-3 rounded-sm"
                      style={{
                        backgroundColor:
                          intensity > 0
                            ? `rgba(139, 92, 246, ${intensity})`
                            : "#f3f4f6",
                      }}
                    />
                  ))}
                </div>
                <span>More</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Difficulty vs Success Rate */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <BarChart3 className="h-5 w-5 mr-2" />
              Difficulty vs Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={analyticsData?.difficulty_analysis || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="difficulty" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="success_rate" fill={COLORS.success} />
                <Bar dataKey="habit_count" fill={COLORS.info} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Time of Day Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Clock className="h-5 w-5 mr-2" />
              Peak Performance Times
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={analyticsData?.hourly_performance || []}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="hour" tickFormatter={(hour) => `${hour}:00`} />
                <YAxis />
                <Tooltip
                  labelFormatter={(hour) => `${hour}:00 - ${hour + 1}:00`}
                />
                <Area
                  type="monotone"
                  dataKey="completions"
                  stroke={COLORS.secondary}
                  fill={COLORS.secondary}
                  fillOpacity={0.6}
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Streak Analysis */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Zap className="h-5 w-5 mr-2" />
              Streak Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {(analyticsData?.streak_analysis || []).map((habit, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-sm">{habit.title}</span>
                    <span className="text-sm text-gray-500">
                      {habit.current_streak} days
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-gradient-to-r from-yellow-400 to-orange-500 h-2 rounded-full"
                      style={{
                        width: `${Math.min(
                          (habit.current_streak / habit.best_streak) * 100,
                          100
                        )}%`,
                      }}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-gray-500">
                    <span>Best: {habit.best_streak} days</span>
                    <span>Average: {habit.average_streak} days</span>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* AI Insights Section */}
      {analyticsData?.ai_insights && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              🤖 AI-Powered Insights
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {analyticsData.ai_insights.map((insight, index) => (
                <div
                  key={index}
                  className="p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-200"
                >
                  <h4 className="font-semibold text-purple-900 mb-2">
                    {insight.title}
                  </h4>
                  <p className="text-sm text-purple-700 mb-3">
                    {insight.description}
                  </p>
                  <div className="space-y-1">
                    {insight.recommendations.map((rec, recIndex) => (
                      <div
                        key={recIndex}
                        className="text-xs text-purple-600 flex items-start"
                      >
                        <span className="mr-1">•</span>
                        <span>{rec}</span>
                      </div>
                    ))}
                  </div>
                  <div className="mt-3 text-xs text-purple-500">
                    Confidence: {(insight.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Metric card component
const MetricCard = ({ title, value, change, icon, color }) => {
  const colorClasses = {
    primary: "text-purple-600 bg-purple-100",
    success: "text-green-600 bg-green-100",
    warning: "text-yellow-600 bg-yellow-100",
    error: "text-red-600 bg-red-100",
    info: "text-blue-600 bg-blue-100",
  };

  const changeColor =
    change > 0
      ? "text-green-600"
      : change < 0
      ? "text-red-600"
      : "text-gray-500";

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">{title}</p>
            <p className="text-2xl font-bold text-gray-900">{value}</p>
            {change !== undefined && (
              <p className={`text-sm ${changeColor}`}>
                {change > 0 ? "+" : ""}
                {change}%
                <span className="text-gray-500 ml-1">vs last period</span>
              </p>
            )}
          </div>
          <div className={`p-3 rounded-full ${colorClasses[color]}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default AdvancedAnalyticsDashboard;
