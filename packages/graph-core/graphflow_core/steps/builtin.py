"""Built-in step types."""

import json
from typing import Any, Dict
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry
from graphflow_core.memory.store import MemoryStore


@StepRegistry.register(category="control", description="Entry point for graph execution")
class StartStep(StepBase):
    """
    Start step - entry point for graph execution.

    This step performs no operations and is used as the starting node.
    """

    @classmethod
    def get_type(cls) -> str:
        return "start"

    async def execute(self, memory: MemoryStore) -> None:
        """No-op execution."""
        pass


@StepRegistry.register(category="control", description="Map intermediate values to outputs")
class OutputStep(StepBase):
    """
    Output step - map intermediate/input values to output namespace.

    Config:
        mapping: Dict[str, str] - Maps output keys to memory keys
                 Example: {"answer": "llm_response", "score": "confidence"}
    """

    @classmethod
    def get_type(cls) -> str:
        return "output"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "mapping": {
                    "type": "object",
                    "description": "Maps output keys to memory keys",
                    "additionalProperties": {"type": "string"}
                }
            },
            "required": ["mapping"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Map values from memory to outputs."""
        mapping = self.config.get("mapping", {})

        for output_key, source_key in mapping.items():
            try:
                value = memory.read(source_key)
                memory.write(output_key, value)
            except KeyError as e:
                raise KeyError(
                    f"OutputStep {self.id}: Cannot map {source_key} to {output_key}: {e}"
                )


@StepRegistry.register(category="control", description="Conditional branching based on memory values")
class ConditionalStep(StepBase):
    """
    Conditional step - evaluates condition and sets branch indicator.

    This step evaluates a Python expression against memory and writes
    the boolean result. The graph execution engine uses this for branching.

    Config:
        condition: str - Python expression to evaluate
        result_key: str - Memory key to write boolean result

    The condition expression can reference memory keys directly.
    Example: "score > 0.8 and status == 'ready'"
    """

    @classmethod
    def get_type(cls) -> str:
        return "conditional"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "condition": {
                    "type": "string",
                    "description": "Python expression to evaluate"
                },
                "result_key": {
                    "type": "string",
                    "description": "Memory key to write result"
                }
            },
            "required": ["condition", "result_key"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Evaluate condition and write result."""
        condition = self.config.get("condition")
        result_key = self.config.get("result_key")

        if not condition:
            raise ValueError(f"ConditionalStep {self.id}: condition not specified")
        if not result_key:
            raise ValueError(f"ConditionalStep {self.id}: result_key not specified")

        # Build evaluation context from memory reads
        eval_context = {}
        for key in self.memory_reads:
            try:
                eval_context[key.replace('.', '_')] = memory.read(key)
            except KeyError:
                # Allow missing keys (treat as None)
                eval_context[key.replace('.', '_')] = None

        # Evaluate condition
        try:
            # Replace dotted keys in condition with underscored versions
            adjusted_condition = condition
            for key in self.memory_reads:
                if '.' in key:
                    adjusted_condition = adjusted_condition.replace(key, key.replace('.', '_'))

            result = eval(adjusted_condition, {"__builtins__": {}}, eval_context)
            memory.write(result_key, bool(result))
        except Exception as e:
            raise RuntimeError(
                f"ConditionalStep {self.id}: Error evaluating condition '{condition}': {e}"
            )


@StepRegistry.register(category="data", description="Transform data using Python code")
class TransformStep(StepBase):
    """
    Transform step - apply Python function to transform data.

    Config:
        operation: str - Name of operation (for documentation)
        code: str - Python code to execute
        input_keys: List[str] - Memory keys to read and pass as variables
        output_key: str - Memory key to write result

    The code should return a value that will be written to output_key.
    Input keys are made available as variables in the code.
    """

    @classmethod
    def get_type(cls) -> str:
        return "transform"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "description": "Operation name"
                },
                "code": {
                    "type": "string",
                    "description": "Python code to execute (should return a value)"
                },
                "input_keys": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Memory keys to pass to code"
                },
                "output_key": {
                    "type": "string",
                    "description": "Memory key to write result"
                }
            },
            "required": ["code", "output_key"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute transformation code."""
        code = self.config.get("code")
        output_key = self.config.get("output_key")
        input_keys = self.config.get("input_keys", self.memory_reads)

        if not code:
            raise ValueError(f"TransformStep {self.id}: code not specified")
        if not output_key:
            raise ValueError(f"TransformStep {self.id}: output_key not specified")

        # Build execution context
        exec_context: Dict[str, Any] = {}
        for key in input_keys:
            try:
                # Make available with both original and underscored name
                value = memory.read(key)
                exec_context[key.replace('.', '_')] = value
                if '.' not in key:
                    exec_context[key] = value
            except KeyError:
                exec_context[key.replace('.', '_')] = None
                if '.' not in key:
                    exec_context[key] = None

        # Add json module for convenience
        exec_context['json'] = json

        # Execute code
        try:
            # Wrap code in function and execute
            func_code = f"def _transform():\n"
            for line in code.split('\n'):
                func_code += f"    {line}\n"
            func_code += "\n_result = _transform()"

            local_vars: Dict[str, Any] = {}
            exec(func_code, exec_context, local_vars)
            result = local_vars['_result']

            # Write result
            memory.write(output_key, result)

        except Exception as e:
            raise RuntimeError(
                f"TransformStep {self.id}: Error executing code: {e}"
            )


@StepRegistry.register(category="control", description="Synchronization point for multiple branches")
class JoinStep(StepBase):
    """
    Join step - synchronization point for multiple graph branches.

    This step waits for multiple predecessor steps to complete before proceeding.
    The execution engine is responsible for managing the synchronization logic.

    Config:
        wait_for: List[str] - Step IDs that must complete before this step executes
    """

    @classmethod
    def get_type(cls) -> str:
        return "join"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "wait_for": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Step IDs to wait for"
                }
            },
            "required": ["wait_for"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        """No-op execution - synchronization is handled by execution engine."""
        pass
