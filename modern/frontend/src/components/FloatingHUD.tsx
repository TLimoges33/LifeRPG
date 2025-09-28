// Modern HUD System - Floating Progress Indicators
import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Trophy, Zap, Target, Star, TrendingUp } from "lucide-react";

interface HUDData {
  level: number;
  xp: number;
  xpToNext: number;
  momentum: number;
  title: string;
  achievements: Achievement[];
  streak: number;
  todayCompleted: number;
  todayTotal: number;
}

interface Achievement {
  id: string;
  name: string;
  description: string;
  xpAwarded: number;
  unlockedAt: Date;
}

interface FloatingHUDProps {
  data: HUDData;
  position?: "top-left" | "top-right" | "bottom-left" | "bottom-right";
  autoHide?: boolean;
  theme?: "dark" | "light" | "wizard";
}

export const FloatingHUD: React.FC<FloatingHUDProps> = ({
  data,
  position = "top-left",
  autoHide = true,
  theme = "wizard",
}) => {
  const [isVisible, setIsVisible] = useState(true);
  const [isMinimized, setIsMinimized] = useState(false);
  const [recentAchievements, setRecentAchievements] = useState<Achievement[]>(
    []
  );

  // Auto-hide on mouse hover (like legacy AHK)
  useEffect(() => {
    if (!autoHide) return;

    let hideTimer: NodeJS.Timeout;
    const handleMouseMove = (e: MouseEvent) => {
      const rect = document
        .getElementById("floating-hud")
        ?.getBoundingClientRect();
      if (!rect) return;

      const isHovering =
        e.clientX >= rect.left &&
        e.clientX <= rect.right &&
        e.clientY >= rect.top &&
        e.clientY <= rect.bottom;

      if (isHovering) {
        setIsVisible(false);
        clearTimeout(hideTimer);
      } else {
        clearTimeout(hideTimer);
        hideTimer = setTimeout(() => setIsVisible(true), 1000);
      }
    };

    document.addEventListener("mousemove", handleMouseMove);
    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      clearTimeout(hideTimer);
    };
  }, [autoHide]);

  // Show recent achievements
  useEffect(() => {
    const recent = data.achievements
      .filter((a) => {
        const timeSince = Date.now() - a.unlockedAt.getTime();
        return timeSince < 5000; // Show for 5 seconds
      })
      .slice(0, 3);
    setRecentAchievements(recent);
  }, [data.achievements]);

  const positionClasses = {
    "top-left": "top-4 left-4",
    "top-right": "top-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "bottom-right": "bottom-4 right-4",
  };

  const themeClasses = {
    dark: "bg-slate-900/90 border-slate-700 text-white",
    light: "bg-white/90 border-gray-300 text-gray-900",
    wizard:
      "bg-gradient-to-br from-purple-900/90 to-slate-900/90 border-purple-500 text-white",
  };

  const xpProgress = (data.xp / (data.xp + data.xpToNext)) * 100;
  const momentumColor =
    data.momentum >= 70
      ? "bg-green-500"
      : data.momentum >= 40
      ? "bg-yellow-500"
      : "bg-red-500";

  return (
    <>
      <AnimatePresence>
        {isVisible && (
          <motion.div
            id="floating-hud"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            className={`fixed ${positionClasses[position]} z-50 ${themeClasses[theme]} 
                       backdrop-blur-md rounded-lg border shadow-2xl min-w-[300px]`}
          >
            {/* Header with minimize button */}
            <div className="flex items-center justify-between p-3 border-b border-white/10">
              <div className="flex items-center space-x-2">
                <div className="text-2xl">🧙‍♂️</div>
                <div className="text-sm font-bold">{data.title}</div>
              </div>
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="text-white/70 hover:text-white transition-colors"
              >
                {isMinimized ? "◢" : "◤"}
              </button>
            </div>

            {!isMinimized && (
              <div className="p-4 space-y-3">
                {/* Level Progress */}
                <div>
                  <div className="flex justify-between text-sm mb-1">
                    <span>LEVEL {data.level}</span>
                    <span>
                      {data.xp}/{data.xp + data.xpToNext} XP
                    </span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2">
                    <motion.div
                      className="bg-gradient-to-r from-blue-400 to-purple-500 h-2 rounded-full"
                      initial={{ width: 0 }}
                      animate={{ width: `${xpProgress}%` }}
                      transition={{ duration: 1, ease: "easeOut" }}
                    />
                  </div>
                </div>

                {/* Momentum Bar */}
                <div>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <div className="flex items-center space-x-1">
                      <Zap className="w-3 h-3" />
                      <span>MMT</span>
                    </div>
                    <span>{data.momentum}%</span>
                  </div>
                  <div className="w-full bg-white/20 rounded-full h-2">
                    <motion.div
                      className={`${momentumColor} h-2 rounded-full`}
                      initial={{ width: 0 }}
                      animate={{ width: `${data.momentum}%` }}
                      transition={{ duration: 0.8 }}
                    />
                  </div>
                </div>

                {/* Daily Progress */}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-1">
                    <Target className="w-3 h-3" />
                    <span>Today</span>
                  </div>
                  <span>
                    {data.todayCompleted}/{data.todayTotal}
                  </span>
                </div>

                {/* Streak */}
                <div className="flex items-center justify-between text-sm">
                  <div className="flex items-center space-x-1">
                    <TrendingUp className="w-3 h-3" />
                    <span>Streak</span>
                  </div>
                  <span>{data.streak} days</span>
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Recent Achievements Notifications */}
      <AnimatePresence>
        {recentAchievements.map((achievement, index) => (
          <motion.div
            key={achievement.id}
            initial={{
              opacity: 0,
              x: position.includes("right") ? 100 : -100,
              scale: 0.8,
            }}
            animate={{ opacity: 1, x: 0, scale: 1 }}
            exit={{
              opacity: 0,
              x: position.includes("right") ? 100 : -100,
              scale: 0.8,
            }}
            className={`fixed ${positionClasses[position]} z-[60] ${themeClasses[theme]} 
                       backdrop-blur-md rounded-lg border shadow-2xl p-4 min-w-[280px]`}
            style={{
              [position.includes("top") ? "top" : "bottom"]: position.includes(
                "top"
              )
                ? `${120 + index * 80}px`
                : `${120 + index * 80}px`,
            }}
          >
            <div className="flex items-center space-x-3">
              <div className="text-2xl">🏆</div>
              <div className="flex-1">
                <div className="font-bold text-sm">{achievement.name}</div>
                <div className="text-xs opacity-80">
                  {achievement.description}
                </div>
                <div className="text-xs text-yellow-400">
                  +{achievement.xpAwarded} XP
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>
    </>
  );
};

// Hook for managing HUD data
export const useHUDData = (userId: string) => {
  const [hudData, setHudData] = useState<HUDData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchHUDData = async () => {
      try {
        const [profile, stats, habits] = await Promise.all([
          fetch(`/api/v1/users/${userId}/profile`).then((r) => r.json()),
          fetch(`/api/v1/gamification/stats`).then((r) => r.json()),
          fetch(`/api/v1/habits/today`).then((r) => r.json()),
        ]);

        setHudData({
          level: stats.level,
          xp: stats.xp,
          xpToNext: stats.xp_to_next,
          momentum: stats.momentum,
          title: profile.title,
          achievements: stats.recent_achievements || [],
          streak: stats.current_streak,
          todayCompleted: habits.completed.length,
          todayTotal: habits.total.length,
        });
      } catch (error) {
        console.error("Failed to fetch HUD data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchHUDData();
    const interval = setInterval(fetchHUDData, 30000); // Update every 30s

    return () => clearInterval(interval);
  }, [userId]);

  return { hudData, loading };
};

// Achievement Notification System
export const useAchievementNotifications = () => {
  const [notifications, setNotifications] = useState<Achievement[]>([]);

  const showAchievement = (achievement: Achievement) => {
    setNotifications((prev) => [
      ...prev,
      { ...achievement, unlockedAt: new Date() },
    ]);

    // Auto-remove after 5 seconds
    setTimeout(() => {
      setNotifications((prev) => prev.filter((n) => n.id !== achievement.id));
    }, 5000);
  };

  useEffect(() => {
    // Listen for achievement events from WebSocket or EventSource
    const handleAchievementEvent = (event: CustomEvent<Achievement>) => {
      showAchievement(event.detail);
    };

    window.addEventListener(
      "achievement-unlocked",
      handleAchievementEvent as EventListener
    );
    return () =>
      window.removeEventListener(
        "achievement-unlocked",
        handleAchievementEvent as EventListener
      );
  }, []);

  return { notifications, showAchievement };
};

export default FloatingHUD;
