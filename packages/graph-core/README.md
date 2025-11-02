# graphflow-core

Core library for GraphFlow providing shared abstractions, models, and utilities.

## Features

- **Graph Definition Models**: Pydantic models for graph structure, steps, and edges
- **Memory Store**: Runtime memory management with typed schemas
- **Step System**: Base classes and registry for step types
- **Built-in Steps**: Common step types (start, llm, output, conditional, etc.)

## Installation

```bash
pip install -e .
```

## Usage

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

## Development

Run tests:
```bash
pytest
```
