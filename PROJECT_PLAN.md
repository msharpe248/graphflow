# GraphFlow - Project Plan & Architecture

**Last Updated:** 2025-10-29
**Status:** ✅ **PHASES 1-3 COMPLETE** | ⏳ Phase 4 (UI) Pending

## Implementation Status

| Phase | Component | Status | Completion |
|-------|-----------|--------|------------|
| **Phase 1** | graph-core | ✅ COMPLETE | 100% |
| **Phase 2** | graph-compiler | ✅ COMPLETE | 100% |
| **Phase 3** | graph-runtime | ✅ COMPLETE | 100% |
| **Phase 4** | graph-builder (UI) | ⏳ PLANNED | 0% |

**What Works Now:**
- ✅ 10 built-in step types (start, llm, http, loop, conditional, etc.)
- ✅ Pydantic AI & LangGraph code generation
- ✅ CLI tools (graphflow-compile, graphflow-runtime)
- ✅ Full REST API with 15+ endpoints
- ✅ Async execution engine with memory inspection
- ✅ End-to-end tested and working!

**See**: [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) for complete details.

---

## Project Overview

GraphFlow is a low-code agent builder system inspired by n8n and Langflow, with a focus on:
- **Decoupled control and data flow**: Edges define control flow, memory store handles data
- **Framework agnostic**: Compile to Pydantic AI or LangGraph from same graph definition
- **Better runtime environment**: Long-running agents with queryable memory and full lifecycle management

### Three Main Components

1. **graph-builder** - React UI for visual graph construction
2. **graph-compiler** - Transpiler from graph JSON to executable Python (Pydantic AI / LangGraph)
3. **graph-runtime-manager** - FastAPI execution environment for running and managing agents

---

## Key Architectural Principle

**Control Flow ≠ Data Flow**

- **Control Flow**: Defined by graph edges (which step executes next)
- **Data Flow**: Defined by memory store reads/writes (steps declare what they read/write)
- **Synchronization**: Join steps allow multiple branches to merge

This allows:
- Steps to access any data in memory, not just from predecessor
- Parallel execution paths that can synchronize
- Flexible data access patterns independent of graph topology

---

## Project Structure

```
graphflow/
├── packages/
│   ├── graph-core/              # Shared core library
│   │   ├── graphflow_core/
│   │   │   ├── models/          # Pydantic models for graph definitions
│   │   │   ├── memory/          # Memory store abstractions
│   │   │   ├── steps/           # Step registry and base classes
│   │   │   └── schemas/         # JSON schemas for validation
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── graph-compiler/          # Compiler component
│   │   ├── graphflow_compiler/
│   │   │   ├── generators/
│   │   │   │   ├── pydantic_ai.py
│   │   │   │   └── langgraph.py
│   │   │   ├── templates/       # Code generation templates
│   │   │   └── cli.py           # CLI tool for compilation
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── graph-runtime/           # Runtime manager component
│   │   ├── graphflow_runtime/
│   │   │   ├── api/             # FastAPI endpoints
│   │   │   ├── executor/        # Graph execution engine
│   │   │   ├── storage/         # SQLAlchemy models
│   │   │   └── main.py          # FastAPI app
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   └── graph-builder/           # React UI component
│       ├── src/
│       │   ├── components/
│       │   │   ├── GraphCanvas/
│       │   │   ├── StepPalette/
│       │   │   ├── StepConfig/
│       │   │   └── MemoryInspector/
│       │   ├── api/             # API client for runtime
│       │   ├── types/           # TypeScript types
│       │   └── App.tsx
│       ├── package.json
│       └── README.md
│
├── examples/                     # Example graph definitions and programs
├── docs/                        # Documentation
├── PROJECT_PLAN.md              # This file
├── pyproject.toml              # Root project config
└── README.md
```

---

## Core Data Model: Graph Definition JSON

The graph definition is the contract between all components. The UI exports this, the compiler reads this, and the runtime can accept this.

### Complete Example

