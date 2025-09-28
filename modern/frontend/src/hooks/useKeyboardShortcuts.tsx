// Keyboard Shortcuts System - AHK-inspired hotkeys for power users
import { useEffect, useCallback, useState } from "react";

interface KeyboardShortcut {
  key: string;
  description: string;
  action: () => void;
  category: string;
}

interface ShortcutCategory {
  name: string;
  shortcuts: KeyboardShortcut[];
}

export const useKeyboardShortcuts = () => {
  const [shortcuts] = useState<KeyboardShortcut[]>([
    // Navigation shortcuts (like AHK Alt+ combinations)
    {
      key: "Alt+A",
      description: "Add new habit/project",
      action: () => triggerAction("add-habit"),
      category: "Navigation",
    },
    {
      key: "Alt+E",
      description: "Edit selected item",
      action: () => triggerAction("edit-item"),
      category: "Navigation",
    },
    {
      key: "Alt+C",
      description: "Focus search box",
      action: () => triggerAction("focus-search"),
      category: "Navigation",
    },
    {
      key: "Alt+R",
      description: "Remove/delete selected",
      action: () => triggerAction("remove-item"),
      category: "Navigation",
    },
    {
      key: "Alt+D",
      description: "Mark as done",
      action: () => triggerAction("mark-done"),
      category: "Actions",
    },

    // View shortcuts (like AHK function keys)
    {
      key: "F2",
      description: "Toggle HUD visibility",
      action: () => triggerAction("toggle-hud"),
      category: "View",
    },
    {
      key: "F3",
      description: "Show skills view",
      action: () => triggerAction("show-skills"),
      category: "View",
    },
    {
      key: "F4",
      description: "Show analytics",
      action: () => triggerAction("show-analytics"),
      category: "View",
    },
    {
      key: "Ctrl+/",
      description: "Show keyboard shortcuts",
      action: () => triggerAction("show-shortcuts"),
      category: "Help",
    },

    // Quick actions
    {
      key: "Space",
      description: "Quick complete selected habit",
      action: () => triggerAction("quick-complete"),
      category: "Actions",
    },
    {
      key: "Escape",
      description: "Close dialogs/cancel",
      action: () => triggerAction("cancel"),
      category: "Actions",
    },
    {
      key: "Enter",
      description: "Confirm/submit",
      action: () => triggerAction("confirm"),
      category: "Actions",
    },

    // List navigation
    {
      key: "ArrowUp",
      description: "Select previous item",
      action: () => triggerAction("select-previous"),
      category: "Navigation",
    },
    {
      key: "ArrowDown",
      description: "Select next item",
      action: () => triggerAction("select-next"),
      category: "Navigation",
    },

    // Filters (like AHK dropdown shortcuts)
    {
      key: "Ctrl+1",
      description: "Filter by high importance",
      action: () => triggerAction("filter-high"),
      category: "Filters",
    },
    {
      key: "Ctrl+2",
      description: "Filter by medium importance",
      action: () => triggerAction("filter-medium"),
      category: "Filters",
    },
    {
      key: "Ctrl+3",
      description: "Filter by low importance",
      action: () => triggerAction("filter-low"),
      category: "Filters",
    },
    {
      key: "Ctrl+0",
      description: "Clear all filters",
      action: () => triggerAction("clear-filters"),
      category: "Filters",
    },
  ]);

  const triggerAction = (actionType: string) => {
    // Dispatch custom events that components can listen to
    window.dispatchEvent(
      new CustomEvent("keyboard-action", {
        detail: { actionType },
      })
    );
  };

  const buildKeyCombo = (e: KeyboardEvent): string => {
    const parts: string[] = [];

    if (e.ctrlKey) parts.push("Ctrl");
    if (e.altKey) parts.push("Alt");
    if (e.shiftKey) parts.push("Shift");
    if (e.metaKey) parts.push("Cmd");

    // Handle special keys
    const specialKeys: Record<string, string> = {
      ArrowUp: "ArrowUp",
      ArrowDown: "ArrowDown",
      ArrowLeft: "ArrowLeft",
      ArrowRight: "ArrowRight",
      Enter: "Enter",
      Escape: "Escape",
      " ": "Space",
      F1: "F1",
      F2: "F2",
      F3: "F3",
      F4: "F4",
      F5: "F5",
      F6: "F6",
      F7: "F7",
      F8: "F8",
      F9: "F9",
      F10: "F10",
      F11: "F11",
      F12: "F12",
      "/": "/",
    };

    const key = specialKeys[e.key] || e.key.toUpperCase();
    parts.push(key);

    return parts.join("+");
  };

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      // Don't trigger shortcuts when typing in inputs
      const activeElement = document.activeElement;
      const isInputFocused =
        activeElement &&
        (activeElement.tagName === "INPUT" ||
          activeElement.tagName === "TEXTAREA" ||
          activeElement.hasAttribute("contenteditable"));

      // Allow some shortcuts even in inputs
      const allowedInInputs = ["Escape", "Enter", "F2", "Ctrl+/", "Alt+C"];
      const combo = buildKeyCombo(e);

      if (isInputFocused && !allowedInInputs.includes(combo)) {
        return;
      }

      const shortcut = shortcuts.find((s) => s.key === combo);
      if (shortcut) {
        e.preventDefault();
        e.stopPropagation();
        shortcut.action();
      }
    };

    document.addEventListener("keydown", handleKeyPress);
    return () => document.removeEventListener("keydown", handleKeyPress);
  }, [shortcuts]);

  const getShortcutsByCategory = (): ShortcutCategory[] => {
    const categories = [...new Set(shortcuts.map((s) => s.category))];
    return categories.map((category) => ({
      name: category,
      shortcuts: shortcuts.filter((s) => s.category === category),
    }));
  };

  return { shortcuts, getShortcutsByCategory };
};

