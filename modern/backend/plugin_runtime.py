"""
WASM Plugin Runtime for LifeRPG

This module provides a secure sandboxed environment for executing WASM plugins
with controlled access to host functions and resource limits.
"""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import threading
import queue

# For WASM runtime, we'll use wasmtime-py
try:
    import wasmtime
except ImportError:
    wasmtime = None
    logging.warning("wasmtime-py not installed. Plugin execution will be limited.")

from plugins import PluginMetadata, PluginPermission

logger = logging.getLogger("liferpg.plugin_runtime")


class ResourceMonitor:
    """Enhanced resource monitoring with security controls."""
    
    def __init__(self, limits: Dict[str, Any]):
        self.memory_limit_mb = limits.get('memory_mb', 16)
        self.cpu_time_limit = limits.get('cpu_time_seconds', 5.0)
        self.network_requests_limit = limits.get('network_requests', 0)  # Default: no network
        self.file_operations_limit = limits.get('file_operations', 0)  # Default: no file access
        self.start_time = None
        self.peak_memory = 0
        self.network_requests_count = 0
        self.file_operations_count = 0
        self.blocked_operations = []
    
    def start_monitoring(self):
        """Start monitoring resource usage."""
        self.start_time = time.time()
        self.peak_memory = 0
        self.network_requests_count = 0
        self.file_operations_count = 0
        self.blocked_operations = []
    
    def check_limits(self) -> bool:
        """Check if resource limits have been exceeded."""
        if self.start_time is None:
            return True
            
        # Check CPU time limit
        elapsed = time.time() - self.start_time
        if elapsed > self.cpu_time_limit:
            self.blocked_operations.append(f"CPU time limit exceeded: {elapsed:.2f}s > {self.cpu_time_limit}s")
            return False
        
        return True
    
    def check_network_permission(self) -> bool:
        """Check if plugin can make network requests."""
        if self.network_requests_count >= self.network_requests_limit:
            self.blocked_operations.append(f"Network requests limit exceeded: {self.network_requests_count}")
            return False
        self.network_requests_count += 1
        return True
    
    def check_file_permission(self, path: str) -> bool:
        """Check if plugin can access files."""
        if self.file_operations_count >= self.file_operations_limit:
            self.blocked_operations.append(f"File operations limit exceeded: {self.file_operations_count}")
            return False
        
        # Additional security: restrict file access to specific directories
        allowed_paths = ['/tmp/liferpg_plugin', '/var/liferpg/plugin_data']
        if not any(path.startswith(allowed) for allowed in allowed_paths):
            self.blocked_operations.append(f"File access denied: {path} not in allowed paths")
            return False
        
        self.file_operations_count += 1
        return True
    
    def _check_cpu_time_limit(self, start_time: float) -> bool:
        """Check if plugin has exceeded CPU time limit."""
        elapsed = time.time() - start_time
        if elapsed > self.cpu_time_limit:
            logger.warning(f"Plugin exceeded CPU time limit: {elapsed:.2f}s > {self.cpu_time_limit}s")
            return False
            
        return True
    
    def update_memory_usage(self, memory_bytes: int):
        """Update peak memory usage."""
        memory_mb = memory_bytes / (1024 * 1024)
        if memory_mb > self.peak_memory:
            self.peak_memory = memory_mb
            
        if memory_mb > self.memory_limit_mb:
            logger.warning(f"Plugin exceeded memory limit: {memory_mb:.2f}MB > {self.memory_limit_mb}MB")
            return False
        return True


