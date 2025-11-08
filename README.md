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
- **Dynamic Memory Management**: Dedicated Memory Schema panel with auto-binding, usage tracking, and editable outputs
- **Plugin System**: Extensible architecture with dynamically loaded step types, categorization, and search
- **Decoupled Control & Data Flow**: Edges define control flow, memory store handles data independently
- **Multi-Framework Support**: Compile the same graph to Pydantic AI or LangGraph
- **Comprehensive Step Library**:
  - 10+ built-in steps (control flow, AI, data transformation)
  - 17 HTTP plugin steps (requests, URL utils, data transforms, HTML processing)
  - Memory manipulation steps (read-memory, write-memory)
- **Runtime Environment**: Long-running agents with queryable memory and full lifecycle management
- **CLI Tools**: `graphflow-compile` and `graphflow-runtime`
- **REST API**: 15+ endpoints for complete agent lifecycle management

## 🏗️ Architecture

GraphFlow consists of four main components plus an extensible plugin system:

### Core Components

| Component | Description | Status |
|-----------|-------------|--------|
| **graph-core** | Shared library with step types, memory management, and graph models | ✅ Complete |
| **graph-compiler** | Transpiler from graph JSON to Python (Pydantic AI / LangGraph) | ✅ Complete |
| **graph-runtime** | FastAPI service for executing and managing agents | ✅ Complete |
| **graph-builder** | React UI for visual graph construction and runtime monitoring | 🚧 POC |

### Plugin Packages

| Plugin | Description | Steps | Status |
|--------|-------------|-------|--------|
| **[graph-plugins-http](packages/graph-plugins-http/README.md)** | Comprehensive HTTP client with request handling, URL utilities, data transforms, and HTML processing | 17 steps | ✅ Complete |
| **[graphflow-plugin-example](packages/graphflow-plugin-example/README.md)** | Example plugin demonstrating notification steps (Email, Slack) | 2 steps | ✅ Reference |

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone <repo-url>
cd graphflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all packages in editable mode (recommended for development)
make install

# Start development environment
make dev-start
```

**For detailed development instructions, see [DEVELOPMENT.md](DEVELOPMENT.md)**

### Alternative: Manual Installation

```bash
# Install packages manually
pip install -e packages/graph-core
pip install -e packages/graph-compiler
pip install -e packages/graph-runtime
pip install -e packages/graph-plugins-ai
pip install -e packages/graph-plugins-http
pip install -e packages/graphflow-plugin-example
```

### Visual UI (Recommended)

```bash
# Using Makefile (easiest)
make dev-start

# Or manually:
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

# Terminal 2: Run integration tests
cd tests
pytest test_runtime_execution.py -v
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

## 🛠️ Step Types

GraphFlow provides a rich ecosystem of step types organized by category:

### Built-in Steps (graph-core)

| Category | Step | Description |
|----------|------|-------------|
| **Control** | `start` | Entry point for workflow execution |
| | `conditional` | Branching logic for if/else flows |
| | `loop` | Iterate over collections |
| | `join` | Synchronization point to merge parallel branches |
| **AI** | `llm` | LLM call with tools and structured output |
| **Data** | `transform` | Execute Python code for data transformation |
| | `read-memory` | Copy values from any memory section |
| | `write-memory` | Write values to any memory section |
| | `output` | Map intermediate values to final outputs |
| **Integration** | `http` | Basic HTTP request step |
| | `db_query` | Database query execution |
| **Human** | `human_input` | Wait for human review/input |

### HTTP Plugin Steps (graph-plugins-http)

See **[HTTP Plugin Documentation](packages/graph-plugins-http/README.md)** for complete details.

| Category | Steps | Description |
|----------|-------|-------------|
| **HTTP Requests** | `http-get`, `http-post`, `http-put`, `http-patch`, `http-delete` | Full HTTP method support with auth, retries, SSL config |
| **URL Utilities** | `url-parse`, `url-build`, `url-escape`, `url-unescape` | URL manipulation and construction |
| **Data Transform** | `json-parse`, `json-stringify`, `base64-encode`, `base64-decode` | Data format conversions |
| **HTML Processing** | `html-strip`, `html-parse`, `html-find-links`, `html-table-extract` | Extract data from HTML content |

### Creating Custom Steps

See **[Plugin Example](packages/graphflow-plugin-example/README.md)** to learn how to create your own plugin packages with custom step types.

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
- **Outputs Section**: View and edit all step outputs with:
  - Output name and type badges
  - Editable memory locations (clean names without `_key` suffixes)
  - Descriptions from output schemas
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

## 🔌 Plugin System

GraphFlow features an extensible plugin architecture that allows you to create custom step types:

**How Plugins Work:**
- Plugins are Python packages with a `graphflow.plugins` entry point
- The runtime automatically discovers and loads all installed plugins
- Each plugin provides a `manifest.json` listing its step types
- Steps appear in the UI palette with plugin namespacing (e.g., `http.HTTPGetStep`)

**Creating a Plugin:**
1. Create a Python package with `pyproject.toml` defining the entry point
2. Add a `manifest.json` describing your plugin and step types
3. Implement step classes inheriting from `StepBase`
4. Define configuration schemas, labels, categories, and execute logic
5. Install with `pip install -e .` and restart the runtime

**Example Plugins:**
- **[graph-plugins-http](packages/graph-plugins-http/README.md)**: Production-ready HTTP client with 17 steps
- **[graphflow-plugin-example](packages/graphflow-plugin-example/README.md)**: Reference implementation with notification steps

