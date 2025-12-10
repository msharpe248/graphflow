# graphflow-core

Core library for GraphFlow providing shared abstractions, models, and utilities.

## Features

- **Graph Definition Models**: Pydantic models for graph structure, steps, and edges
- **Memory Store**: Runtime memory management with typed schemas
- **Template Resolution**: Centralized `TemplateResolver` for `{namespace.field}` pattern resolution
- **Step System**: Base classes, registry, and `MemoryMixin` for step types
- **Built-in Steps**: Common step types (start, llm, output, conditional, etc.)

## Installation

```bash
pip install -e .
```

## Usage

### Basic Usage

```python
from graphflow_core.models import GraphDefinition
from graphflow_core.memory import MemoryStore
from graphflow_core.steps import StepRegistry

# Load graph definition
graph = GraphDefinition.model_validate_json(json_string)

# Create memory store
memory = MemoryStore(schema=graph.memory)

# Get step class
step_class = StepRegistry.get("llm")
step = step_class(id="llm_1", config={...}, memory_reads=[], memory_writes=[])

# Execute step
await step.execute(memory)
```

### Template Resolution

Use `TemplateResolver` for consistent resolution of `{namespace.field}` patterns:

```python
from graphflow_core.memory.resolver import TemplateResolver

# Instance methods (runtime resolution)
resolver = TemplateResolver(memory)
url = resolver.resolve("https://api.example.com/users/{memory.user_id}")
config = resolver.resolve_dict({"url": "{config.api_base}", "key": "{secrets.api_key}"})

# Static methods (compile-time analysis)
refs = TemplateResolver.find_references("{memory.query} and {secrets.key}")
# Returns: {"memory.query", "secrets.key"}
```

### MemoryMixin for Steps

Use `MemoryMixin` for standardized memory operations in custom steps:

```python
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.memory_mixin import MemoryMixin

class MyStep(StepBase, MemoryMixin):
    async def execute(self, memory):
        # Resolve templates
        url = self._resolve(self.config["url"], memory)
        headers = self._resolve_dict(self.config["headers"], memory)

        # Read with defaults
        timeout = self._get_value("timeout", memory, default=30)

        # Write output
        self._write_output("result", {"data": "..."}, memory)
```

## Development

Run tests:
```bash
pytest
```
