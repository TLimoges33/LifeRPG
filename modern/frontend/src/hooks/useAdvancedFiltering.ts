// Advanced Filtering System - Matching AHK's powerful search and filter capabilities
import { useMemo, useState, useCallback } from "react";

export interface FilterState {
  // Text search (like AHK search box)
  searchQuery: string;

  // Importance filter (like AHK importance dropdown)
  importance: "All" | "High" | "Medium" | "Low";

  // Skill filter (like AHK skill dropdown)
  skill: string | "All" | "None";

  // Status filters
  showCompleted: boolean;
  showActive: boolean;
  showPaused: boolean;

  // Difficulty range
  difficultyRange: [number, number];

  // Date filters
  dateRange: {
    start: Date | null;
    end: Date | null;
  };

  // Category filter
  categories: string[];

  // Streak filters
  minStreak: number;
  maxStreak: number;

  // Sorting
  sortBy:
    | "name"
    | "difficulty"
    | "importance"
    | "created"
    | "streak"
    | "completion";
  sortOrder: "asc" | "desc";
}

export interface FilterableItem {
  id: string;
  title: string;
  notes?: string;
  importance: "High" | "Medium" | "Low";
  difficulty: number;
  skill?: string;
  categories: string[];
  status: "active" | "completed" | "paused";
  createdAt: Date;
  completedAt?: Date;
  streak: number;
  completionRate: number;
}

const defaultFilterState: FilterState = {
  searchQuery: "",
  importance: "All",
  skill: "All",
  showCompleted: true,
  showActive: true,
  showPaused: true,
  difficultyRange: [1, 10],
  dateRange: { start: null, end: null },
  categories: [],
  minStreak: 0,
  maxStreak: 999,
  sortBy: "created",
  sortOrder: "desc",
};

