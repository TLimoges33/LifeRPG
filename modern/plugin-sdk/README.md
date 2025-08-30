# LifeRPG Plugin SDK

This SDK allows you to create plugins for the LifeRPG application using AssemblyScript, which compiles to WebAssembly.

## Getting Started

### Prerequisites

- Node.js 18 or later
- npm or yarn

### Installation

```bash
npm install @liferpg/plugin-sdk
```

### Creating a Simple Plugin

1. Create a new directory for your plugin:

```bash
mkdir my-liferpg-plugin
cd my-liferpg-plugin
```

2. Initialize a new npm project:

```bash
npm init -y
```

3. Install the LifeRPG Plugin SDK:

```bash
npm install @liferpg/plugin-sdk
```

4. Create an `assembly` directory and add your plugin code:

```bash
mkdir assembly
```

5. Create a file `assembly/index.ts` with the following content:

```typescript
import { PluginContext, API } from "@liferpg/plugin-sdk";

// Export the initialize function
export function initialize(context: PluginContext): void {
  // Log a message
  context.log("My plugin initialized!");
  
  // Register a dashboard widget
  context.api.registerDashboardWidget(
    "my-widget",
    "My Custom Widget",
    "<div>Hello from my plugin!</div>"
  );
}
```

6. Add a build script to your `package.json`:

```json
{
  "scripts": {
    "build": "asc assembly/index.ts --target release"
  }
}
```

7. Build your plugin:

```bash
npm run build
```

This will create a `.wasm` file in the `build` directory.

## Plugin API Reference

### PluginContext

The `PluginContext` is passed to your plugin's initialize function and provides access to the LifeRPG API.

#### Methods

- `log(message: string): void` - Log a message to the console

### API

The API object provides access to LifeRPG data and functionality.

#### Habits

- `getHabits(): Habit[]` - Get all habits
- `completeHabit(habitId: i32): boolean` - Complete a habit

#### Projects

- `getProjects(): Project[]` - Get all projects

#### UI

- `registerDashboardWidget(id: string, title: string, html: string): boolean` - Register a dashboard widget
- `registerMenuItem(id: string, title: string, path: string): boolean` - Register a menu item

#### Storage

- `getStorage(key: string): string` - Get a value from plugin storage
- `setStorage(key: string, value: string): boolean` - Store a value in plugin storage

## Example Plugins

### Pomodoro Timer

```typescript
import { PluginContext, API } from "@liferpg/plugin-sdk";

export function initialize(context: PluginContext): void {
  context.log("Pomodoro plugin initialized");
  
  // Register a dashboard widget with a Pomodoro timer
  context.api.registerDashboardWidget(
    "pomodoro-timer",
    "Pomodoro Timer",
    `
    <div class="pomodoro-timer">
      <div class="timer">25:00</div>
      <button class="start-button">Start</button>
      <button class="reset-button">Reset</button>
    </div>
    <script>
      // Timer implementation would go here
      // This script will run in a sandbox
    </script>
    `
  );
}
```

### GitHub Integration

```typescript
import { PluginContext, API } from "@liferpg/plugin-sdk";

export function initialize(context: PluginContext): void {
  context.log("GitHub plugin initialized");
  
  // Register a dashboard widget showing GitHub stats
  context.api.registerDashboardWidget(
    "github-stats",
    "GitHub Activity",
    `
    <div class="github-stats">
      <h3>Recent Commits</h3>
      <div class="commits-list">
        Loading commits...
      </div>
    </div>
    `
  );
  
  // Register a settings page for GitHub authentication
  context.api.registerMenuItem(
    "github-settings",
    "GitHub Integration",
    "/settings/github"
  );
}
```

## Building and Packaging

To build your plugin for distribution:

```bash
npm run build
```

This will generate a WebAssembly binary that can be uploaded to LifeRPG.

## Plugin Manifest

Each plugin must provide a manifest (automatically generated during build):

```json
{
  "id": "com.example.myplugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "A custom plugin for LifeRPG",
  "targetApiVersion": "1.0",
  "minAppVersion": "1.0.0",
  "permissions": [
    "habits:read",
    "ui:dashboard"
  ],
  "extensionPoints": [
    "dashboard.widget"
  ],
  "entryPoint": "initialize"
}
```

## Security Considerations

Plugins run in a sandboxed WebAssembly environment with the following restrictions:

- Limited memory allocation
- No direct DOM access
- Controlled API access based on permissions
- Storage quotas

## License

MIT
