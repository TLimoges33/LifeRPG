// Real-time Notification System - AHK-style popups for achievements and updates
import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X,
  Trophy,
  Zap,
  Target,
  Star,
  CheckCircle,
  AlertCircle,
} from "lucide-react";

export interface NotificationData {
  id: string;
  type:
    | "achievement"
    | "xp_gain"
    | "level_up"
    | "streak"
    | "habit_complete"
    | "warning"
    | "info";
  title: string;
  message: string;
  xpAwarded?: number;
  icon?: React.ReactNode;
  duration?: number; // ms, 0 = persistent
  action?: {
    label: string;
    onClick: () => void;
  };
  sound?: boolean;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left";
}

interface NotificationSystemProps {
  maxNotifications?: number;
  defaultDuration?: number;
  playSound?: boolean;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left";
}

export const NotificationSystem: React.FC<NotificationSystemProps> = ({
  maxNotifications = 5,
  defaultDuration = 5000,
  playSound = true,
  position = "top-right",
}) => {
  const [notifications, setNotifications] = useState<NotificationData[]>([]);

  // Auto-remove notifications after duration
  useEffect(() => {
    const timers = notifications
      .filter((n) => n.duration !== 0)
      .map((notification) => {
        const duration = notification.duration || defaultDuration;
        return setTimeout(() => {
          removeNotification(notification.id);
        }, duration);
      });

    return () => timers.forEach(clearTimeout);
  }, [notifications, defaultDuration]);

  const addNotification = useCallback(
    (notification: Omit<NotificationData, "id">) => {
      const id = `notification-${Date.now()}-${crypto.randomUUID()}`;
      const newNotification: NotificationData = {
        ...notification,
        id,
        position: notification.position || position,
      };

      setNotifications((prev) => {
        const updated = [newNotification, ...prev];
        // Keep only max notifications
        return updated.slice(0, maxNotifications);
      });

      // Play notification sound (like AHK notification sounds)
      if (playSound && notification.sound !== false) {
        playNotificationSound(notification.type);
      }
    },
    [maxNotifications, playSound, position]
  );

  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  // Listen for global notification events
  useEffect(() => {
    const handleGlobalNotification = (event: CustomEvent<NotificationData>) => {
      addNotification(event.detail);
    };

    window.addEventListener(
      "show-notification",
      handleGlobalNotification as EventListener
    );
    return () =>
      window.removeEventListener(
        "show-notification",
        handleGlobalNotification as EventListener
      );
  }, [addNotification]);

  const getNotificationIcon = (type: NotificationData["type"]) => {
    switch (type) {
      case "achievement":
        return <Trophy className="w-5 h-5 text-yellow-500" />;
      case "xp_gain":
        return <Zap className="w-5 h-5 text-blue-500" />;
      case "level_up":
        return <Star className="w-5 h-5 text-purple-500" />;
      case "streak":
        return <Target className="w-5 h-5 text-green-500" />;
      case "habit_complete":
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case "warning":
        return <AlertCircle className="w-5 h-5 text-orange-500" />;
      case "info":
      default:
        return <AlertCircle className="w-5 h-5 text-blue-500" />;
    }
  };

  const getNotificationColors = (type: NotificationData["type"]) => {
    switch (type) {
      case "achievement":
        return "border-yellow-300 bg-gradient-to-r from-yellow-50 to-amber-50 dark:from-yellow-900/20 dark:to-amber-900/20";
      case "xp_gain":
        return "border-blue-300 bg-gradient-to-r from-blue-50 to-cyan-50 dark:from-blue-900/20 dark:to-cyan-900/20";
      case "level_up":
        return "border-purple-300 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20";
      case "streak":
        return "border-green-300 bg-gradient-to-r from-green-50 to-emerald-50 dark:from-green-900/20 dark:to-emerald-900/20";
      case "habit_complete":
        return "border-green-300 bg-gradient-to-r from-green-50 to-teal-50 dark:from-green-900/20 dark:to-teal-900/20";
      case "warning":
        return "border-orange-300 bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/20 dark:to-red-900/20";
      case "info":
      default:
        return "border-gray-300 bg-gradient-to-r from-gray-50 to-slate-50 dark:from-gray-800 dark:to-slate-800";
    }
  };

  const positionClasses = {
    "top-right": "top-4 right-4",
    "top-left": "top-4 left-4",
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
  };

  const getAnimationProps = (index: number, position: string) => {
    const fromRight = position.includes("right");
    const fromTop = position.includes("top");

    return {
      initial: {
        opacity: 0,
        x: fromRight ? 100 : -100,
        y: 0,
        scale: 0.8,
      },
      animate: {
        opacity: 1,
        x: 0,
        y: fromTop ? index * 10 : -index * 10,
        scale: 1,
      },
      exit: {
        opacity: 0,
        x: fromRight ? 100 : -100,
        scale: 0.8,
      },
    };
  };

  return (
    <div
      className={`fixed ${positionClasses[position]} z-[200] space-y-2 max-w-sm`}
    >
      <AnimatePresence mode="popLayout">
        {notifications.map((notification, index) => (
          <motion.div
            key={notification.id}
            className={`rounded-lg border shadow-lg backdrop-blur-sm p-4 
                       ${getNotificationColors(notification.type)} 
                       min-w-[320px] max-w-sm`}
            {...getAnimationProps(index, notification.position || position)}
            transition={{
              type: "spring",
              stiffness: 300,
              damping: 30,
              mass: 0.8,
            }}
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="flex items-start space-x-3">
              {/* Icon */}
              <div className="flex-shrink-0 mt-0.5">
                {notification.icon || getNotificationIcon(notification.type)}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0">
                <div className="flex items-start justify-between">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                      {notification.title}
                    </p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">
                      {notification.message}
                    </p>

                    {/* XP Award Display */}
                    {notification.xpAwarded && (
                      <div className="flex items-center space-x-1 mt-2">
                        <Zap className="w-4 h-4 text-yellow-500" />
                        <span className="text-xs font-bold text-yellow-600 dark:text-yellow-400">
                          +{notification.xpAwarded} XP
                        </span>
                      </div>
                    )}

                    {/* Action Button */}
                    {notification.action && (
                      <button
                        onClick={notification.action.onClick}
                        className="mt-2 text-xs bg-blue-100 dark:bg-blue-900/30 
                                 text-blue-700 dark:text-blue-300 px-2 py-1 rounded
                                 hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
                      >
                        {notification.action.label}
                      </button>
                    )}
                  </div>

                  {/* Close Button */}
                  <button
                    onClick={() => removeNotification(notification.id)}
                    className="flex-shrink-0 ml-2 text-gray-400 hover:text-gray-600 
                             dark:text-gray-500 dark:hover:text-gray-300 transition-colors"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          </motion.div>
        ))}
      </AnimatePresence>

      {/* Clear All Button (when multiple notifications) */}
      {notifications.length > 1 && (
        <motion.button
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={clearAll}
          className="w-full text-xs text-center py-1 px-2 bg-gray-200 dark:bg-gray-700 
                   text-gray-600 dark:text-gray-400 rounded hover:bg-gray-300 
                   dark:hover:bg-gray-600 transition-colors"
        >
          Clear All ({notifications.length})
        </motion.button>
      )}
    </div>
  );
};