// Keyboard Shortcuts Help Modal
export const KeyboardShortcutsHelp: React.FC<{
  isOpen: boolean;
  onClose: () => void;
}> = ({ isOpen, onClose }) => {
  const { getShortcutsByCategory } = useKeyboardShortcuts();
  const categories = getShortcutsByCategory();

  useEffect(() => {
    const handleKeyPress = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleKeyPress);
      return () => document.removeEventListener("keydown", handleKeyPress);
    }
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-4">
      <div className="bg-white dark:bg-slate-800 rounded-lg shadow-2xl max-w-2xl w-full max-h-[80vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200 dark:border-slate-700">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
              ⌨️ Keyboard Shortcuts
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 text-2xl"
            >
              ×
            </button>
          </div>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Power-user shortcuts inspired by the legacy AutoHotkey version
          </p>
        </div>

        <div className="p-6 space-y-6">
          {categories.map((category) => (
            <div key={category.name}>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3">
                {category.name}
              </h3>
              <div className="grid gap-2">
                {category.shortcuts.map((shortcut) => (
                  <div
                    key={shortcut.key}
                    className="flex items-center justify-between p-2 rounded hover:bg-gray-50 dark:hover:bg-slate-700"
                  >
                    <span className="text-gray-700 dark:text-gray-300">
                      {shortcut.description}
                    </span>
                    <kbd className="px-2 py-1 bg-gray-100 dark:bg-slate-600 text-gray-800 dark:text-gray-200 rounded text-sm font-mono">
                      {shortcut.key}
                    </kbd>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="p-6 border-t border-gray-200 dark:border-slate-700 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Press{" "}
            <kbd className="px-1 py-0.5 bg-gray-100 dark:bg-slate-600 rounded text-xs font-mono">
              Escape
            </kbd>{" "}
            to close
          </p>
        </div>
      </div>
    </div>
  );
};

// Hook to listen for keyboard actions in components
export const useKeyboardActions = () => {
  const [lastAction, setLastAction] = useState<string | null>(null);

  useEffect(() => {
    const handleKeyboardAction = (event: CustomEvent) => {
      setLastAction(event.detail.actionType);

      // Clear the action after a brief moment so components can react
      setTimeout(() => setLastAction(null), 100);
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
  }, []);

  return { lastAction };
};

// Context provider for keyboard shortcuts
import React, { createContext, useContext, ReactNode } from "react";

interface KeyboardShortcutsContextType {
  shortcuts: KeyboardShortcut[];
  getShortcutsByCategory: () => ShortcutCategory[];
}

const KeyboardShortcutsContext = createContext<
  KeyboardShortcutsContextType | undefined
>(undefined);

export const KeyboardShortcutsProvider: React.FC<{ children: ReactNode }> = ({
  children,
}) => {
  const { shortcuts, getShortcutsByCategory } = useKeyboardShortcuts();

  return (
    <KeyboardShortcutsContext.Provider
      value={{ shortcuts, getShortcutsByCategory }}
    >
      {children}
    </KeyboardShortcutsContext.Provider>
  );
};

export const useKeyboardShortcutsContext = () => {
  const context = useContext(KeyboardShortcutsContext);
  if (!context) {
    throw new Error(
      "useKeyboardShortcutsContext must be used within KeyboardShortcutsProvider"
    );
  }
  return context;
};
