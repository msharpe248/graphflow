# Data Flow Visualization Feature - Implementation Plan

## Overview
Add a data flow visualization mode to the graph builder that shows how data moves through the graph via memory bindings. This view will display property-level dependencies, showing which step outputs connect to which step inputs through memory references, making it easier to understand and debug complex data transformations.

## Core Concepts

### Data Flow vs Execution Flow
- **Execution Flow** (current): Shows the order steps execute (edges between steps)
- **Data Flow** (new): Shows how data properties move between steps through memory

### Example Scenario
```
Step A (HTTP Get):
  Outputs: {memory.api_response}

Step B (Transform):
  Inputs: {memory.api_response}
  Outputs: {memory.transformed_data}

Step C (LLM):
  Inputs: system_prompt = "Process this: {memory.transformed_data}"
  Outputs: {memory.llm_result}
```

**Data Flow Visualization** would show:
```
api_response (A) ──────> api_response (B input)
                         transformed_data (B) ──────> transformed_data (C input)
                                                      llm_result (C)
```

### Visualization Modes
1. **Execution Mode** (default): Current view with step boxes and execution edges
2. **Data Flow Mode** (new): Toggle that highlights memory bindings as colored paths
3. **Combined Mode** (optional): Shows both execution and data flow simultaneously

## Architecture Components

## 1. **Data Flow Analysis Engine**

**1.1 Data Flow Analyzer** (NEW: `packages/graph-builder/src/utils/dataFlowAnalyzer.ts`)
Analyzes the graph to extract data dependencies:

```typescript
interface PropertyReference {
  stepId: string;
  stepLabel: string;
  propertyPath: string;  // e.g., "config.url" or "outputs.result"
  memoryKey: string;     // e.g., "api_response"
  type: 'read' | 'write';
  namespace: 'inputs' | 'outputs' | 'intermediate';
}

interface DataFlowEdge {
  id: string;
  sourceStepId: string;
  sourceProperty: string;
  targetStepId: string;
  targetProperty: string;
  memoryKey: string;
  dataType?: string;
}

interface DataFlowGraph {
  nodes: DataFlowNode[];
  edges: DataFlowEdge[];
}

interface DataFlowNode {
  stepId: string;
  stepType: string;
  stepLabel: string;
  inputs: PropertyReference[];   // Properties this step reads
  outputs: PropertyReference[];  // Properties this step writes
}

class DataFlowAnalyzer {
  constructor(private graph: Graph) {}

  /**
   * Analyze graph and extract data flow
   */
  analyze(): DataFlowGraph {
    const nodes: DataFlowNode[] = [];
    const edges: DataFlowEdge[] = [];

    // 1. For each step, find all memory references
    for (const step of this.graph.steps) {
      const node = this.analyzeStep(step);
      nodes.push(node);
    }

    // 2. Connect readers to writers
    const writes = new Map<string, PropertyReference[]>();
    const reads = new Map<string, PropertyReference[]>();

    for (const node of nodes) {
      for (const output of node.outputs) {
        if (!writes.has(output.memoryKey)) {
          writes.set(output.memoryKey, []);
        }
        writes.get(output.memoryKey)!.push(output);
      }

      for (const input of node.inputs) {
        if (!reads.has(input.memoryKey)) {
          reads.set(input.memoryKey, []);
        }
        reads.get(input.memoryKey)!.push(input);
      }
    }

    // 3. Create edges from writers to readers
    for (const [memoryKey, writers] of writes.entries()) {
      const readers = reads.get(memoryKey) || [];
      for (const writer of writers) {
        for (const reader of readers) {
          if (writer.stepId !== reader.stepId) {
            edges.push({
              id: `df_${writer.stepId}_${reader.stepId}_${memoryKey}`,
              sourceStepId: writer.stepId,
              sourceProperty: writer.propertyPath,
              targetStepId: reader.stepId,
              targetProperty: reader.propertyPath,
              memoryKey: memoryKey,
              dataType: this.getDataType(memoryKey)
            });
          }
        }
      }
    }

    return { nodes, edges };
  }

  /**
   * Recursively scan step config and outputs for {memory.x} references
   */
  private analyzeStep(step: Step): DataFlowNode {
    const inputs: PropertyReference[] = [];
    const outputs: PropertyReference[] = [];

    // Scan config for reads
    this.scanObject(step.config, `config`, (path, memoryKey) => {
      inputs.push({
        stepId: step.id,
        stepLabel: this.getStepLabel(step),
        propertyPath: path,
        memoryKey,
        type: 'read',
        namespace: this.getNamespace(memoryKey)
      });
    });

    // Scan outputs for writes
    for (const [key, value] of Object.entries(step.outputs || {})) {
      if (typeof value === 'string' && value.startsWith('{memory.')) {
        const memoryKey = value.slice(8, -1);  // Extract from {memory.X}
        outputs.push({
          stepId: step.id,
          stepLabel: this.getStepLabel(step),
          propertyPath: `outputs.${key}`,
          memoryKey,
          type: 'write',
          namespace: this.getNamespace(memoryKey)
        });
      }
    }

    return {
      stepId: step.id,
      stepType: step.type,
      stepLabel: this.getStepLabel(step),
      inputs,
      outputs
    };
  }

  /**
   * Recursively scan object for {memory.x} patterns
   */
  private scanObject(
    obj: any,
    path: string,
    callback: (path: string, memoryKey: string) => void
  ): void {
    if (typeof obj === 'string') {
      const matches = obj.matchAll(/\{memory\.([^}]+)\}/g);
      for (const match of matches) {
        callback(path, match[1]);
      }
    } else if (Array.isArray(obj)) {
      obj.forEach((item, index) => {
        this.scanObject(item, `${path}[${index}]`, callback);
      });
    } else if (obj && typeof obj === 'object') {
      for (const [key, value] of Object.entries(obj)) {
        this.scanObject(value, `${path}.${key}`, callback);
      }
    }
  }

  private getNamespace(memoryKey: string): 'inputs' | 'outputs' | 'intermediate' {
    if (this.graph.memory.inputs[memoryKey]) return 'inputs';
    if (this.graph.memory.outputs[memoryKey]) return 'outputs';
    return 'intermediate';
  }

  private getDataType(memoryKey: string): string | undefined {
    const field = this.graph.memory.inputs[memoryKey] ||
                  this.graph.memory.outputs[memoryKey] ||
                  this.graph.memory.intermediate[memoryKey];
    return field?.type;
  }

  private getStepLabel(step: Step): string {
    const stepType = pluginStore.getState().stepTypes[step.type];
    return stepType?.label || step.type;
  }
}
```

