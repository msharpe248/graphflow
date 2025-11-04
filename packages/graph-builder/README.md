# GraphFlow Builder

🚧 **Status: Proof of Concept - In Active Development**

Visual graph builder UI for creating and monitoring GraphFlow agents with a drag-and-drop interface.

## Features

### Builder View
- **Visual Graph Editor**: Drag-and-drop interface powered by ReactFlow
- **Plugin-Based Step Palette**: Dynamically loaded step types from installed plugins
  - Category-based organization (Control, AI, Data, Transform, etc.)
  - Plugin-based filtering (view steps by plugin)
  - Search functionality to quickly find steps
  - Collapsible sections for better organization
- **Node Configuration**: Edit step properties with smart memory binding
- **Properties Panel**:
  - Configure step settings with labeled fields
  - Visual memory binding indicators with "Bound to" buttons
  - Editable outputs section showing all step outputs
  - Memory location editing without `_key` suffixes
  - Step behavior information from schemas
  - Delete step functionality
- **Memory Schema Panel**:
  - Manage three memory namespaces: inputs, outputs, intermediate
  - Collapsible sections with usage counts
  - Add/remove memory fields with type definitions
  - Set default values and required flags
  - "Used by" badges showing which steps reference each field
  - Auto-cleanup of unused memory fields
- **Memory Binding System**:
  - Auto-create memory fields when steps are added
  - Auto-bind config values to `{memory.<step_id>.<field>}` format
  - Change bindings to hardcoded values or different memory locations
  - Visual highlighting of bound fields
  - Binding dialog with search and filtering
  - Value synchronization across panels
- **Position Persistence**: Node positions saved and restored on export/import
- **Graph Metadata Editor**: Edit name, description, version, tags, and author
- **Import/Export**: Load and save graph definitions as JSON
- **Real-time Validation**: Visual feedback on graph structure

### Runtime View
- **Agent Management**: View all agents uploaded to the runtime
- **Run Monitoring**: Track execution of agent runs in real-time
- **3-Column Layout**:
  - Agents list with creation timestamps
  - Runs list for selected agent with status indicators
  - Run details with tabs for comprehensive information
- **Run Details**:
  - **Details Tab**: Timeline, inputs, outputs, and errors
  - **Memory Tab**: View memory state across all namespaces (inputs, intermediate, outputs)
  - **Execution Tab**: Step-by-step execution log with inputs/outputs
    - Grouped by step with read/write operations
    - Horizontal scrollbars for long values
    - JSON formatting for complex data
- **Runtime Connection Settings**: Configure runtime server URL
- **Agent Creation**: Upload graphs directly to runtime from builder
- **Run Execution**: Execute agents with custom inputs via modal

## Quick Start

### Development

```bash
# Install dependencies
npm install

# Start dev server (requires runtime server running)
npm run dev

# Visit http://localhost:3000
```

### Build for Production

```bash
# Build static files
npm run build

# Preview production build
npm run preview
```

## Usage

### Creating a Graph

1. **Drag steps from palette** onto the canvas (categorized by plugin/type)
2. **Connect steps** by dragging from output handle to input handle
3. **Select a node** to configure its properties in the Properties Panel
4. **Edit outputs** to bind step outputs to memory locations
5. **Configure memory bindings** using "Bound to" buttons or manual editing
6. **Manage memory schema** via the Memory Schema panel (collapsible right panel)
7. **Export graph** to JSON when complete

### Monitoring Agent Runs

1. **Switch to Runtime tab** in the toolbar
2. **Configure runtime connection** if needed (Settings icon)
3. **View agents** in the left column
4. **Select an agent** to see its runs
5. **Select a run** to view detailed execution information
6. **Explore tabs** (Details, Memory, Execution) for comprehensive insights

### Step Types

The available steps depend on installed plugins. Built-in steps include:

**Control**
- Start - Entry point
- Output - Map intermediate values to outputs
- Conditional - Branch based on condition
- Join - Wait for multiple branches
- Loop - Iterate over collection

**AI**
- LLM - Call LLM with tools and structured output
- Human Input - Wait for human input

**Data**
- Read Memory - Read values from memory
- Write Memory - Write values to memory
- Transform - Execute Python code

**General**
- HTTP - Make HTTP requests
- DB Query - Execute database queries

**HTTP Plugin** (if installed)
- 17 additional HTTP-related steps (http-get, http-post, url-parse, json-parse, html-strip, etc.)

See [HTTP Plugin Documentation](../graph-plugins-http/README.md) for details.

### Keyboard Shortcuts

- `Delete` - Delete selected node/edge
- `Ctrl/Cmd + Z` - Undo (ReactFlow built-in)
- `Ctrl/Cmd + C/V` - Copy/paste nodes

## Architecture

### Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety
- **ReactFlow** - Graph visualization
- **Zustand** - State management
- **TanStack Query** - Server state management for runtime API
- **Tailwind CSS** - Styling with Lucide icons
- **Vite** - Build tooling

### Project Structure

