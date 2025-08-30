import React, { useState } from 'react';
import usePluginManager, { PluginMetadata } from './PluginManager';

/**
 * Plugin administration component
 */
export const PluginAdmin: React.FC = () => {
  const {
    installedPlugins,
    loadingPlugins,
    installPlugin,
    uninstallPlugin,
    enablePlugin,
    disablePlugin
  } = usePluginManager();

  const [uploadFile, setUploadFile] = useState<File | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      setUploadFile(e.target.files[0]);
    }
  };

  const handleInstall = async () => {
    if (uploadFile) {
      await installPlugin(uploadFile);
      setUploadFile(null);
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Plugin Management</h2>

      {/* Plugin uploader */}
      <div className="bg-card border border-border rounded-lg p-4 mb-6">
        <h3 className="text-lg font-semibold mb-2">Install New Plugin</h3>
        <div className="flex gap-2">
          <input
            type="file"
            accept=".wasm,.zip"
            onChange={handleFileChange}
            className="flex-1 border border-border rounded p-2"
          />
          <button
            onClick={handleInstall}
            disabled={!uploadFile}
            className="bg-primary text-primary-foreground px-4 py-2 rounded font-medium disabled:opacity-50"
          >
            Install
          </button>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Upload a plugin in .wasm or .zip format.
        </p>
      </div>

      {/* Installed plugins list */}
      <div className="bg-card border border-border rounded-lg p-4">
        <h3 className="text-lg font-semibold mb-2">Installed Plugins</h3>

        {loadingPlugins ? (
          <div className="text-center py-8">Loading plugins...</div>
        ) : installedPlugins.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            No plugins installed
          </div>
        ) : (
          <div className="divide-y divide-border">
            {installedPlugins.map((plugin) => (
              <PluginItem
                key={plugin.id}
                plugin={plugin}
                onEnable={() => enablePlugin(plugin.id)}
                onDisable={() => disablePlugin(plugin.id)}
                onUninstall={() => uninstallPlugin(plugin.id)}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * Individual plugin item component
 */
interface PluginItemProps {
  plugin: PluginMetadata;
  onEnable: () => void;
  onDisable: () => void;
  onUninstall: () => void;
}

const PluginItem: React.FC<PluginItemProps> = ({
  plugin,
  onEnable,
  onDisable,
  onUninstall
}) => {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="py-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="font-medium">{plugin.name}</h4>
          <p className="text-sm text-muted-foreground">v{plugin.version}</p>
        </div>

        <div className="flex items-center gap-2">
          {plugin.status === 'active' ? (
            <button
              onClick={onDisable}
              className="bg-secondary text-secondary-foreground px-3 py-1 rounded-md text-sm"
            >
              Disable
            </button>
          ) : (
            <button
              onClick={onEnable}
              className="bg-primary text-primary-foreground px-3 py-1 rounded-md text-sm"
              disabled={plugin.status === 'rejected'}
            >
              Enable
            </button>
          )}

          <button
            onClick={onUninstall}
            className="bg-destructive text-destructive-foreground px-3 py-1 rounded-md text-sm"
          >
            Uninstall
          </button>

          <button
            onClick={() => setExpanded(!expanded)}
            className="ml-2 text-muted-foreground"
          >
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      {expanded && (
        <div className="mt-2 text-sm">
          <p className="mb-2">{plugin.description}</p>

          <div className="grid grid-cols-2 gap-x-4 gap-y-1">
            <div>
              <span className="font-medium">Author:</span> {plugin.author}
            </div>
            <div>
              <span className="font-medium">Status:</span> {plugin.status}
            </div>
            <div>
              <span className="font-medium">API Version:</span> {plugin.targetApiVersion}
            </div>
            <div>
              <span className="font-medium">Min App Version:</span> {plugin.minAppVersion}
            </div>
          </div>

          {plugin.permissions.length > 0 && (
            <div className="mt-2">
              <span className="font-medium">Permissions:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {plugin.permissions.map((perm) => (
                  <span
                    key={perm}
                    className="bg-secondary px-2 py-0.5 rounded-full text-xs"
                  >
                    {perm}
                  </span>
                ))}
              </div>
            </div>
          )}

          {plugin.extensionPoints.length > 0 && (
            <div className="mt-2">
              <span className="font-medium">Extension Points:</span>
              <div className="flex flex-wrap gap-1 mt-1">
                {plugin.extensionPoints.map((ext) => (
                  <span
                    key={ext}
                    className="bg-secondary px-2 py-0.5 rounded-full text-xs"
                  >
                    {ext}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default PluginAdmin;
