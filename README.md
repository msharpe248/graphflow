# GraphFlow

🚀 **Status**: ✅ **Active Development**

A low-code agent builder for creating, compiling, and running AI agents with graph-based workflows.

## 🎯 What is GraphFlow?

GraphFlow is a comprehensive agent development platform that lets you:
- **Build** agents visually with drag-and-drop interface
- **Compile** graphs to executable Python (Pydantic AI or LangGraph)
- **Execute** agents in a managed runtime environment
- **Debug** with breakpoints, step-through execution, and memory editing
- **Monitor** execution with real-time memory inspection

## ✨ Key Features

- **Visual Graph Builder**: Drag-and-drop UI with ReactFlow for building agent workflows
- **Chat UI**: Standalone conversational interface for interacting with chat-enabled graphs
- **Dynamic Memory Management**: Dedicated Memory Schema panel with auto-binding, usage tracking, and editable outputs
- **Interactive Debugger**: Set breakpoints before/after steps, step through execution, pause/resume, inspect and edit memory values in real-time
- **LLM Tool Support**: Visual tool builder with MappedStepTools - wrap any step type as an LLM-callable tool
- **Multi-Provider LLM**: Support for Ollama, LM Studio, OpenRouter, Anthropic, and OpenAI out of the box
- **Chat History / Sessions**: LLM steps can maintain conversation context across multiple calls for multi-turn conversations
- **Plugin System**: Extensible architecture with dynamically loaded step types, categorization, and search
- **Decoupled Control & Data Flow**: Edges define control flow, memory store handles data independently
- **Multi-Framework Support**: Compile the same graph to Pydantic AI or LangGraph
- **Comprehensive Step Library**:
  - 10+ built-in steps (control flow, AI, data transformation)
  - 80+ plugin steps across 10 plugins (HTTP, URL, XML/HTML, Encoding, Text, JSON, YAML, CSV, AI, Example)
  - Memory manipulation steps (read-memory, write-memory)
- **Runtime Environment**: Long-running agents with queryable memory and full lifecycle management
- **CLI Tools**: `graphflow-compile` and `graphflow-runtime`
- **REST API**: 20+ endpoints for complete agent lifecycle and debug management

## 🏗️ Architecture

GraphFlow consists of four main components plus an extensible plugin system:

### Core Components

| Component | Description | Status |
|-----------|-------------|--------|
| **graph-core** | Shared library with step types, memory management, and graph models | ✅ Complete |
| **graph-compiler** | Transpiler from graph JSON to Python (Pydantic AI / LangGraph) | ✅ Complete |
| **graph-runtime** | FastAPI service for executing and managing agents | ✅ Complete |
| **graph-builder** | React UI for visual graph construction and runtime monitoring | ✅ Complete |
| **graph-chat** | React UI for conversational interaction with chat-enabled graphs | ✅ Complete |

### Plugin Packages

| Plugin | Description | Steps | Status |
|--------|-------------|-------|--------|
| **[graph-plugins-http](packages/graph-plugins-http/README.md)** | HTTP client (GET, POST, PUT, PATCH, DELETE) | 5 steps | ✅ Complete |
| **[graph-plugins-url](packages/graph-plugins-url/README.md)** | URL manipulation and parsing | 4 steps | ✅ Complete |
| **[graph-plugins-xmlhtml](packages/graph-plugins-xmlhtml/README.md)** | XML parsing and HTML manipulation | 14 steps | ✅ Complete |
| **[graph-plugins-encoding](packages/graph-plugins-encoding/README.md)** | Base64, Hex, Hashing, and Gzip compression | 12 steps | ✅ Complete |
| **[graph-plugins-text](packages/graph-plugins-text/README.md)** | Text and string manipulation (join, split, replace, regex, case conversion) | 13 steps | ✅ Complete |
| **[graph-plugins-json](packages/graph-plugins-json/README.md)** | JSON parsing, manipulation, JSONPath queries, and schema validation | 9 steps | ✅ Complete |
| **[graph-plugins-yaml](packages/graph-plugins-yaml/README.md)** | YAML parsing, multi-document support, and JSON conversion | 10 steps | ✅ Complete |
| **[graph-plugins-csv](packages/graph-plugins-csv/README.md)** | CSV parsing, filtering, sorting, column operations, and merging | 14 steps | ✅ Complete |
| **[graphflow-plugin-example](packages/graphflow-plugin-example/README.md)** | Example plugin demonstrating notification steps (Email, Slack) | 3 steps | ✅ Reference |

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

