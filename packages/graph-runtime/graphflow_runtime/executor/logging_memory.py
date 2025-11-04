"""Logging wrapper for MemoryStore to track execution."""

from datetime import datetime
from typing import Any, Dict, List
from graphflow_core.memory.store import MemoryStore


class LogEntry:
    """Single memory operation log entry."""

    def __init__(
        self,
        timestamp: str,
        operation: str,
        key: str,
        value: Any = None,
        namespace: str = None,
        step_id: str = None,
        step_label: str = None
    ):
        """
        Initialize log entry.

        Args:
            timestamp: ISO timestamp of operation
            operation: 'read' or 'write'
            key: Memory key accessed
            value: Value (for writes)
            namespace: Memory namespace (inputs, outputs, intermediate)
            step_id: ID of the step executing this operation
            step_label: Human-readable label of the step
        """
        self.timestamp = timestamp
        self.operation = operation
        self.key = key
        self.value = value
        self.namespace = namespace
        self.step_id = step_id
        self.step_label = step_label

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        entry = {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "key": self.key,
            "namespace": self.namespace,
            "step_id": self.step_id,
            "step_label": self.step_label,
            "value": self.value,  # Always include value (for both reads and writes)
        }
        return entry


class LoggingMemoryStore(MemoryStore):
    """
    Memory store wrapper that logs all read/write operations.

    Maintains an execution log with timestamps for debugging and observability.
    """

    def __init__(self, *args, **kwargs):
        """Initialize logging memory store."""
        super().__init__(*args, **kwargs)
        self._log: List[LogEntry] = []
        self._current_step_id: str = None
        self._current_step_label: str = None

    def set_current_step(self, step_id: str, step_label: str = None):
        """
        Set the currently executing step.

        Args:
            step_id: Unique identifier for the step
            step_label: Human-readable label for the step
        """
        self._current_step_id = step_id
        self._current_step_label = step_label or step_id

    def _determine_namespace(self, key: str) -> str:
        """Determine which namespace a key belongs to."""
        if key in self.schema.inputs:
            return "inputs"
        elif key in self.schema.outputs:
            return "outputs"
        elif key in self.schema.intermediate:
            return "intermediate"
        return "unknown"

    def read(self, key: str) -> Any:
        """Read value and log the operation."""
        value = super().read(key)
        namespace = self._determine_namespace(key)

        log_entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation="read",
            key=key,
            value=value,  # Log read values so they can be displayed
            namespace=namespace,
            step_id=self._current_step_id,
            step_label=self._current_step_label
        )
        self._log.append(log_entry)

        return value

    def write(self, key: str, value: Any) -> None:
        """Write value and log the operation."""
        namespace = self._determine_namespace(key)

        log_entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            operation="write",
            key=key,
            value=value,
            namespace=namespace,
            step_id=self._current_step_id,
            step_label=self._current_step_label
        )
        self._log.append(log_entry)

        super().write(key, value)

    def get_log(self) -> List[Dict[str, Any]]:
        """
        Get execution log.

        Returns:
            List of log entries as dictionaries
        """
        return [entry.to_dict() for entry in self._log]

    def clear_log(self) -> None:
        """Clear execution log."""
        self._log.clear()
