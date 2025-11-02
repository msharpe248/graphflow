# GraphFlow Builder

Visual graph builder UI for creating GraphFlow agents with drag-and-drop interface.

## Features

- **Visual Graph Editor**: Drag-and-drop interface powered by ReactFlow
- **10 Step Types**: All GraphFlow step types available in palette
- **Node Configuration**: Edit step properties, memory reads/writes, and configuration
- **Memory Schema Editor**: Define inputs, outputs, and intermediate fields
- **Graph Metadata**: Edit name, description, version, tags, and author
- **Import/Export**: Load and save graph definitions as JSON
- **Real-time Validation**: Visual feedback on graph structure

## Quick Start

### Development

```bash
# Install dependencies
npm install

# Start dev server
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

1. **Drag steps from palette** onto the canvas
2. **Connect steps** by dragging from output handle to input handle
3. **Select a node** to configure its properties
4. **Edit memory schema** via Settings → Memory Schema tab
5. **Export graph** to JSON when complete

### Step Types

Available in the left palette, organized by category:

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
- HTTP - Make HTTP requests
- DB Query - Execute database queries

**Transform**
- Transform - Execute Python code

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
- **Tailwind CSS** - Styling
- **Vite** - Build tooling

### Project Structure

```
src/
├── components/          # React components
│   ├── CustomNode.tsx   # Node component
│   ├── GraphCanvas.tsx  # ReactFlow canvas
│   ├── StepPalette.tsx  # Step type palette
│   ├── PropertiesPanel.tsx # Node properties editor
│   ├── SettingsModal.tsx   # Graph settings modal
│   └── Toolbar.tsx      # Top toolbar
├── stores/
│   └── graphStore.ts    # Zustand store for graph state
├── types/
│   └── graph.ts         # TypeScript types
├── utils/
│   └── stepTypes.ts     # Step type definitions
├── App.tsx              # Main app component
├── main.tsx             # Entry point
└── index.css            # Global styles
```

## Graph JSON Format

The builder exports graphs in the standard GraphFlow JSON format:

```json
{
  "version": "1.0",
  "metadata": {
    "name": "My Agent",
    "description": "Agent description",
    "tags": ["ai", "automation"]
  },
  "memory": {
    "inputs": {
      "user_question": {"type": "string"}
    },
    "outputs": {
      "answer": {"type": "string"}
    },
    "intermediate": {}
  },
  "steps": [
    {
      "id": "start_1",
      "type": "start",
      "config": {},
      "memory_reads": [],
      "memory_writes": []
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

## Integration with GraphFlow

### Export & Compile

```bash
# 1. Export graph from UI (Download JSON)

# 2. Compile to executable
graphflow-compile compile my_graph.json \
  --framework pydantic_ai \
  --output agent.py

# 3. Run standalone
python agent.py inputs.json
```

### Upload to Runtime

```bash
# 1. Export graph from UI

# 2. Upload via API
curl -X POST http://localhost:8000/api/v1/agents \
  -H "Content-Type: application/json" \
  -d @my_graph.json
```

## Development

### Adding New Step Types

1. Add step definition to `src/utils/stepTypes.ts`
2. Define config schema
3. Step will automatically appear in palette

### Customizing Node Appearance

Edit `src/components/CustomNode.tsx` to modify node styling.

### Adding Validation

Add validation logic in `src/stores/graphStore.ts` export function.

## Troubleshooting

### Nodes not draggable
- Make sure ReactFlow has proper dimensions (use `h-full w-full`)
- Check that drag handlers are properly set

### Export not working
- Check browser console for errors
- Verify graph has valid structure

### Port 3000 already in use
- Change port in `vite.config.ts` under `server.port`

## Future Enhancements

- [ ] Real-time collaboration
- [ ] Undo/redo stack
- [ ] Graph templates library
- [ ] Subgraph support
- [ ] Validation error highlighting
- [ ] Runtime execution integration
- [ ] Step debugging
- [ ] Auto-layout algorithm

## License

MIT