export const useAdvancedFiltering = <T extends FilterableItem>(
  items: T[],
  initialFilters?: Partial<FilterState>
) => {
  const [filters, setFilters] = useState<FilterState>({
    ...defaultFilterState,
    ...initialFilters,
  });

  // Memoized filtering logic for performance
  const filteredItems = useMemo(() => {
    let filtered = [...items];

    // Text search - search in title, notes, and categories
    if (filters.searchQuery.trim()) {
      const query = filters.searchQuery.toLowerCase();
      filtered = filtered.filter(
        (item) =>
          item.title.toLowerCase().includes(query) ||
          (item.notes && item.notes.toLowerCase().includes(query)) ||
          item.categories.some((cat) => cat.toLowerCase().includes(query)) ||
          (item.skill && item.skill.toLowerCase().includes(query))
      );
    }

    // Importance filter
    if (filters.importance !== "All") {
      filtered = filtered.filter(
        (item) => item.importance === filters.importance
      );
    }

    // Skill filter
    if (filters.skill !== "All") {
      if (filters.skill === "None") {
        filtered = filtered.filter((item) => !item.skill);
      } else {
        filtered = filtered.filter((item) => item.skill === filters.skill);
      }
    }

    // Status filters
    const statusFilters = [];
    if (filters.showActive) statusFilters.push("active");
    if (filters.showCompleted) statusFilters.push("completed");
    if (filters.showPaused) statusFilters.push("paused");

    filtered = filtered.filter((item) => statusFilters.includes(item.status));

    // Difficulty range
    filtered = filtered.filter(
      (item) =>
        item.difficulty >= filters.difficultyRange[0] &&
        item.difficulty <= filters.difficultyRange[1]
    );

    // Date range filter
    if (filters.dateRange.start || filters.dateRange.end) {
      filtered = filtered.filter((item) => {
        const itemDate = item.completedAt || item.createdAt;
        if (filters.dateRange.start && itemDate < filters.dateRange.start)
          return false;
        if (filters.dateRange.end && itemDate > filters.dateRange.end)
          return false;
        return true;
      });
    }

    // Categories filter
    if (filters.categories.length > 0) {
      filtered = filtered.filter((item) =>
        filters.categories.every((cat) => item.categories.includes(cat))
      );
    }

    // Streak range filter
    filtered = filtered.filter(
      (item) =>
        item.streak >= filters.minStreak && item.streak <= filters.maxStreak
    );

    // Sorting
    filtered.sort((a, b) => {
      let aValue: any;
      let bValue: any;

      switch (filters.sortBy) {
        case "name":
          aValue = a.title.toLowerCase();
          bValue = b.title.toLowerCase();
          break;
        case "difficulty":
          aValue = a.difficulty;
          bValue = b.difficulty;
          break;
        case "importance":
          const importanceOrder = { High: 3, Medium: 2, Low: 1 };
          aValue = importanceOrder[a.importance];
          bValue = importanceOrder[b.importance];
          break;
        case "created":
          aValue = a.createdAt;
          bValue = b.createdAt;
          break;
        case "streak":
          aValue = a.streak;
          bValue = b.streak;
          break;
        case "completion":
          aValue = a.completionRate;
          bValue = b.completionRate;
          break;
        default:
          return 0;
      }

      if (aValue < bValue) return filters.sortOrder === "asc" ? -1 : 1;
      if (aValue > bValue) return filters.sortOrder === "asc" ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [items, filters]);

  // Update filter functions
  const updateFilter = useCallback(
    <K extends keyof FilterState>(key: K, value: FilterState[K]) => {
      setFilters((prev) => ({ ...prev, [key]: value }));
    },
    []
  );

  const updateFilters = useCallback((newFilters: Partial<FilterState>) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(defaultFilterState);
  }, []);

  const clearSearch = useCallback(() => {
    updateFilter("searchQuery", "");
  }, [updateFilter]);

  // Quick filter presets (like AHK's quick buttons)
  const quickFilters = {
    todayActive: () => {
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      updateFilters({
        showActive: true,
        showCompleted: false,
        showPaused: false,
        dateRange: { start: today, end: null },
      });
    },

    highPriority: () => {
      updateFilters({
        importance: "High",
        showActive: true,
        showCompleted: false,
      });
    },

    longStreaks: () => {
      updateFilters({
        minStreak: 7,
        sortBy: "streak",
        sortOrder: "desc",
      });
    },

    recentlyCompleted: () => {
      const weekAgo = new Date();
      weekAgo.setDate(weekAgo.getDate() - 7);
      updateFilters({
        showCompleted: true,
        showActive: false,
        dateRange: { start: weekAgo, end: null },
        sortBy: "created",
        sortOrder: "desc",
      });
    },

    difficultTasks: () => {
      updateFilters({
        difficultyRange: [7, 10],
        sortBy: "difficulty",
        sortOrder: "desc",
      });
    },
  };

  // Search suggestions based on current data
  const getSearchSuggestions = useCallback(
    (query: string): string[] => {
      if (!query.trim()) return [];

      const suggestions = new Set<string>();
      const queryLower = query.toLowerCase();

      items.forEach((item) => {
        // Title suggestions
        if (item.title.toLowerCase().includes(queryLower)) {
          suggestions.add(item.title);
        }

        // Category suggestions
        item.categories.forEach((cat) => {
          if (cat.toLowerCase().includes(queryLower)) {
            suggestions.add(cat);
          }
        });

        // Skill suggestions
        if (item.skill && item.skill.toLowerCase().includes(queryLower)) {
          suggestions.add(item.skill);
        }
      });

      return Array.from(suggestions).slice(0, 10);
    },
    [items]
  );

  // Get available filter options from data
  const getFilterOptions = useCallback(() => {
    const skills = new Set<string>();
    const categories = new Set<string>();
    let minDifficulty = 10;
    let maxDifficulty = 1;
    let minStreak = 999;
    let maxStreak = 0;

    items.forEach((item) => {
      if (item.skill) skills.add(item.skill);
      item.categories.forEach((cat) => categories.add(cat));
      minDifficulty = Math.min(minDifficulty, item.difficulty);
      maxDifficulty = Math.max(maxDifficulty, item.difficulty);
      minStreak = Math.min(minStreak, item.streak);
      maxStreak = Math.max(maxStreak, item.streak);
    });

    return {
      skills: ["All", "None", ...Array.from(skills)],
      categories: Array.from(categories),
      difficultyRange: [minDifficulty, maxDifficulty] as [number, number],
      streakRange: [minStreak, maxStreak] as [number, number],
    };
  }, [items]);

  return {
    filters,
    filteredItems,
    updateFilter,
    updateFilters,
    resetFilters,
    clearSearch,
    quickFilters,
    getSearchSuggestions,
    getFilterOptions,
    totalCount: items.length,
    filteredCount: filteredItems.length,
  };
};

// Filter statistics for UI display
export const useFilterStats = (
  filters: FilterState,
  totalItems: number,
  filteredItems: number
) => {
  return useMemo(() => {
    const activeFilters = [];

    if (filters.searchQuery.trim()) {
      activeFilters.push(`Search: "${filters.searchQuery}"`);
    }

    if (filters.importance !== "All") {
      activeFilters.push(`Importance: ${filters.importance}`);
    }

    if (filters.skill !== "All") {
      activeFilters.push(`Skill: ${filters.skill}`);
    }

    if (!filters.showCompleted || !filters.showActive || !filters.showPaused) {
      const statuses = [];
      if (filters.showActive) statuses.push("Active");
      if (filters.showCompleted) statuses.push("Completed");
      if (filters.showPaused) statuses.push("Paused");
      activeFilters.push(`Status: ${statuses.join(", ")}`);
    }

    if (filters.categories.length > 0) {
      activeFilters.push(`Categories: ${filters.categories.join(", ")}`);
    }

    return {
      activeFilters,
      hasActiveFilters: activeFilters.length > 0,
      filteredPercentage:
        totalItems > 0 ? (filteredItems / totalItems) * 100 : 0,
    };
  }, [filters, totalItems, filteredItems]);
};