class PluginHostFunctions:
    """Host functions available to WASM plugins."""
    
    def __init__(self, plugin_id: str, permissions: List[PluginPermission], db_session):
        self.plugin_id = plugin_id
        self.permissions = permissions
        self.db = db_session
        self.extension_points = {}
        
    def has_permission(self, permission: PluginPermission) -> bool:
        """Check if plugin has a specific permission."""
        return permission in self.permissions
    
    # Console/Logging functions
    def console_log(self, caller, message_ptr: int, message_len: int) -> None:
        """Log a message from the plugin."""
        try:
            memory = caller.get_export("memory")
            message_bytes = memory.data(caller)[message_ptr:message_ptr + message_len]
            message = message_bytes.decode('utf-8')
            logger.info(f"Plugin {self.plugin_id}: {message}")
        except Exception as e:
            logger.error(f"Error in console_log: {e}")
    
    def console_error(self, caller, message_ptr: int, message_len: int) -> None:
        """Log an error message from the plugin."""
        try:
            memory = caller.get_export("memory")
            message_bytes = memory.data(caller)[message_ptr:message_ptr + message_len]
            message = message_bytes.decode('utf-8')
            logger.error(f"Plugin {self.plugin_id}: {message}")
        except Exception as e:
            logger.error(f"Error in console_error: {e}")
    
    # Data access functions
    def get_habits(self, caller) -> int:
        """Get user habits (if permission granted)."""
        if not self.has_permission(PluginPermission.HABITS_READ):
            logger.warning(f"Plugin {self.plugin_id} attempted to access habits without permission")
            return 0
        
        try:
            # This would normally query the database
            # For now, return a pointer to JSON data
            habits_data = json.dumps([
                {"id": 1, "title": "Exercise", "streak": 5},
                {"id": 2, "title": "Read", "streak": 3}
            ])
            
            # Allocate memory in WASM and write data
            memory = caller.get_export("memory")
            alloc_func = caller.get_export("plugin_alloc")
            
            data_bytes = habits_data.encode('utf-8')
            ptr = alloc_func(caller, len(data_bytes))
            memory.data(caller)[ptr:ptr + len(data_bytes)] = data_bytes
            
            return ptr
        except Exception as e:
            logger.error(f"Error in get_habits: {e}")
            return 0
    
    def create_habit(self, caller, name_ptr: int, name_len: int) -> int:
        """Create a new habit (if permission granted)."""
        if not self.has_permission(PluginPermission.HABITS_WRITE):
            logger.warning(f"Plugin {self.plugin_id} attempted to create habit without permission")
            return 0
        
        try:
            memory = caller.get_export("memory")
            name_bytes = memory.data(caller)[name_ptr:name_ptr + name_len]
            name = name_bytes.decode('utf-8')
            
            # Create habit in database (simplified)
            logger.info(f"Plugin {self.plugin_id} creating habit: {name}")
            
            # Return new habit ID
            return 123  # Mock ID
        except Exception as e:
            logger.error(f"Error in create_habit: {e}")
            return 0
    
    # UI Extension functions
    def register_dashboard_widget(self, caller, config_ptr: int, config_len: int) -> int:
        """Register a dashboard widget."""
        if not self.has_permission(PluginPermission.UI_DASHBOARD):
            logger.warning(f"Plugin {self.plugin_id} attempted to register widget without permission")
            return 0
        
        try:
            memory = caller.get_export("memory")
            config_bytes = memory.data(caller)[config_ptr:config_ptr + config_len]
            config = json.loads(config_bytes.decode('utf-8'))
            
            widget_id = f"{self.plugin_id}_{config.get('id', 'widget')}"
            
            if 'dashboard' not in self.extension_points:
                self.extension_points['dashboard'] = []
            
            self.extension_points['dashboard'].append({
                'id': widget_id,
                'plugin_id': self.plugin_id,
                'config': config
            })
            
            logger.info(f"Plugin {self.plugin_id} registered dashboard widget: {widget_id}")
            return 1  # Success
        except Exception as e:
            logger.error(f"Error in register_dashboard_widget: {e}")
            return 0