### Makefile Commands

GraphFlow includes a comprehensive Makefile for development. Here are the most common commands:

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make install` | Install all packages in editable mode |
| `make dev-start` | Start full dev environment (runtime + builder + chat) |
| `make dev-stop` | Stop all services |
| `make status` | Show status of all services and certificates |
| `make test` | Run all tests |
| `make reset` | Full reset: stop, clean, reinstall, restart |

**Service Control:**
- `make runtime-start` / `make runtime-stop` - Runtime server (port 8000)
- `make builder-start` / `make builder-stop` - Builder UI (port 3000)
- `make chat-start` / `make chat-stop` - Chat UI (port 3001)
- `make runtime-logs` / `make builder-logs` / `make chat-logs` - View logs

**SSL Certificates:**
- `make certs` - Generate self-signed SSL certificates
- `make certs-check` - Check certificate status and validity
- `make certs-clean` - Remove certificates

**See [docs/MAKEFILE.md](docs/MAKEFILE.md) for complete documentation.**

### Alternative: Manual Installation

```bash
# Install packages manually
pip install -e packages/graph-core
pip install -e packages/graph-compiler
pip install -e packages/graph-runtime
pip install -e packages/graph-plugins-ai
pip install -e packages/graph-plugins-http
pip install -e packages/graph-plugins-url
pip install -e packages/graph-plugins-xmlhtml
pip install -e packages/graph-plugins-encoding
pip install -e packages/graphflow-plugin-example
```

### Visual UI (Recommended)

```bash
# Using Makefile (easiest) - starts runtime, builder, and chat UI
make dev-start

# Or manually:
# Terminal 1: Start runtime server (port 8000)
graphflow-runtime

# Terminal 2: Start Builder UI (port 3000)
cd packages/graph-builder && npm install && npm run dev

# Terminal 3: Start Chat UI (port 3001)
cd packages/graph-chat && npm install && npm run dev

# Visit https://localhost:3000 for Builder (accept self-signed cert)
# - Builder tab: Visual graph editor with drag-and-drop steps
#   - Step Palette: Browse steps by category or plugin
#   - Properties Panel: Configure step settings and memory bindings
#   - Memory Schema Panel: Manage inputs, outputs, and intermediate memory
# - Runtime tab: Monitor and debug running agents
#   - View all agents and their runs
#   - Enable debug mode with breakpoints and step-through execution
#   - Inspect and edit memory values in real-time
#   - View execution logs and step properties

# Visit https://localhost:3001 for Chat UI (accept self-signed cert)
# - Conversational interface for chat-enabled graphs
# - Multi-graph and multi-session support
# - Per-conversation debug mode toggle
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

# Create agent in runtime (use verify=False for self-signed certs)
async with httpx.AsyncClient(verify=False) as client:
    # Upload agent
    response = await client.post("https://localhost:8000/api/v1/agents", json={
        "name": "My Agent",
        "framework": "pydantic_ai",
        "graph_definition": graph
    })
    agent = response.json()

    # Start run
    response = await client.post(
        f"https://localhost:8000/api/v1/agents/{agent['id']}/runs",
        json={"inputs": {"user_question": "What is AI?"}}
    )
    run = response.json()

    # Check status
    response = await client.get(
        f"https://localhost:8000/api/v1/agents/{agent['id']}/runs/{run['id']}"
    )
    print(response.json())
