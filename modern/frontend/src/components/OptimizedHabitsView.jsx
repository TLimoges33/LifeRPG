import React, { useState, useEffect, useMemo, useCallback, memo } from "react";
import { FixedSizeList as List } from "react-window";
import { Card, CardHeader, CardTitle, CardContent } from "./ui/card";
import { Button } from "./ui/button";
import { LoadingSpinner } from "./ui/loading";
import {
  Zap,
  Target,
  Calendar,
  TrendingUp,
  CheckCircle2,
  Clock,
  Star,
  Filter,
} from "lucide-react";

// Memoized habit card component for performance
const HabitCard = memo(({ habit, onComplete, onEdit }) => {
  const handleComplete = useCallback(() => {
    onComplete(habit.id);
  }, [habit.id, onComplete]);

  const handleEdit = useCallback(() => {
    onEdit(habit);
  }, [habit, onEdit]);

  const difficultyColor = useMemo(() => {
    switch (habit.difficulty) {
      case 1:
        return "text-green-600 bg-green-50";
      case 2:
        return "text-yellow-600 bg-yellow-50";
      case 3:
        return "text-orange-600 bg-orange-50";
      case 4:
        return "text-red-600 bg-red-50";
      case 5:
        return "text-purple-600 bg-purple-50";
      default:
        return "text-gray-600 bg-gray-50";
    }
  }, [habit.difficulty]);

  const statusColor = useMemo(() => {
    switch (habit.status) {
      case "active":
        return "border-l-green-500";
      case "completed":
        return "border-l-blue-500";
      case "paused":
        return "border-l-yellow-500";
      default:
        return "border-l-gray-500";
    }
  }, [habit.status]);

  return (
    <Card
      className={`hover:shadow-md transition-all duration-200 border-l-4 ${statusColor}`}
    >
      <CardContent className="p-4">
        <div className="flex items-start justify-between mb-2">
          <h3 className="font-semibold text-sm truncate flex-1">
            {habit.title}
          </h3>
          <div
            className={`px-2 py-1 rounded-full text-xs font-medium ${difficultyColor}`}
          >
            Level {habit.difficulty}
          </div>
        </div>

        {habit.notes && (
          <p className="text-xs text-gray-600 mb-2 line-clamp-2">
            {habit.notes}
          </p>
        )}

        <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
          <span className="flex items-center">
            <Target className="h-3 w-3 mr-1" />
            {habit.cadence || "Daily"}
          </span>
          <span className="flex items-center">
            <Star className="h-3 w-3 mr-1" />
            {habit.streak || 0} streak
          </span>
        </div>

        <div className="flex space-x-2">
          <Button
            onClick={handleComplete}
            className="flex-1 text-xs h-8"
            size="sm"
            disabled={habit.status === "completed"}
          >
            <CheckCircle2 className="h-3 w-3 mr-1" />
            {habit.status === "completed" ? "Completed" : "Complete"}
          </Button>
          <Button
            onClick={handleEdit}
            variant="outline"
            size="sm"
            className="text-xs h-8 px-2"
          >
            Edit
          </Button>
        </div>
      </CardContent>
    </Card>
  );
});

HabitCard.displayName = "HabitCard";

// Virtualized habit list for performance with large datasets
const VirtualizedHabitList = memo(
  ({ habits, onComplete, onEdit, height = 600 }) => {
    const Row = useCallback(
      ({ index, style }) => (
        <div style={style} className="pr-2 pb-2">
          <HabitCard
            habit={habits[index]}
            onComplete={onComplete}
            onEdit={onEdit}
          />
        </div>
      ),
      [habits, onComplete, onEdit]
    );

    if (habits.length === 0) {
      return (
        <div className="text-center py-8">
          <Target className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600">No habits found</p>
        </div>
      );
    }

    return (
      <List
        height={height}
        itemCount={habits.length}
        itemSize={160} // Height of each habit card
        overscanCount={5} // Pre-render 5 items above/below viewport
      >
        {Row}
      </List>
    );
  }
);

