"""Built-in step types."""

import json
from typing import Any, Dict
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry
from graphflow_core.steps.memory_mixin import MemoryMixin
from graphflow_core.memory.store import MemoryStore


@StepRegistry.register(category="control", description="Entry point for graph execution")
class StartStep(StepBase):
    """
    Start step - entry point for graph execution.

    This step performs no operations and is used as the starting node.
    """

    can_be_tool = False
    tool_ineligible_reason = "Entry point steps cannot be used as tools"

    @classmethod
    def get_type(cls) -> str:
        return "start"

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """Start step has no inputs."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """Start step has no outputs."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }

    async def execute(self, memory: MemoryStore) -> None:
        """No-op execution."""
        pass


@StepRegistry.register(category="control", description="Map intermediate values to outputs")
class OutputStep(StepBase, MemoryMixin):
    """
    Output step - map intermediate/input values to output namespace.

    Outputs dict maps output names to memory locations using {memory.variable} syntax.
    Example: {"answer": "{memory.llm_response}", "score": "{memory.confidence}"}

    Inherits from MemoryMixin for centralized template resolution.
    """

    can_be_tool = False
    tool_ineligible_reason = "Output mapping steps cannot be used as tools"

    @classmethod
    def get_type(cls) -> str:
        return "output"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
            "description": "OutputStep uses outputs dict instead of config"
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """
        OutputStep reads from any memory location specified in outputs dict.
        The actual inputs are dynamic based on the outputs values.
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Reads memory keys referenced in outputs dict using {memory.variable} syntax"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """
        OutputStep writes to output namespace.
        The actual outputs are dynamic based on the outputs dict keys.
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Writes to output namespace using keys from outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Map values from memory to outputs."""
        resolver = self._get_resolver(memory)

        for output_key, source_template in self.outputs.items():
            try:
                # Extract source key from {namespace.field} syntax
                refs = resolver.extract_references(source_template)
                if refs:
                    # Get the first reference (output bindings typically have one ref)
                    source_key = next(iter(refs))
                    value = memory.read(source_key)
                    memory.write(output_key, value)
                else:
                    raise ValueError(
                        f"OutputStep {self.id}: Invalid memory reference '{source_template}'. "
                        f"Must use {{memory.variable}} syntax"
                    )
            except KeyError as e:
                raise KeyError(
                    f"OutputStep {self.id}: Cannot map {source_template} to {output_key}: {e}"
                )


@StepRegistry.register(category="control", description="Conditional branching based on memory values")
class ConditionalStep(StepBase, MemoryMixin):
    """
    Conditional step - evaluates condition and sets branch indicator.

    This step evaluates a Python expression against memory and writes
    the boolean result. The graph execution engine uses this for branching.

    Config:
        condition: str - Python expression to evaluate using {memory.variable} syntax

    Outputs:
        result: {memory.variable} - Where to write the boolean result

    The condition expression can reference memory keys using {memory.variable}.
    Example: "{memory.score} > 0.8 and {memory.status} == 'ready'"

    Inherits from MemoryMixin for centralized template resolution.
    """

    can_be_tool = False
    tool_ineligible_reason = "Control flow steps cannot be used as tools"

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
                    "description": "Python expression to evaluate using {memory.variable} syntax"
                }
            },
            "required": ["condition"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """
        ConditionalStep reads any memory keys referenced in the condition.
        Inputs are dynamic based on the condition expression.
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Reads memory keys referenced in condition using {memory.variable} syntax"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """ConditionalStep writes the boolean result."""
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "boolean",
                    "description": "Boolean result of condition evaluation"
                }
            },
            "description": "Writes boolean result to location specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Evaluate condition and write result."""
        condition = self.config.get("condition")
        if not condition:
            raise ValueError(f"ConditionalStep {self.id}: condition not specified")

        resolver = self._get_resolver(memory)

        # Extract all memory references from condition
        refs = resolver.extract_references(condition)

        # Build evaluation context from memory references
        eval_context = {}
        adjusted_condition = condition

        for full_key in refs:
            # full_key is like "memory.variable" or "config.setting"
            parts = full_key.split('.', 1)
            namespace = parts[0]
            field_key = parts[1] if len(parts) > 1 else full_key

            # Prefix with _mem_ to avoid shadowing Python built-ins
            var_name = '_mem_' + full_key.replace('.', '_')

            try:
                eval_context[var_name] = memory.read(full_key)
            except KeyError:
                # Allow missing keys (treat as None)
                eval_context[var_name] = None

            # Replace {namespace.variable} with var_name in condition
            adjusted_condition = adjusted_condition.replace(f'{{{full_key}}}', var_name)

        # Evaluate condition
        try:
            result = eval(adjusted_condition, {"__builtins__": {}}, eval_context)

            # Write result to output location
            if self.outputs and 'result' in self.outputs:
                result_template = self.outputs['result']
                output_refs = resolver.extract_references(result_template)
                if output_refs:
                    result_key = next(iter(output_refs))
                    memory.write(result_key, bool(result))
                else:
                    raise ValueError(f"ConditionalStep {self.id}: Invalid output reference '{result_template}'")
            else:
                raise ValueError(f"ConditionalStep {self.id}: outputs.result not specified")

        except Exception as e:
            raise RuntimeError(
                f"ConditionalStep {self.id}: Error evaluating condition '{condition}': {e}"
            )