```

## 📚 Examples

See the `examples/` directory for complete graph definitions:

1. **simple_agent.json** - Basic linear workflow
2. **conditional_agent.json** - Branching with join
3. **llm_agent.json** - LLM with tools and structured output
4. **ollama_tool_agent.json** - LLM with MappedStepTool for URL fetching (Ollama)
5. **advanced_research_agent.json** - Complex multi-step with loops, HTTP, LLM, and human review

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

### AI Plugin Steps (graph-plugins-ai)

| Step | Description |
|------|-------------|
| `ai.LLMStep` | LLM call with multi-provider support, tools, and structured output |
| `ai.HumanInputStep` | Wait for human review/input |

**Supported LLM Providers:**
| Provider | Models | API Key Environment Variable |
|----------|--------|------------------------------|
| **Ollama** | llama3.1, llama3.2, mistral, etc. | (none - local) |
| **LM Studio** | Any loaded model | (none - local) |
| **OpenRouter** | Claude, GPT-4, Llama, etc. | `OPENROUTER_API_KEY` |
| **Anthropic** | Claude 3.5 Sonnet, Claude 3 Opus | `ANTHROPIC_API_KEY` |
| **OpenAI** | GPT-4, GPT-3.5-turbo | `OPENAI_API_KEY` |

### HTTP Plugin Steps (graph-plugins-http)

See **[HTTP Plugin Documentation](packages/graph-plugins-http/README.md)** for complete details.

| Step | Description |
|------|-------------|
| `http.HTTPGetStep` | HTTP GET request with auth, headers, retries |
| `http.HTTPPostStep` | HTTP POST request with JSON/form body support |
| `http.HTTPPutStep` | HTTP PUT request |
| `http.HTTPPatchStep` | HTTP PATCH request |
| `http.HTTPDeleteStep` | HTTP DELETE request |

### URL Plugin Steps (graph-plugins-url)

See **[URL Plugin Documentation](packages/graph-plugins-url/README.md)** for complete details.

| Step | Description |
|------|-------------|
| `url.URLParseStep` | Parse URL into components (scheme, host, path, query) |
| `url.URLBuildStep` | Build URL from components |
| `url.URLEscapeStep` | URL encode a string (percent encoding) |
| `url.URLUnescapeStep` | Decode percent-encoded string |

### XML/HTML Plugin Steps (graph-plugins-xmlhtml)

See **[XML/HTML Plugin Documentation](packages/graph-plugins-xmlhtml/README.md)** for complete details.

| Category | Steps | Description |
|----------|-------|-------------|
| **HTML Core** | `HTMLStripStep`, `HTMLParseStep`, `HTMLFindLinksStep`, `HTMLTableExtractStep` | Extract data from HTML |
| **HTML Extraction** | `HTMLSelectAllStep`, `HTMLAttributeExtractStep`, `HTMLFormExtractStep`, `HTMLMetaExtractStep` | Advanced HTML extraction |
| **HTML Transform** | `HTMLToMarkdownStep`, `HTMLCleanStep`, `XPathStep` | Convert and sanitize HTML |
| **XML** | `XMLParseStep`, `XMLToJSONStep`, `JSONToXMLStep` | XML parsing and conversion |

### Encoding Plugin Steps (graph-plugins-encoding)

See **[Encoding Plugin Documentation](packages/graph-plugins-encoding/README.md)** for complete details.

| Category | Steps | Description |
|----------|-------|-------------|
| **Base64** | `Base64EncodeStep`, `Base64DecodeStep`, `Base64URLEncodeStep`, `Base64URLDecodeStep` | Base64 encoding/decoding |
| **Hex** | `HexEncodeStep`, `HexDecodeStep` | Hexadecimal encoding |
| **Hashing** | `MD5HashStep`, `SHA1HashStep`, `SHA256HashStep`, `SHA512HashStep` | Cryptographic hashing |
| **Compression** | `GzipCompressStep`, `GzipDecompressStep` | Gzip compression |

### Text Plugin Steps (graph-plugins-text)

See **[Text Plugin Documentation](packages/graph-plugins-text/README.md)** for complete details.

| Category | Steps | Description |
|----------|-------|-------------|
| **String Operations** | `text.join`, `text.split`, `text.replace`, `text.reverse`, `text.repeat` | Basic string manipulation |
| **Formatting** | `text.format`, `text.case`, `text.trim`, `text.pad`, `text.substring`, `text.truncate` | Text formatting and extraction |
| **Regex** | `text.regex-match`, `text.regex-replace` | Pattern matching and replacement |

### JSON Plugin Steps (graph-plugins-json)

See **[JSON Plugin Documentation](packages/graph-plugins-json/README.md)** for complete details.

| Category | Steps | Description |
|----------|-------|-------------|
| **Core** | `json.parse`, `json.stringify` | Parse and serialize JSON |
| **Manipulation** | `json.get`, `json.set`, `json.merge`, `json.keys`, `json.values` | Access and modify JSON data |
| **Advanced** | `json.path`, `json.schema-validate` | JSONPath queries and schema validation |

### YAML Plugin Steps (graph-plugins-yaml)

See **[YAML Plugin Documentation](packages/graph-plugins-yaml/README.md)** for complete details.

| Category | Steps | Description |
|----------|-------|-------------|
| **Core** | `yaml.parse`, `yaml.stringify` | Parse and serialize YAML |
| **Multi-Document** | `yaml.parse-all`, `yaml.stringify-all` | Handle multi-document YAML files |
| **Conversion** | `yaml.to-json`, `yaml.from-json` | Convert between YAML and JSON |
| **Advanced** | `yaml.validate`, `yaml.merge`, `yaml.get`, `yaml.set` | Validation and manipulation |

### CSV Plugin Steps (graph-plugins-csv)

See **[CSV Plugin Documentation](packages/graph-plugins-csv/README.md)** for complete details.

| Category | Steps | Description |
|----------|-------|-------------|
| **Core** | `csv.parse`, `csv.stringify`, `csv.get-headers` | Parse and serialize CSV |
| **Conversion** | `csv.to-json`, `csv.from-json` | Convert between CSV and JSON |
| **Filter & Sort** | `csv.filter`, `csv.sort` | Filter rows by conditions, sort by columns |
| **Column Ops** | `csv.select-columns`, `csv.get-column`, `csv.add-column`, `csv.rename-columns` | Column manipulation |
| **Row Ops** | `csv.get-row`, `csv.merge`, `csv.group-by` | Row operations and dataset merging |

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

## 💬 Chat UI

The Chat UI provides a conversational interface for interacting with chat-enabled graphs:

**Graph Eligibility**
- Graphs must have a `query` input and `query_response` output in their memory schema
- Eligible graphs show a chat icon in the Runtime agents list
- The "Chat" button in the Builder toolbar opens eligible graphs in Chat UI

**Core Features**
- **Multi-Graph Support**: Multiple graphs can be active simultaneously in the sidebar
- **Multi-Session**: Create multiple conversations per graph with independent history
- **Real-time Responses**: Poll-based message delivery with typing indicators
- **Debug Mode Toggle**: Per-conversation debug mode - when enabled, runs appear in Runtime UI for debugging
- **Session Persistence**: Conversations use session IDs for multi-turn context in LLM steps

**Accessing Chat UI**
- From Builder: Click "Chat" button in toolbar (green, shows when graph is eligible)
- From Runtime: Click chat icon next to eligible agents in the agents list
- Direct URL: `https://localhost:3001?agentId={agent_id}`

