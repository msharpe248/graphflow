"""Base class for all step types."""

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Set
from graphflow_core.memory.store import MemoryStore


class StepBase(ABC):
    """
    Abstract base class for all step types.

    Steps are the nodes in the graph. Each step can read from and write to
    the memory store. The execution logic is defined in the execute() method.
    """

    def __init__(
        self,
        id: str,
        config: Dict[str, Any],
        outputs: Dict[str, str]
    ):
        """
        Initialize step.

        Args:
            id: Unique step identifier
            config: Step-specific configuration
            outputs: Output mappings (output_name -> memory location)
        """
        self.id = id
        self.config = config
        self.outputs = outputs

    def _extract_memory_refs(self, value: Any) -> Set[str]:
        """
        Recursively extract memory references from a value.

        Looks for {memory.variable} pattern in strings, dicts, and lists.

        Args:
            value: Value to scan for memory references

        Returns:
            Set of memory keys referenced
        """
        refs = set()
        pattern = re.compile(r'\{memory\.([^}]+)\}')

        if isinstance(value, str):
            for match in pattern.finditer(value):
                refs.add(match.group(1))
        elif isinstance(value, dict):
            for v in value.values():
                refs.update(self._extract_memory_refs(v))
        elif isinstance(value, list):
            for item in value:
                refs.update(self._extract_memory_refs(item))

        return refs

    @property
    def memory_reads(self) -> List[str]:
        """Extract memory reads from config by parsing {memory.field} syntax."""
        return sorted(self._extract_memory_refs(self.config))

    @property
    def memory_writes(self) -> List[str]:
        """Extract memory writes from outputs by parsing {memory.field} syntax."""
        return sorted(self._extract_memory_refs(self.outputs))

    @abstractmethod
    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute step logic.

        This method should:
        1. Read required values from memory using memory.read(key)
        2. Perform step-specific logic
        3. Write results to memory using memory.write(key, value)

        Args:
            memory: Memory store instance

        Raises:
            Any exceptions during execution should be propagated
        """
        pass

    @classmethod
    @abstractmethod
    def get_type(cls) -> str:
        """
        Return step type identifier.

        This is used in the graph definition and for registry lookup.

        Returns:
            Step type string (e.g., "start", "llm", "output")
        """
        pass

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Return JSON schema for step configuration.

        Override this to provide schema for UI config forms.

        Returns:
            JSON schema dict defining config structure
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """
        Return schema for step inputs (what it reads from memory).

        Override this to specify what inputs this step expects.

        Returns:
            JSON schema dict defining expected inputs:
            {
                "properties": {
                    "input_name": {
                        "type": "string",
                        "description": "Description of input",
                        "required": True
                    }
                }
            }
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """
        Return schema for step outputs (what it writes to memory).

        Override this to specify what outputs this step produces.

        Returns:
            JSON schema dict defining produced outputs:
            {
                "properties": {
                    "output_name": {
                        "type": "string",
                        "description": "Description of output"
                    }
                }
            }
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True
        }

    def validate_config(self) -> List[str]:
        """
        Validate step configuration.

        Override this to add custom validation logic.

        Returns:
            List of error messages (empty if valid)
        """
        return []

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, type={self.get_type()})"