// Sound effects for notifications (like AHK notification sounds)
const playNotificationSound = (type: NotificationData["type"]) => {
  // Create audio context for sound effects
  const audioContext = new (window.AudioContext ||
    (window as any).webkitAudioContext)();

  const playTone = (
    frequency: number,
    duration: number,
    type: OscillatorType = "sine"
  ) => {
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();

    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);

    oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
    oscillator.type = type;

    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(
      0.01,
      audioContext.currentTime + duration
    );

    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + duration);
  };

  switch (type) {
    case "achievement":
      // Triumphant ascending tones
      playTone(523, 0.15); // C5
      setTimeout(() => playTone(659, 0.15), 100); // E5
      setTimeout(() => playTone(784, 0.3), 200); // G5
      break;
    case "xp_gain":
      // Quick positive chirp
      playTone(800, 0.1, "square");
      setTimeout(() => playTone(1000, 0.1, "square"), 50);
      break;
    case "level_up":
      // Major chord progression
      playTone(523, 0.2); // C5
      setTimeout(() => playTone(659, 0.2), 100); // E5
      setTimeout(() => playTone(784, 0.2), 200); // G5
      setTimeout(() => playTone(1047, 0.4), 300); // C6
      break;
    case "streak":
      // Bouncy rhythm
      playTone(700, 0.08);
      setTimeout(() => playTone(800, 0.08), 80);
      setTimeout(() => playTone(900, 0.15), 160);
      break;
    case "habit_complete":
      // Simple completion sound
      playTone(600, 0.1);
      setTimeout(() => playTone(800, 0.15), 80);
      break;
    case "warning":
      // Alert tone
      playTone(400, 0.15, "triangle");
      setTimeout(() => playTone(300, 0.15, "triangle"), 150);
      break;
    case "info":
    default:
      // Gentle notification
      playTone(600, 0.12);
      break;
  }
};

// Hook for easy notification management
export const useNotifications = () => {
  const showNotification = useCallback(
    (notification: Omit<NotificationData, "id">) => {
      window.dispatchEvent(
        new CustomEvent("show-notification", { detail: notification })
      );
    },
    []
  );

  const showAchievement = useCallback(
    (title: string, description: string, xpAwarded: number) => {
      showNotification({
        type: "achievement",
        title,
        message: description,
        xpAwarded,
        duration: 8000, // Longer for achievements
        sound: true,
      });
    },
    [showNotification]
  );

  const showXPGain = useCallback(
    (xp: number, source: string) => {
      showNotification({
        type: "xp_gain",
        title: `+${xp} XP Gained!`,
        message: `From: ${source}`,
        xpAwarded: xp,
        duration: 3000,
      });
    },
    [showNotification]
  );

  const showLevelUp = useCallback(
    (newLevel: number, xpAwarded: number) => {
      showNotification({
        type: "level_up",
        title: `🎉 Level Up!`,
        message: `You've reached Level ${newLevel}!`,
        xpAwarded,
        duration: 10000, // Even longer for level ups
        sound: true,
      });
    },
    [showNotification]
  );

  const showStreak = useCallback(
    (habitName: string, streakCount: number) => {
      showNotification({
        type: "streak",
        title: `🔥 Streak Achievement!`,
        message: `${habitName}: ${streakCount} days in a row!`,
        duration: 6000,
      });
    },
    [showNotification]
  );

  const showHabitComplete = useCallback(
    (habitName: string, xpAwarded: number) => {
      showNotification({
        type: "habit_complete",
        title: "Habit Completed!",
        message: habitName,
        xpAwarded,
        duration: 3000,
      });
    },
    [showNotification]
  );

  return {
    showNotification,
    showAchievement,
    showXPGain,
    showLevelUp,
    showStreak,
    showHabitComplete,
  };
};

export default NotificationSystem;