@StepRegistry.register(category="data", description="Transform data using Python code")
class TransformStep(StepBase, MemoryMixin):
    """
    Transform step - apply Python function to transform data.

    Config:
        operation: str - Name of operation (for documentation)
        code: str - Python code to execute (can use {memory.variable} syntax)

    Outputs:
        result: {memory.variable} - Where to write the transformation result

    The code should return a value that will be written to the output location.
    Memory references in code using {memory.variable} will be available as variables.

    Inherits from MemoryMixin for centralized template resolution.
    """

    can_be_tool = True  # Transform steps can be wrapped as LLM tools

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
                    "description": "Python code to execute (can use {memory.variable} syntax)"
                }
            },
            "required": ["code"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """TransformStep reads memory keys referenced in code."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Reads memory keys referenced in code using {memory.variable} syntax"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """TransformStep writes result."""
        return {
            "type": "object",
            "properties": {
                "result": {
                    "description": "Result of transformation"
                }
            },
            "description": "Writes transformation result to location specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute transformation code."""
        code = self.config.get("code")
        if not code:
            raise ValueError(f"TransformStep {self.id}: code not specified")

        resolver = self._get_resolver(memory)

        # Extract all memory references from code
        refs = resolver.extract_references(code)

        # Build execution context
        exec_context: Dict[str, Any] = {}
        adjusted_code = code

        for full_key in refs:
            # full_key is like "memory.variable" or "config.setting"
            # Prefix with _mem_ to avoid shadowing Python built-ins like input, id, etc.
            var_name = '_mem_' + full_key.replace('.', '_')

            try:
                exec_context[var_name] = memory.read(full_key)
            except KeyError:
                exec_context[var_name] = None

            # Replace {namespace.variable} with var_name in code
            adjusted_code = adjusted_code.replace(f'{{{full_key}}}', var_name)

        # Add json module for convenience
        exec_context['json'] = json

        # Execute code
        try:
            # Wrap code in function and execute
            func_code = f"def _transform():\n"
            for line in adjusted_code.split('\n'):
                func_code += f"    {line}\n"
            func_code += "\n_result = _transform()"

            local_vars: Dict[str, Any] = {}
            exec(func_code, exec_context, local_vars)
            result = local_vars['_result']

            # Write result to output location
            if self.outputs and 'result' in self.outputs:
                result_template = self.outputs['result']
                output_refs = resolver.extract_references(result_template)
                if output_refs:
                    output_key = next(iter(output_refs))
                    memory.write(output_key, result)
                else:
                    raise ValueError(f"TransformStep {self.id}: Invalid output reference '{result_template}'")
            else:
                raise ValueError(f"TransformStep {self.id}: outputs.result not specified")

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

    can_be_tool = False
    tool_ineligible_reason = "Synchronization steps cannot be used as tools"

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

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """JoinStep has no specific inputs - it's a synchronization point."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
            "description": "Synchronization point - no specific inputs"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """JoinStep has no specific outputs - it's a synchronization point."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
            "description": "Synchronization point - no specific outputs"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """No-op execution - synchronization is handled by execution engine."""
        pass


@StepRegistry.register(category="data", description="Read value from memory")
class ReadMemoryStep(StepBase, MemoryMixin):
    """
    Read Memory step - read a value from any memory section.

    This step allows copying data from inputs, intermediate, or outputs
    to another location in memory.

    Config:
        source: str - Memory reference to read from using {memory.variable} syntax

    Outputs:
        value: {memory.variable} - Where to write the copied value

    Inherits from MemoryMixin for centralized template resolution.
    """

    name = "Read Memory"
    label = "Read Memory"
    can_be_tool = False
    tool_ineligible_reason = "Memory operations cannot be used as tools"

    @classmethod
    def get_type(cls) -> str:
        return "read-memory"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Memory reference to read from using {memory.variable} syntax"
                }
            },
            "required": ["source"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """ReadMemoryStep reads from source."""
        return {
            "type": "object",
            "properties": {
                "value": {
                    "description": "Value read from source"
                }
            },
            "description": "Reads value from source specified in config"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """ReadMemoryStep writes the value."""
        return {
            "type": "object",
            "properties": {
                "value": {
                    "description": "Value copied from source"
                }
            },
            "description": "Writes value to location specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Read value from memory."""
        source_template = self.config.get("source")
        if not source_template:
            raise ValueError(f"ReadMemoryStep {self.id}: source not specified")

        resolver = self._get_resolver(memory)

        try:
            # Extract source key using resolver
            source_refs = resolver.extract_references(source_template)
            if source_refs:
                source_key = next(iter(source_refs))
                value = memory.read(source_key)

                # Write to output location
                if self.outputs and 'value' in self.outputs:
                    output_template = self.outputs['value']
                    output_refs = resolver.extract_references(output_template)
                    if output_refs:
                        output_key = next(iter(output_refs))
                        memory.write(output_key, value)
                    else:
                        raise ValueError(f"ReadMemoryStep {self.id}: Invalid output reference '{output_template}'")
                else:
                    raise ValueError(f"ReadMemoryStep {self.id}: outputs.value not specified")
            else:
                raise ValueError(f"ReadMemoryStep {self.id}: Invalid source reference '{source_template}'")

        except KeyError as e:
            raise KeyError(
                f"ReadMemoryStep {self.id}: Cannot read from {source_template}: {e}"
            )


@StepRegistry.register(category="data", description="Write value to memory")
class WriteMemoryStep(StepBase, MemoryMixin):
    """
    Write Memory step - write a value to any memory section.

    This step allows moving data from intermediate memory to outputs,
    or organizing intermediate values.

    Config:
        source: str - Memory reference to read from using {memory.variable} syntax

    Outputs:
        value: {memory.variable} - Where to write the value

    Inherits from MemoryMixin for centralized template resolution.
    """

    name = "Write Memory"
    label = "Write Memory"
    can_be_tool = False
    tool_ineligible_reason = "Memory operations cannot be used as tools"

    @classmethod
    def get_type(cls) -> str:
        return "write-memory"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "Memory reference to read from using {memory.variable} syntax"
                }
            },
            "required": ["source"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """WriteMemoryStep reads from source."""
        return {
            "type": "object",
            "properties": {
                "value": {
                    "description": "Value to write"
                }
            },
            "description": "Reads value from source specified in config"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """WriteMemoryStep writes the value to target location."""
        return {
            "type": "object",
            "properties": {
                "value": {
                    "description": "Value written to target"
                }
            },
            "description": "Writes value to location specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Write value to memory."""
        source_template = self.config.get("source")
        if not source_template:
            raise ValueError(f"WriteMemoryStep {self.id}: source not specified")

        resolver = self._get_resolver(memory)

        try:
            # Extract source key using resolver (supports all namespaces)
            source_refs = resolver.extract_references(source_template)
            if source_refs:
                source_key = next(iter(source_refs))
                value = memory.read(source_key)

                # Write to output location
                if self.outputs and 'value' in self.outputs:
                    output_template = self.outputs['value']
                    output_refs = resolver.extract_references(output_template)
                    if output_refs:
                        output_key = next(iter(output_refs))
                        memory.write(output_key, value)
                    else:
                        raise ValueError(f"WriteMemoryStep {self.id}: Invalid output reference '{output_template}'")
                else:
                    raise ValueError(f"WriteMemoryStep {self.id}: outputs.value not specified")
            else:
                raise ValueError(f"WriteMemoryStep {self.id}: Invalid source reference '{source_template}'")

        except KeyError as e:
            raise KeyError(
                f"WriteMemoryStep {self.id}: Cannot read from {source_template}: {e}"
            )


@StepRegistry.register(category="control", description="Sleep/delay for a specified duration")
class SleepStep(StepBase, MemoryMixin):
    """
    Sleep step - pause execution for a specified duration.

    Useful for:
    - Rate limiting API calls
    - Testing time-sensitive workflows
    - Simulating long-running operations
    - Adding delays between steps

    Config:
        duration: float - Duration in seconds (can use {memory.*} syntax)

    Example:
        {"duration": 2.5}  # Sleep for 2.5 seconds
        {"duration": "{memory.delay_seconds}"}  # Read from memory

    Inherits from MemoryMixin for centralized template resolution.
    """

    name = "Sleep"
    label = "Sleep"
    can_be_tool = False
    tool_ineligible_reason = "Timing/delay steps cannot be used as tools"

    @classmethod
    def get_type(cls) -> str:
        return "sleep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "duration": {
                    "type": ["number", "string"],
                    "description": "Duration in seconds (can use {memory.*} syntax to read from memory)",
                    "minimum": 0
                }
            },
            "required": ["duration"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """SleepStep may read duration from memory."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "May read duration from memory if using {memory.*} syntax"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """SleepStep has no outputs."""
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
            "description": "Sleep has no outputs"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Sleep for the specified duration."""
        import asyncio

        duration_config = self.config.get("duration")
        if duration_config is None:
            raise ValueError(f"SleepStep {self.id}: duration not specified")

        resolver = self._get_resolver(memory)

        # Check if duration is a memory reference
        if isinstance(duration_config, str):
            refs = resolver.extract_references(duration_config)
            if refs:
                # Read duration from memory
                memory_key = next(iter(refs))
                try:
                    duration = memory.read(memory_key)
                    # Convert to float
                    duration = float(duration)
                except KeyError:
                    raise KeyError(f"SleepStep {self.id}: Memory key not found: {memory_key}")
                except (TypeError, ValueError):
                    raise ValueError(f"SleepStep {self.id}: Duration must be a number, got {type(duration)}")
            else:
                # Try to parse as number
                try:
                    duration = float(duration_config)
                except ValueError:
                    raise ValueError(f"SleepStep {self.id}: Invalid duration: {duration_config}")
        else:
            # Assume it's a number
            try:
                duration = float(duration_config)
            except (TypeError, ValueError):
                raise ValueError(f"SleepStep {self.id}: Duration must be a number, got {type(duration_config)}")

        # Validate duration is non-negative
        if duration < 0:
            raise ValueError(f"SleepStep {self.id}: Duration must be non-negative, got {duration}")

        # Sleep
        await asyncio.sleep(duration)