```json
{
  "version": "1.0",
  "metadata": {
    "name": "My Agent",
    "description": "Example agent",
    "created": "2025-10-29T00:00:00Z",
    "framework_hints": ["pydantic_ai", "langgraph"]
  },

  "memory": {
    "inputs": {
      "user_query": {
        "type": "string",
        "description": "User question",
        "required": true
      },
      "context": {
        "type": "object",
        "description": "Additional context",
        "required": false
      }
    },
    "outputs": {
      "answer": {
        "type": "string",
        "description": "Final answer"
      },
      "confidence": {
        "type": "number",
        "description": "Confidence score"
      }
    },
    "intermediate": {
      "llm_response": {"type": "string"},
      "search_results": {"type": "array"},
      "processed_data": {"type": "object"}
    },
    "secrets": {
      "api_key": {
        "provider": "env",
        "key": "OPENAI_API_KEY"
      }
    }
  },

  "steps": [
    {
      "id": "start_1",
      "type": "start",
      "config": {},
      "memory_reads": [],
      "memory_writes": []
    },
    {
      "id": "llm_1",
      "type": "llm",
      "config": {
        "model": "gpt-4",
        "prompt_template": "Answer the question: {{user_query}}\n\nContext: {{context}}",
        "mcp_servers": [],
        "tools": ["web_search"],
        "temperature": 0.7
      },
      "memory_reads": ["user_query", "context"],
      "memory_writes": ["llm_response"]
    },
    {
      "id": "transform_1",
      "type": "transform",
      "config": {
        "operation": "add_confidence",
        "code": "return {'processed': llm_response, 'score': 0.95}"
      },
      "memory_reads": ["llm_response"],
      "memory_writes": ["processed_data"]
    },
    {
      "id": "output_1",
      "type": "output",
      "config": {
        "mapping": {
          "answer": "processed_data.processed",
          "confidence": "processed_data.score"
        }
      },
      "memory_reads": ["processed_data"],
      "memory_writes": ["answer", "confidence"]
    }
  ],

  "edges": [
    {
      "id": "edge_1",
      "from": "start_1",
      "to": "llm_1",
      "condition": null
    },
    {
      "id": "edge_2",
      "from": "llm_1",
      "to": "transform_1",
      "condition": null
    },
    {
      "id": "edge_3",
      "from": "transform_1",
      "to": "output_1",
      "condition": null
    }
  ]
}
```

### Key Schema Components

**Memory Sections:**
- `inputs`: Values provided when agent starts (runtime inputs)
- `outputs`: Final results from agent execution
- `intermediate`: Temporary storage for step results
- `secrets`: Secure values (API keys, credentials)

**Step Definition:**
- `id`: Unique identifier
- `type`: Step type from registry
- `config`: Step-specific configuration
- `memory_reads`: List of memory keys this step reads
- `memory_writes`: List of memory keys this step writes

**Edge Definition:**
- `from`: Source step ID
- `to`: Target step ID
- `condition`: Optional condition for conditional branching (evaluated against memory)

---

## Component 1: graph-core

### Purpose
Shared library providing core abstractions, models, and utilities used by all other components.

### Key Classes

```python
# models/graph.py
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class Metadata(BaseModel):
    name: str
    description: Optional[str] = None
    created: str
    framework_hints: List[str] = []

class FieldDefinition(BaseModel):
    type: str  # string, number, boolean, object, array
    description: Optional[str] = None
    required: bool = True

class SecretDefinition(BaseModel):
    provider: str  # env, vault, aws_secrets
    key: str

class MemorySchema(BaseModel):
    inputs: Dict[str, FieldDefinition]
    outputs: Dict[str, FieldDefinition]
    intermediate: Dict[str, FieldDefinition]
    secrets: Dict[str, SecretDefinition]

class Step(BaseModel):
    id: str
    type: str
    config: Dict[str, Any]
    memory_reads: List[str]
    memory_writes: List[str]

class Edge(BaseModel):
    id: str
    from_: str  # Use from_ to avoid Python keyword
    to: str
    condition: Optional[str] = None  # Python expression evaluated against memory

class GraphDefinition(BaseModel):
    version: str
    metadata: Metadata
    memory: MemorySchema
    steps: List[Step]
    edges: List[Edge]

    class Config:
        # Allow 'from' field in Edge
        fields = {'from_': 'from'}
```