## 2. **Backend: No Changes Required**
All data flow information can be computed client-side from the existing graph structure. No backend changes needed.

## 3. **Frontend: Data Flow Visualization Modes**

### Option A: Overlay Mode (Recommended)
Add data flow edges on top of existing graph canvas

**Pros:**
- Shows relationship between execution flow and data flow
- No context switching
- Easy to understand causality

**Cons:**
- Can get cluttered with complex graphs
- Two types of edges to distinguish

**Implementation:**
- Toggle button in toolbar: "Show Data Flow"
- When enabled, render data flow edges in addition to execution edges
- Use different styling: dashed lines, different colors
- Add labels showing memory key and data type

### Option B: Separate View Mode
Switch between Execution View and Data Flow View

**Pros:**
- Clean, focused visualization
- No clutter from mixing two concerns
- Can optimize layout for each view

**Cons:**
- Requires toggling to see both perspectives
- More implementation work

**Implementation:**
- Radio buttons in toolbar: "Execution" | "Data Flow"
- Data Flow mode hides execution edges, shows data flow edges
- Rearrange nodes in data flow-optimized layout (optional)

### Option C: Data Flow Panel
Add a new right-side panel showing data flow list

**Pros:**
- No changes to canvas
- Simple to implement
- Good for detailed inspection

**Cons:**
- Doesn't show visual flow
- Less intuitive than graph visualization

### Recommendation: Implement Option A (Overlay Mode) First
- Most intuitive for users
- Leverages existing React Flow infrastructure
- Can add Option B later if needed

## 4. **Frontend: Custom Data Flow Edges**

**4.1 DataFlowEdge Component** (NEW: `packages/graph-builder/src/components/edges/DataFlowEdge.tsx`)