**Adding Graphs**
- Click "+" button to add graphs from runtime or upload files
- Upload new graph files directly (creates agent in runtime automatically)
- Select from existing eligible agents in runtime

## 🐛 Interactive Debugger

GraphFlow includes a full-featured debugger for troubleshooting and understanding agent execution:

**Debugging Controls**
- **Debug Mode**: Enable when starting a run to pause before execution begins
- **Breakpoints**: Click connection handles on nodes to set breakpoints before or after step execution
  - Gray handle: No breakpoint
  - Red handle: Breakpoint set
  - Yellow pulsing: Execution paused here
  - Blue pulsing: Currently executing
- **Execution Controls**: Step, Resume, Pause buttons to control execution flow
- **Debug State**: Real-time display of execution status and current step

**Memory Inspection & Editing**
- **Live Memory View**: See all memory values update in real-time as execution progresses
- **Rich Property Editors**: View step inputs/outputs with syntax highlighting (JSON, Code, Markdown, etc.)
- **Memory Editing**: Modify memory values while paused to test different scenarios
  - Editable when paused (green "(editable while paused)" indicator)
  - Read-only when running
  - Smart namespace detection for memory bindings
- **Step Properties Panel**: Inspect configuration, current values, and outputs for each step

**Execution Log**
- **Live Tool Call Visibility**: See LLM tool calls and results in real-time while paused at breakpoints
- **Grouped by Step**: Execution log entries organized by step with inputs/outputs/tool calls
- **Error Preservation**: Execution logs are captured even when runs fail for debugging

