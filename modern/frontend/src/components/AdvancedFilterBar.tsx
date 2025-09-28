// Advanced Filter UI Component - Matching AHK's search and filter interface
import React, { useState, useRef, useEffect } from "react";
import {
  Search,
  X,
  Filter,
  SortAsc,
  SortDesc,
  Calendar,
  Target,
  Zap,
} from "lucide-react";
import {
  FilterState,
  useAdvancedFiltering,
  useFilterStats,
  FilterableItem,
} from "../hooks/useAdvancedFiltering";

interface AdvancedFilterBarProps<T extends FilterableItem> {
  items: T[];
  onFilteredItemsChange: (items: T[]) => void;
  className?: string;
  showQuickFilters?: boolean;
  initialFilters?: Partial<FilterState>;
}

export const AdvancedFilterBar = <T extends FilterableItem>({
  items,
  onFilteredItemsChange,
  className = "",
  showQuickFilters = true,
  initialFilters,
}: AdvancedFilterBarProps<T>) => {
  const {
    filters,
    filteredItems,
    updateFilter,
    updateFilters,
    resetFilters,
    clearSearch,
    quickFilters,
    getSearchSuggestions,
    getFilterOptions,
    totalCount,
    filteredCount,
  } = useAdvancedFiltering(items, initialFilters);

  const { activeFilters, hasActiveFilters, filteredPercentage } =
    useFilterStats(filters, totalCount, filteredCount);

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [searchSuggestions, setSearchSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchInputRef = useRef<HTMLInputElement>(null);
  const filterOptions = getFilterOptions();

  // Update parent component with filtered items
  useEffect(() => {
    onFilteredItemsChange(filteredItems);
  }, [filteredItems, onFilteredItemsChange]);

  // Handle search input changes
  const handleSearchChange = (value: string) => {
    updateFilter("searchQuery", value);

    if (value.trim()) {
      const suggestions = getSearchSuggestions(value);
      setSearchSuggestions(suggestions);
      setShowSuggestions(true);
    } else {
      setShowSuggestions(false);
    }
  };

  // Handle keyboard shortcuts from the keyboard shortcuts system
  useEffect(() => {
    const handleKeyboardAction = (event: CustomEvent) => {
      const action = event.detail.actionType;

      switch (action) {
        case "focus-search":
          searchInputRef.current?.focus();
          break;
        case "clear-filters":
          resetFilters();
          break;
        case "filter-high":
          updateFilter("importance", "High");
          break;
        case "filter-medium":
          updateFilter("importance", "Medium");
          break;
        case "filter-low":
          updateFilter("importance", "Low");
          break;
      }
    };

    window.addEventListener(
      "keyboard-action",
      handleKeyboardAction as EventListener
    );
    return () =>
      window.removeEventListener(
        "keyboard-action",
        handleKeyboardAction as EventListener
      );
  }, [updateFilter, resetFilters]);

  const ImportanceIndicator = ({
    level,
  }: {
    level: "High" | "Medium" | "Low";
  }) => {
    const colors = {
      High: "bg-red-500",
      Medium: "bg-yellow-500",
      Low: "bg-green-500",
    };
    return <div className={`w-3 h-3 rounded-full ${colors[level]}`} />;
  };

  return (
    <div className={`space-y-4 ${className}`}>
      {/* Main Filter Bar */}
      <div className="flex flex-wrap items-center gap-4 p-4 bg-white dark:bg-slate-800 rounded-lg border border-gray-200 dark:border-slate-700 shadow-sm">
        {/* Search Box (like AHK) */}
        <div className="relative flex-1 min-w-[300px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              ref={searchInputRef}
              type="text"
              placeholder="Search habits, projects, categories... (Alt+C)"
              value={filters.searchQuery}
              onChange={(e) => handleSearchChange(e.target.value)}
              onFocus={() =>
                filters.searchQuery.trim() && setShowSuggestions(true)
              }
              onBlur={() => setTimeout(() => setShowSuggestions(false), 200)}
              className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-slate-600 rounded-md 
                         bg-white dark:bg-slate-700 text-gray-900 dark:text-white
                         focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
            {filters.searchQuery && (
              <button
                onClick={clearSearch}
                className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Search Suggestions */}
          {showSuggestions && searchSuggestions.length > 0 && (
            <div className="absolute top-full left-0 right-0 mt-1 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-md shadow-lg z-50">
              {searchSuggestions.map((suggestion, index) => (
                <button
                  key={index}
                  onClick={() => {
                    updateFilter("searchQuery", suggestion);
                    setShowSuggestions(false);
                  }}
                  className="w-full px-4 py-2 text-left hover:bg-gray-50 dark:hover:bg-slate-700 first:rounded-t-md last:rounded-b-md"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Importance Filter (like AHK dropdown) */}
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Importance:
          </label>
          <select
            value={filters.importance}
            onChange={(e) => updateFilter("importance", e.target.value as any)}
            className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md 
                       bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm
                       focus:ring-2 focus:ring-blue-500"
          >
            <option value="All">All</option>
            <option value="High">🔴 High</option>
            <option value="Medium">🟡 Medium</option>
            <option value="Low">🟢 Low</option>
          </select>
        </div>

        {/* Skill Filter (like AHK skill dropdown) */}
        <div className="flex items-center space-x-2">
          <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Skill:
          </label>
          <select
            value={filters.skill}
            onChange={(e) => updateFilter("skill", e.target.value)}
            className="px-3 py-2 border border-gray-300 dark:border-slate-600 rounded-md 
                       bg-white dark:bg-slate-700 text-gray-900 dark:text-white text-sm
                       focus:ring-2 focus:ring-blue-500"
          >
            {filterOptions.skills.map((skill) => (
              <option key={skill} value={skill}>
                {skill}
              </option>
            ))}
          </select>
        </div>

        {/* Show Completed Checkbox (like AHK) */}
        <label className="flex items-center space-x-2 text-sm">
          <input
            type="checkbox"
            checked={filters.showCompleted}
            onChange={(e) => updateFilter("showCompleted", e.target.checked)}
            className="rounded border-gray-300 dark:border-slate-600 text-blue-600 
                       focus:ring-blue-500 dark:bg-slate-700"
          />
          <span className="text-gray-700 dark:text-gray-300">
            Show completed
          </span>
        </label>

        {/* Advanced Filters Toggle */}
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center space-x-1 px-3 py-2 text-sm text-gray-700 dark:text-gray-300 
                     hover:bg-gray-100 dark:hover:bg-slate-700 rounded-md transition-colors"
        >
          <Filter className="w-4 h-4" />
          <span>Advanced</span>
        </button>

        {/* Clear Filters */}
        {hasActiveFilters && (
          <button
            onClick={resetFilters}
            className="flex items-center space-x-1 px-3 py-2 text-sm text-red-600 dark:text-red-400 
                       hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md transition-colors"
          >
            <X className="w-4 h-4" />
            <span>Clear</span>
          </button>
        )}
      </div>

      {/* Quick Filters (like AHK quick buttons) */}
      {showQuickFilters && (
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Quick:
          </span>
          <button
            onClick={quickFilters.todayActive}
            className="px-3 py-1 text-xs bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 
                       rounded-full hover:bg-blue-200 dark:hover:bg-blue-900/50 transition-colors"
          >
            <Target className="w-3 h-3 inline mr-1" />
            Today Active
          </button>
          <button
            onClick={quickFilters.highPriority}
            className="px-3 py-1 text-xs bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 
                       rounded-full hover:bg-red-200 dark:hover:bg-red-900/50 transition-colors"
          >
            High Priority
          </button>
          <button
            onClick={quickFilters.longStreaks}
            className="px-3 py-1 text-xs bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 
                       rounded-full hover:bg-green-200 dark:hover:bg-green-900/50 transition-colors"
          >
            <Zap className="w-3 h-3 inline mr-1" />
            Long Streaks
          </button>
          <button
            onClick={quickFilters.difficultTasks}
            className="px-3 py-1 text-xs bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 
                       rounded-full hover:bg-purple-200 dark:hover:bg-purple-900/50 transition-colors"
          >
            Difficult
          </button>
        </div>
      )}

      {/* Advanced Filter Panel */}
      {showAdvanced && (
        <div className="p-4 bg-gray-50 dark:bg-slate-700 rounded-lg border border-gray-200 dark:border-slate-600">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {/* Status Filters */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Status
              </label>
              <div className="space-y-2">
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filters.showActive}
                    onChange={(e) =>
                      updateFilter("showActive", e.target.checked)
                    }
                    className="rounded border-gray-300 dark:border-slate-600 text-blue-600"
                  />
                  <span className="text-sm">Active</span>
                </label>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={filters.showPaused}
                    onChange={(e) =>
                      updateFilter("showPaused", e.target.checked)
                    }
                    className="rounded border-gray-300 dark:border-slate-600 text-blue-600"
                  />
                  <span className="text-sm">Paused</span>
                </label>
              </div>
            </div>

            {/* Difficulty Range */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Difficulty: {filters.difficultyRange[0]} -{" "}
                {filters.difficultyRange[1]}
              </label>
              <div className="space-y-2">
                <input
                  type="range"
                  min={filterOptions.difficultyRange[0]}
                  max={filterOptions.difficultyRange[1]}
                  value={filters.difficultyRange[0]}
                  onChange={(e) =>
                    updateFilter("difficultyRange", [
                      parseInt(e.target.value),
                      filters.difficultyRange[1],
                    ])
                  }
                  className="w-full"
                />
                <input
                  type="range"
                  min={filterOptions.difficultyRange[0]}
                  max={filterOptions.difficultyRange[1]}
                  value={filters.difficultyRange[1]}
                  onChange={(e) =>
                    updateFilter("difficultyRange", [
                      filters.difficultyRange[0],
                      parseInt(e.target.value),
                    ])
                  }
                  className="w-full"
                />
              </div>
            </div>

            {/* Sorting */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Sort By
              </label>
              <div className="flex space-x-2">
                <select
                  value={filters.sortBy}
                  onChange={(e) =>
                    updateFilter("sortBy", e.target.value as any)
                  }
                  className="flex-1 px-2 py-1 text-sm border border-gray-300 dark:border-slate-600 rounded 
                             bg-white dark:bg-slate-700"
                >
                  <option value="name">Name</option>
                  <option value="difficulty">Difficulty</option>
                  <option value="importance">Importance</option>
                  <option value="created">Created</option>
                  <option value="streak">Streak</option>
                  <option value="completion">Completion</option>
                </select>
                <button
                  onClick={() =>
                    updateFilter(
                      "sortOrder",
                      filters.sortOrder === "asc" ? "desc" : "asc"
                    )
                  }
                  className="px-2 py-1 border border-gray-300 dark:border-slate-600 rounded 
                             hover:bg-gray-100 dark:hover:bg-slate-600 transition-colors"
                >
                  {filters.sortOrder === "asc" ? (
                    <SortAsc className="w-4 h-4" />
                  ) : (
                    <SortDesc className="w-4 h-4" />
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filter Stats */}
      <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
        <div className="flex items-center space-x-4">
          <span>
            Showing {filteredCount.toLocaleString()} of{" "}
            {totalCount.toLocaleString()} items
            {filteredPercentage < 100 && (
              <span className="ml-1">({filteredPercentage.toFixed(1)}%)</span>
            )}
          </span>
          {hasActiveFilters && (
            <div className="flex flex-wrap items-center gap-1">
              <span>Filters:</span>
              {activeFilters.map((filter, index) => (
                <span
                  key={index}
                  className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 
                             rounded text-xs"
                >
                  {filter}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdvancedFilterBar;