```typescript
import { BaseEdge, EdgeLabelRenderer, EdgeProps, getSmoothStepPath } from '@xyflow/react';

interface DataFlowEdgeData {
  memoryKey: string;
  dataType?: string;
  sourceProperty: string;
  targetProperty: string;
}

export function DataFlowEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  markerEnd,
}: EdgeProps<DataFlowEdgeData>) {
  const [edgePath, labelX, labelY] = getSmoothStepPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    borderRadius: 8,
  });

  const namespace = data?.namespace || 'intermediate';
  const color = getNamespaceColor(namespace);

  return (
    <>
      {/* Main path */}
      <BaseEdge
        id={id}
        path={edgePath}
        markerEnd={markerEnd}
        style={{
          stroke: color,
          strokeWidth: 2,
          strokeDasharray: '5,5',  // Dashed line to distinguish from execution edges
          opacity: 0.7,
        }}
      />

      {/* Label */}
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          <div
            className="rounded px-2 py-1 text-xs font-medium shadow-sm border"
            style={{
              backgroundColor: 'white',
              borderColor: color,
              color: color,
            }}
          >
            <div className="font-semibold">{data?.memoryKey}</div>
            {data?.dataType && (
              <div className="text-gray-500 text-xs">{data.dataType}</div>
            )}
          </div>
        </div>
      </EdgeLabelRenderer>
    </>
  );
}

function getNamespaceColor(namespace: string): string {
  switch (namespace) {
    case 'inputs': return '#3b82f6';      // Blue
    case 'outputs': return '#10b981';     // Green
    case 'intermediate': return '#8b5cf6'; // Purple
    default: return '#6b7280';            // Gray
  }
}
```

**4.2 Register Custom Edge Type** (in `GraphCanvas.tsx`):
```typescript
import { DataFlowEdge } from './edges/DataFlowEdge';

const edgeTypes = {
  dataFlow: DataFlowEdge,
};

<ReactFlow
  nodes={nodes}
  edges={edges}
  edgeTypes={edgeTypes}
  // ... other props
/>
```

## 5. **Frontend: Data Flow Toggle UI**

**5.1 Update Toolbar** (`packages/graph-builder/src/components/Toolbar.tsx`)

Add toggle button for data flow mode:

```typescript
const [showDataFlow, setShowDataFlow] = useState(false);

<div className="flex items-center gap-2">
  {/* Existing buttons... */}

  <button
    onClick={() => setShowDataFlow(!showDataFlow)}
    className={cn(
      "px-3 py-1.5 rounded border text-sm font-medium transition-colors",
      showDataFlow
        ? "bg-purple-600 text-white border-purple-600"
        : "bg-white text-gray-700 border-gray-300 hover:bg-gray-50"
    )}
    title="Toggle data flow visualization"
  >
    <div className="flex items-center gap-2">
      <GitBranch size={16} />
      Data Flow
    </div>
  </button>
</div>
```

**5.2 Pass to GraphCanvas**
```typescript
<GraphCanvas
  // ... existing props
  showDataFlow={showDataFlow}
/>
```

## 6. **Frontend: GraphCanvas Updates**

**6.1 Update GraphCanvas Component** (`packages/graph-builder/src/components/GraphCanvas.tsx`)

```typescript
interface GraphCanvasProps {
  // ... existing props
  showDataFlow?: boolean;
}

export function GraphCanvas({ showDataFlow = false, ...props }: GraphCanvasProps) {
  const graph = useGraphStore(state => state.graph);

  // Existing edges (execution flow)
  const executionEdges = useMemo(() => {
    return graph.edges.map(edge => ({
      id: edge.id,
      source: edge.from,
      target: edge.to,
      type: 'default',
      markerEnd: { type: MarkerType.ArrowClosed },
      style: { stroke: '#374151', strokeWidth: 2 },
    }));
  }, [graph.edges]);

  // NEW: Data flow edges
  const dataFlowEdges = useMemo(() => {
    if (!showDataFlow) return [];

    const analyzer = new DataFlowAnalyzer(graph);
    const dataFlow = analyzer.analyze();

    return dataFlow.edges.map(edge => ({
      id: edge.id,
      source: edge.sourceStepId,
      target: edge.targetStepId,
      type: 'dataFlow',
      data: {
        memoryKey: edge.memoryKey,
        dataType: edge.dataType,
        sourceProperty: edge.sourceProperty,
        targetProperty: edge.targetProperty,
        namespace: analyzer.getNamespace(edge.memoryKey),
      },
      markerEnd: { type: MarkerType.ArrowClosed },
    }));
  }, [graph, showDataFlow]);

  // Combine edges
  const allEdges = useMemo(() => {
    return [...executionEdges, ...dataFlowEdges];
  }, [executionEdges, dataFlowEdges]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={allEdges}  // Show both execution and data flow edges
      edgeTypes={edgeTypes}
      // ... other props
    />
  );
}
```