```python
# memory/store.py
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

class MemoryStore:
    """Runtime memory implementation"""

    def __init__(self, schema: MemorySchema):
        self.schema = schema
        self._inputs: Dict[str, Any] = {}
        self._outputs: Dict[str, Any] = {}
        self._intermediate: Dict[str, Any] = {}
        self._secrets: Dict[str, str] = {}

    def read(self, key: str) -> Any:
        """Read from memory (checks all sections)"""
        # Check inputs first, then intermediate, then outputs
        if key in self._inputs:
            return self._inputs[key]
        if key in self._intermediate:
            return self._intermediate[key]
        if key in self._outputs:
            return self._outputs[key]
        raise KeyError(f"Memory key not found: {key}")

    def write(self, key: str, value: Any) -> None:
        """Write to memory (determines section from schema)"""
        if key in self.schema.outputs:
            self._outputs[key] = value
        elif key in self.schema.intermediate:
            self._intermediate[key] = value
        else:
            raise KeyError(f"Memory key not in schema: {key}")

    def set_input(self, key: str, value: Any) -> None:
        """Set input value (called during initialization)"""
        if key not in self.schema.inputs:
            raise KeyError(f"Not an input key: {key}")
        self._inputs[key] = value

    def get_secret(self, key: str) -> str:
        """Get secret value"""
        if key not in self._secrets:
            # Load secret based on provider
            secret_def = self.schema.secrets[key]
            if secret_def.provider == "env":
                import os
                self._secrets[key] = os.getenv(secret_def.key, "")
            # TODO: Support other providers (vault, aws_secrets)
        return self._secrets[key]

    def get_all_inputs(self) -> Dict[str, Any]:
        return self._inputs.copy()

    def get_all_outputs(self) -> Dict[str, Any]:
        return self._outputs.copy()

    def get_all_intermediate(self) -> Dict[str, Any]:
        return self._intermediate.copy()

    def to_dict(self) -> Dict[str, Any]:
        """Return complete memory state"""
        return {
            "inputs": self._inputs,
            "outputs": self._outputs,
            "intermediate": self._intermediate
        }
```

```python
# steps/base.py
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class StepBase(ABC):
    """Base class for all step types"""

    def __init__(self, id: str, config: Dict[str, Any],
                 memory_reads: List[str], memory_writes: List[str]):
        self.id = id
        self.config = config
        self.memory_reads = memory_reads
        self.memory_writes = memory_writes

    @abstractmethod
    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute step logic.
        Read from memory using memory.read(key)
        Write to memory using memory.write(key, value)
        """
        pass

    @classmethod
    def get_type(cls) -> str:
        """Return step type identifier"""
        raise NotImplementedError


# steps/registry.py
from typing import Type, Dict

class StepRegistry:
    """Global registry for step types"""
    _registry: Dict[str, Type[StepBase]] = {}

    @classmethod
    def register(cls, step_type: str):
        """Decorator to register a step class"""
        def decorator(step_class: Type[StepBase]):
            cls._registry[step_type] = step_class
            return step_class
        return decorator

    @classmethod
    def get(cls, step_type: str) -> Type[StepBase]:
        """Get step class by type"""
        if step_type not in cls._registry:
            raise ValueError(f"Unknown step type: {step_type}")
        return cls._registry[step_type]

    @classmethod
    def list_types(cls) -> List[str]:
        """List all registered step types"""
        return list(cls._registry.keys())
```

### Built-in Step Types

| Step Type | Description | Config Parameters | Typical Memory Usage |
|-----------|-------------|-------------------|---------------------|
| `start` | Entry point, no operation | None | Reads: none, Writes: none |
| `llm` | LLM call with tools/MCP | model, prompt_template, tools, mcp_servers, temperature | Reads: user-defined, Writes: response |
| `output` | Map intermediate → outputs | mapping (dict) | Reads: intermediate, Writes: outputs |
| `conditional` | Branching logic | condition (expression) | Reads: user-defined, Writes: none |
| `loop` | Iteration | collection_key, item_key, max_iterations | Reads: collection, Writes: iteration results |
| `http` | HTTP request | method, url_template, headers, body_template | Reads: request params, Writes: response |
| `transform` | Data transformation | operation, code/function | Reads: input data, Writes: transformed data |
| `human_input` | Wait for human | prompt, input_type | Reads: prompt data, Writes: user input |
| `join` | Synchronization point | wait_for (list of step IDs) | Reads: none, Writes: none |
| `db_query` | Database query | connection, query_template | Reads: query params, Writes: results |
| `data_extract` | Parse/extract data | extractor_type (json, xml, regex), pattern | Reads: raw data, Writes: extracted data |

### Dependencies
- Python 3.11+
- Pydantic 2.x
- typing-extensions

---

## Component 2: graph-compiler

### Purpose
Transpile graph JSON definitions into executable Python code for different frameworks (Pydantic AI, LangGraph).

### Architecture