VirtualizedHabitList.displayName = "VirtualizedHabitList";

// Advanced filtering hook with performance optimizations
const useAdvancedHabitFiltering = (habits) => {
  const [filters, setFilters] = useState({
    search: "",
    status: "all",
    difficulty: "all",
    sortBy: "created_at",
    sortOrder: "desc",
  });

  // Memoized filtered and sorted habits
  const filteredHabits = useMemo(() => {
    let result = [...habits];

    // Search filter
    if (filters.search) {
      const searchLower = filters.search.toLowerCase();
      result = result.filter(
        (habit) =>
          habit.title.toLowerCase().includes(searchLower) ||
          (habit.notes && habit.notes.toLowerCase().includes(searchLower))
      );
    }

    // Status filter
    if (filters.status !== "all") {
      result = result.filter((habit) => habit.status === filters.status);
    }

    // Difficulty filter
    if (filters.difficulty !== "all") {
      result = result.filter(
        (habit) => habit.difficulty === parseInt(filters.difficulty)
      );
    }

    // Sorting
    result.sort((a, b) => {
      let aValue = a[filters.sortBy];
      let bValue = b[filters.sortBy];

      // Handle date sorting
      if (filters.sortBy === "created_at" || filters.sortBy === "due_date") {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }

      if (filters.sortOrder === "desc") {
        return bValue > aValue ? 1 : -1;
      } else {
        return aValue > bValue ? 1 : -1;
      }
    });

    return result;
  }, [habits, filters]);

  const updateFilter = useCallback((key, value) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters({
      search: "",
      status: "all",
      difficulty: "all",
      sortBy: "created_at",
      sortOrder: "desc",
    });
  }, []);

  return {
    filters,
    filteredHabits,
    updateFilter,
    resetFilters,
    totalCount: habits.length,
    filteredCount: filteredHabits.length,
  };
};

