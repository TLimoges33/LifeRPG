import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';

/**
 * PluginWidget - Renders a widget from a plugin
 */
const PluginWidget = ({ widget }) => {
    const [content, setContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        renderWidget();
    }, [widget]);

    const renderWidget = async () => {
        try {
            setLoading(true);
            setError(null);

            // In a real implementation, this would call the plugin's render function
            // For now, we'll just show the widget configuration
            const mockContent = `
        <div class="p-4">
          <h3 class="text-lg font-semibold">${widget.config.title || 'Plugin Widget'}</h3>
          <p class="text-gray-600">Plugin ID: ${widget.plugin_id}</p>
          <p class="text-gray-600">Widget ID: ${widget.id}</p>
          <div class="mt-4">
            <p>This is a placeholder for plugin-rendered content.</p>
            <p>In a real implementation, the plugin's WASM code would generate this content.</p>
          </div>
        </div>
      `;

            setContent(mockContent);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <Card>
                <CardContent className="p-4">
                    <div className="animate-pulse">
                        <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                        <div className="h-4 bg-gray-200 rounded w-1/2"></div>
                    </div>
                </CardContent>
            </Card>
        );
    }

    if (error) {
        return (
            <Card>
                <CardContent className="p-4">
                    <div className="text-red-600">
                        <p className="font-semibold">Widget Error</p>
                        <p className="text-sm">{error}</p>
                    </div>
                </CardContent>
            </Card>
        );
    }

    return (
        <Card>
            <div dangerouslySetInnerHTML={{ __html: content }} />
        </Card>
    );
};

/**
 * PluginExtensionContainer - Container for plugin extensions
 */
const PluginExtensionContainer = ({ extensionPoint }) => {
    const [extensions, setExtensions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchExtensions();
    }, [extensionPoint]);

    const fetchExtensions = async () => {
        try {
            const response = await fetch('/api/v1/plugins/extension-points');
            if (!response.ok) {
                throw new Error('Failed to fetch extension points');
            }

            const data = await response.json();
            const extensionData = data.extension_points[extensionPoint] || [];
            setExtensions(extensionData);
        } catch (error) {
            console.error('Error fetching extensions:', error);
        } finally {
            setLoading(false);
        }
    };

    if (loading) {
        return (
            <div className="space-y-4">
                <div className="animate-pulse">
                    <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
                    <div className="h-32 bg-gray-200 rounded"></div>
                </div>
            </div>
        );
    }

    if (extensions.length === 0) {
        return null; // Don't render anything if no extensions
    }

    return (
        <div className="space-y-4">
            <h3 className="text-lg font-semibold">Plugin Extensions</h3>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                {extensions.map((extension, index) => (
                    <PluginWidget key={`${extension.plugin_id}-${index}`} widget={extension} />
                ))}
            </div>
        </div>
    );
};

export { PluginWidget, PluginExtensionContainer };
export default PluginExtensionContainer;