```python
# generators/base.py
from abc import ABC, abstractmethod
from graphflow_core.models import GraphDefinition

class CodeGenerator(ABC):
    """Base class for code generators"""

    @abstractmethod
    def generate(self, graph: GraphDefinition) -> str:
        """Generate Python code from graph definition"""
        pass

    def generate_imports(self, graph: GraphDefinition) -> str:
        """Generate import statements"""
        pass

    def generate_memory_setup(self, graph: GraphDefinition) -> str:
        """Generate memory store initialization"""
        pass

    def generate_steps(self, graph: GraphDefinition) -> str:
        """Generate step instantiation code"""
        pass

    def generate_execution_logic(self, graph: GraphDefinition) -> str:
        """Generate graph execution logic (framework-specific)"""
        pass


# generators/pydantic_ai.py
from jinja2 import Template

class PydanticAIGenerator(CodeGenerator):
    """Generate code using Pydantic AI + Pydantic AI Graph"""

    def generate(self, graph: GraphDefinition) -> str:
        template = self._load_template("pydantic_ai_agent.py.jinja")
        return template.render(graph=graph)

    def generate_execution_logic(self, graph: GraphDefinition) -> str:
        # Use Pydantic AI Graph for execution flow
        # Generate nodes and edges
        pass


# generators/langgraph.py
class LangGraphGenerator(CodeGenerator):
    """Generate code using LangGraph/LangChain"""

    def generate(self, graph: GraphDefinition) -> str:
        template = self._load_template("langgraph_agent.py.jinja")
        return template.render(graph=graph)

    def generate_execution_logic(self, graph: GraphDefinition) -> str:
        # Use LangGraph StateGraph
        # Generate nodes and edges
        pass
```

### CLI Tool

```python
# cli.py
import click
from pathlib import Path
from graphflow_core.models import GraphDefinition
from .generators.pydantic_ai import PydanticAIGenerator
from .generators.langgraph import LangGraphGenerator

@click.command()
@click.argument('graph_file', type=click.Path(exists=True))
@click.option('--framework',
              type=click.Choice(['pydantic_ai', 'langgraph']),
              default='pydantic_ai',
              help='Target framework')
@click.option('--output',
              type=click.Path(),
              help='Output file path (default: stdout)')
@click.option('--standalone/--runtime',
              default=True,
              help='Generate standalone script or runtime-compatible module')
def compile(graph_file: str, framework: str, output: str, standalone: bool):
    """Compile graph definition to executable Python code"""

    # Load graph definition
    with open(graph_file) as f:
        graph_dict = json.load(f)
    graph = GraphDefinition(**graph_dict)

    # Select generator
    if framework == 'pydantic_ai':
        generator = PydanticAIGenerator()
    else:
        generator = LangGraphGenerator()

    # Generate code
    code = generator.generate(graph)

    # Add standalone wrapper if needed
    if standalone:
        code = generator.add_standalone_wrapper(code)

    # Output
    if output:
        Path(output).write_text(code)
        click.echo(f"Generated code written to {output}")
    else:
        click.echo(code)


if __name__ == '__main__':
    compile()
```

### Generated Code Structure (Standalone)

```python
# Example: generated_agent.py
"""
Auto-generated by GraphFlow Compiler
Framework: pydantic_ai
Graph: My Agent
Generated: 2025-10-29
"""

from graphflow_core.memory import MemoryStore
from graphflow_core.models import MemorySchema, FieldDefinition
from graphflow_core.steps import StepRegistry
import asyncio

# Memory schema
MEMORY_SCHEMA = MemorySchema(
    inputs={
        "user_query": FieldDefinition(type="string", description="User question")
    },
    outputs={
        "answer": FieldDefinition(type="string", description="Final answer")
    },
    intermediate={
        "llm_response": FieldDefinition(type="string")
    },
    secrets={}
)

class GeneratedAgent:
    def __init__(self):
        self.memory = MemoryStore(schema=MEMORY_SCHEMA)

        # Initialize steps
        self.steps = {
            "start_1": StepRegistry.get("start")("start_1", {}, [], []),
            "llm_1": StepRegistry.get("llm")("llm_1", {...}, ["user_query"], ["llm_response"]),
            "output_1": StepRegistry.get("output")("output_1", {...}, ["llm_response"], ["answer"])
        }

    async def run(self, inputs: dict) -> dict:
        # Populate inputs
        for key, value in inputs.items():
            self.memory.set_input(key, value)

        # Execute graph (using Pydantic AI Graph or manual flow)
        await self.steps["start_1"].execute(self.memory)
        await self.steps["llm_1"].execute(self.memory)
        await self.steps["output_1"].execute(self.memory)

        # Return outputs
        return self.memory.get_all_outputs()

    def get_memory(self) -> dict:
        return self.memory.to_dict()


# Standalone CLI entry point
async def main():
    import sys
    import json

    if len(sys.argv) < 2:
        print("Usage: python generated_agent.py <inputs.json>")
        sys.exit(1)

    with open(sys.argv[1]) as f:
        inputs = json.load(f)

    agent = GeneratedAgent()
    outputs = await agent.run(inputs)
    print(json.dumps(outputs, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
```

