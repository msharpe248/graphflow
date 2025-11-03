# GraphFlow

🚀 **Status**: 🚧 **In Development - Proof of Concept**

A low-code agent builder for creating, compiling, and running AI agents with graph-based workflows.

## 🎯 What is GraphFlow?

GraphFlow is a comprehensive agent development platform that lets you:
- **Build** agents visually with drag-and-drop interface
- **Compile** graphs to executable Python (Pydantic AI or LangGraph)
- **Execute** agents in a managed runtime environment
- **Monitor** execution with real-time memory inspection

## ✨ Key Features

- **Visual Graph Builder**: Drag-and-drop UI with ReactFlow for building agent workflows
- **Dynamic Memory Management**: Dedicated Memory Schema panel with auto-binding and usage tracking
- **Plugin System**: Dynamically load step types from runtime with categorization and search
- **Decoupled Control & Data Flow**: Edges define control flow, memory store handles data independently
- **Multi-Framework Support**: Compile the same graph to Pydantic AI or LangGraph
- **10 Built-in Step Types**: start, llm, http, loop, conditional, transform, join, db_query, human_input, output
- **Runtime Environment**: Long-running agents with queryable memory and full lifecycle management
- **CLI Tools**: `graphflow-compile` and `graphflow-runtime`
- **REST API**: 15+ endpoints for complete agent lifecycle management

## 🏗️ Architecture

GraphFlow consists of four main components:

| Component | Description | Status |
|-----------|-------------|--------|
| **graph-core** | Shared library with step types, memory management, and graph models | ✅ Complete |
| **graph-compiler** | Transpiler from graph JSON to Python (Pydantic AI / LangGraph) | ✅ Complete |
| **graph-runtime** | FastAPI service for executing and managing agents | ✅ Complete |
| **graph-builder** | React UI for visual graph construction and runtime monitoring | 🚧 POC |

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd graphflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all packages
pip install -e packages/graph-core
pip install -e packages/graph-compiler
pip install -e packages/graph-runtime
```

### Visual UI (Recommended)

```bash
# Terminal 1: Start runtime server
graphflow-runtime

# Terminal 2: Start UI
cd packages/graph-builder
npm install
npm run dev

# Visit http://localhost:3000
# - Builder tab: Visual graph editor with drag-and-drop steps
#   - Step Palette: Browse steps by category or plugin
#   - Properties Panel: Configure step settings and memory bindings
#   - Memory Schema Panel: Manage inputs, outputs, and intermediate memory
# - Runtime tab: Monitor running agents (coming soon)
```

### Example 1: Compile and Run Standalone Agent

```bash
# Validate a graph
graphflow-compile validate examples/simple_agent.json

# Compile to Python (Pydantic AI)
graphflow-compile compile examples/simple_agent.json \
  --framework pydantic_ai \
  --output my_agent.py

# Run the generated agent
echo '{"user_question": "Hello!"}' > inputs.json
python my_agent.py inputs.json

# Or run as a server
python my_agent.py --server
```

### Example 2: Use Runtime Manager

```bash
# Terminal 1: Start runtime server
graphflow-runtime

# Terminal 2: Upload and run agent
python test_end_to_end.py
```

### Example 3: API Usage

```python
import httpx
import json

# Load graph definition
with open("examples/simple_agent.json") as f:
    graph = json.load(f)

# Create agent in runtime
async with httpx.AsyncClient() as client:
    # Upload agent
    response = await client.post("http://localhost:8000/api/v1/agents", json={
        "name": "My Agent",
        "framework": "pydantic_ai",
        "graph_definition": graph
    })
    agent = response.json()

    # Start run
    response = await client.post(
        f"http://localhost:8000/api/v1/agents/{agent['id']}/runs",
        json={"inputs": {"user_question": "What is AI?"}}
    )
    run = response.json()

    # Check status
    response = await client.get(
        f"http://localhost:8000/api/v1/agents/{agent['id']}/runs/{run['id']}"
    )
    print(response.json())
