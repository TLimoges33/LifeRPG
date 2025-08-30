/**
 * LifeRPG Plugin Manager
 * 
 * Manages the loading, registration, and execution of plugins in the frontend.
 */
import { useState, useEffect, useCallback } from 'react';

// Types for plugin system
export interface PluginMetadata {
  id: string;
  name: string;
  version: string;
  author: string;
  description: string;
  homepage?: string;
  targetApiVersion: string;
  minAppVersion: string;
  permissions: string[];
  extensionPoints: string[];
  entryPoint: string;
  resourceLimits: {
    memoryMb: number;
    storageMb: number;
    cpuLimit: 'low' | 'moderate' | 'high';
  };
  createdAt: string;
  updatedAt: string;
  status: 'active' | 'disabled' | 'pending_review' | 'rejected';
}

export interface PluginInstance {
  metadata: PluginMetadata;
  instance: any;
  extensionPoints: Record<string, any[]>;
}

export interface PluginManagerContextType {
  plugins: PluginInstance[];
  installedPlugins: PluginMetadata[];
  loadingPlugins: boolean;
  installPlugin: (file: File) => Promise<void>;
  uninstallPlugin: (pluginId: string) => Promise<void>;
  enablePlugin: (pluginId: string) => Promise<void>;
  disablePlugin: (pluginId: string) => Promise<void>;
  getExtensions: (extensionPoint: string) => any[];
}

/**
 * Hook for using the plugin manager
 */