### Dependencies
- graphflow-core
- Jinja2 (templating)
- Click (CLI)
- Pydantic AI (for pydantic_ai generator)
- LangGraph/LangChain (for langgraph generator)

---

## Component 3: graph-runtime-manager

### Purpose
Long-running FastAPI service for executing and managing compiled agents.

### API Endpoints

#### Agent Management

**POST /agents/upload**
Upload a compiled agent or graph definition.

Request:
```json
{
  "name": "my_agent",
  "framework": "pydantic_ai",
  "graph_definition": {...},  // Compile on-the-fly
  // OR
  "code": "base64_encoded_module"  // Pre-compiled
}
```

Response:
```json
{
  "agent_id": "uuid",
  "name": "my_agent",
  "framework": "pydantic_ai",
  "created_at": "2025-10-29T..."
}
```

**GET /agents**
List all agents.

**GET /agents/{agent_id}**
Get agent details.

**DELETE /agents/{agent_id}**
Delete agent and all its runs.

#### Execution Management

**POST /agents/{agent_id}/run**
Start a new agent execution.

Request:
```json
{
  "inputs": {
    "user_query": "What is the weather?"
  },
  "run_id": "optional_custom_id"
}
```

Response:
```json
{
  "run_id": "uuid",
  "agent_id": "uuid",
  "status": "running",
  "started_at": "2025-10-29T..."
}
```

**GET /agents/{agent_id}/runs**
List all runs for an agent.

**GET /agents/{agent_id}/runs/{run_id}/status**
Get run status.

Response:
```json
{
  "run_id": "uuid",
  "agent_id": "uuid",
  "status": "running|completed|failed|stopped",
  "started_at": "2025-10-29T...",
  "completed_at": "2025-10-29T...",
  "error": null
}
```

**POST /agents/{agent_id}/runs/{run_id}/stop**
Stop a running agent.

**DELETE /agents/{agent_id}/runs/{run_id}**
Release memory and cleanup.

#### Memory Inspection

**GET /agents/{agent_id}/runs/{run_id}/memory**
Get complete memory state.

Response:
```json
{
  "inputs": {...},
  "outputs": {...},
  "intermediate": {...}
}
```

**GET /agents/{agent_id}/runs/{run_id}/memory/{key}**
Get specific memory value.

Response:
```json
{
  "key": "llm_response",
  "value": "The weather is sunny."
}
```

### Database Schema

```python
# storage/models.py
from sqlalchemy import Column, String, DateTime, JSON, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    framework = Column(String, nullable=False)  # pydantic_ai | langgraph
    graph_definition = Column(JSON, nullable=False)
    code_path = Column(String, nullable=True)  # Path to compiled module
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    status = Column(String, nullable=False)  # running|completed|failed|stopped
    inputs = Column(JSON, nullable=False)
    outputs = Column(JSON, nullable=True)  # Populated on completion
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error = Column(Text, nullable=True)
```

### Execution Engine

```python
# executor/async_executor.py
import asyncio
from typing import Dict
from graphflow_core.memory import MemoryStore

class AsyncExecutor:
    """Manages async execution of agents"""

    def __init__(self):
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._memory_stores: Dict[str, MemoryStore] = {}

    async def start_run(self, agent_module, run_id: str, inputs: dict) -> None:
        """Start agent execution in background"""
        task = asyncio.create_task(self._execute(agent_module, run_id, inputs))
        self._running_tasks[run_id] = task

    async def _execute(self, agent_module, run_id: str, inputs: dict):
        """Execute agent and handle lifecycle"""
        try:
            # Create agent instance
            agent = agent_module.GeneratedAgent()

            # Store memory reference for inspection
            self._memory_stores[run_id] = agent.memory

            # Run agent
            outputs = await agent.run(inputs)

            # Update database with completion
            # ...

        except Exception as e:
            # Update database with error
            # ...
        finally:
            # Cleanup task reference
            if run_id in self._running_tasks:
                del self._running_tasks[run_id]

    def get_memory(self, run_id: str) -> MemoryStore:
        """Get memory store for a run"""
        return self._memory_stores.get(run_id)

    def stop_run(self, run_id: str):
        """Stop a running agent"""
        if run_id in self._running_tasks:
            self._running_tasks[run_id].cancel()

    def release_memory(self, run_id: str):
        """Release memory for a run"""
        if run_id in self._memory_stores:
            del self._memory_stores[run_id]
```

