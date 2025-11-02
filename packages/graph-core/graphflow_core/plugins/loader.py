"""
Plugin Loader

Discovers and loads GraphFlow plugins from Python packages via entry points.
"""

import importlib
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from importlib.metadata import entry_points, EntryPoint

logger = logging.getLogger(__name__)


class PluginInfo:
    """Information about a discovered plugin."""

    def __init__(
        self,
        name: str,
        version: str,
        module: Any,
        manifest: Optional[Dict[str, Any]] = None,
        entry_point: Optional[EntryPoint] = None,
    ):
        self.name = name
        self.version = version
        self.module = module
        self.manifest = manifest or {}
        self.entry_point = entry_point

    @property
    def steps(self) -> List[str]:
        """List of step types provided by this plugin."""
        return self.manifest.get("steps", [])

    @property
    def ui_components(self) -> Dict[str, str]:
        """Map of step types to custom UI component paths."""
        return self.manifest.get("ui_components", {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "steps": self.steps,
            "ui_components": self.ui_components,
            "has_manifest": self.manifest is not None,
        }


class PluginLoader:
    """
    Loads GraphFlow plugins from installed packages.

    Plugins are discovered via the 'graphflow.plugins' entry point group.
    Each plugin package should define an entry point that points to its module.
    """

    ENTRY_POINT_GROUP = "graphflow.plugins"

    def __init__(self):
        self.discovered_plugins: Dict[str, PluginInfo] = {}

    def discover_plugins(self) -> Dict[str, PluginInfo]:
        """
        Discover all installed GraphFlow plugins.

        Returns:
            Dictionary mapping plugin names to PluginInfo objects
        """
        logger.info(f"Discovering plugins from entry point group: {self.ENTRY_POINT_GROUP}")

        plugins = {}

        try:
            # Get entry points for GraphFlow plugins
            eps = entry_points()

            # Handle both old and new API
            if hasattr(eps, "select"):
                # Python 3.10+
                plugin_entries = eps.select(group=self.ENTRY_POINT_GROUP)
            elif hasattr(eps, "get"):
                # Python 3.9
                plugin_entries = eps.get(self.ENTRY_POINT_GROUP, [])
            else:
                # Fallback
                plugin_entries = eps.get(self.ENTRY_POINT_GROUP, [])

            for entry_point in plugin_entries:
                try:
                    plugin_info = self._load_plugin(entry_point)
                    plugins[plugin_info.name] = plugin_info
                    logger.info(f"Loaded plugin: {plugin_info.name} v{plugin_info.version}")
                except Exception as e:
                    logger.error(f"Failed to load plugin '{entry_point.name}': {e}")

        except Exception as e:
            logger.error(f"Error discovering plugins: {e}")

        self.discovered_plugins = plugins
        return plugins

    def _load_plugin(self, entry_point: EntryPoint) -> PluginInfo:
        """
        Load a single plugin from an entry point.

        Args:
            entry_point: Entry point to load

        Returns:
            PluginInfo object
        """
        # Load the module
        module = entry_point.load()

        # Get plugin name (use entry point name)
        plugin_name = entry_point.name

        # Try to get version from module
        version = getattr(module, "__version__", "unknown")

        # Try to load manifest.json from plugin directory
        manifest = self._load_manifest(module)

        return PluginInfo(
            name=plugin_name,
            version=version,
            module=module,
            manifest=manifest,
            entry_point=entry_point,
        )

    def _load_manifest(self, module: Any) -> Optional[Dict[str, Any]]:
        """
        Load manifest.json from plugin module if it exists.

        Args:
            module: Plugin module

        Returns:
            Manifest dictionary or None if not found
        """
        try:
            # Get module path
            if hasattr(module, "__file__") and module.__file__:
                module_path = Path(module.__file__).parent
                manifest_path = module_path / "manifest.json"

                if manifest_path.exists():
                    with open(manifest_path, "r") as f:
                        manifest = json.load(f)
                    logger.debug(f"Loaded manifest from {manifest_path}")
                    return manifest
        except Exception as e:
            logger.warning(f"Could not load manifest for module {module}: {e}")

        return None

    def get_plugin(self, name: str) -> Optional[PluginInfo]:
        """
        Get a specific plugin by name.

        Args:
            name: Plugin name

        Returns:
            PluginInfo or None if not found
        """
        return self.discovered_plugins.get(name)

    def list_plugins(self) -> List[PluginInfo]:
        """
        List all discovered plugins.

        Returns:
            List of PluginInfo objects
        """
        return list(self.discovered_plugins.values())