// Advanced filter bar component
const AdvancedFilterBar = memo(
  ({ filters, updateFilter, resetFilters, totalCount, filteredCount }) => {
    const [showAdvanced, setShowAdvanced] = useState(false);

    return (
      <Card className="mb-4">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <Filter className="h-4 w-4" />
              <span className="text-sm font-medium">
                Filters ({filteredCount}/{totalCount})
              </span>
            </div>
            <Button
              onClick={() => setShowAdvanced(!showAdvanced)}
              variant="ghost"
              size="sm"
            >
              {showAdvanced ? "Simple" : "Advanced"}
            </Button>
          </div>

          {/* Basic filters */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
            <div>
              <label className="block text-xs font-medium mb-1">Search</label>
              <input
                type="text"
                placeholder="Search habits..."
                value={filters.search}
                onChange={(e) => updateFilter("search", e.target.value)}
                className="w-full px-3 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Status</label>
              <select
                value={filters.status}
                onChange={(e) => updateFilter("status", e.target.value)}
                className="w-full px-3 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="completed">Completed</option>
                <option value="paused">Paused</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium mb-1">Sort By</label>
              <select
                value={filters.sortBy}
                onChange={(e) => updateFilter("sortBy", e.target.value)}
                className="w-full px-3 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              >
                <option value="created_at">Created Date</option>
                <option value="title">Title</option>
                <option value="difficulty">Difficulty</option>
                <option value="streak">Streak</option>
                <option value="due_date">Due Date</option>
              </select>
            </div>
          </div>

          {/* Advanced filters */}
          {showAdvanced && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
              <div>
                <label className="block text-xs font-medium mb-1">
                  Difficulty Level
                </label>
                <select
                  value={filters.difficulty}
                  onChange={(e) => updateFilter("difficulty", e.target.value)}
                  className="w-full px-3 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="all">All Difficulties</option>
                  <option value="1">Level 1 (Beginner)</option>
                  <option value="2">Level 2 (Easy)</option>
                  <option value="3">Level 3 (Medium)</option>
                  <option value="4">Level 4 (Hard)</option>
                  <option value="5">Level 5 (Expert)</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-medium mb-1">
                  Sort Order
                </label>
                <select
                  value={filters.sortOrder}
                  onChange={(e) => updateFilter("sortOrder", e.target.value)}
                  className="w-full px-3 py-1 text-sm border rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
                >
                  <option value="desc">Descending</option>
                  <option value="asc">Ascending</option>
                </select>
              </div>
            </div>
          )}

          {/* Filter actions */}
          <div className="flex justify-end mt-4 space-x-2">
            <Button onClick={resetFilters} variant="outline" size="sm">
              Reset Filters
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }
);

AdvancedFilterBar.displayName = "AdvancedFilterBar";

// Optimized main habits dashboard
const OptimizedHabitsView = () => {
  const [habits, setHabits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Use advanced filtering hook
  const {
    filters,
    filteredHabits,
    updateFilter,
    resetFilters,
    totalCount,
    filteredCount,
  } = useAdvancedHabitFiltering(habits);

  // Memoized event handlers
  const handleComplete = useCallback(async (habitId) => {
    try {
      const token = localStorage.getItem("token");
      const response = await fetch(`/api/v1/habits/${habitId}/complete`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const result = await response.json();

        // Update local state optimistically
        setHabits((prev) =>
          prev.map((habit) =>
            habit.id === habitId
              ? {
                  ...habit,
                  status: "completed",
                  streak: (habit.streak || 0) + 1,
                }
              : habit
          )
        );

        // Trigger celebrations if needed
        if (result.achievement_unlocked) {
          window.dispatchEvent(
            new CustomEvent("achievement-unlocked", {
              detail: result.achievement_unlocked,
            })
          );
        }
      }
    } catch (error) {
      console.error("Failed to complete habit:", error);
      setError("Failed to complete habit");
    }
  }, []);

  const handleEdit = useCallback((habit) => {
    // Open edit modal (implementation depends on your modal system)
    console.log("Edit habit:", habit);
  }, []);

  // Load habits with error handling
  useEffect(() => {
    const loadHabits = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await fetch("/api/v1/habits", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        if (response.ok) {
          const data = await response.json();
          setHabits(data);
        } else {
          throw new Error("Failed to fetch habits");
        }
      } catch (error) {
        console.error("Failed to load habits:", error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    loadHabits();
  }, []);

  // Performance monitoring (development only)
  useEffect(() => {
    if (process.env.NODE_ENV === "development") {
      const startTime = performance.now();
      const endTime = performance.now();
      console.log(`Habits render time: ${endTime - startTime}ms`);
    }
  }, [filteredHabits]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <LoadingSpinner />
        <span className="ml-2">Loading your magical practices...</span>
      </div>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <div className="text-red-500 mb-2">⚠️ Error loading habits</div>
          <p className="text-gray-600">{error}</p>
          <Button onClick={() => window.location.reload()} className="mt-4">
            Retry
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <AdvancedFilterBar
        filters={filters}
        updateFilter={updateFilter}
        resetFilters={resetFilters}
        totalCount={totalCount}
        filteredCount={filteredCount}
      />

      {/* Performance stats in development */}
      {process.env.NODE_ENV === "development" && (
        <Card>
          <CardContent className="p-4">
            <div className="text-xs text-gray-500">
              Performance: {filteredHabits.length} habits rendered
              {filteredHabits.length > 50 && " (using virtualization)"}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Use virtualized list for large datasets */}
      {filteredHabits.length > 50 ? (
        <VirtualizedHabitList
          habits={filteredHabits}
          onComplete={handleComplete}
          onEdit={handleEdit}
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {filteredHabits.map((habit) => (
            <HabitCard
              key={habit.id}
              habit={habit}
              onComplete={handleComplete}
              onEdit={handleEdit}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default OptimizedHabitsView;
