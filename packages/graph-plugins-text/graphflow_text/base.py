"""Base class for text manipulation steps."""
import re
from abc import ABC
from typing import Any, Dict, Optional

from graphflow_core.steps.base import StepBase
from graphflow_core.memory import MemoryStore


class BaseTextStep(StepBase, ABC):
    """Base class for text steps with shared functionality."""

    category = "text"
    can_be_tool = True  # All text steps can be wrapped as LLM tools

    # Pattern for extracting memory references
    _memory_pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')

    def _get_input_value(self, memory: MemoryStore, config_key: str) -> Any:
        """
        Get input value from memory using config reference.

        Args:
            memory: Memory store
            config_key: Key in self.config containing the memory reference

        Returns:
            Value from memory

        Raises:
            ValueError: If config key not found or invalid reference
        """
        if config_key not in self.config:
            raise ValueError(f"{self.__class__.__name__} {self.id}: Missing required config '{config_key}'")

        template = self.config[config_key]
        match = self._memory_pattern.search(template)

        if match:
            namespace = match.group(1)
            field_key = match.group(2)
            full_key = f"{namespace}.{field_key}"
            return memory.read(full_key)
        else:
            raise ValueError(f"{self.__class__.__name__} {self.id}: Invalid input reference in '{config_key}'")

    def _get_input_string(self, memory: MemoryStore, config_key: str) -> str:
        """
        Get input value from memory as string.

        Args:
            memory: Memory store
            config_key: Key in self.config containing the memory reference

        Returns:
            String value from memory
        """
        value = self._get_input_value(memory, config_key)
        return str(value) if value is not None else ""

    def _write_output(self, memory: MemoryStore, output_name: str, value: Any) -> None:
        """
        Write a value to memory using the outputs dict.

        Args:
            memory: Memory store
            output_name: Name of the output in the outputs dict
            value: Value to write
        """
        if output_name not in self.outputs:
            return

        output_template = self.outputs[output_name]
        match = self._memory_pattern.search(output_template)

        if match:
            namespace = match.group(1)
            field_key = match.group(2)
            memory.write(f"{namespace}.{field_key}", value)

    def _get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a config value with optional default.

        Args:
            key: Config key
            default: Default value if not found

        Returns:
            Config value or default
        """
        return self.config.get(key, default)