export const usePluginManager = () => {
  const [plugins, setPlugins] = useState<PluginInstance[]>([]);
  const [installedPlugins, setInstalledPlugins] = useState<PluginMetadata[]>([]);
  const [loadingPlugins, setLoadingPlugins] = useState(true);

  // Fetch installed plugins from the backend
  const fetchInstalledPlugins = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/plugins');
      if (!response.ok) {
        throw new Error('Failed to fetch plugins');
      }
      const data = await response.json();
      setInstalledPlugins(data);
    } catch (error) {
      console.error('Error fetching plugins:', error);
    } finally {
      setLoadingPlugins(false);
    }
  }, []);

  // Load a plugin from its WASM binary
  const loadPlugin = useCallback(async (metadata: PluginMetadata) => {
    try {
      // Fetch the WASM binary
      const response = await fetch(`/api/v1/plugins/${metadata.id}/wasm`);
      if (!response.ok) {
        throw new Error(`Failed to fetch WASM for plugin ${metadata.id}`);
      }

      const wasmBinary = await response.arrayBuffer();

      // Create a new WebAssembly instance
      const wasmModule = await WebAssembly.compile(wasmBinary);
      const instance = await WebAssembly.instantiate(wasmModule, {
        // Define the host environment
        env: {
          // Console logging
          console_log: (ptr, len) => {
            // Implementation of console.log for WASM
            // This would need to read from WASM memory
          },

          // API access functions
          // These would be implemented to provide controlled access to app functionality
        }
      });

      // Call the entry point function
      const entryPoint = metadata.entryPoint || 'initialize';
      if (typeof instance.exports[entryPoint] === 'function') {
        instance.exports[entryPoint]();
      } else {
        console.warn(`Entry point ${entryPoint} not found in plugin ${metadata.id}`);
      }

      // Add the plugin to the list
      setPlugins(prev => [
        ...prev,
        {
          metadata,
          instance,
          extensionPoints: {} // Would be populated during initialization
        }
      ]);

      console.log(`Plugin ${metadata.name} v${metadata.version} loaded successfully`);
    } catch (error) {
      console.error(`Error loading plugin ${metadata.id}:`, error);
    }
  }, []);

  // Load all active plugins
  useEffect(() => {
    const loadActivePlugins = async () => {
      setLoadingPlugins(true);

      try {
        // Fetch active plugins
        const response = await fetch('/api/v1/plugins?status=active');
        if (!response.ok) {
          throw new Error('Failed to fetch active plugins');
        }

        const activePlugins = await response.json();

        // Load each plugin
        for (const plugin of activePlugins) {
          await loadPlugin(plugin);
        }
      } catch (error) {
        console.error('Error loading active plugins:', error);
      } finally {
        setLoadingPlugins(false);
      }
    };

    loadActivePlugins();
    fetchInstalledPlugins();
  }, [loadPlugin, fetchInstalledPlugins]);

  // Install a new plugin
  const installPlugin = useCallback(async (file: File) => {
    setLoadingPlugins(true);

    try {
      // Read the file as an ArrayBuffer
      const fileBuffer = await file.arrayBuffer();

      // Create form data
      const formData = new FormData();
      formData.append('wasm_file', new Blob([fileBuffer]));

      // Add metadata from the plugin manifest
      // In a real implementation, we would extract this from the plugin package
      const metadata = {
        id: 'example-plugin',
        name: 'Example Plugin',
        version: '1.0.0',
        author: 'Plugin Author',
        description: 'An example plugin',
        targetApiVersion: '1.0',
        minAppVersion: '1.0.0',
        permissions: [],
        extensionPoints: [],
        entryPoint: 'initialize'
      };

      formData.append('metadata', JSON.stringify(metadata));

      // Upload the plugin
      const response = await fetch('/api/v1/plugins', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Failed to install plugin');
      }

      // Refresh the plugin list
      await fetchInstalledPlugins();

      // Load the plugin if it's active
      const responseData = await response.json();
      if (responseData.status === 'active') {
        await loadPlugin(metadata);
      }
    } catch (error) {
      console.error('Error installing plugin:', error);
    } finally {
      setLoadingPlugins(false);
    }
  }, [fetchInstalledPlugins, loadPlugin]);

  // Uninstall a plugin
  const uninstallPlugin = useCallback(async (pluginId: string) => {
    setLoadingPlugins(true);

    try {
      const response = await fetch(`/api/v1/plugins/${pluginId}`, {
        method: 'DELETE'
      });

      if (!response.ok) {
        throw new Error(`Failed to uninstall plugin ${pluginId}`);
      }

      // Remove the plugin from the list
      setPlugins(prev => prev.filter(p => p.metadata.id !== pluginId));

      // Refresh the installed plugins list
      await fetchInstalledPlugins();
    } catch (error) {
      console.error(`Error uninstalling plugin ${pluginId}:`, error);
    } finally {
      setLoadingPlugins(false);
    }
  }, [fetchInstalledPlugins]);

  // Enable a plugin
  const enablePlugin = useCallback(async (pluginId: string) => {
    try {
      const response = await fetch(`/api/v1/plugins/${pluginId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'active' })
      });

      if (!response.ok) {
        throw new Error(`Failed to enable plugin ${pluginId}`);
      }

      // Refresh the installed plugins list
      await fetchInstalledPlugins();

      // Load the plugin
      const plugin = installedPlugins.find(p => p.id === pluginId);
      if (plugin) {
        await loadPlugin(plugin);
      }
    } catch (error) {
      console.error(`Error enabling plugin ${pluginId}:`, error);
    }
  }, [fetchInstalledPlugins, installedPlugins, loadPlugin]);

  // Disable a plugin
  const disablePlugin = useCallback(async (pluginId: string) => {
    try {
      const response = await fetch(`/api/v1/plugins/${pluginId}/status`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: 'disabled' })
      });

      if (!response.ok) {
        throw new Error(`Failed to disable plugin ${pluginId}`);
      }

      // Remove the plugin from the active list
      setPlugins(prev => prev.filter(p => p.metadata.id !== pluginId));

      // Refresh the installed plugins list
      await fetchInstalledPlugins();
    } catch (error) {
      console.error(`Error disabling plugin ${pluginId}:`, error);
    }
  }, [fetchInstalledPlugins]);

  // Get extensions for a specific extension point
  const getExtensions = useCallback((extensionPoint: string) => {
    return plugins.flatMap(plugin =>
      plugin.extensionPoints[extensionPoint] || []
    );
  }, [plugins]);

  return {
    plugins,
    installedPlugins,
    loadingPlugins,
    installPlugin,
    uninstallPlugin,
    enablePlugin,
    disablePlugin,
    getExtensions
  };
};

export default usePluginManager;