### FastAPI Application

```python
# main.py
from fastapi import FastAPI, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .storage.models import Base, Agent, AgentRun
from .executor.async_executor import AsyncExecutor
import uuid

app = FastAPI(title="GraphFlow Runtime Manager")
executor = AsyncExecutor()

# Database setup
engine = create_engine("sqlite:///graphflow.db")
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)

@app.post("/agents/upload")
async def upload_agent(request: dict):
    """Upload new agent"""
    # Validate and store agent
    # If graph_definition provided, compile on-the-fly
    pass

@app.post("/agents/{agent_id}/run")
async def start_run(agent_id: str, request: dict):
    """Start agent execution"""
    run_id = request.get("run_id", str(uuid.uuid4()))
    inputs = request["inputs"]

    # Load agent module
    # Start execution
    await executor.start_run(agent_module, run_id, inputs)

    return {"run_id": run_id, "status": "running"}

@app.get("/agents/{agent_id}/runs/{run_id}/memory")
async def get_memory(agent_id: str, run_id: str):
    """Get memory state"""
    memory = executor.get_memory(run_id)
    if not memory:
        raise HTTPException(404, "Run not found or memory released")
    return memory.to_dict()

# ... other endpoints
```

### Dependencies
- graphflow-core
- FastAPI
- Uvicorn
- SQLAlchemy
- Pydantic
- (Optional) Celery/RQ for separate process execution

---

## Component 4: graph-builder (React UI)

### Purpose
Visual graph builder and runtime monitor.

### Key Features

1. **Graph Canvas** - ReactFlow-based visual editor
2. **Step Palette** - Drag-and-drop step types
3. **Step Configuration** - Edit step properties and memory bindings
4. **Memory Schema Editor** - Define inputs/outputs/intermediate
5. **Export/Import** - Save/load graph definitions
6. **Runtime Monitor** - View running agents, inspect memory
7. **Compilation Integration** - Trigger compilation and download

### Component Structure

```
graph-builder/
├── src/
│   ├── components/
│   │   ├── GraphCanvas/
│   │   │   ├── GraphCanvas.tsx       # Main ReactFlow canvas
│   │   │   ├── StepNode.tsx          # Custom node component
│   │   │   └── EdgeComponent.tsx     # Custom edge component
│   │   ├── StepPalette/
│   │   │   ├── StepPalette.tsx       # Draggable step list
│   │   │   └── StepCard.tsx          # Individual step card
│   │   ├── StepConfig/
│   │   │   ├── StepConfigPanel.tsx   # Configuration sidebar
│   │   │   ├── ConfigForm.tsx        # Dynamic form for step config
│   │   │   └── MemoryBindings.tsx    # Memory read/write selector
│   │   ├── MemoryEditor/
│   │   │   ├── MemorySchemaEditor.tsx  # Edit memory schema
│   │   │   └── FieldEditor.tsx         # Edit individual field
│   │   ├── Runtime/
│   │   │   ├── AgentList.tsx         # List of agents
│   │   │   ├── RunMonitor.tsx        # Monitor specific run
│   │   │   └── MemoryInspector.tsx   # View memory state
│   │   └── Toolbar/
│   │       ├── Toolbar.tsx           # Top toolbar
│   │       └── ActionButtons.tsx     # Save/Load/Export/Compile
│   ├── api/
│   │   ├── runtimeClient.ts          # API client for runtime
│   │   └── types.ts                  # API types
│   ├── types/
│   │   └── graph.ts                  # Graph definition types
│   ├── store/
│   │   └── graphStore.ts             # Zustand store for graph state
│   ├── App.tsx
│   └── main.tsx
├── package.json
└── vite.config.ts
```

### TypeScript Types

```typescript
// types/graph.ts
export interface GraphDefinition {
  version: string;
  metadata: Metadata;
  memory: MemorySchema;
  steps: Step[];
  edges: Edge[];
}

export interface MemorySchema {
  inputs: Record<string, FieldDefinition>;
  outputs: Record<string, FieldDefinition>;
  intermediate: Record<string, FieldDefinition>;
  secrets: Record<string, SecretDefinition>;
}

export interface Step {
  id: string;
  type: string;
  config: Record<string, any>;
  memory_reads: string[];
  memory_writes: string[];
  // UI-specific properties (not exported to JSON)
  position?: { x: number; y: number };
}

export interface Edge {
  id: string;
  from: string;
  to: string;
  condition?: string;
}
```

