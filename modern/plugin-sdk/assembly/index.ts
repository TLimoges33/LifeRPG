// LifeRPG Plugin SDK for AssemblyScript

// Import AssemblyScript builtins
import { Console } from "as-console";

// Type definitions for LifeRPG entities
export class Habit {
  id: i32;
  title: string;
  description: string;
  frequency: string;
  difficulty: i32;
  tags: string[];
  streak: i32;
  isComplete: boolean;

  constructor(
    id: i32,
    title: string,
    description: string,
    frequency: string,
    difficulty: i32
  ) {
    this.id = id;
    this.title = title;
    this.description = description;
    this.frequency = frequency;
    this.difficulty = difficulty;
    this.tags = [];
    this.streak = 0;
    this.isComplete = false;
  }
}

export class Project {
  id: i32;
  title: string;
  description: string;
  status: string;
  priority: i32;
  dueDate: string;
  progress: f32;

  constructor(
    id: i32,
    title: string,
    description: string
  ) {
    this.id = id;
    this.title = title;
    this.description = description;
    this.status = "pending";
    this.priority = 1;
    this.dueDate = "";
    this.progress = 0;
  }
}

// External functions defined by the host environment
// These are implemented in the JavaScript runtime

// Console logging
@external("env", "console_log")
declare function consoleLog(message: string): void;

// API access functions
@external("env", "get_habits")
declare function getHabitsRaw(): string;

@external("env", "get_projects")
declare function getProjectsRaw(): string;

@external("env", "complete_habit")
declare function completeHabitRaw(habitId: i32): bool;

@external("env", "register_dashboard_widget")
declare function registerDashboardWidgetRaw(id: string, title: string, html: string): bool;

@external("env", "register_menu_item")
declare function registerMenuItemRaw(id: string, title: string, path: string): bool;

@external("env", "get_plugin_storage")
declare function getPluginStorageRaw(key: string): string;

@external("env", "set_plugin_storage")
declare function setPluginStorageRaw(key: string, value: string): bool;

// Utility class for JSON parsing (simplified)
export class JSON {
  static parse<T>(text: string): T {
    // This is a placeholder. In a real implementation, we would
    // need a proper JSON parser for AssemblyScript
    // For now, plugins must use the raw string data
    return text as unknown as T;
  }

  static stringify<T>(value: T): string {
    // This is a placeholder. In a real implementation, we would
    // need a proper JSON serializer for AssemblyScript
    return value as unknown as string;
  }
}

// API wrappers for cleaner usage in plugins
export class API {
  // Habit API
  static getHabits(): Habit[] {
    const habitsJson = getHabitsRaw();
    // In a real implementation, we would parse the JSON
    // For now, this is a placeholder
    return [] as Habit[];
  }

  static completeHabit(habitId: i32): boolean {
    return completeHabitRaw(habitId);
  }

  // Project API
  static getProjects(): Project[] {
    const projectsJson = getProjectsRaw();
    // In a real implementation, we would parse the JSON
    // For now, this is a placeholder
    return [] as Project[];
  }

  // UI API
  static registerDashboardWidget(id: string, title: string, html: string): boolean {
    return registerDashboardWidgetRaw(id, title, html);
  }

  static registerMenuItem(id: string, title: string, path: string): boolean {
    return registerMenuItemRaw(id, title, path);
  }

  // Storage API
  static getStorage(key: string): string {
    return getPluginStorageRaw(key);
  }

  static setStorage(key: string, value: string): boolean {
    return setPluginStorageRaw(key, value);
  }
}

// Plugin context provided to the initialize function
export class PluginContext {
  // Logger
  log(message: string): void {
    consoleLog(message);
  }

  // API access
  api: API = new API();
}

/**
 * LifeRPG Plugin SDK - AssemblyScript Example
 * 
 * This is an example plugin that demonstrates how to create a simple
 * dashboard widget and interact with the LifeRPG host application.
 */

// Import host functions (these are provided by the WASM runtime)
declare function console_log(ptr: usize, len: usize): void;
declare function console_error(ptr: usize, len: usize): void;
declare function get_habits(): usize;
declare function create_habit(name_ptr: usize, name_len: usize): i32;
declare function register_dashboard_widget(config_ptr: usize, config_len: usize): i32;

// Memory allocation functions (required by WASM runtime)
export function plugin_alloc(size: usize): usize {
  return heap.alloc(size);
}

export function plugin_free(ptr: usize): void {
  heap.free(ptr);
}

// Utility functions for string handling
function stringToWasm(str: string): usize {
  const buffer = String.UTF8.encode(str);
  const ptr = plugin_alloc(buffer.byteLength);
  memory.copy(ptr, buffer.dataStart, buffer.byteLength);
  return ptr;
}

function log(message: string): void {
  const ptr = stringToWasm(message);
  console_log(ptr, String.UTF8.encode(message).byteLength);
  plugin_free(ptr);
}

function logError(message: string): void {
  const ptr = stringToWasm(message);
  console_error(ptr, String.UTF8.encode(message).byteLength);
  plugin_free(ptr);
}

// Plugin main entry point
export function initialize(): void {
  log("Example Plugin: Initializing...");

  // Register a dashboard widget
  const widgetConfig = `{
    "id": "example-widget",
    "title": "Example Plugin Widget",
    "description": "A simple example widget from a WASM plugin",
    "size": "medium"
  }`;

  const configPtr = stringToWasm(widgetConfig);
  const result = register_dashboard_widget(configPtr, String.UTF8.encode(widgetConfig).byteLength);
  plugin_free(configPtr);

  if (result === 1) {
    log("Example Plugin: Dashboard widget registered successfully");
  } else {
    logError("Example Plugin: Failed to register dashboard widget");
  }

  log("Example Plugin: Initialization complete");
}

// Plugin cleanup function (called when plugin is unloaded)
export function cleanup(): void {
  log("Example Plugin: Cleaning up...");
  // Perform any necessary cleanup here
}

// Example function to create a habit
export function createExampleHabit(): i32 {
  log("Example Plugin: Creating example habit...");

  const habitName = "Example Habit from Plugin";
  const namePtr = stringToWasm(habitName);
  const habitId = create_habit(namePtr, String.UTF8.encode(habitName).byteLength);
  plugin_free(namePtr);

  if (habitId > 0) {
    log(`Example Plugin: Created habit with ID: ${habitId}`);
  } else {
    logError("Example Plugin: Failed to create habit");
  }

  return habitId;
}

// Example function to get and display habits
export function displayHabits(): void {
  log("Example Plugin: Fetching habits...");

  const habitsPtr = get_habits();
  if (habitsPtr === 0) {
    logError("Example Plugin: Failed to fetch habits");
    return;
  }

  // In a real implementation, you would parse the JSON data here
  // For now, just log that we received data
  log("Example Plugin: Successfully fetched habits data");

  // Note: In a real plugin, you would need to properly parse the JSON
  // and potentially free the memory allocated by the host
}