**Framework Support**
- Works with both Pydantic AI and LangGraph compiled agents
- Transparent to plugin developers - no special code required
- Full debugging API for programmatic control

## 🔧 LLM Tools

GraphFlow supports giving LLMs access to tools that can be called during execution:

**MappedStepTools**
- Wrap any existing step type as an LLM-callable tool
- Visual tool builder in the UI for configuring parameter mappings
- Parameters can be:
  - **LLM-provided**: The LLM decides the value (e.g., URL to fetch)
  - **Runtime-bound**: Value comes from memory (e.g., API key from secrets)
- Tool errors are returned to the LLM instead of aborting, allowing adaptive behavior

**Example: HTTP Fetch Tool**
```json
{
  "tools": [{
    "type": "mapped_step",
    "definition": {
      "name": "fetch_url",
      "description": "Fetch content from a URL",
      "source_step_type": "http.HTTPGetStep",
      "property_mappings": [{
        "source_property": "url",
        "visibility": "llm",
        "llm_parameter_name": "url",
        "llm_description": "The URL to fetch",
        "required": true
      }],
      "output_key": "response"
    }
  }]
}
```

**Supported in Both Frameworks**
- **Pydantic AI**: Tools passed to Agent constructor with RunContext for memory access
- **LangGraph**: Tools created via closure factory for memory access

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
- **[graph-plugins-http](packages/graph-plugins-http/README.md)**: HTTP client with 5 request steps
- **[graph-plugins-url](packages/graph-plugins-url/README.md)**: URL parsing and manipulation (4 steps)
- **[graph-plugins-xmlhtml](packages/graph-plugins-xmlhtml/README.md)**: XML/HTML processing (14 steps)
- **[graph-plugins-encoding](packages/graph-plugins-encoding/README.md)**: Encoding, hashing, compression (12 steps)
- **[graphflow-plugin-example](packages/graphflow-plugin-example/README.md)**: Reference implementation with notification steps

See the [Example Plugin Documentation](packages/graphflow-plugin-example/README.md) for a complete guide on creating custom plugins.

## 📖 Documentation

### Core Documentation
- **[GRAPH_FORMAT.md](docs/GRAPH_FORMAT.md)** - **Complete JSON format specification** for graph definitions
- **[MEMORY_USER_GUIDE.md](docs/MEMORY_USER_GUIDE.md)** - **User guide for memory system** - bindings, namespaces, Builder UI
- **[MEMORY_SYSTEM.md](docs/MEMORY_SYSTEM.md)** - Technical reference for memory implementation
- **[MAKEFILE.md](docs/MAKEFILE.md)** - Complete Makefile command reference
- **[PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md)** - Guide to creating custom plugin steps
- **[PROJECT_PLAN.md](docs/PROJECT_PLAN.md)** - Complete technical specification
- **[TEMPLATE_ARCHITECTURE.md](docs/TEMPLATE_ARCHITECTURE.md)** - Step template system design
- **API Docs** - Visit https://localhost:8000/docs when runtime is running

### Component Documentation
- **[graph-core](packages/graph-core/README.md)** - Core library with step types and memory management
- **[graph-compiler](packages/graph-compiler/README.md)** - Transpiler from graph JSON to Python code
- **[graph-runtime](packages/graph-runtime/README.md)** - FastAPI service for agent execution
- **[graph-builder](packages/graph-builder/README.md)** - React UI for visual graph construction
- **[graph-chat](packages/graph-chat/README.md)** - React UI for conversational interaction with graphs