## 7. **Frontend: Enhanced Node Display (Optional)**

**7.1 Add Property Ports to Nodes** (in `CustomNode.tsx`)

Show input/output properties as small ports on nodes:

```typescript
export function CustomNode({ data, selected }: NodeProps) {
  const graph = useGraphStore(state => state.graph);
  const showDataFlow = useGraphStore(state => state.showDataFlow);

  // Get data flow info for this node
  const dataFlowNode = useMemo(() => {
    if (!showDataFlow) return null;
    const analyzer = new DataFlowAnalyzer(graph);
    const dataFlow = analyzer.analyze();
    return dataFlow.nodes.find(n => n.stepId === data.id);
  }, [showDataFlow, graph, data.id]);

  return (
    <div className={cn(/* existing styles */)}>
      {/* Existing node header */}

      {/* NEW: Input properties (left side) */}
      {showDataFlow && dataFlowNode && dataFlowNode.inputs.length > 0 && (
        <div className="mt-2 border-t pt-2">
          <div className="text-xs font-semibold text-gray-500 mb-1">Inputs:</div>
          {dataFlowNode.inputs.map((input, i) => (
            <div key={i} className="text-xs text-blue-600 mb-0.5">
              ← {input.memoryKey}
            </div>
          ))}
        </div>
      )}

      {/* NEW: Output properties (right side) */}
      {showDataFlow && dataFlowNode && dataFlowNode.outputs.length > 0 && (
        <div className="mt-2 border-t pt-2">
          <div className="text-xs font-semibold text-gray-500 mb-1">Outputs:</div>
          {dataFlowNode.outputs.map((output, i) => (
            <div key={i} className="text-xs text-green-600 mb-0.5">
              {output.memoryKey} →
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

## 8. **Frontend: Data Flow Inspector Panel (Optional)**

**8.1 DataFlowPanel Component** (NEW: `packages/graph-builder/src/components/DataFlowPanel.tsx`)

Optional detailed view showing all data flows as a list:

```typescript
export function DataFlowPanel() {
  const graph = useGraphStore(state => state.graph);

  const dataFlow = useMemo(() => {
    const analyzer = new DataFlowAnalyzer(graph);
    return analyzer.analyze();
  }, [graph]);

  // Group by memory key
  const flowsByKey = useMemo(() => {
    const map = new Map<string, DataFlowEdge[]>();
    for (const edge of dataFlow.edges) {
      if (!map.has(edge.memoryKey)) {
        map.set(edge.memoryKey, []);
      }
      map.get(edge.memoryKey)!.push(edge);
    }
    return map;
  }, [dataFlow.edges]);

  return (
    <div className="p-4 space-y-4">
      <h3 className="text-lg font-semibold">Data Flow</h3>

      {Array.from(flowsByKey.entries()).map(([memoryKey, edges]) => (
        <div key={memoryKey} className="border rounded p-3">
          <div className="font-medium text-purple-600 mb-2">
            {memoryKey}
          </div>
          <div className="space-y-1">
            {edges.map(edge => (
              <div key={edge.id} className="text-sm text-gray-600 flex items-center gap-2">
                <span className="font-medium">{edge.sourceStepId}</span>
                <span className="text-gray-400">→</span>
                <span className="font-medium">{edge.targetStepId}</span>
                <span className="text-xs text-gray-400">
                  ({edge.sourceProperty} → {edge.targetProperty})
                </span>
              </div>
            ))}
          </div>
        </div>
      ))}

      {flowsByKey.size === 0 && (
        <div className="text-sm text-gray-500 text-center py-8">
          No data flows detected
        </div>
      )}
    </div>
  );
}
```

**8.2 Add to BuilderView** (optional third panel or collapsible section in Memory panel)

## 9. **Frontend: Minimap Enhancement (Optional)**

**9.1 Custom MiniMap with Data Flow** (in `GraphCanvas.tsx`)

```typescript
import { MiniMap } from '@xyflow/react';

// Custom node color function for minimap
const nodeColor = (node: Node) => {
  if (showDataFlow) {
    // Color by number of connections
    const dataFlowNode = dataFlow.nodes.find(n => n.stepId === node.id);
    const connectionCount =
      (dataFlowNode?.inputs.length || 0) + (dataFlowNode?.outputs.length || 0);

    if (connectionCount === 0) return '#e5e7eb';  // Gray - no data flow
    if (connectionCount <= 2) return '#93c5fd';   // Light blue
    if (connectionCount <= 4) return '#60a5fa';   // Blue
    return '#3b82f6';                             // Dark blue - hub node
  }

  // Default: color by category
  const stepType = pluginStore.getState().stepTypes[node.data.type];
  return stepType?.color || '#6b7280';
};