class WasmPluginRuntime:
    """WASM Plugin Runtime with sandboxing and resource limits."""
    
    def __init__(self):
        self.engine = None
        self.active_instances = {}
        
        if wasmtime:
            self.engine = wasmtime.Engine()
            logger.info("WASM runtime initialized with wasmtime")
        else:
            logger.warning("WASM runtime not available - plugins will run in limited mode")
    
    async def load_plugin(self, plugin_id: str, metadata: PluginMetadata, wasm_binary: bytes, db_session) -> bool:
        """Load and initialize a WASM plugin."""
        if not self.engine:
            logger.error("WASM engine not available")
            return False
        
        try:
            # Create resource monitor
            monitor = ResourceMonitor(metadata.resource_limits.dict())
            
            # Create host functions
            host_functions = PluginHostFunctions(plugin_id, metadata.permissions, db_session)
            
            # Create WASM store with resource limits
            store = wasmtime.Store(self.engine)
            
            # Set memory limits
            memory_pages = (metadata.resource_limits.memory_mb * 1024 * 1024) // (64 * 1024)  # 64KB per page
            store.set_limits(memory_size=memory_pages * 64 * 1024)
            
            # Define host function imports
            def create_console_log():
                return wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []), 
                                   host_functions.console_log)
            
            def create_console_error():
                return wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], []), 
                                   host_functions.console_error)
            
            def create_get_habits():
                return wasmtime.Func(store, wasmtime.FuncType([], [wasmtime.ValType.i32()]), 
                                   host_functions.get_habits)
            
            def create_create_habit():
                return wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()]), 
                                   host_functions.create_habit)
            
            def create_register_dashboard_widget():
                return wasmtime.Func(store, wasmtime.FuncType([wasmtime.ValType.i32(), wasmtime.ValType.i32()], [wasmtime.ValType.i32()]), 
                                   host_functions.register_dashboard_widget)
            
            # Create import object
            imports = {
                "env": {
                    "console_log": create_console_log(),
                    "console_error": create_console_error(),
                    "get_habits": create_get_habits(),
                    "create_habit": create_create_habit(),
                    "register_dashboard_widget": create_register_dashboard_widget(),
                }
            }
            
            # Compile and instantiate the module
            module = wasmtime.Module(self.engine, wasm_binary)
            instance = wasmtime.Instance(store, module, imports)
            
            # Store the instance
            self.active_instances[plugin_id] = {
                'instance': instance,
                'store': store,
                'monitor': monitor,
                'host_functions': host_functions,
                'metadata': metadata
            }
            
            # Call the entry point
            entry_point = metadata.entry_point or 'initialize'
            if hasattr(instance.exports, entry_point):
                monitor.start_monitoring()
                
                # Execute with timeout
                def execute_entry_point():
                    try:
                        getattr(instance.exports, entry_point)(store)
                        return True
                    except Exception as e:
                        logger.error(f"Error executing plugin entry point: {e}")
                        return False
                
                # Run in thread with timeout
                result_queue = queue.Queue()
                thread = threading.Thread(target=lambda: result_queue.put(execute_entry_point()))
                thread.start()
                thread.join(timeout=metadata.resource_limits.cpu_limit == 'high' and 10.0 or 5.0)
                
                if thread.is_alive():
                    logger.error(f"Plugin {plugin_id} entry point timed out")
                    return False
                
                if not result_queue.empty():
                    success = result_queue.get()
                    if success:
                        logger.info(f"Plugin {plugin_id} loaded successfully")
                        return True
            else:
                logger.warning(f"Plugin {plugin_id} does not have entry point: {entry_point}")
                return True  # Still consider it loaded
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_id}: {e}")
            return False
        
        return False
    
    async def unload_plugin(self, plugin_id: str) -> bool:
        """Unload a plugin and clean up resources."""
        if plugin_id in self.active_instances:
            try:
                instance_data = self.active_instances[plugin_id]
                
                # Call cleanup function if it exists
                instance = instance_data['instance']
                store = instance_data['store']
                
                if hasattr(instance.exports, 'cleanup'):
                    instance.exports.cleanup(store)
                
                # Remove from active instances
                del self.active_instances[plugin_id]
                
                logger.info(f"Plugin {plugin_id} unloaded successfully")
                return True
                
            except Exception as e:
                logger.error(f"Error unloading plugin {plugin_id}: {e}")
                return False
        
        return True
    
    async def call_plugin_function(self, plugin_id: str, function_name: str, *args) -> Any:
        """Call a function in a loaded plugin."""
        if plugin_id not in self.active_instances:
            logger.error(f"Plugin {plugin_id} is not loaded")
            return None
        
        try:
            instance_data = self.active_instances[plugin_id]
            instance = instance_data['instance']
            store = instance_data['store']
            monitor = instance_data['monitor']
            
            if not hasattr(instance.exports, function_name):
                logger.error(f"Plugin {plugin_id} does not have function: {function_name}")
                return None
            
            # Check resource limits before execution
            if not monitor.check_limits():
                logger.error(f"Plugin {plugin_id} has exceeded resource limits")
                return None
            
            # Execute function
            func = getattr(instance.exports, function_name)
            result = func(store, *args)
            
            return result
            
        except Exception as e:
            logger.error(f"Error calling plugin function {plugin_id}.{function_name}: {e}")
            return None
    
    def get_extension_points(self, plugin_id: str) -> Dict[str, List[Any]]:
        """Get extension points registered by a plugin."""
        if plugin_id in self.active_instances:
            return self.active_instances[plugin_id]['host_functions'].extension_points
        return {}
    
    def get_all_extension_points(self) -> Dict[str, List[Any]]:
        """Get all extension points from all loaded plugins."""
        all_extensions = {}
        
        for plugin_id, instance_data in self.active_instances.items():
            extensions = instance_data['host_functions'].extension_points
            
            for ext_point, items in extensions.items():
                if ext_point not in all_extensions:
                    all_extensions[ext_point] = []
                all_extensions[ext_point].extend(items)
        
        return all_extensions


# Global runtime instance
plugin_runtime = WasmPluginRuntime()


async def get_plugin_runtime() -> WasmPluginRuntime:
    """Get the global plugin runtime instance."""
    return plugin_runtime