### Plugin Documentation
- **[HTTP Plugin](packages/graph-plugins-http/README.md)** - HTTP requests (GET, POST, PUT, PATCH, DELETE)
- **[URL Plugin](packages/graph-plugins-url/README.md)** - URL parsing, building, and encoding
- **[XML/HTML Plugin](packages/graph-plugins-xmlhtml/README.md)** - HTML extraction, XML parsing, conversions
- **[Encoding Plugin](packages/graph-plugins-encoding/README.md)** - Base64, Hex, Hashing, Gzip compression
- **[Text Plugin](packages/graph-plugins-text/README.md)** - String manipulation and regex operations
- **[JSON Plugin](packages/graph-plugins-json/README.md)** - JSON parsing, JSONPath, and schema validation
- **[YAML Plugin](packages/graph-plugins-yaml/README.md)** - YAML parsing and multi-document support
- **[CSV Plugin](packages/graph-plugins-csv/README.md)** - CSV manipulation, filtering, and analysis
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

Graphs are defined in JSON format. See **[GRAPH_FORMAT.md](docs/GRAPH_FORMAT.md)** for the complete specification.

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
# Start server (auto-generates SSL certificates)
graphflow-runtime

# Custom port
graphflow-runtime --port 9000

# Development mode with auto-reload
graphflow-runtime --reload

# Disable SSL verification for client calls (self-signed certs)
graphflow-runtime --insecure

# Use custom certificates
graphflow-runtime --ssl-keyfile /path/to/key --ssl-certfile /path/to/cert

# Use certificates from custom directory
graphflow-runtime --cert-dir /path/to/certs
```

## 🔐 HTTPS / SSL Configuration

All GraphFlow services run with HTTPS by default using self-signed certificates for secure local development.

### Quick Start

```bash
# Generate certificates (optional - auto-generated on first run)
make certs

# Start all services with HTTPS
make dev-start

# Check certificate status
make certs-check
```

### Certificate Management

| Command | Description |
|---------|-------------|
| `make certs` | Generate self-signed SSL certificates in `.certs/` |
| `make certs-check` | Verify certificates exist and show expiry dates |
| `make certs-clean` | Remove certificates (will be regenerated on next start) |

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GRAPHFLOW_SSL_KEYFILE` | Path to SSL private key | `.certs/graphflow.key` |
| `GRAPHFLOW_SSL_CERTFILE` | Path to SSL certificate | `.certs/graphflow.crt` |
| `GRAPHFLOW_CERT_DIR` | Certificate directory | `.certs` |
| `GRAPHFLOW_AUTO_SSL` | Auto-generate certs if missing | `true` |
| `GRAPHFLOW_INSECURE` | Skip SSL verification for client calls | `false` |

### Browser Certificate Warning

When first visiting HTTPS URLs with self-signed certificates, browsers will show a security warning:

- **Chrome/Edge**: Click "Advanced" → "Proceed to localhost (unsafe)"
- **Safari**: Click "Show Details" → "visit this website"
- **Firefox**: Click "Advanced..." → "Accept the Risk and Continue"

You'll need to accept the certificate for each port (8000, 3000, 3001) on first visit.

### Command Line Access