See the [Example Plugin Documentation](packages/graphflow-plugin-example/README.md) for a complete guide on creating custom plugins.

## 📖 Documentation

### Core Documentation
- **[GRAPH_FORMAT.md](GRAPH_FORMAT.md)** - **Complete JSON format specification** for graph definitions
- **[PROJECT_PLAN.md](PROJECT_PLAN.md)** - Complete technical specification
- **[IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md)** - What we built and how it works
- **API Docs** - Visit http://localhost:8000/docs when runtime is running

### Component Documentation
- **[graph-core](packages/graph-core/README.md)** - Core library with step types and memory management
- **[graph-compiler](packages/graph-compiler/README.md)** - Transpiler from graph JSON to Python code
- **[graph-runtime](packages/graph-runtime/README.md)** - FastAPI service for agent execution
- **[graph-builder](packages/graph-builder/README.md)** - React UI for visual graph construction (if available)

### Plugin Documentation
- **[HTTP Plugin](packages/graph-plugins-http/README.md)** - 17 steps for HTTP requests, URL utilities, data transforms, and HTML processing
- **[Example Plugin](packages/graphflow-plugin-example/README.md)** - Reference implementation for creating custom plugins

## 🧪 Testing

GraphFlow has a comprehensive test suite covering all major use cases:

```bash
# Run all tests
cd tests
./run_tests.sh all

# Run specific test categories
./run_tests.sh compilation    # Test graph compilation
./run_tests.sh standalone      # Test standalone execution
./run_tests.sh runtime         # Test runtime server

# Run with coverage
./run_tests.sh coverage

# Or use pytest directly
pytest tests/ -v
```

**Test Coverage:**
- ✅ Graph compilation (Pydantic AI & LangGraph)
- ✅ Standalone execution (CLI & server modes)
- ✅ Multi-graph runtime (CRUD, execution, memory)
- ✅ Core functionality (graph definition, memory, steps)
- ✅ Error handling and validation

See **[tests/README.md](tests/README.md)** for detailed testing documentation.

## 🎨 Graph Definition Format

Graphs are defined in JSON format. See **[GRAPH_FORMAT.md](GRAPH_FORMAT.md)** for the complete specification.

**Key Components:**
- **version**: Format version (currently `"1.0"`)
- **metadata**: Name, description, tags, framework hints
- **memory**: Schemas for inputs, outputs, intermediate data, and secrets
- **steps**: Array of step definitions (nodes in the graph)
- **edges**: Array of connections between steps (control flow)

**Quick Example:**
```json
{
  "version": "1.0",
  "metadata": {"name": "My Agent", "description": "What it does"},
  "memory": {
    "inputs": {"question": {"type": "string", "required": true}},
    "outputs": {"answer": {"type": "string"}},
    "intermediate": {"processed": {"type": "string"}},
    "secrets": {}
  },
  "steps": [
    {
      "id": "start",
      "type": "start",
      "config": {},
    },
    {
      "id": "llm",
      "type": "llm",
      "config": {
        "model": "gpt-4",
        "prompt": "{memory.question}",
        "output_key": "processed"
      },
    },
    {
      "id": "output",
      "type": "output",
      "config": {"mapping": {"answer": "processed"}},
    }
  ],
  "edges": [
    {"id": "e1", "from": "start", "to": "llm"},
    {"id": "e2", "from": "llm", "to": "output"}
  ]
}
```

📘 **See [GRAPH_FORMAT.md](GRAPH_FORMAT.md) for:**
- Complete field specifications
- Memory schema details
- Step configuration examples
- The `_key` suffix convention
- Template syntax (`{memory.variable}`)
- Validation rules
- Best practices

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
- ✅ Visual memory binding with "Bound to" buttons
- ✅ Editable outputs section with clean memory locations
- ✅ HTTP plugin with 17 production-ready steps
- ✅ Memory manipulation steps (read-memory, write-memory)
- ✅ Position persistence (node layouts saved/restored)
- ✅ Runtime monitoring view with agents/runs/details
- ✅ Execution log with horizontal scrollbars
- ✅ Upload to runtime and execute graphs
- 🚧 Graph templates
- 🚧 Auto-refresh for runtime view
- 🚧 Compile from UI

**Future**:
- Plugin marketplace/registry
- MCP server integration
- Graph versioning
- Distributed execution
- Streaming support
- Collaborative editing
- More plugin packages (Database, Cloud Services, Notifications, etc.)

## 📝 License

MIT

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines (coming soon).

## 📬 Contact

- Issues: [GitHub Issues](https://github.com/your-repo/graphflow/issues)
- Discussions: [GitHub Discussions](https://github.com/your-repo/graphflow/discussions)

---

## 🔗 Quick Links

- **[Graph Format Specification](GRAPH_FORMAT.md)** - Complete JSON format documentation
- **[HTTP Plugin Documentation](packages/graph-plugins-http/README.md)** - 17 steps for web APIs and data processing
- **[Plugin Development Guide](packages/graphflow-plugin-example/README.md)** - Create your own custom steps
- **[Core Documentation](packages/graph-core/README.md)** - Step types and memory management
- **[Runtime API](http://localhost:8000/docs)** - FastAPI documentation (when server is running)

---

**Built with**: Python, FastAPI, Pydantic, SQLAlchemy, React, ReactFlow, TypeScript, and ❤️