```

## 📚 Examples

See the `examples/` directory for complete graph definitions:

1. **simple_agent.json** - Basic linear workflow
2. **conditional_agent.json** - Branching with join
3. **llm_agent.json** - LLM with tools and structured output
4. **advanced_research_agent.json** - Complex multi-step with loops, HTTP, LLM, and human review

## 🛠️ Built-in Step Types

| Step | Description | Use Case |
|------|-------------|----------|
| `start` | Entry point | Begin execution |
| `llm` | LLM call with tools | AI reasoning, analysis |
| `http` | HTTP request | API calls, web scraping |
| `loop` | Iterate over collection | Process lists, batch operations |
| `conditional` | Branching logic | If/else flows |
| `transform` | Python code execution | Data transformation |
| `join` | Synchronization point | Merge parallel branches |
| `db_query` | Database query | Data retrieval |
| `human_input` | Wait for human | Human-in-the-loop |
| `output` | Map to outputs | Final results |

## 🎨 Graph Builder UI Features

The visual graph builder provides an intuitive interface for creating agent workflows:

**Step Palette**
- Browse steps by category (AI, Integration, Control Flow, etc.) or by plugin
- Search functionality to quickly find step types
- Collapsible sections for organized navigation
- Color-coded step types with icons

**Canvas**
- Drag-and-drop steps from palette onto canvas
- Connect steps with edges to define control flow
- Visual node representation with step info
- Pan and zoom for large graphs

**Properties Panel**
- Configure step settings when a node is selected
- Smart labels: converts `model_name` to "Model Name"
- Memory binding support with `{memory.field}` syntax
- Visual badges showing active memory bindings
- Step behavior info showing inputs/outputs schemas
- Delete step button

**Memory Schema Panel**
- Manage three memory namespaces: inputs, intermediate, outputs
- Add/remove memory fields with type definitions
- Set default values for memory locations
- Required field indicators for inputs
- "Used by" badges showing which steps reference each field
- Auto-cleanup of unused memory fields

**Memory Binding System**
- Auto-create memory fields when steps are added
- Auto-bind config values to `{memory.<step_id>.<field>}` format
- Change bindings to hardcoded values or different memory locations
- Visual highlighting of bound fields with blue background
- Autocomplete suggestions for memory field names

## 📖 Documentation

- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Complete technical specification
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - What we built and how it works
- **Per-package READMEs** - Detailed docs for each component
- **API Docs** - Visit http://localhost:8000/docs when runtime is running

## 🧪 Testing

```bash
# Run end-to-end test
python test_end_to_end.py

# Expected output:
# ✓ Graph loaded
# ✓ Agent created
# ✓ Run completed
# ✓ Outputs retrieved
# ✓ Memory inspected
```

## 🎨 Graph Definition Format

Graphs are defined in JSON with:
- **metadata**: Name, description, tags
- **memory**: Input/output/intermediate schemas
- **steps**: Array of step definitions
- **edges**: Array of connections

```json
{
  "version": "1.0",
  "metadata": {"name": "My Agent"},
  "memory": {
    "inputs": {"question": {"type": "string"}},
    "outputs": {"answer": {"type": "string"}},
    "intermediate": {}
  },
  "steps": [
    {"id": "start", "type": "start"},
    {"id": "llm", "type": "llm", "config": {...}},
    {"id": "output", "type": "output", "config": {...}}
  ],
  "edges": [
    {"id": "e1", "from": "start", "to": "llm"},
    {"id": "e2", "from": "llm", "to": "output"}
  ]
}
```

## 🔧 CLI Tools

### graphflow-compile

```bash
# Compile graph
graphflow-compile compile graph.json --framework pydantic_ai --output agent.py

# Validate graph
graphflow-compile validate graph.json

# Show graph info
graphflow-compile info graph.json

# List frameworks
graphflow-compile list-frameworks
```

### graphflow-runtime

```bash
# Start server
graphflow-runtime

# Custom port
graphflow-runtime --port 9000

# Development mode
graphflow-runtime --reload
```

## 📊 API Endpoints

**Agents**:
- `POST /api/v1/agents` - Create agent
- `GET /api/v1/agents` - List agents
- `GET /api/v1/agents/{id}` - Get agent
- `DELETE /api/v1/agents/{id}` - Delete agent

**Runs**:
- `POST /api/v1/agents/{id}/runs` - Start run
- `GET /api/v1/agents/{id}/runs` - List runs
- `GET /api/v1/agents/{id}/runs/{run_id}` - Get run status
- `POST /api/v1/agents/{id}/runs/{run_id}/stop` - Stop run
- `DELETE /api/v1/agents/{id}/runs/{run_id}` - Delete run

**Memory**:
- `GET /api/v1/agents/{id}/runs/{run_id}/memory` - Get memory state
- `GET /api/v1/agents/{id}/runs/{run_id}/memory/{key}` - Get specific value

**Step Types**:
- `GET /api/v1/step-types` - List all available step types with schemas

**Health**:
- `GET /api/v1/health` - Health check

## 🎯 Key Differentiators

| Feature | GraphFlow | n8n | Langflow |
|---------|-----------|-----|----------|
| Control/Data Separation | ✅ | ❌ | ❌ |
| Multi-Framework Compile | ✅ | ❌ | ⚠️ |
| Standalone Generation | ✅ | ❌ | ❌ |
| Visual Graph Builder | 🚧 POC | ✅ | ✅ |
| Memory Schema Management | ✅ | ⚠️ | ⚠️ |
| Memory Inspection | ✅ | ⚠️ | ⚠️ |
| Runtime API | ✅ | ✅ | ✅ |

## 🚧 Roadmap

**Phase 4: UI Builder** (In Progress - POC)
- ✅ React app with ReactFlow
- ✅ Drag-and-drop graph builder
- ✅ Plugin system with step palette
- ✅ Memory schema management
- ✅ Visual memory binding
- 🚧 Real-time runtime monitoring
- 🚧 Graph templates
- 🚧 Save/load graphs
- 🚧 Compile from UI

**Future**:
- MCP server integration
- Tool marketplace
- Graph versioning
- Distributed execution
- Streaming support
- Collaborative editing

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines (coming soon).

## 📬 Contact

- Issues: [GitHub Issues](https://github.com/your-repo/graphflow/issues)
- Discussions: [GitHub Discussions](https://github.com/your-repo/graphflow/discussions)

---

**Built with**: Python, FastAPI, Pydantic, SQLAlchemy, Jinja2, and ❤️
