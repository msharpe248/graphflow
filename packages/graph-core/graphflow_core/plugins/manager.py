"""
Plugin Manager

Manages the lifecycle of GraphFlow plugins including discovery, loading,
registration, and validation.
"""

import logging
from typing import Dict, List, Optional, Set
from pathlib import Path
import json

from graphflow_core.plugins.loader import PluginLoader, PluginInfo
from graphflow_core.steps.registry import StepRegistry

logger = logging.getLogger(__name__)


class PluginManager:
    """
    Manages GraphFlow plugins throughout their lifecycle.

    Responsibilities:
    - Plugin discovery and loading
    - Step registration with namespace support
    - Plugin validation and conflict detection
    - Configuration-based enable/disable
    - Plugin information access
    """

    def __init__(
        self,
        step_registry: Optional[StepRegistry] = None,
        config_path: Optional[Path] = None
    ):
        """
        Initialize the plugin manager.

        Args:
            step_registry: StepRegistry instance to register steps with.
                          If None, uses the global registry.
            config_path: Path to plugin configuration file (optional)
        """
        self.loader = PluginLoader()
        self.step_registry = step_registry or StepRegistry()
        self.config_path = config_path
        self.config = self._load_config()

        # Tracking
        self.loaded_plugins: Dict[str, PluginInfo] = {}
        self.registered_steps: Dict[str, str] = {}  # step_type -> plugin_name

    def _load_config(self) -> Dict:
        """
        Load plugin configuration from file.

        Returns:
            Configuration dictionary
        """
        if not self.config_path or not self.config_path.exists():
            return {
                "enabled_plugins": [],
                "disabled_plugins": [],
                "plugin_settings": {}
            }

        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not load plugin config from {self.config_path}: {e}")
            return {
                "enabled_plugins": [],
                "disabled_plugins": [],
                "plugin_settings": {}
            }

    def _should_load_plugin(self, plugin_name: str) -> bool:
        """
        Determine if a plugin should be loaded based on configuration.

        Args:
            plugin_name: Name of the plugin

        Returns:
            True if plugin should be loaded
        """
        # If disabled list is populated, check it
        if self.config["disabled_plugins"]:
            if plugin_name in self.config["disabled_plugins"]:
                return False

        # If enabled list is populated, only load those
        if self.config["enabled_plugins"]:
            return plugin_name in self.config["enabled_plugins"]

        # Default: load all plugins
        return True

    def discover_and_load(self) -> Dict[str, PluginInfo]:
        """
        Discover and load all plugins.

        Returns:
            Dictionary of loaded plugins
        """
        logger.info("Starting plugin discovery and loading")

        # Discover all available plugins
        discovered = self.loader.discover_plugins()

        # Load plugins based on configuration
        for plugin_name, plugin_info in discovered.items():
            if self._should_load_plugin(plugin_name):
                try:
                    self._load_plugin(plugin_info)
                except Exception as e:
                    logger.error(f"Failed to load plugin '{plugin_name}': {e}")
            else:
                logger.info(f"Skipping disabled plugin: {plugin_name}")

        logger.info(f"Loaded {len(self.loaded_plugins)} plugins with {len(self.registered_steps)} steps")
        return self.loaded_plugins

    def _load_plugin(self, plugin_info: PluginInfo) -> None:
        """
        Load a single plugin and register its steps.

        Args:
            plugin_info: Plugin information
        """
        logger.info(f"Loading plugin: {plugin_info.name} v{plugin_info.version}")

        # Validate plugin
        self._validate_plugin(plugin_info)

        # Check for step conflicts
        conflicts = self._check_step_conflicts(plugin_info)
        if conflicts:
            raise ValueError(
                f"Plugin '{plugin_info.name}' has step type conflicts: {conflicts}"
            )

        # Register plugin steps with namespace
        self._register_plugin_steps(plugin_info)

        # Track loaded plugin
        self.loaded_plugins[plugin_info.name] = plugin_info

        logger.info(
            f"Successfully loaded plugin '{plugin_info.name}' "
            f"with {len(plugin_info.steps)} step types"
        )

    def _validate_plugin(self, plugin_info: PluginInfo) -> None:
        """
        Validate plugin structure and metadata.

        Args:
            plugin_info: Plugin to validate

        Raises:
            ValueError: If plugin is invalid
        """
        # Check required attributes
        if not plugin_info.name:
            raise ValueError("Plugin must have a name")

        if not plugin_info.module:
            raise ValueError(f"Plugin '{plugin_info.name}' has no module")

        # Validate step types if manifest exists
        if plugin_info.manifest and plugin_info.steps:
            for step_type in plugin_info.steps:
                # Check if step class exists in module
                if not hasattr(plugin_info.module, step_type):
                    logger.warning(
                        f"Plugin '{plugin_info.name}' declares step '{step_type}' "
                        f"but it's not found in module"
                    )

    def _check_step_conflicts(self, plugin_info: PluginInfo) -> List[str]:
        """
        Check for conflicts with already registered step types.

        Args:
            plugin_info: Plugin to check

        Returns:
            List of conflicting step types
        """
        conflicts = []

        for step_type in plugin_info.steps:
            # Create namespaced step type
            namespaced_type = f"{plugin_info.name}.{step_type}"

            # Check if already registered
            if namespaced_type in self.registered_steps:
                conflicts.append(
                    f"{namespaced_type} (registered by {self.registered_steps[namespaced_type]})"
                )

        return conflicts

    def _register_plugin_steps(self, plugin_info: PluginInfo) -> None:
        """
        Register all steps from a plugin with the step registry.

        Args:
            plugin_info: Plugin whose steps to register
        """
        for step_class_name in plugin_info.steps:
            # Get step class from plugin module
            step_class = getattr(plugin_info.module, step_class_name, None)

            if step_class is None:
                logger.warning(
                    f"Could not find step class '{step_class_name}' in plugin '{plugin_info.name}'"
                )
                continue

            # Get the actual step type from the class
            try:
                actual_step_type = step_class.get_type()
            except Exception as e:
                logger.warning(
                    f"Could not get type from step class '{step_class_name}': {e}"
                )
                continue

            # Check if step is already registered (via decorator)
            if self.step_registry.is_registered(actual_step_type):
                # Step already registered via decorator - just track it
                self.registered_steps[actual_step_type] = plugin_info.name
                logger.info(
                    f"[PLUGIN] Step '{actual_step_type}' already registered, "
                    f"associating with plugin '{plugin_info.name}'"
                )
            else:
                # Step not registered yet - register it with namespaced type
                namespaced_type = f"{plugin_info.name}.{step_class_name}"
                try:
                    self.step_registry.register_step(namespaced_type, step_class)
                    self.registered_steps[namespaced_type] = plugin_info.name
                    logger.info(f"[PLUGIN] Registered NEW step: {namespaced_type}")
                except Exception as e:
                    logger.error(
                        f"Failed to register step '{namespaced_type}' "
                        f"from plugin '{plugin_info.name}': {e}"
                    )

    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """
        Get a loaded plugin by name.

        Args:
            name: Plugin name

        Returns:
            PluginInfo or None if not found
        """
        return self.loaded_plugins.get(name)

    def list_plugins(self) -> List[PluginInfo]:
        """
        List all loaded plugins.

        Returns:
            List of PluginInfo objects
        """
        return list(self.loaded_plugins.values())

    def get_all_steps(self) -> Dict[str, Dict]:
        """
        Get metadata for all registered steps (both built-in and plugin steps).

        Returns:
            Dictionary mapping step types to their metadata
        """
        all_steps = {}

        # First, add all steps from StepRegistry (built-in and decorator-registered plugin steps)
        for step_type in self.step_registry.list_types():
            try:
                step_class = self.step_registry.get(step_type)
                metadata = self.step_registry.get_metadata(step_type)

                # Get plugin name and version
                plugin_name = metadata.get("plugin", "built-in")
                plugin_version = "1.0.0"

                # If this is a plugin step, try to get the plugin version
                if plugin_name != "built-in" and plugin_name in self.loaded_plugins:
                    plugin_version = self.loaded_plugins[plugin_name].version

                all_steps[step_type] = {
                    "type": step_type,
                    "plugin": plugin_name,
                    "plugin_version": plugin_version,
                    "label": getattr(step_class, "label", step_type.replace("_", " ").title()),
                    "description": metadata.get("description", ""),
                    "category": metadata.get("category", "general"),
                    "config_schema": metadata.get("schema", {}),
                    "inputs_schema": step_class.get_inputs_schema() if hasattr(step_class, "get_inputs_schema") else {},
                    "outputs_schema": step_class.get_outputs_schema() if hasattr(step_class, "get_outputs_schema") else {},
                    "ui_component": None,
                    "can_be_tool": getattr(step_class, "can_be_tool", False),
                    "tool_ineligible_reason": getattr(step_class, "tool_ineligible_reason", None),
                }
            except Exception as e:
                logger.warning(f"Could not get metadata for step '{step_type}': {e}")

        # Then, add plugin steps that were registered via manifest
        # (decorator-registered steps were already handled above)
        for plugin_info in self.loaded_plugins.values():
            for step_class_name in plugin_info.steps:
                # Get step class
                step_class = getattr(plugin_info.module, step_class_name, None)
                if step_class is None:
                    continue

                # Get actual step type from class
                try:
                    actual_step_type = step_class.get_type()
                except:
                    actual_step_type = None

                # Check if this step was already registered via decorator
                if actual_step_type and actual_step_type in self.registered_steps:
                    # Already handled in first loop above
                    continue

                # Not registered via decorator - use namespaced type
                namespaced_type = f"{plugin_info.name}.{step_class_name}"

                # Build step metadata
                all_steps[namespaced_type] = {
                    "type": namespaced_type,
                    "plugin": plugin_info.name,
                    "plugin_version": plugin_info.version,
                    "label": getattr(step_class, "label", step_class_name.replace("_", " ").title()),
                    "description": getattr(step_class, "description", ""),
                    "category": getattr(step_class, "category", "general"),
                    "config_schema": step_class.get_schema() if hasattr(step_class, "get_schema") else {},
                    "inputs_schema": step_class.get_inputs_schema() if hasattr(step_class, "get_inputs_schema") else {},
                    "outputs_schema": step_class.get_outputs_schema() if hasattr(step_class, "get_outputs_schema") else {},
                    "ui_component": plugin_info.ui_components.get(step_class_name),
                    "can_be_tool": getattr(step_class, "can_be_tool", False),
                    "tool_ineligible_reason": getattr(step_class, "tool_ineligible_reason", None),
                }

        return all_steps

    def get_plugin_info_dict(self) -> List[Dict]:
        """
        Get serializable information about all loaded plugins.

        Returns:
            List of plugin information dictionaries
        """
        return [plugin.to_dict() for plugin in self.loaded_plugins.values()]

    def reload_plugin(self, plugin_name: str) -> bool:
        """
        Reload a specific plugin.

        Args:
            plugin_name: Name of plugin to reload

        Returns:
            True if successful
        """
        logger.info(f"Reloading plugin: {plugin_name}")

        # Unload current plugin
        if plugin_name in self.loaded_plugins:
            self._unload_plugin(plugin_name)

        # Rediscover and reload
        discovered = self.loader.discover_plugins()
        plugin_info = discovered.get(plugin_name)

        if not plugin_info:
            logger.error(f"Plugin '{plugin_name}' not found during reload")
            return False

        try:
            self._load_plugin(plugin_info)
            return True
        except Exception as e:
            logger.error(f"Failed to reload plugin '{plugin_name}': {e}")
            return False

    def _unload_plugin(self, plugin_name: str) -> None:
        """
        Unload a plugin and unregister its steps.

        Args:
            plugin_name: Name of plugin to unload
        """
        if plugin_name not in self.loaded_plugins:
            return

        # Unregister steps
        steps_to_remove = [
            step_type for step_type, pname in self.registered_steps.items()
            if pname == plugin_name
        ]

        for step_type in steps_to_remove:
            try:
                self.step_registry.unregister_step(step_type)
                del self.registered_steps[step_type]
            except Exception as e:
                logger.warning(f"Could not unregister step '{step_type}': {e}")

        # Remove from loaded plugins
        del self.loaded_plugins[plugin_name]

        logger.info(f"Unloaded plugin: {plugin_name}")
