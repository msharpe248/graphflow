"""Runtime configuration management."""
import os
from typing import Dict, Any


class RuntimeConfig:
    """
    Global runtime configuration.

    Provides system-level config values that are injected into all graph executions.
    These values are read-only from the graph's perspective.
    """

    def __init__(self):
        """Initialize runtime config with default values."""
        self._config: Dict[str, Any] = {
            'cwd': os.getcwd(),
            'runtime_url': os.getenv('GRAPHFLOW_RUNTIME_URL', 'https://localhost:8000'),
            'insecure': os.getenv('GRAPHFLOW_INSECURE', 'false').lower() == 'true',
        }

    def get_all(self) -> Dict[str, Any]:
        """Get all config values as a dictionary."""
        return self._config.copy()

    def get(self, key: str, default: Any = None) -> Any:
        """Get a specific config value."""
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set a config value.

        Note: This is for runtime initialization only.
        Config values are read-only from graph execution perspective.
        """
        self._config[key] = value

    def update(self, values: Dict[str, Any]) -> None:
        """Update multiple config values at once."""
        self._config.update(values)


# Global runtime config instance
runtime_config = RuntimeConfig()
