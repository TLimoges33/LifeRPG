import React, { useState, useEffect, useCallback, useMemo } from "react";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  CheckCircle2,
  Clock,
  Flame,
  Star,
  Target,
  TrendingUp,
  Calendar,
  Plus,
  Settings,
  Smartphone,
  Bell,
  Zap,
  Award,
} from "lucide-react";

// Mobile-first habit tracker component
const MobileHabitTracker = ({ userId, isMobile = false }) => {
  const [habits, setHabits] = useState([]);
  const [todayStats, setTodayStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [selectedHabit, setSelectedHabit] = useState(null);
  const [showQuickAdd, setShowQuickAdd] = useState(false);
  const [notifications, setNotifications] = useState([]);

  // Touch/swipe handling for mobile
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);

  // Load data
  useEffect(() => {
    loadHabits();
    loadTodayStats();
    if (isMobile) {
      setupNotifications();
    }
  }, [userId, isMobile]);

  const loadHabits = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("/api/v1/habits/today", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setHabits(data);
      }
    } catch (error) {
      console.error("Failed to load habits:", error);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadTodayStats = useCallback(async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("/api/v1/analytics/today", {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setTodayStats(data);
      }
    } catch (error) {
      console.error("Failed to load today stats:", error);
    }
  }, []);

  const setupNotifications = useCallback(() => {
    if ("serviceWorker" in navigator && "Notification" in window) {
      // Request notification permissions
      Notification.requestPermission().then((permission) => {
        if (permission === "granted") {
          // Setup WebSocket for real-time notifications
          const ws = new WebSocket(`ws://localhost:8000/ws/${userId}`);

          ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === "notification") {
              showNotification(data.notification);
            }
          };
        }
      });
    }
  }, [userId]);

  const showNotification = useCallback((notification) => {
    if (Notification.permission === "granted") {
      new Notification(notification.title, {
        body: notification.message,
        icon: "/icon-192.png",
        badge: "/badge-72.png",
        tag: notification.id,
        requireInteraction: notification.priority === "high",
      });
    }

    // Add to in-app notifications
    setNotifications((prev) => [notification, ...prev.slice(0, 4)]);
  }, []);

  // Swipe gesture handling
  const onTouchStart = useCallback((e) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  }, []);

  const onTouchMove = useCallback((e) => {
    setTouchEnd(e.targetTouches[0].clientX);
  }, []);

  const onTouchEnd = useCallback(
    (habitId) => {
      if (!touchStart || !touchEnd) return;

      const distance = touchStart - touchEnd;
      const isLeftSwipe = distance > 50;
      const isRightSwipe = distance < -50;

      if (isLeftSwipe) {
        // Swipe left to complete habit
        completeHabit(habitId);
      } else if (isRightSwipe) {
        // Swipe right to snooze/skip
        snoozeHabit(habitId);
      }
    },
    [touchStart, touchEnd]
  );

  const completeHabit = useCallback(async (habitId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`/api/v1/habits/${habitId}/complete`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.ok) {
        const result = await response.json();

        // Update local state
        setHabits((prev) =>
          prev.map((habit) =>
            habit.id === habitId
              ? {
                  ...habit,
                  completed_today: true,
                  streak: (habit.streak || 0) + 1,
                }
              : habit
          )
        );

        // Show celebration if streak milestone
        if (result.streak_milestone) {
          showCelebration(result.streak_milestone);
        }

        // Update today's stats
        setTodayStats((prev) => ({
          ...prev,
          completed: (prev.completed || 0) + 1,
          completion_rate: ((prev.completed + 1) / prev.total_habits) * 100,
        }));
      }
    } catch (error) {
      console.error("Failed to complete habit:", error);
    }
  }, []);

  const snoozeHabit = useCallback(async (habitId) => {
    try {
      const token = localStorage.getItem("token");
      await fetch(`/api/v1/habits/${habitId}/snooze`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
        body: JSON.stringify({ snooze_minutes: 60 }),
      });

      // Update local state
      setHabits((prev) =>
        prev.map((habit) =>
          habit.id === habitId
            ? {
                ...habit,
                snoozed_until: new Date(Date.now() + 60 * 60000).toISOString(),
              }
            : habit
        )
      );
    } catch (error) {
      console.error("Failed to snooze habit:", error);
    }
  }, []);

  const showCelebration = useCallback((milestone) => {
    // Mobile-friendly celebration animation
    const celebration = document.createElement("div");
    celebration.className =
      "fixed inset-0 flex items-center justify-center z-50 pointer-events-none";
    celebration.innerHTML = `
            <div class="bg-gradient-to-r from-yellow-400 to-orange-500 text-white rounded-full p-8 animate-bounce shadow-2xl">
                <div class="text-4xl">🔥</div>
                <div class="text-xl font-bold mt-2">${milestone} Day Streak!</div>
            </div>
        `;

    document.body.appendChild(celebration);

    setTimeout(() => {
      document.body.removeChild(celebration);
    }, 3000);
  }, []);

  // Quick add habit
  const quickAddHabit = useCallback(async (habitTitle) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch("/api/v1/habits", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          title: habitTitle,
          difficulty: 1,
          cadence: "daily",
          quick_add: true,
        }),
      });

      if (response.ok) {
        const newHabit = await response.json();
        setHabits((prev) => [...prev, newHabit]);
        setShowQuickAdd(false);
      }
    } catch (error) {
      console.error("Failed to add habit:", error);
    }
  }, []);

  // Calculated stats
  const todayProgress = useMemo(() => {
    const completed = habits.filter((h) => h.completed_today).length;
    const total = habits.length;
    return {
      completed,
      total,
      percentage: total > 0 ? (completed / total) * 100 : 0,
    };
  }, [habits]);

  const streakHabits = useMemo(() => {
    return habits
      .filter((h) => h.streak > 0)
      .sort((a, b) => b.streak - a.streak)
      .slice(0, 3);
  }, [habits]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-pulse">
          <Smartphone className="h-8 w-8 text-purple-500 animate-bounce" />
        </div>
        <span className="ml-2">Loading your habits...</span>
      </div>
    );
  }

  return (
    <div className={`space-y-4 ${isMobile ? "pb-20" : ""}`}>
      {/* Header with notifications */}
      <Card className="bg-gradient-to-r from-purple-500 to-pink-500 text-white">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-bold">Today's Quest</h2>
              <p className="text-purple-100">
                {new Date().toLocaleDateString("en-US", {
                  weekday: "long",
                  month: "long",
                  day: "numeric",
                })}
              </p>
            </div>
            <div className="relative">
              <Bell className="h-6 w-6" />
              {notifications.length > 0 && (
                <Badge className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-1">
                  {notifications.length}
                </Badge>
              )}
            </div>
          </div>

          {/* Progress Ring */}
          <div className="mt-4 flex items-center justify-center">
            <div className="relative w-32 h-32">
              <svg className="w-32 h-32 transform -rotate-90">
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="rgba(255,255,255,0.2)"
                  strokeWidth="8"
                  fill="none"
                />
                <circle
                  cx="64"
                  cy="64"
                  r="56"
                  stroke="white"
                  strokeWidth="8"
                  fill="none"
                  strokeDasharray={`${2 * Math.PI * 56}`}
                  strokeDashoffset={`${
                    2 * Math.PI * 56 * (1 - todayProgress.percentage / 100)
                  }`}
                  className="transition-all duration-500 ease-in-out"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-2xl font-bold">
                    {todayProgress.completed}/{todayProgress.total}
                  </div>
                  <div className="text-sm text-purple-100">
                    {Math.round(todayProgress.percentage)}%
                  </div>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-3">
        <Card className="text-center">
          <CardContent className="p-3">
            <Flame className="h-6 w-6 mx-auto mb-1 text-orange-500" />
            <div className="text-lg font-bold">
              {streakHabits[0]?.streak || 0}
            </div>
            <div className="text-xs text-gray-600">Best Streak</div>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="p-3">
            <Award className="h-6 w-6 mx-auto mb-1 text-yellow-500" />
            <div className="text-lg font-bold">
              {todayStats.achievements || 0}
            </div>
            <div className="text-xs text-gray-600">Achievements</div>
          </CardContent>
        </Card>

        <Card className="text-center">
          <CardContent className="p-3">
            <TrendingUp className="h-6 w-6 mx-auto mb-1 text-green-500" />
            <div className="text-lg font-bold">
              {Math.round(todayStats.weekly_avg || 0)}%
            </div>
            <div className="text-xs text-gray-600">Weekly Avg</div>
          </CardContent>
        </Card>
      </div>

      {/* Today's Habits */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center">
              <Target className="h-5 w-5 mr-2" />
              Today's Habits
            </CardTitle>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setShowQuickAdd(true)}
            >
              <Plus className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-3">
          {habits.map((habit) => (
            <HabitCard
              key={habit.id}
              habit={habit}
              onComplete={() => completeHabit(habit.id)}
              onSnooze={() => snoozeHabit(habit.id)}
              isMobile={isMobile}
              onTouchStart={onTouchStart}
              onTouchMove={onTouchMove}
              onTouchEnd={() => onTouchEnd(habit.id)}
            />
          ))}

          {habits.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <Target className="h-12 w-12 mx-auto mb-4 opacity-50" />
              <p>No habits for today</p>
              <Button
                onClick={() => setShowQuickAdd(true)}
                className="mt-2"
                size="sm"
              >
                Add your first habit
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Streak Highlights */}
      {streakHabits.length > 0 && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="flex items-center">
              <Flame className="h-5 w-5 mr-2 text-orange-500" />
              Streak Leaders
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {streakHabits.map((habit, index) => (
              <div
                key={habit.id}
                className="flex items-center justify-between p-2 bg-orange-50 rounded-lg"
              >
                <div className="flex items-center space-x-3">
                  <div className="text-2xl">
                    {index === 0 ? "🥇" : index === 1 ? "🥈" : "🥉"}
                  </div>
                  <div>
                    <div className="font-medium text-sm">{habit.title}</div>
                    <div className="text-xs text-gray-600">
                      {habit.streak} days
                    </div>
                  </div>
                </div>
                <Flame className="h-5 w-5 text-orange-500" />
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Quick Add Modal */}
      {showQuickAdd && (
        <QuickAddModal
          onAdd={quickAddHabit}
          onClose={() => setShowQuickAdd(false)}
        />
      )}

      {/* Mobile Bottom Navigation Spacer */}
      {isMobile && <div className="h-16" />}
    </div>
  );
};

// Individual habit card component
const HabitCard = ({
  habit,
  onComplete,
  onSnooze,
  isMobile,
  onTouchStart,
  onTouchMove,
  onTouchEnd,
}) => {
  const isCompleted = habit.completed_today;
  const isSnoozed =
    habit.snoozed_until && new Date(habit.snoozed_until) > new Date();

  const difficultyColors = {
    1: "bg-green-100 text-green-800",
    2: "bg-yellow-100 text-yellow-800",
    3: "bg-orange-100 text-orange-800",
    4: "bg-red-100 text-red-800",
    5: "bg-purple-100 text-purple-800",
  };

  const touchProps = isMobile
    ? {
        onTouchStart,
        onTouchMove,
        onTouchEnd,
      }
    : {};

  return (
    <div
      className={`flex items-center space-x-3 p-3 rounded-lg border transition-all duration-200 ${
        isCompleted
          ? "bg-green-50 border-green-200"
          : isSnoozed
          ? "bg-gray-50 border-gray-200"
          : "bg-white border-gray-200 hover:shadow-md"
      }`}
      {...touchProps}
    >
      {/* Completion Button */}
      <button
        onClick={onComplete}
        disabled={isCompleted}
        className={`flex-shrink-0 w-8 h-8 rounded-full border-2 flex items-center justify-center transition-all ${
          isCompleted
            ? "bg-green-500 border-green-500 text-white"
            : "border-gray-300 hover:border-purple-500 hover:bg-purple-50"
        }`}
      >
        {isCompleted && <CheckCircle2 className="h-5 w-5" />}
      </button>

      {/* Habit Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center space-x-2 mb-1">
          <h4
            className={`font-medium truncate ${
              isCompleted ? "line-through text-gray-500" : ""
            }`}
          >
            {habit.title}
          </h4>
          <Badge
            variant="secondary"
            className={`text-xs ${
              difficultyColors[habit.difficulty] || difficultyColors[1]
            }`}
          >
            L{habit.difficulty}
          </Badge>
        </div>

        {habit.streak > 0 && (
          <div className="flex items-center space-x-1 text-xs text-orange-600">
            <Flame className="h-3 w-3" />
            <span>{habit.streak} day streak</span>
          </div>
        )}

        {isSnoozed && (
          <div className="flex items-center space-x-1 text-xs text-gray-500">
            <Clock className="h-3 w-3" />
            <span>
              Snoozed until {new Date(habit.snoozed_until).toLocaleTimeString()}
            </span>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      {!isCompleted && !isSnoozed && isMobile && (
        <div className="text-xs text-gray-400 text-center">
          <div>← Complete</div>
          <div>Snooze →</div>
        </div>
      )}

      {!isMobile && !isCompleted && (
        <div className="flex space-x-1">
          <Button size="sm" variant="outline" onClick={onSnooze}>
            <Clock className="h-3 w-3" />
          </Button>
          <Button size="sm" onClick={onComplete}>
            <CheckCircle2 className="h-3 w-3" />
          </Button>
        </div>
      )}
    </div>
  );
};

// Quick add habit modal
const QuickAddModal = ({ onAdd, onClose }) => {
  const [title, setTitle] = useState("");
  const [isAdding, setIsAdding] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsAdding(true);
    await onAdd(title.trim());
    setIsAdding(false);
    setTitle("");
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Quick Add Habit</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="What habit do you want to build?"
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              autoFocus
            />
            <div className="flex space-x-2">
              <Button
                type="button"
                variant="outline"
                onClick={onClose}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!title.trim() || isAdding}
                className="flex-1"
              >
                {isAdding ? "Adding..." : "Add Habit"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default MobileHabitTracker;
