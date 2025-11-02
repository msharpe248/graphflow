# graphflow-compiler

Compiler for GraphFlow that transpiles graph definitions to executable Python code.

## Features

- **Multi-Framework Support**: Generate code for Pydantic AI or LangGraph
- **Standalone Programs**: Generated code can run independently
- **Runtime Compatible**: Generated code can also run in graphflow-runtime
- **Template-Based**: Uses Jinja2 for flexible code generation
- **CLI Tool**: Command-line interface for compilation

## Installation

```bash
pip install -e .

# With Pydantic AI support
pip install -e ".[pydantic_ai]"

# With LangGraph support
pip install -e ".[langgraph]"

# With both
pip install -e ".[pydantic_ai,langgraph]"
```

## Usage

### Command Line

```bash
# Compile to Pydantic AI
graphflow-compile examples/simple_agent.json --framework pydantic_ai --output agent.py

# Compile to LangGraph
graphflow-compile examples/simple_agent.json --framework langgraph --output agent.py

# Compile for runtime (no standalone wrappers)
graphflow-compile examples/simple_agent.json --framework pydantic_ai --runtime
```

### Python API

```python
from graphflow_compiler import compile_graph
from graphflow_core import GraphDefinition

# Load graph
graph = GraphDefinition.model_validate_json(json_str)

# Compile
code = compile_graph(graph, framework="pydantic_ai", standalone=True)

# Write to file
with open("agent.py", "w") as f:
    f.write(code)
```

## Generated Code

The compiler generates Python code with:
- Memory store initialization
- Step execution logic
- Framework-specific constructs (Pydantic AI Agent or LangGraph StateGraph)
- Optional CLI/FastAPI wrappers for standalone execution

## Development

Run tests:
```bash
pytest
```
