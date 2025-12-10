# GraphFlow Memory System - Technical Reference

This document provides a comprehensive technical reference for the GraphFlow memory system, covering architecture, implementation details, and internals for developers and contributors.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Memory Namespaces](#memory-namespaces)
- [Supported Types](#supported-types)
- [Field Definitions](#field-definitions)
- [Memory Lifecycle](#memory-lifecycle)
- [Template Syntax and Resolution](#template-syntax-and-resolution)
- [Validation](#validation)
- [Debug Mode Memory Editing](#debug-mode-memory-editing)
- [Key Source Files](#key-source-files)

---

## Architecture Overview

### Design Principles

GraphFlow separates **control flow** from **data flow**:

- **Control Flow**: Defined by edges connecting steps - determines execution order
- **Data Flow**: Managed through memory - steps read inputs and write outputs to a shared memory store

This separation provides:
1. Clear visualization of how data moves through the graph
2. Easy debugging with memory inspection
3. Flexibility in how steps communicate
4. Support for parallel execution paths

### MemoryStore Class

The `MemoryStore` class (`packages/graph-core/graphflow_core/memory/store.py`) is the central runtime container for all data during graph execution.

```python
class MemoryStore:
    """Memory store for graph execution with namespace support."""

    def __init__(self, schema: MemorySchema):
        self.schema = schema
        self._inputs: Dict[str, Any] = {}
        self._outputs: Dict[str, Any] = {}
        self._intermediate: Dict[str, Any] = {}
        self._secrets: Dict[str, str] = {}
        self._initialized = False
```

Each run gets its own `MemoryStore` instance, ensuring isolation between concurrent executions.

---

## Memory Namespaces

GraphFlow organizes memory into six distinct namespaces, each with specific purposes and behaviors:

### Namespace Summary

| Namespace | Syntax | Purpose | Read | Write | Scope |
|-----------|--------|---------|------|-------|-------|
| `memory.inputs` | `{memory.field}` | Run inputs | Yes | No* | Per-run |
| `memory.intermediate` | `{memory.field}` | Step outputs, temp values | Yes | Yes | Per-run |
| `memory.outputs` | `{memory.field}` | Final outputs | Yes | Yes | Per-run |
| `config.*` | `{config.field}` | System configuration | Yes | No | Global |
| `env.*` | `{env.field}` | Environment variables | Yes | Yes | Global |
| `secrets.*` | `{secrets.field}` | Sensitive values | Yes | No** | Per-run |

\* Inputs are set at initialization and should not be modified during execution
\** Secrets can be cached/set programmatically but UI editing is restricted

### 1. Memory Namespace (`memory.*`)

The primary namespace for graph execution data. Contains three sub-sections:

#### Inputs (`memory.inputs`)
- Values provided when the graph starts execution
- Set via `initialize_inputs()` method
- Read-only during execution (not enforced, but convention)
- Missing required inputs raise validation errors

#### Intermediate (`memory.intermediate`)
- Temporary values used during execution
- Where step outputs are typically written
- Auto-created by the Builder UI with pattern `{stepId}.{propertyName}`
- Cleaned up automatically when steps are deleted

#### Outputs (`memory.outputs`)
- Final results returned when the graph completes
- Typically written by `output` steps or final steps
- Returned to the caller after execution

**Read Resolution Order** (for legacy non-namespaced syntax):
```python
# When reading "field_name" without namespace prefix:
# 1. Check inputs
# 2. Check intermediate
# 3. Check outputs
# 4. Return "" (empty string) if not found
```

### 2. Config Namespace (`config.*`)

System configuration values that are:
- **Read-only** at runtime (writes raise `ValueError`)
- **Globally shared** across all MemoryStore instances in a process
- Populated by the runtime before execution

```python
# Global registry
_RUNTIME_CONFIG: Dict[str, Any] = {}

# Common config values:
# - cwd: Current working directory
# - runtime_url: Runtime API URL (e.g., "http://localhost:8000")
# - ui_url: Builder URL (e.g., "http://localhost:3000")
# - runtime_id: Runtime instance identifier
```

### 3. Environment Namespace (`env.*`)

Direct proxy to `os.environ` with schema-defined mappings:

```python
# Schema definition
"environment": {
    "api_url": {
        "type": "string",
        "key": "API_BASE_URL",  # Actual env var name
        "required": true
    }
}

# Usage: {env.api_url} reads os.environ["API_BASE_URL"]
```

- **Readable and writable** at runtime
- Changes affect `os.environ` directly
- Schema maps friendly names to actual environment variable names

### 4. Secrets Namespace (`secrets.*`)

Sensitive values loaded from secret providers:

```python
# Schema definition
"secrets": {
    "api_key": {
        "provider": "env",           # Provider: env, vault, aws_secrets
        "key": "OPENAI_API_KEY",     # Provider-specific key
        "description": "OpenAI API key"
    }
}
```

**Supported Providers:**
| Provider | Implementation | Status |
|----------|---------------|--------|
| `env` | Reads from environment variable | Implemented |
| `vault` | HashiCorp Vault integration | Planned |
| `aws_secrets` | AWS Secrets Manager | Planned |

**Behavior:**
- Cached after first read (avoid repeated provider calls)
- UI editing restricted for security
- Debug mode does not expose secret values

---

## Supported Types

Memory fields support six data types, each with a defined "zero value" used for initialization:

| Type | Zero Value | Python Equivalent | JSON Schema Type |
|------|-----------|-------------------|------------------|
| `string` | `""` | `str` | `"string"` |
| `number` | `0` | `int` or `float` | `"number"` |
| `boolean` | `False` | `bool` | `"boolean"` |
| `object` | `{}` | `dict` | `"object"` |
| `array` | `[]` | `list` | `"array"` |
| `any` | `None` | `Any` | N/A |

### Zero Value Implementation

```python
def _get_zero_value(self, field_type: str) -> Any:
    """Get the zero value for a field type."""
    zero_values = {
        'string': '',
        'number': 0,
        'boolean': False,
        'object': {},
        'array': [],
        'any': None,
    }
    return zero_values.get(field_type, None)
```

### Type Validation

Types are validated at schema definition time:

```python
@field_validator('type')
@classmethod
def validate_type(cls, v: str) -> str:
    valid_types = {'string', 'number', 'boolean', 'object', 'array', 'any'}
    if v not in valid_types:
        raise ValueError(f'type must be one of {valid_types}')
    return v
```

---

## Field Definitions

### FieldDefinition (inputs, outputs, intermediate)

```python
class FieldDefinition(BaseModel):
    """Definition of a memory field."""
    type: str           # string, number, boolean, object, array, any
    description: Optional[str] = None
    required: bool = True
    default: Optional[Any] = None
```

### SecretDefinition

```python
class SecretDefinition(BaseModel):
    """Definition of a secret."""
    provider: str       # env, vault, aws_secrets
    key: str            # Provider-specific key (e.g., env var name)
    description: Optional[str] = None
```

### ConfigDefinition

```python
class ConfigDefinition(BaseModel):
    """Definition of a configuration value."""
    type: str           # string, number, boolean (limited types)
    description: Optional[str] = None
```

### EnvironmentDefinition

```python
class EnvironmentDefinition(BaseModel):
    """Definition of an environment variable reference."""
    type: str           # string, number, boolean
    key: str            # Actual environment variable name
    description: Optional[str] = None
    required: bool = True
```

---

## Memory Lifecycle

### 1. Schema Parsing

When a graph is loaded, the memory schema is parsed into a `MemorySchema` object:

```python
class MemorySchema(BaseModel):
    """Schema for memory store."""
    inputs: Dict[str, FieldDefinition] = Field(default_factory=dict)
    outputs: Dict[str, FieldDefinition] = Field(default_factory=dict)
    intermediate: Dict[str, FieldDefinition] = Field(default_factory=dict)
    secrets: Dict[str, SecretDefinition] = Field(default_factory=dict)
    config: Dict[str, ConfigDefinition] = Field(default_factory=dict)
    environment: Dict[str, EnvironmentDefinition] = Field(default_factory=dict)
```

### 2. MemoryStore Initialization

```python
def __init__(self, schema: MemorySchema):
    # Initialize intermediate fields with defaults or zero values
    for key, field_def in schema.intermediate.items():
        if field_def.default is not None:
            self._intermediate[key] = field_def.default
        else:
            self._intermediate[key] = self._get_zero_value(field_def.type)

    # Initialize output fields similarly
    for key, field_def in schema.outputs.items():
        if field_def.default is not None:
            self._outputs[key] = field_def.default
        else:
            self._outputs[key] = self._get_zero_value(field_def.type)
```

### 3. Input Initialization

```python
def initialize_inputs(self, inputs: Dict[str, Any]) -> None:
    """Initialize inputs with provided values."""
    # Apply defaults for missing optional inputs
    for key, field_def in self.schema.inputs.items():
        if key not in inputs:
            if field_def.default is not None:
                inputs[key] = field_def.default
            elif field_def.required:
                raise ValueError(f"Required input missing: {key}")

    self._inputs = inputs.copy()
    self._initialized = True
```

### 4. Runtime Config Population

```python
def populate_config(self, config_values: Dict[str, Any]) -> None:
    """Populate global runtime configuration."""
    global _RUNTIME_CONFIG
    _RUNTIME_CONFIG.update(config_values)
```

### 5. Step Execution

Steps read and write during execution:

```python
async def execute(self, memory: MemoryStore) -> None:
    # Read inputs
    value = memory.read("memory.input_field")

    # Process...
    result = process(value)

    # Write outputs
    memory.write("memory.output_field", result)
```

### 6. Output Collection

After execution completes, outputs are extracted:

```python
def get_outputs(self) -> Dict[str, Any]:
    """Return the outputs namespace."""
    return self._outputs.copy()
```

---

## Template Syntax and Resolution

### Primary Syntax: `{namespace.field}`

The standard template syntax uses single braces with namespaced keys:

```
{memory.user_input}      → reads from memory (inputs/intermediate/outputs)
{config.runtime_url}     → reads from global config
{env.api_url}            → reads from environment variable
{secrets.api_key}        → reads from secret provider
```

### Legacy Syntax: `{{variable}}`

Used in specific contexts like SQL queries (deprecated, use namespaced syntax):

```python
# Legacy syntax - still supported for backwards compatibility
"SELECT * FROM users WHERE id = {{user_id}}"
```

---

## Centralized Template Resolution

### TemplateResolver Class

GraphFlow provides a centralized `TemplateResolver` class in `graph-core` that all plugins and steps should use for template resolution. This ensures consistent behavior across the entire platform.

**Location:** `packages/graph-core/graphflow_core/memory/resolver.py`

```python
from graphflow_core.memory.resolver import TemplateResolver

# Instance usage (runtime resolution)
resolver = TemplateResolver(memory)
result = resolver.resolve("Hello {memory.user_name}!")
data = resolver.resolve_dict({"url": "{config.api_base}/users"})

# Static usage (compile-time analysis)
refs = TemplateResolver.find_references("{memory.query} and {secrets.api_key}")
# Returns: {"memory.query", "secrets.api_key"}
```

### TemplateResolver API

| Method | Type | Purpose |
|--------|------|---------|
| `resolve(template)` | Instance | Resolve all `{namespace.field}` patterns in a string |
| `resolve_dict(data)` | Instance | Recursively resolve all strings in a dictionary |
| `resolve_list(data)` | Instance | Recursively resolve all strings in a list |
| `find_references(template)` | Static | Extract all memory references without resolving |

### MemoryMixin for Steps

Steps can use the `MemoryMixin` class to get standardized memory operations:

**Location:** `packages/graph-core/graphflow_core/steps/memory_mixin.py`

```python
from graphflow_core.steps.memory_mixin import MemoryMixin

class MyStep(StepBase, MemoryMixin):
    async def execute(self, memory: MemoryStore) -> None:
        # Resolve a template string
        url = self._resolve(self.config["url"], memory)

        # Resolve all strings in a dict
        headers = self._resolve_dict(self.config["headers"], memory)

        # Get a value with optional resolution
        value = self._get_value("field_name", memory, default="fallback")

        # Write output to memory
        self._write_output("result", my_data, memory)
```

### MemoryMixin API

| Method | Purpose |
|--------|---------|
| `_get_resolver(memory)` | Get a TemplateResolver for the memory store |
| `_resolve(template, memory)` | Resolve a single template string |
| `_resolve_dict(data, memory)` | Resolve all strings in a dictionary |
| `_get_value(key, memory, default, resolve)` | Read and optionally resolve a value |
| `_write_output(key, value, memory, namespace)` | Write to memory with namespace handling |

### MemoryStore Convenience Methods

The `MemoryStore` class also provides direct access to template resolution:

```python
# Get a resolver
resolver = memory.get_resolver()

# Or use the convenience method
result = memory.resolve_template("Hello {memory.user_name}!")
```

---

## Legacy Template Resolution (Deprecated)

> **Note:** The patterns below are deprecated. Use `TemplateResolver` and `MemoryMixin` instead.

#### Variable Name Prefixing (eval/exec contexts)

When injecting memory values into Python code (conditional, transform steps), variables are prefixed to avoid shadowing built-ins:

```python
# Original condition: {memory.score} > 0.8
# Becomes: _mem_score > 0.8

for match in pattern.finditer(condition):
    memory_key = match.group(1)
    var_name = '_mem_' + memory_key.replace('.', '_')
    eval_context[var_name] = memory.read(memory_key)
    adjusted_condition = adjusted_condition.replace(
        f'{{memory.{memory_key}}}', var_name
    )

# Safe evaluation with restricted namespace
result = eval(adjusted_condition, {"__builtins__": {}}, eval_context)
```

### Memory Reference Extraction

The system automatically extracts memory references from step configuration:

```python
def _extract_memory_refs(self, value: Any) -> Set[str]:
    """Recursively extract memory references from a value."""
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
    """Memory keys read by this step (from config)."""
    return sorted(self._extract_memory_refs(self.config))

@property
def memory_writes(self) -> List[str]:
    """Memory keys written by this step (from outputs)."""
    return sorted(self._extract_memory_refs(self.outputs))
```

---

## Validation

### Graph-Level Validation

The graph validates all memory references at load time:

```python
def validate_graph_structure(self) -> List[str]:
    """Validate graph structure and return list of errors."""
    errors = []

    # Build set of all valid namespaced keys
    all_namespaced_keys = (
        {f"memory.{k}" for k in self.memory.inputs.keys()} |
        {f"memory.{k}" for k in self.memory.outputs.keys()} |
        {f"memory.{k}" for k in self.memory.intermediate.keys()} |
        {f"config.{k}" for k in self.memory.config.keys()} |
        {f"env.{k}" for k in self.memory.environment.keys()} |
        {f"secrets.{k}" for k in self.memory.secrets.keys()}
    )

    for step in self.steps:
        reads, writes = parse_memory_references(step.config, step.outputs)

        for key in reads:
            if key not in all_namespaced_keys:
                errors.append(
                    f"Step {step.id}: memory reference '{{{key}}}' "
                    f"references undeclared memory key"
                )

    return errors
```

### Runtime Validation

```python
def validate_references(self) -> list:
    """Validate that all required config/env/secrets exist."""
    warnings = []

    # Check required environment variables
    for schema_key, env_def in self.schema.environment.items():
        if env_def.required and os.getenv(env_def.key) is None:
            warnings.append(f"Required env var not set: {env_def.key}")

    # Check secrets availability
    for key, secret_def in self.schema.secrets.items():
        if secret_def.provider == "env":
            if os.getenv(secret_def.key) is None:
                warnings.append(f"Secret not available: {secret_def.key}")

    return warnings
```

### Graceful Handling

Missing memory keys in the `memory.*` namespace return empty string instead of raising errors:

```python
def read(self, key: str) -> Any:
    if namespace == "memory":
        if field_key in self._inputs:
            return self._inputs[field_key]
        elif field_key in self._intermediate:
            return self._intermediate[field_key]
        elif field_key in self._outputs:
            return self._outputs[field_key]
        else:
            return ""  # Graceful handling for missing keys
```

---

## Debug Mode Memory Editing

### ExecutionController Integration

The `ExecutionController` manages pause/resume/step operations:

```python
class ExecutionController:
    def __init__(self, run_id: str, initial_breakpoints: Set[str] = None):
        self.state = ExecutionState.PAUSED  # Start paused in debug mode
        self.breakpoints: Set[str] = initial_breakpoints or set()
        self._resume_event = asyncio.Event()

    async def wait_if_paused(self, step_id: str) -> None:
        """Check if should pause before executing step."""
        if step_id in self.breakpoints:
            self.state = ExecutionState.PAUSED
            self._resume_event.clear()

        if self.state == ExecutionState.PAUSED:
            await self._resume_event.wait()
```

### Memory Update API

```python
def update_memory_value(
    self, run_id: str, namespace: str, key: str, value: Any
) -> bool:
    """Update memory value while paused (debug mode only)."""
    memory = self.get_memory(run_id)
    controller = self.get_controller(run_id)

    # Only allow editing when paused
    if controller.get_state()['status'] != 'paused':
        return False

    # Update based on namespace
    if namespace == 'inputs':
        memory.set_input(key, value)
    elif namespace == 'outputs':
        memory.set_output(key, value)
    elif namespace == 'intermediate':
        memory.set_intermediate(key, value)
    elif namespace == 'config':
        memory.set_config(key, value)
    elif namespace == 'environment':
        memory.set_environment(key, value)
    elif namespace == 'secrets':
        return False  # Secrets cannot be edited for security

    return True
```

### REST API Endpoint

```
PUT /api/v1/agents/{agent_id}/runs/{run_id}/debug/memory
Content-Type: application/json

{
    "namespace": "intermediate",
    "key": "step_output",
    "value": {"modified": "data"}
}
```

---

## Key Source Files

### Core Implementation

| File | Description |
|------|-------------|
| `packages/graph-core/graphflow_core/memory/store.py` | `MemoryStore` class - main memory container |
| `packages/graph-core/graphflow_core/memory/resolver.py` | `TemplateResolver` - centralized template resolution |
| `packages/graph-core/graphflow_core/steps/memory_mixin.py` | `MemoryMixin` - standardized step memory operations |
| `packages/graph-core/graphflow_core/models/graph.py` | Schema models (`MemorySchema`, `FieldDefinition`, etc.) |
| `packages/graph-core/graphflow_core/steps/base.py` | `StepBase` with memory reference extraction |

### Runtime Integration

| File | Description |
|------|-------------|
| `packages/graph-runtime/graphflow_runtime/executor/async_executor.py` | Memory initialization and debug editing |
| `packages/graph-runtime/graphflow_runtime/executor/logging_memory.py` | `LoggingMemoryStore` for execution tracking |
| `packages/graph-runtime/graphflow_runtime/executor/execution_controller.py` | Debug mode pause/resume control |

### Plugin Examples

| File | Description |
|------|-------------|
| `packages/graph-plugins-http/graphflow_http/base.py` | HTTP step using MemoryMixin |
| `packages/graph-plugins-ai/graphflow_ai/templates/llm/pydantic_ai.jinja` | LLM step memory access |
| `packages/graph-plugins-json/graphflow_json/base.py` | JSON step using MemoryMixin |

---

## Related Documentation

- **[Memory User Guide](MEMORY_USER_GUIDE.md)** - User-focused guide for Builder UI
- **[Graph Format Specification](GRAPH_FORMAT.md)** - Memory schema in graph JSON
- **[Plugin Development Guide](PLUGIN_DEVELOPMENT.md)** - Memory operations for plugins

---

**Version:** 1.1
**Last Updated:** 2025-12-09