```bash
# Use -k flag with curl to skip certificate verification
curl -k https://localhost:8000/api/v1/health
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
- `PUT /api/v1/agents/{id}/runs/{run_id}/memory/{namespace}/{key}` - Update memory value (debug mode)

**Debug Control**:
- `GET /api/v1/agents/{id}/runs/{run_id}/debug/state` - Get debug state
- `POST /api/v1/agents/{id}/runs/{run_id}/debug/pause` - Pause execution
- `POST /api/v1/agents/{id}/runs/{run_id}/debug/resume` - Resume execution
- `POST /api/v1/agents/{id}/runs/{run_id}/debug/step` - Execute one step
- `POST /api/v1/agents/{id}/runs/{run_id}/debug/breakpoints/{step_id}` - Set breakpoint
- `DELETE /api/v1/agents/{id}/runs/{run_id}/debug/breakpoints/{step_id}` - Clear breakpoint

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
| Visual Graph Builder | ✅ | ✅ | ✅ |
| Interactive Debugger | ✅ | ❌ | ❌ |
| Breakpoint Support | ✅ | ❌ | ❌ |
| Step-Through Execution | ✅ | ❌ | ❌ |
| Runtime Memory Editing | ✅ | ❌ | ❌ |
| Memory Schema Management | ✅ | ⚠️ | ⚠️ |
| Memory Inspection | ✅ | ⚠️ | ⚠️ |
| LLM Tool Builder | ✅ | ⚠️ | ✅ |
| Multi-Provider LLM | ✅ | ⚠️ | ✅ |
| Runtime API | ✅ | ✅ | ✅ |

## 🚧 Roadmap

**Phase 4: UI Builder** ✅ Complete
- ✅ React app with ReactFlow
- ✅ Drag-and-drop graph builder
- ✅ Plugin system with step palette (unique icons/colors per plugin)
- ✅ Memory schema management
- ✅ Visual memory binding with "Bound to" buttons
- ✅ Editable outputs section with clean memory locations
- ✅ 9 production plugins (HTTP, URL, XML/HTML, Encoding, Text, JSON, YAML, CSV, Example)
- ✅ Memory manipulation steps (read-memory, write-memory)
- ✅ Position persistence (node layouts saved/restored)
- ✅ Runtime monitoring view with agents/runs/details
- ✅ Execution log with horizontal scrollbars
- ✅ Upload to runtime and execute graphs
- ✅ Auto-refresh for runtime view (polling-based)
- ✅ Interactive debugger with breakpoints
- ✅ Step-through execution (step/pause/resume)
- ✅ Real-time memory inspection and editing
- ✅ Rich property editors in debug mode
- ✅ Multi-provider LLM support (Ollama, LM Studio, OpenRouter, Anthropic, OpenAI)
- ✅ LLM tool support with visual tool builder (MappedStepTools)
- ✅ Live execution log with tool call visibility during debugging
- ✅ Tool error handling (errors returned to LLM for adaptive behavior)
- ✅ MCP tool integration for LLM steps (connect to any MCP server)
- ✅ Chat UI for conversational interaction with eligible graphs
- ✅ Multi-graph and multi-session chat support
- ✅ Per-conversation debug mode toggle
- ✅ Cross-app navigation (Builder/Runtime to Chat)

**Phase 5: Future Enhancements**
- 🚧 Graph templates
- 🚧 Compile from UI
- Plugin marketplace/registry
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

- **[Graph Format Specification](docs/GRAPH_FORMAT.md)** - Complete JSON format documentation
- **[Memory User Guide](docs/MEMORY_USER_GUIDE.md)** - How to use memory bindings and namespaces
- **[Memory Technical Reference](docs/MEMORY_SYSTEM.md)** - Memory system internals
- **[Makefile Reference](docs/MAKEFILE.md)** - Complete development command reference
- **Plugin Documentation**:
  - [HTTP Plugin](packages/graph-plugins-http/README.md) - HTTP requests
  - [URL Plugin](packages/graph-plugins-url/README.md) - URL parsing and encoding
  - [XML/HTML Plugin](packages/graph-plugins-xmlhtml/README.md) - HTML/XML processing
  - [Encoding Plugin](packages/graph-plugins-encoding/README.md) - Base64, Hex, Hashing, Gzip
  - [Text Plugin](packages/graph-plugins-text/README.md) - String manipulation and regex
  - [JSON Plugin](packages/graph-plugins-json/README.md) - JSON parsing and JSONPath
  - [YAML Plugin](packages/graph-plugins-yaml/README.md) - YAML parsing and conversion
  - [CSV Plugin](packages/graph-plugins-csv/README.md) - CSV manipulation and analysis
- **[Plugin Development Guide](packages/graphflow-plugin-example/README.md)** - Create your own custom steps
- **[Core Documentation](packages/graph-core/README.md)** - Step types and memory management
- **[Runtime API](https://localhost:8000/docs)** - FastAPI documentation (when server is running)

---

**Built with**: Python, FastAPI, Pydantic, SQLAlchemy, React, ReactFlow, TypeScript, and ❤️
