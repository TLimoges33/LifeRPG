import React, { useState, useEffect, useCallback } from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import MobileHabitTracker from "./MobileHabitTracker";
import AdvancedAnalyticsDashboard from "./AdvancedAnalyticsDashboard";
import { Card, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import {
  Home,
  BarChart3,
  Settings,
  User,
  Plus,
  Menu,
  X,
  Wifi,
  WifiOff,
  Download,
  Smartphone,
  Monitor,
  Bell,
} from "lucide-react";

// Mobile app shell component
const MobileAppShell = () => {
  const [isMobile, setIsMobile] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [installPrompt, setInstallPrompt] = useState(null);
  const [isInstalled, setIsInstalled] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("habits");
  const [notificationPermission, setNotificationPermission] =
    useState("default");

  // Detect mobile device and screen size
  useEffect(() => {
    const checkMobile = () => {
      const isMobileDevice =
        /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
          navigator.userAgent
        );
      const isSmallScreen = window.innerWidth <= 768;
      setIsMobile(isMobileDevice || isSmallScreen);
    };

    checkMobile();
    window.addEventListener("resize", checkMobile);

    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Network status monitoring
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // PWA install prompt handling
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      e.preventDefault();
      setInstallPrompt(e);
    };

    const handleAppInstalled = () => {
      setIsInstalled(true);
      setInstallPrompt(null);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    // Check if already installed
    if (
      window.matchMedia &&
      window.matchMedia("(display-mode: standalone)").matches
    ) {
      setIsInstalled(true);
    }

    return () => {
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt
      );
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  // Service worker registration
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration) => {
          console.log("SW registered:", registration);
        })
        .catch((error) => {
          console.log("SW registration failed:", error);
        });
    }
  }, []);

  // Notification permission handling
  useEffect(() => {
    if ("Notification" in window) {
      setNotificationPermission(Notification.permission);
    }
  }, []);

  const handleInstallApp = useCallback(async () => {
    if (installPrompt) {
      installPrompt.prompt();
      const choiceResult = await installPrompt.userChoice;

      if (choiceResult.outcome === "accepted") {
        console.log("User accepted the install prompt");
      }

      setInstallPrompt(null);
    }
  }, [installPrompt]);

  const requestNotificationPermission = useCallback(async () => {
    if ("Notification" in window) {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
    }
  }, []);

  const navigationItems = [
    { id: "habits", label: "Habits", icon: Home },
    { id: "analytics", label: "Analytics", icon: BarChart3 },
    { id: "settings", label: "Settings", icon: Settings },
    { id: "profile", label: "Profile", icon: User },
  ];

  const renderContent = () => {
    switch (activeTab) {
      case "habits":
        return <MobileHabitTracker userId={1} isMobile={isMobile} />;
      case "analytics":
        return <AdvancedAnalyticsDashboard userId={1} />;
      case "settings":
        return (
          <SettingsPanel
            isMobile={isMobile}
            isOnline={isOnline}
            installPrompt={installPrompt}
            onInstall={handleInstallApp}
            notificationPermission={notificationPermission}
            onRequestNotifications={requestNotificationPermission}
          />
        );
      case "profile":
        return <ProfilePanel isMobile={isMobile} />;
      default:
        return <MobileHabitTracker userId={1} isMobile={isMobile} />;
    }
  };

  return (
    <div className={`min-h-screen bg-gray-50 ${isMobile ? "pb-16" : ""}`}>
      {/* Header */}
      <header className="bg-white shadow-sm border-b sticky top-0 z-40">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center space-x-3">
            {isMobile && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                {sidebarOpen ? (
                  <X className="h-5 w-5" />
                ) : (
                  <Menu className="h-5 w-5" />
                )}
              </Button>
            )}
            <h1 className="text-xl font-bold text-purple-600">LifeRPG</h1>
          </div>

          <div className="flex items-center space-x-2">
            {/* Network status */}
            <div
              className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs ${
                isOnline
                  ? "bg-green-100 text-green-800"
                  : "bg-red-100 text-red-800"
              }`}
            >
              {isOnline ? (
                <Wifi className="h-3 w-3" />
              ) : (
                <WifiOff className="h-3 w-3" />
              )}
              <span>{isOnline ? "Online" : "Offline"}</span>
            </div>

            {/* Install button */}
            {installPrompt && !isInstalled && (
              <Button
                size="sm"
                onClick={handleInstallApp}
                className="hidden sm:flex"
              >
                <Download className="h-4 w-4 mr-1" />
                Install
              </Button>
            )}

            {/* Device indicator */}
            <div className="flex items-center space-x-1 text-gray-500">
              {isMobile ? (
                <Smartphone className="h-4 w-4" />
              ) : (
                <Monitor className="h-4 w-4" />
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Mobile sidebar overlay */}
      {isMobile && sidebarOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 z-30"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar for mobile */}
      {isMobile && (
        <div
          className={`fixed left-0 top-0 h-full w-64 bg-white shadow-lg transform transition-transform duration-300 z-40 ${
            sidebarOpen ? "translate-x-0" : "-translate-x-full"
          }`}
        >
          <div className="p-4 border-b">
            <h2 className="text-lg font-semibold">Menu</h2>
          </div>

          <nav className="p-4 space-y-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    setActiveTab(item.id);
                    setSidebarOpen(false);
                  }}
                  className={`w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left ${
                    activeTab === item.id
                      ? "bg-purple-100 text-purple-600"
                      : "hover:bg-gray-100"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span>{item.label}</span>
                </button>
              );
            })}

            {/* PWA actions */}
            <div className="pt-4 border-t">
              {installPrompt && !isInstalled && (
                <button
                  onClick={handleInstallApp}
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-100"
                >
                  <Download className="h-5 w-5" />
                  <span>Install App</span>
                </button>
              )}

              {notificationPermission === "default" && (
                <button
                  onClick={requestNotificationPermission}
                  className="w-full flex items-center space-x-3 px-3 py-2 rounded-lg text-left hover:bg-gray-100"
                >
                  <Bell className="h-5 w-5" />
                  <span>Enable Notifications</span>
                </button>
              )}
            </div>
          </nav>
        </div>
      )}

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Desktop navigation tabs */}
        {!isMobile && (
          <div className="flex space-x-1 mb-6 bg-white rounded-lg p-1 shadow-sm">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all ${
                    activeTab === item.id
                      ? "bg-purple-100 text-purple-600 shadow-sm"
                      : "hover:bg-gray-100"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Content */}
        {renderContent()}
      </main>

      {/* Mobile bottom navigation */}
      {isMobile && (
        <nav className="fixed bottom-0 left-0 right-0 bg-white border-t shadow-lg">
          <div className="flex items-center justify-around py-2">
            {navigationItems.slice(0, 4).map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex flex-col items-center space-y-1 p-2 rounded-lg ${
                    activeTab === item.id ? "text-purple-600" : "text-gray-600"
                  }`}
                >
                  <Icon className="h-5 w-5" />
                  <span className="text-xs">{item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>
      )}
    </div>
  );
};

// Settings panel component
const SettingsPanel = ({
  isMobile,
  isOnline,
  installPrompt,
  onInstall,
  notificationPermission,
  onRequestNotifications,
}) => {
  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <h3 className="text-lg font-semibold mb-4">App Settings</h3>

          <div className="space-y-4">
            {/* PWA Install */}
            {installPrompt && (
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">Install App</h4>
                  <p className="text-sm text-gray-600">
                    Install LifeRPG for better performance and offline access
                  </p>
                </div>
                <Button onClick={onInstall}>
                  <Download className="h-4 w-4 mr-2" />
                  Install
                </Button>
              </div>
            )}

            {/* Notifications */}
            {notificationPermission === "default" && (
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">Push Notifications</h4>
                  <p className="text-sm text-gray-600">
                    Get reminded about your habits and achievements
                  </p>
                </div>
                <Button onClick={onRequestNotifications}>
                  <Bell className="h-4 w-4 mr-2" />
                  Enable
                </Button>
              </div>
            )}

            {/* Status indicators */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
              <div className="flex items-center space-x-3">
                <div
                  className={`w-3 h-3 rounded-full ${
                    isOnline ? "bg-green-500" : "bg-red-500"
                  }`}
                />
                <span className="text-sm">
                  {isOnline ? "Online" : "Offline"}
                </span>
              </div>

              <div className="flex items-center space-x-3">
                <div
                  className={`w-3 h-3 rounded-full ${
                    notificationPermission === "granted"
                      ? "bg-green-500"
                      : "bg-gray-500"
                  }`}
                />
                <span className="text-sm">
                  Notifications {notificationPermission}
                </span>
              </div>

              <div className="flex items-center space-x-3">
                {isMobile ? (
                  <Smartphone className="h-4 w-4" />
                ) : (
                  <Monitor className="h-4 w-4" />
                )}
                <span className="text-sm">
                  {isMobile ? "Mobile" : "Desktop"}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

// Profile panel component
const ProfilePanel = ({ isMobile }) => {
  const [profile, setProfile] = useState({
    name: "Habit Warrior",
    level: 12,
    totalHabits: 45,
    streakRecord: 30,
    achievements: 18,
  });

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center space-x-4 mb-6">
            <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center">
              <User className="h-8 w-8 text-purple-600" />
            </div>
            <div>
              <h2 className="text-2xl font-bold">{profile.name}</h2>
              <p className="text-gray-600">Level {profile.level} Adventurer</p>
            </div>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {profile.totalHabits}
              </div>
              <div className="text-sm text-gray-600">Total Habits</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {profile.streakRecord}
              </div>
              <div className="text-sm text-gray-600">Best Streak</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {profile.achievements}
              </div>
              <div className="text-sm text-gray-600">Achievements</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {profile.level}
              </div>
              <div className="text-sm text-gray-600">Current Level</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default MobileAppShell;