<MiniMap
  nodeColor={nodeColor}
  nodeStrokeWidth={3}
  zoomable
  pannable
/>
```

## 10. **Frontend: Store Updates**

**10.1 Add Data Flow State to GraphStore** (`packages/graph-builder/src/stores/graphStore.ts`)

```typescript
interface GraphState {
  // ... existing state

  // NEW: Data flow visualization state
  showDataFlow: boolean;
  dataFlowGraph: DataFlowGraph | null;

  // NEW: Actions
  setShowDataFlow: (show: boolean) => void;
  computeDataFlow: () => void;
}

// In store implementation
setShowDataFlow: (show) => {
  set({ showDataFlow: show });
  if (show) {
    get().computeDataFlow();
  }
},

computeDataFlow: () => {
  const graph = get().graph;
  const analyzer = new DataFlowAnalyzer(graph);
  const dataFlowGraph = analyzer.analyze();
  set({ dataFlowGraph });
},
```

## Implementation Phases

### Phase 1: Data Flow Analyzer
1. Create `DataFlowAnalyzer` class
2. Implement memory reference scanning
3. Implement edge connection logic
4. Add unit tests with sample graphs
5. Test with complex nested references

### Phase 2: Custom Data Flow Edges
1. Create `DataFlowEdge` component
2. Style with dashed lines and colors
3. Add edge labels with memory key
4. Register edge type in React Flow
5. Test rendering with sample data

### Phase 3: Graph Canvas Integration
1. Add `showDataFlow` prop to GraphCanvas
2. Compute data flow edges when enabled
3. Combine with execution edges
4. Handle edge overlapping/routing
5. Test with various graph layouts

### Phase 4: Toolbar Toggle UI
1. Add toggle button to Toolbar
2. Wire up to graph store state
3. Add keyboard shortcut (e.g., Ctrl+D)
4. Add tooltip and icon
5. Persist preference to localStorage

### Phase 5: Enhanced Node Display (Optional)
1. Update CustomNode to show input/output properties
2. Add visual indicators for data connections
3. Style property lists
4. Handle overflow with scrolling
5. Test with nodes with many properties

### Phase 6: Data Flow Panel (Optional)
1. Create DataFlowPanel component
2. Show grouped list of data flows
3. Add click-to-highlight in canvas
4. Add filtering and search
5. Integrate into BuilderView layout

### Phase 7: Testing & Polish
1. Test with real-world complex graphs
2. Performance optimization for large graphs
3. Edge routing optimization to avoid overlaps
4. Animation effects (optional)
5. Documentation and examples
6. User feedback and iteration

## Technical Decisions & Considerations

### Edge Styling Strategy
- **Execution edges**: Solid lines, dark gray (#374151)
- **Data flow edges**: Dashed lines, colored by namespace
  - Inputs: Blue (#3b82f6)
  - Outputs: Green (#10b981)
  - Intermediate: Purple (#8b5cf6)
- **Edge labels**: Show memory key and data type
- **Hover effects**: Highlight connected nodes

### Performance Considerations
- **Memoization**: Cache data flow computation with `useMemo`
- **Lazy computation**: Only compute when data flow mode enabled
- **Incremental updates**: Recompute only affected edges on graph change
- **Large graphs**: Consider edge filtering or clustering for 50+ nodes

### Layout Optimization
- **No automatic re-layout**: Keep node positions stable when toggling
- **Edge routing**: Use React Flow's built-in smooth step paths
- **Overlap handling**: Let React Flow handle edge crossings
- **Optional**: Add "Optimize Layout for Data Flow" button (Phase 8)

### User Experience
- **Toggle discoverability**: Prominent button with icon in toolbar
- **First-time hint**: Show tooltip or onboarding for new users
- **Color legend**: Add legend explaining edge colors
- **Keyboard shortcuts**: Ctrl+D to toggle, familiar for developers

### Edge Cases
- **Circular dependencies**: Handle loops gracefully (A → B → A)
- **Unused memory**: Show dangling writes (no readers) with warning indicator
- **Multiple writers**: Show when multiple steps write to same memory key
- **Template strings**: Parse complex templates like `"Hello {memory.name}!"`
- **Array/object access**: Handle `{memory.data[0]}` or `{memory.user.name}`

### Advanced Features (Future)
- **Data type validation**: Show warnings for type mismatches
- **Data flow filtering**: Show only flows for selected node
- **Data flow search**: Find all flows using specific memory key
- **Export data flow diagram**: Save as image or Mermaid diagram
- **Data lineage tracking**: Show full path from input to output
- **Impact analysis**: "What depends on this output?"

## Files to Create

**Frontend** (~800 lines total):
1. `packages/graph-builder/src/utils/dataFlowAnalyzer.ts` (~300 lines)
2. `packages/graph-builder/src/components/edges/DataFlowEdge.tsx` (~100 lines)
3. `packages/graph-builder/src/components/DataFlowPanel.tsx` (~200 lines) - optional
4. `packages/graph-builder/src/hooks/useDataFlow.ts` (~50 lines)
5. `packages/graph-builder/src/types/dataFlow.ts` (~150 lines)

## Files to Modify

**Frontend** (~200 lines changes):
1. `packages/graph-builder/src/components/GraphCanvas.tsx` (+80 lines)
2. `packages/graph-builder/src/components/Toolbar.tsx` (+30 lines)
3. `packages/graph-builder/src/components/CustomNode.tsx` (+50 lines) - optional enhanced display
4. `packages/graph-builder/src/stores/graphStore.ts` (+40 lines)

## Estimated Effort
- **Core Data Flow Analyzer**: 2 days
- **Custom Edges & Rendering**: 1-2 days
- **UI Integration & Toggle**: 1 day
- **Enhanced Node Display**: 1 day (optional)
- **Data Flow Panel**: 1-2 days (optional)
- **Testing & Polish**: 1-2 days
- **Total Core Features**: 5-7 days
- **Total with Optional Features**: 8-11 days

## Visual Design Mockup

### Default View (Execution Flow Only)
```
┌─────┐         ┌─────┐         ┌─────┐
│  A  │────────>│  B  │────────>│  C  │
└─────┘         └─────┘         └─────┘
   Solid gray edges (execution order)