```
src/
├── components/              # React components
│   ├── BuilderView.tsx      # Main builder interface
│   ├── RuntimeView.tsx      # Runtime monitoring interface
│   ├── CustomNode.tsx       # ReactFlow node component
│   ├── GraphCanvas.tsx      # ReactFlow canvas wrapper
│   ├── StepPalette.tsx      # Plugin-based step palette
│   ├── PropertiesPanel.tsx  # Node properties editor with outputs
│   ├── MemoryPanel.tsx      # Memory schema management
│   ├── SettingsModal.tsx    # Graph metadata modal
│   ├── Toolbar.tsx          # Top toolbar with actions
│   ├── runtime/
│   │   ├── AgentsList.tsx   # Agents list component
│   │   ├── RunsList.tsx     # Runs list component
│   │   └── RunDetail.tsx    # Run details with tabs
│   └── ...
├── stores/
│   ├── graphStore.ts        # Zustand store for graph state
│   ├── pluginStore.ts       # Plugin management
│   └── appStore.ts          # App-level state (tabs, runtime context)
├── hooks/
│   └── useRuntime.ts        # React Query hooks for runtime API
├── types/
│   ├── graph.ts             # Graph definition TypeScript types
│   └── runtime.ts           # Runtime API types
├── utils/
│   └── graphValidator.ts    # Graph validation logic
├── App.tsx                  # Main app component with tabs
├── main.tsx                 # Entry point
└── index.css                # Global styles
```

## Graph JSON Format

The builder exports graphs in the standard GraphFlow JSON format:

```json
{
  "version": "1.0",
  "metadata": {
    "name": "My Agent",
    "description": "Agent description",
    "version": "1.0",
    "tags": ["ai", "automation"]
  },
  "memory": {
    "inputs": {
      "user_question": {
        "type": "string",
        "required": true
      }
    },
    "outputs": {
      "answer": {
        "type": "string"
      }
    },
    "intermediate": {
      "start_1.initialized": {
        "type": "boolean",
        "description": "initialized for start_1"
      }
    }
  },
  "steps": [
    {
      "id": "start_1",
      "type": "start",
      "config": {},
      "outputs": {
        "initialized": "{memory.start_1.initialized}"
      },
      "position": {"x": 100, "y": 100}
    }
  ],
  "edges": [
    {
      "id": "e1",
      "from": "start_1",
      "to": "llm_1"
    }
  ]
}
```

**Key Changes from Earlier Versions:**
- Steps now use `outputs` object mapping output keys to memory locations
- Old `memory_reads` and `memory_writes` fields are deprecated
- Steps can have optional `position` field for layout persistence
- Memory bindings use `{memory.field}` template syntax

See [GRAPH_FORMAT.md](../../GRAPH_FORMAT.md) for complete specification.

## Integration with GraphFlow

### Export & Compile

```bash
# 1. Export graph from UI (Download JSON button in toolbar)

# 2. Compile to executable Python
graphflow-compile compile my_graph.json \
  --framework pydantic_ai \
  --output agent.py

# 3. Run standalone
python agent.py inputs.json

# Or run as a server
python agent.py --server
```

### Upload to Runtime

The builder can directly upload graphs to a running GraphFlow runtime:

1. Start the runtime server: `graphflow-runtime`
2. Configure connection in Builder (Settings → Runtime Connection)
3. Use "Upload to Runtime" button in Builder toolbar
4. Switch to Runtime tab to monitor execution

## POC Status & Limitations

This is a **Proof of Concept** with the following limitations:

### Working Features ✅
- Visual graph building with drag-and-drop
- Plugin-based step palette with search
- Memory schema management with auto-cleanup
- Memory binding system with visual indicators
- Position persistence
- Runtime monitoring with agent/run/detail views
- Execution log with step-by-step breakdown
- Import/export graphs as JSON
- Direct upload to runtime
- Run execution with custom inputs

### Known Limitations & TODOs ⚠️
- [ ] No undo/redo stack (beyond ReactFlow default)
- [ ] No graph templates library
- [ ] No subgraph support
- [ ] Limited validation error highlighting
- [ ] No step debugging/breakpoints
- [ ] No auto-layout algorithm
- [ ] No collaborative editing
- [ ] Runtime view doesn't auto-refresh (manual refresh needed)
- [ ] No real-time streaming of execution logs
- [ ] Limited error recovery UI

## Development

### Adding New Features

The codebase is organized by feature:

- **Builder features**: Add to `BuilderView.tsx` and related components
- **Runtime features**: Add to `RuntimeView.tsx` and `runtime/` directory
- **Step types**: Install plugin packages (auto-discovered via entry points)
- **Validation**: Add logic to `utils/graphValidator.ts`

### Customizing Node Appearance

Edit `src/components/CustomNode.tsx` to modify node styling and behavior.

### Adding Runtime API Endpoints

Add hooks to `src/hooks/useRuntime.ts` using TanStack Query patterns.

## Troubleshooting

### Nodes not draggable
- Make sure ReactFlow has proper dimensions (use `h-full w-full`)
- Check that drag handlers are properly set

### Export not working
- Check browser console for errors
- Verify graph has valid structure
- Ensure all nodes are connected properly

### Runtime connection fails
- Verify runtime server is running: `graphflow-runtime`
- Check runtime URL in Settings (default: `http://localhost:8000`)
- Look for CORS issues in browser console

### Port 3000 already in use
- Change port in `vite.config.ts` under `server.port`

## Future Enhancements

**Short Term:**
- [ ] Auto-refresh for runtime view
- [ ] Real-time execution streaming
- [ ] Undo/redo implementation
- [ ] Validation error highlighting on canvas
- [ ] Graph templates library

**Medium Term:**
- [ ] Auto-layout algorithm for better node positioning
- [ ] Subgraph support (reusable components)
- [ ] Step debugging with breakpoints
- [ ] Export to multiple formats
- [ ] Version control integration

**Long Term:**
- [ ] Real-time collaboration
- [ ] Graph analytics and optimization suggestions
- [ ] Visual diff for graph changes
- [ ] Plugin marketplace integration

## License

MIT

---

**Part of the GraphFlow project** - See [main README](../../README.md) for the complete platform documentation.