### State Management (Zustand)

```typescript
// store/graphStore.ts
import create from 'zustand';

interface GraphStore {
  graph: GraphDefinition;
  selectedStep: string | null;

  // Actions
  addStep: (step: Step) => void;
  removeStep: (stepId: string) => void;
  updateStep: (stepId: string, updates: Partial<Step>) => void;
  addEdge: (edge: Edge) => void;
  removeEdge: (edgeId: string) => void;
  updateMemorySchema: (schema: MemorySchema) => void;
  setSelectedStep: (stepId: string | null) => void;
  exportGraph: () => string;
  importGraph: (json: string) => void;
}

export const useGraphStore = create<GraphStore>((set, get) => ({
  graph: createEmptyGraph(),
  selectedStep: null,

  addStep: (step) => set((state) => ({
    graph: {
      ...state.graph,
      steps: [...state.graph.steps, step]
    }
  })),

  // ... other actions
}));
```

### API Client

```typescript
// api/runtimeClient.ts
export class RuntimeClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  async uploadAgent(graph: GraphDefinition, framework: string): Promise<string> {
    const response = await fetch(`${this.baseUrl}/agents/upload`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ graph_definition: graph, framework })
    });
    const data = await response.json();
    return data.agent_id;
  }

  async startRun(agentId: string, inputs: any): Promise<string> {
    const response = await fetch(`${this.baseUrl}/agents/${agentId}/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ inputs })
    });
    const data = await response.json();
    return data.run_id;
  }

  async getMemory(agentId: string, runId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/agents/${agentId}/runs/${runId}/memory`);
    return response.json();
  }

  async stopRun(agentId: string, runId: string): Promise<void> {
    await fetch(`${this.baseUrl}/agents/${agentId}/runs/${runId}/stop`, {
      method: 'POST'
    });
  }

  // ... other methods
}
```

### Dependencies
- React 18+
- ReactFlow (graph visualization)
- TanStack Query (API state)
- Zustand (local state)
- Tailwind CSS + shadcn/ui (styling)
- Vite (build tool)

---

## Development Phases

### Phase 1: Core Foundation ✓ (Current Phase)
**Estimated Time:** Week 1-2

**Deliverables:**
1. Project structure created
2. graph-core implemented:
   - Pydantic models for GraphDefinition
   - MemoryStore implementation
   - StepBase and StepRegistry
   - 3-5 basic step types: start, llm, output, conditional, transform
3. JSON schema validation
4. Example graph definitions
5. Basic tests

**Exit Criteria:**
- Can load and validate graph JSON
- Can instantiate steps from registry
- MemoryStore read/write works
- Example graph validates successfully

### Phase 2: Compiler
**Estimated Time:** Week 2-3

**Deliverables:**
1. Pydantic AI code generator
2. LangGraph code generator
3. CLI tool for compilation
4. Generated code includes main() and optional FastAPI wrapper
5. Jinja2 template system
6. Tests for generated code

**Exit Criteria:**
- Can compile example graph to both frameworks
- Generated code runs standalone with CLI
- Generated code can be imported by runtime
- Generated code produces correct outputs

### Phase 3: Runtime Manager
**Estimated Time:** Week 3-4

**Deliverables:**
1. FastAPI app with all endpoints
2. SQLAlchemy models and database setup
3. Agent upload and storage
4. Async execution engine
5. Memory inspection API
6. Basic error handling
7. API tests

**Exit Criteria:**
- Can upload compiled agent or graph definition
- Can start/stop runs
- Can query memory during execution
- Can handle multiple concurrent runs
- Database persistence works

### Phase 4: UI Builder
**Estimated Time:** Week 4-6

**Deliverables:**
1. React app scaffolding with Vite
2. ReactFlow canvas with step nodes
3. Step palette with drag-drop
4. Step configuration panel
5. Memory schema editor
6. Export/import graph JSON
7. Runtime monitor integration
8. Basic styling with Tailwind + shadcn/ui

**Exit Criteria:**
- Can visually build a graph
- Can configure steps and memory bindings
- Can export valid JSON
- Can connect to runtime API
- Can upload to runtime and monitor execution
- Can inspect memory in real-time

### Phase 5: Enhancement
**Estimated Time:** Week 6+

**Deliverables:**
1. Remaining step types (loop, http, db_query, join, etc.)
2. MCP server integration in LLM step
3. Tool registration system
4. Conditional edge evaluation
5. Join/synchronization step implementation
6. Error handling and validation improvements
7. Documentation and examples
8. Performance optimization

**Exit Criteria:**
- All planned step types implemented
- MCP integration working
- Complex graphs with branches and joins work
- Comprehensive documentation
- Multiple example agents

---

## Technical Decisions Summary

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| **Monorepo** | Yes, simple directory structure | Easier development, shared dependencies |
| **Package Manager** | Poetry | Modern Python packaging |
| **Frontend Framework** | React + Vite | Modern, fast, good ecosystem |
| **Graph Library** | ReactFlow | Purpose-built for node editors |
| **Backend Framework** | FastAPI | Modern async Python, auto docs |
| **ORM** | SQLAlchemy | Flexible, database-agnostic |
| **Database (dev)** | SQLite | Simple, no setup required |
| **Memory Storage** | In-memory only | Simplicity, explicit release |
| **Execution Model** | Async tasks in same process | Simple, upgrade to workers if needed |
| **Code Generation** | Jinja2 templates | Flexible, readable templates |
| **Step Registration** | Decorator-based | Clean, Pythonic |
| **Secrets** | Environment variables initially | Simple, secure enough for start |
| **UI Styling** | Tailwind + shadcn/ui | Modern, minimal, customizable |
| **State Management** | Zustand | Lightweight, simple API |

---

## Interface Contracts

### Between UI and Compiler
**Format:** Graph Definition JSON
- UI exports graph as JSON file
- JSON follows schema defined in graph-core
- Can be saved/loaded from filesystem

### Between Compiler and Runtime
**Format:** Python module with standard interface
```python
class GeneratedAgent:
    def __init__(self): ...
    async def run(self, inputs: dict) -> dict: ...
    def get_memory(self) -> MemoryStore: ...
```
- Runtime can import and instantiate the class
- Provides standard methods for execution and inspection

### Between UI and Runtime
**Format:** REST API (JSON)
- UI acts as API client
- All operations via HTTP endpoints
- WebSocket optional for real-time updates (future)

---

## Open Questions & Future Considerations

### Debugging & Development
- **Q:** How to debug/step through graph execution?
- **Ideas:** Breakpoint steps, step-by-step UI execution, logging hooks

### Versioning
- **Q:** How to version graphs and handle schema changes?
- **Ideas:** Version field in graph definition, migration system

### Streaming
- **Q:** Should LLM steps support streaming outputs?
- **Ideas:** SSE or WebSocket for real-time updates to memory

### Sandboxing
- **Q:** Should generated code run in isolated environments?
- **Ideas:** Docker containers, separate processes with resource limits

### Collaboration
- **Q:** Multi-user editing? Sharing graphs?
- **Ideas:** Graph marketplace, import from URL, version control integration

### Testing
- **Q:** Framework for testing individual steps and complete graphs?
- **Ideas:** Test step type, assertions on memory, mock steps

### Performance
- **Q:** How to optimize for large graphs or long-running agents?
- **Ideas:** Parallel execution where possible, step result caching

### Advanced Flow Control
- **Q:** Loops, parallel branches, dynamic subgraphs?
- **Ideas:** Loop step with collection iteration, parallel gateway, subgraph step

---

## Current Status

**Phase:** 1 - Core Foundation (Starting)
**Next Steps:**
1. Create monorepo structure
2. Implement graph-core package
3. Define and validate example graphs

**Dependencies Installed:** None yet
**Database Initialized:** No
**Git Repository:** Yes (clean working tree)

---

## References

### Similar Tools
- n8n: Workflow automation, node-based
- Langflow: LangChain visual builder
- Flowise: Another LangChain UI
- Zapier: Automation platform
- Prefect: Workflow orchestration

### Key Differentiators
1. **Decoupled control and data flow** - Memory store independent of edges
2. **Multi-framework compilation** - Same graph → different frameworks
3. **Better runtime environment** - Long-running agents with full lifecycle management
4. **Queryable memory** - Inspect state at any point during execution

### Documentation Links
- ReactFlow: https://reactflow.dev/
- FastAPI: https://fastapi.tiangolo.com/
- Pydantic AI: https://ai.pydantic.dev/
- LangGraph: https://langchain-ai.github.io/langgraph/
- SQLAlchemy: https://www.sqlalchemy.org/