```

### Data Flow Mode Enabled
```
┌─────┐         ┌─────┐         ┌─────┐
│  A  │────────>│  B  │────────>│  C  │
└─────┘         └─────┘         └─────┘
   │              │               │
   │  api_response │  trans_data │
   ╰··············╯              │
                  ╰···············╯
   Dashed colored edges (data flow)
   Labels show memory keys
```

### Enhanced Node Display (Data Flow Mode)
```
┌─────────────────────┐
│ HTTP Get            │
│ step_1              │
├─────────────────────┤
│ Outputs:            │
│ • api_response →    │
│ • status_code →     │
└─────────────────────┘
        ↓
┌─────────────────────┐
│ Transform           │
│ step_2              │
├─────────────────────┤
│ Inputs:             │
│ ← api_response      │
│ Outputs:            │
│ • transformed_data →│
└─────────────────────┘
```

## Example Use Cases

### Use Case 1: Debugging Data Transformation
**Problem**: User sees incorrect output, needs to trace data path
**Solution**: Enable data flow mode, follow colored edges from input to output

### Use Case 2: Understanding Complex Graph
**Problem**: New team member needs to understand data flow in 20-step graph
**Solution**: Toggle data flow to see which steps exchange data, ignore execution order

### Use Case 3: Refactoring
**Problem**: Want to rename memory variable, need to find all usages
**Solution**: Data flow view shows all readers/writers of that variable

### Use Case 4: Performance Optimization
**Problem**: Want to identify bottleneck steps that many others depend on
**Solution**: MiniMap in data flow mode highlights highly connected "hub" nodes

## Testing Strategy

### Unit Tests
- DataFlowAnalyzer with various graph structures
- Memory reference parsing with edge cases
- Edge deduplication and filtering

### Integration Tests
- Toggle data flow mode on/off
- Verify correct edges rendered
- Test with graphs of varying complexity (5, 20, 50+ nodes)

### Visual Regression Tests
- Snapshot tests for edge rendering
- Test edge label positioning
- Test color coding accuracy

### User Acceptance Tests
- Can user trace data from input to output?
- Is data flow view understandable without training?
- Does it help debug real-world issues?

---

This plan provides a comprehensive data flow visualization feature that enhances understanding of complex graphs while maintaining the clean, professional aesthetic of the GraphFlow builder.
