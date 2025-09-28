import React, { useState, useEffect } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import {
  Brain,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle,
  Clock,
  Target,
  Lightbulb,
  BarChart3,
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

const PredictiveAnalyticsUI = ({ userId }) => {
  const [predictions, setPredictions] = useState([]);
  const [patterns, setPatterns] = useState(null);
  const [suggestions, setSuggestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedHabit, setSelectedHabit] = useState(null);

  useEffect(() => {
    loadAnalytics();
  }, [userId]);

  const loadAnalytics = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };

      // Load pattern analysis
      const patternsRes = await fetch("/api/v1/ai/habits/analyze-patterns", {
        headers,
      });
      if (patternsRes.ok) {
        const patternsData = await patternsRes.json();
        setPatterns(patternsData);
      }

      // Load AI suggestions
      const suggestionsRes = await fetch("/api/v1/ai/habits/suggestions", {
        headers,
      });
      if (suggestionsRes.ok) {
        const suggestionsData = await suggestionsRes.json();
        setSuggestions(suggestionsData.suggestions || []);
      }
    } catch (error) {
      console.error("Failed to load analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  const predictHabitSuccess = async (habitId) => {
    try {
      const token = localStorage.getItem("token");
      const res = await fetch(
        `/api/v1/ai/habits/predict-success?habit_id=${habitId}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (res.ok) {
        const data = await res.json();
        setSelectedHabit({ id: habitId, prediction: data.prediction });
      }
    } catch (error) {
      console.error("Failed to predict habit success:", error);
    }
  };

  const getSuccessProbabilityColor = (probability) => {
    if (probability >= 0.8) return "text-green-600";
    if (probability >= 0.6) return "text-yellow-600";
    return "text-red-600";
  };

  const getSuccessProbabilityIcon = (probability) => {
    if (probability >= 0.8)
      return <CheckCircle className="h-5 w-5 text-green-600" />;
    if (probability >= 0.6)
      return <Clock className="h-5 w-5 text-yellow-600" />;
    return <AlertTriangle className="h-5 w-5 text-red-600" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-pulse">
          <Brain className="h-8 w-8 text-purple-500 animate-bounce" />
        </div>
        <span className="ml-2">Analyzing your habits with AI...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* AI Insights Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-6 w-6 text-purple-600" />
            AI-Powered Habit Analytics
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-gray-600">
            Using advanced AI models to analyze your habit patterns and predict
            success rates.
          </p>
        </CardContent>
      </Card>

      {/* Pattern Analysis */}
      {patterns && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-blue-600" />
              Your Habit Patterns
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Best Time Pattern */}
            {patterns.patterns?.best_time_of_day?.best_hour && (
              <div className="p-4 bg-blue-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Clock className="h-4 w-4 text-blue-600" />
                  <span className="font-semibold text-blue-800">
                    Optimal Time
                  </span>
                </div>
                <p className="text-blue-700">
                  You're most successful at{" "}
                  {patterns.patterns.best_time_of_day.best_hour}:00 (
                  {patterns.patterns.best_time_of_day.success_count}{" "}
                  completions)
                </p>
              </div>
            )}

            {/* Success by Difficulty */}
            {patterns.patterns?.success_by_difficulty && (
              <div className="p-4 bg-green-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Target className="h-4 w-4 text-green-600" />
                  <span className="font-semibold text-green-800">
                    Difficulty Performance
                  </span>
                </div>
                <div className="space-y-2">
                  {Object.entries(patterns.patterns.success_by_difficulty).map(
                    ([difficulty, rate]) => (
                      <div
                        key={difficulty}
                        className="flex items-center justify-between"
                      >
                        <span className="text-green-700 capitalize">
                          {difficulty.replace("_", " ")}
                        </span>
                        <div className="flex items-center gap-2">
                          <Progress value={rate * 100} className="w-20" />
                          <span className="text-sm font-mono">
                            {Math.round(rate * 100)}%
                          </span>
                        </div>
                      </div>
                    )
                  )}
                </div>
              </div>
            )}

            {/* AI Insights */}
            {patterns.insights && patterns.insights.length > 0 && (
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <Lightbulb className="h-4 w-4 text-purple-600" />
                  <span className="font-semibold text-purple-800">
                    AI Insights
                  </span>
                </div>
                <ul className="space-y-1">
                  {patterns.insights.map((insight, index) => (
                    <li key={index} className="text-purple-700 text-sm">
                      • {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Recommendations */}
            {patterns.recommendations &&
              patterns.recommendations.length > 0 && (
                <div className="p-4 bg-orange-50 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <TrendingUp className="h-4 w-4 text-orange-600" />
                    <span className="font-semibold text-orange-800">
                      AI Recommendations
                    </span>
                  </div>
                  <ul className="space-y-1">
                    {patterns.recommendations.map((rec, index) => (
                      <li key={index} className="text-orange-700 text-sm">
                        • {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
          </CardContent>
        </Card>
      )}

      {/* AI Habit Suggestions */}
      {suggestions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-yellow-600" />
              AI Habit Suggestions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3">
              {suggestions.map((suggestion, index) => (
                <div
                  key={index}
                  className="p-3 border rounded-lg hover:bg-gray-50"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{suggestion}</span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => {
                        // Could integrate with habit creation
                        console.log("Create habit:", suggestion);
                      }}
                    >
                      Add Habit
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Habit Success Prediction */}
      {selectedHabit && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-600" />
              Success Prediction
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-4">
              {getSuccessProbabilityIcon(
                selectedHabit.prediction.success_probability
              )}
              <div className="flex-1">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold">Success Probability</span>
                  <span
                    className={`font-mono text-lg ${getSuccessProbabilityColor(
                      selectedHabit.prediction.success_probability
                    )}`}
                  >
                    {Math.round(
                      selectedHabit.prediction.success_probability * 100
                    )}
                    %
                  </span>
                </div>
                <Progress
                  value={selectedHabit.prediction.success_probability * 100}
                  className="h-3"
                />
              </div>
            </div>

            {selectedHabit.prediction.insights &&
              selectedHabit.prediction.insights.length > 0 && (
                <div className="p-3 bg-blue-50 rounded-lg">
                  <h4 className="font-semibold text-blue-800 mb-2">
                    AI Insights
                  </h4>
                  <ul className="space-y-1">
                    {selectedHabit.prediction.insights.map((insight, index) => (
                      <li key={index} className="text-blue-700 text-sm">
                        • {insight}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

            {selectedHabit.prediction.recommended_adjustments &&
              selectedHabit.prediction.recommended_adjustments.length > 0 && (
                <div className="p-3 bg-green-50 rounded-lg">
                  <h4 className="font-semibold text-green-800 mb-2">
                    Recommended Improvements
                  </h4>
                  <ul className="space-y-1">
                    {selectedHabit.prediction.recommended_adjustments.map(
                      (adjustment, index) => (
                        <li key={index} className="text-green-700 text-sm">
                          • {adjustment}
                        </li>
                      )
                    )}
                  </ul>
                </div>
              )}
          </CardContent>
        </Card>
      )}

      {/* Test Prediction Button */}
      <Card>
        <CardHeader>
          <CardTitle>Test Habit Prediction</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-2">
            <Button onClick={() => predictHabitSuccess(1)} variant="outline">
              Predict Habit #1
            </Button>
            <Button onClick={() => predictHabitSuccess(2)} variant="outline">
              Predict Habit #2
            </Button>
          </div>
          <p className="text-sm text-gray-600 mt-2">
            Click to see AI predictions for your habits
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default PredictiveAnalyticsUI;
