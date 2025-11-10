# GraphFlow Debugger - Implementation Plan (Updated)

## Overview
Add a comprehensive debugging system with breakpoints, step-through execution, real-time memory inspection, and graph visualization. The debugger integrates as a new "Graph" tab in the runtime view and provides interactive debugging with loop support.

## Key Features
- **Graph visualization in runtime**: Interactive graph shown as tab alongside Details/Memory/Execution
- **Dynamic breakpoints**: Add/remove breakpoints during paused execution
- **Rich node inspector**: Click nodes to view config, memory, status, timing, execution count
- **Memory editing**: Edit memory values while paused for testing
- **Loop support**: Track and display execution count per step
- **Debug mode checkbox**: Enable debug mode via checkbox in run creation dialog
- **Step-through execution**: Pause before start, step through each operation, resume to next breakpoint

## Architecture Components

### 1. Backend: Database Schema

**Update AgentRun model** (`packages/graph-runtime/graphflow_runtime/storage/models.py`):
```python
class AgentRun(Base):
    # ... existing fields
    debug_mode = Column(Boolean, default=False)
    current_step_id = Column(String, nullable=True)
    breakpoints = Column(JSON, nullable=True)  # List of step IDs
    step_execution_counts = Column(JSON, nullable=True)  # Dict: step_id -> count
    debug_state = Column(String, nullable=True)  # 'before_start' | 'before_step' | 'after_step' | 'completed'
```

### 2. Backend: Execution Controller

**NEW: ExecutionController** (`packages/graph-runtime/graphflow_runtime/executor/execution_controller.py`):
- Manage execution state per run: `running`, `paused`, `stepping`, `stopped`
- Track current step being executed
- Store breakpoints (dynamic set of step IDs)
- Command handling: pause/resume/step operations
- Thread-safe async communication between API and executor
- Event callbacks for WebSocket notifications
- Step execution counter (for loop tracking)

Key methods:
- `wait_if_paused(step_id)` - Check if should pause before step
- `step_completed(step_id)` - Notify step completed, increment counter
- `set_breakpoint(step_id)` - Add breakpoint dynamically
- `clear_breakpoint(step_id)` - Remove breakpoint
- `pause()` - Pause execution
- `resume()` - Resume to next breakpoint or end
- `step()` - Execute one step then pause
- `get_execution_count(step_id)` - Get times step has executed

### 3. Backend: AsyncExecutor Enhancements

**Modify AsyncExecutor** (`packages/graph-runtime/graphflow_runtime/executor/async_executor.py`):
- Add `execution_controllers: Dict[str, ExecutionController]`
- Create controller when debug_mode=True
- Pass controller to generated agent
- New methods:
  - `create_debug_controller(run_id, breakpoints)` - Initialize debug session
  - `get_debug_state(run_id)` - Get current debug state
  - `update_memory_value(run_id, namespace, key, value)` - Edit memory while paused
  - Debug control methods: `pause()`, `resume()`, `step()`, `set_breakpoint()`, `clear_breakpoint()`

### 4. Backend: Code Generation

**Update template** (`packages/graph-compiler/graphflow_compiler/templates/pydantic_ai_agent.py.jinja`):
```python
def __init__(self, use_logging=True, execution_controller=None):
    self.execution_controller = execution_controller
    # ... existing init

async def run(self, inputs):
    self.memory.initialize_inputs(inputs)

    # Check if paused before start (debug mode)
    if self.execution_controller:
        await self.execution_controller.wait_if_paused('__start__')

    for step_id in execution_order:
        if self.execution_controller:
            await self.execution_controller.wait_if_paused(step_id)

        if hasattr(self.memory, 'set_current_step'):
            self.memory.set_current_step(step_id, step_label)

        await self._execute_{step_id}()

        if self.execution_controller:
            self.execution_controller.step_completed(step_id)

    return self.memory.get_all_outputs()
```

### 5. Backend: API Endpoints

**Extend routes** (`packages/graph-runtime/graphflow_runtime/api/routes.py`):

```python
# Enhanced run creation
@router.post("/agents/{agent_id}/runs")
async def create_run(
    agent_id: str,
    run_data: RunCreate,  # Now includes debug_mode: bool
    ...
)

# Debug control endpoints
@router.post("/agents/{agent_id}/runs/{run_id}/debug/pause")
@router.post("/agents/{agent_id}/runs/{run_id}/debug/resume")
@router.post("/agents/{agent_id}/runs/{run_id}/debug/step")

# Breakpoint management
@router.post("/agents/{agent_id}/runs/{run_id}/debug/breakpoints")
@router.delete("/agents/{agent_id}/runs/{run_id}/debug/breakpoints/{step_id}")

# Memory editing
@router.put("/agents/{agent_id}/runs/{run_id}/debug/memory")

# Debug state query
@router.get("/agents/{agent_id}/runs/{run_id}/debug/state")
```

### 6. Backend: WebSocket Support

**NEW: WebSocket handler** (`packages/graph-runtime/graphflow_runtime/api/websocket.py`):
- Endpoint: `WS /agents/{agent_id}/runs/{run_id}/debug`
- Real-time events:
  - `step_started`: `{type, step_id, timestamp, execution_count}`
  - `step_completed`: `{type, step_id, timestamp, execution_count}`
  - `paused`: `{type, step_id, reason: 'breakpoint'|'step'|'user'}`
  - `resumed`: `{type, timestamp}`
  - `breakpoint_added`: `{type, step_id}`
  - `breakpoint_removed`: `{type, step_id}`
  - `memory_updated`: `{type, namespace, key, value}`

### 7. Frontend: Type Definitions

**Update runtime types** (`packages/graph-builder/src/types/runtime.ts`):
```typescript
export interface AgentRun {
  // ... existing fields
  debug_mode?: boolean;
  current_step_id?: string;
  breakpoints?: string[];
  step_execution_counts?: Record<string, number>;
  debug_state?: 'before_start' | 'before_step' | 'after_step' | 'completed';
}

export interface DebugState {
  current_step_id?: string;
  breakpoints: string[];
  step_execution_counts: Record<string, number>;
  status: 'running' | 'paused' | 'completed';
  paused_reason?: 'breakpoint' | 'step' | 'user';
}

export interface DebugEvent {
  type: 'step_started' | 'step_completed' | 'paused' | 'resumed' | 'breakpoint_added' | 'breakpoint_removed' | 'memory_updated';
  step_id?: string;
  timestamp: string;
  execution_count?: number;
  reason?: 'breakpoint' | 'step' | 'user';
  namespace?: string;
  key?: string;
  value?: any;
}
```

### 8. Frontend: Run Input Dialog

**NEW: RunInputDialog** (`packages/graph-builder/src/components/runtime/RunInputDialog.tsx`):
- Modal dialog for run creation
- Dynamic input fields based on agent's memory.inputs schema
- Checkbox: "Enable debug mode" - starts paused before first step
- Validation before submission
- Triggered from AgentsList or RuntimeView

### 9. Frontend: Graph Debug View

**NEW: GraphDebugView** (`packages/graph-builder/src/components/runtime/GraphDebugView.tsx`):
- ReactFlow canvas showing graph from agent definition
- Visual node states:
  - **Breakpoint**: Red dot badge on node
  - **Current step**: Pulsing blue/yellow border
  - **Completed**: Green checkmark badge
  - **Execution count**: Badge showing "3x" if executed multiple times (for loops)
  - **Pending**: Gray/default state
- Click node to open NodeDebugPopup
- Control bar (top):
  - Status indicator: "Running" | "Paused at: [Step Name]" | "Completed"
  - Resume button (F8) - run to next breakpoint or end
  - Step button (F10) - execute one step
  - Pause button - pause running execution
  - Stop button - terminate run
- Real-time updates via WebSocket

### 10. Frontend: Node Debug Popup

**NEW: NodeDebugPopup** (`packages/graph-builder/src/components/runtime/NodeDebugPopup.tsx`):
- Floating modal positioned near clicked node
- Close on click outside or ESC key

**Tabs:**
1. **Config** - Step configuration (read-only)
   - Step type, label, description
   - All config parameters with values

2. **Memory** - Memory values for this step (editable when paused)
   - Inputs read by this step
   - Outputs written by this step
   - Edit button → allows changing values → Save/Cancel
   - Shows "(not executed yet)" if step hasn't run

3. **Status** - Execution status
   - State: Pending | Current | Completed
   - Execution count: "Executed 3 times" (for loops)
   - Timing: Duration if completed

4. **Breakpoint** - Breakpoint control
   - Toggle switch: "Break before this step"
   - Shows if breakpoint is active
   - Can toggle even while paused (dynamic)

### 11. Frontend: RunDetail Updates

**Modify RunDetail** (`packages/graph-builder/src/components/runtime/RunDetail.tsx`):
- Add 'graph' to tab options: `'details' | 'memory' | 'execution' | 'graph'`
- Show 'graph' tab when `run.debug_mode === true`
- Pass run, agentId, and debug state to GraphDebugView
- Auto-switch to 'graph' tab when debug run is created

### 12. Frontend: Services & Hooks

**Update runtime service** (`packages/graph-builder/src/services/runtime.ts`):
```typescript
// Debug control
export const pauseRun = (agentId: string, runId: string)
export const resumeRun = (agentId: string, runId: string)
export const stepRun = (agentId: string, runId: string)

// Breakpoints
export const setBreakpoint = (agentId: string, runId: string, stepId: string)
export const clearBreakpoint = (agentId: string, runId: string, stepId: string)

// Memory editing
export const updateMemory = (agentId: string, runId: string, namespace: string, key: string, value: any)

// Debug state
export const getDebugState = (agentId: string, runId: string)
```

**NEW: useDebugSocket hook** (`packages/graph-builder/src/hooks/useDebugSocket.ts`):
```typescript
export function useDebugSocket(agentId: string, runId: string) {
  return {
    connected: boolean,
    events: DebugEvent[],
    currentStep: string | null,
    status: 'running' | 'paused' | 'completed',
    error: Error | null,
  }
}
```

**Update useRuntime hook** (`packages/graph-builder/src/hooks/useRuntime.ts`):
- Add mutations: `usePauseRun()`, `useResumeRun()`, `useStepRun()`
- Add mutations: `useSetBreakpoint()`, `useClearBreakpoint()`
- Add mutation: `useUpdateMemory()`
- Add query: `useDebugState(agentId, runId)`

## Implementation Phases

### Phase 1: Backend Core (2-3 days)
1. Update database schema, create migration
2. Create ExecutionController class
3. Integrate controller into AsyncExecutor
4. Update code generation template
5. Test with simple graph (manual pause/resume)

### Phase 2: Backend API & WebSocket (1-2 days)
1. Add debug endpoints to routes
2. Implement WebSocket support
3. Connect controller events to WebSocket
4. Test API with Postman/curl

### Phase 3: Frontend Foundation (1-2 days)
1. Update runtime types
2. Create RunInputDialog component
3. Update runtime service with debug functions
4. Create useDebugSocket hook
5. Update useRuntime with debug mutations

### Phase 4: Graph Debug View (2-3 days)
1. Create GraphDebugView component
2. Load and render graph from agent definition
3. Add visual indicators (breakpoints, current step, counts)
4. Implement control bar with buttons
5. Connect to debug API and WebSocket
6. Add to RunDetail as new tab

### Phase 5: Node Debug Popup (2 days)
1. Create NodeDebugPopup component
2. Implement Config tab (read-only)
3. Implement Memory tab with editing
4. Implement Status tab with timing
5. Implement Breakpoint tab with toggle
6. Wire up to API for memory updates and breakpoints

### Phase 6: Integration & Testing (1-2 days)
1. Connect RunInputDialog to AgentsList/RuntimeView
2. Auto-switch to graph tab on debug run start
3. Test loop execution with counters
4. Test dynamic breakpoint management
5. Test memory editing and validation
6. Keyboard shortcuts (F8, F10, F9)

### Phase 7: Polish & Edge Cases (1 day)
1. Error handling and user feedback
2. Loading states and animations
3. WebSocket reconnection logic
4. Handle stopped/cancelled runs
5. Documentation and examples

## Technical Decisions

### Memory Editing
- Only editable when execution is paused
- Validate against memory schema before saving
- Show confirmation dialog for edits
- Log edits in execution log as special entries
- Reject edits to secrets namespace for security

### Breakpoint Behavior
- Always pause BEFORE step execution
- Dynamic add/remove updates controller immediately
- Breakpoints persist in database for inspection/debugging
- "Resume" runs until next breakpoint or completion
- "Step" ignores breakpoints, executes exactly one step

### Execution Count (Loop Support)
- Counter increments before each step execution
- Resets to {} when run starts
- Display as badge on nodes (e.g., "3x" if executed 3 times)
- Stored in database for post-run analysis

### Graph Rendering
- Load graph from `agent.graph_definition`
- Use ReactFlow for rendering (same as builder)
- Read-only - no editing in debug view
- Auto-layout if positions not specified
- Highlight current node with pulsing animation

### WebSocket & Polling
- WebSocket for real-time step events (low latency)
- Poll debug state every 500ms if WebSocket fails
- Poll memory state every 500ms when paused
- Stop polling when running or completed
- Graceful degradation for all features

### Debug State Machine
States:
1. `before_start` - Debug run created, paused before first step
2. `before_step` - Paused before a specific step (breakpoint or step command)
3. `after_step` - Step completed, about to proceed (transient)
4. `completed` - Execution finished

## Files to Create

### Backend
1. `packages/graph-runtime/graphflow_runtime/executor/execution_controller.py` (~200 lines)
2. `packages/graph-runtime/graphflow_runtime/api/websocket.py` (~250 lines)
3. Migration file for database schema changes (~30 lines)

### Frontend
1. `packages/graph-builder/src/components/runtime/RunInputDialog.tsx` (~150 lines)
2. `packages/graph-builder/src/components/runtime/GraphDebugView.tsx` (~400 lines)
3. `packages/graph-builder/src/components/runtime/NodeDebugPopup.tsx` (~350 lines)
4. `packages/graph-builder/src/hooks/useDebugSocket.ts` (~120 lines)

## Files to Modify

### Backend
1. `packages/graph-runtime/graphflow_runtime/storage/models.py` (+15 lines)
2. `packages/graph-runtime/graphflow_runtime/executor/async_executor.py` (+150 lines)
3. `packages/graph-runtime/graphflow_runtime/api/routes.py` (+200 lines)
4. `packages/graph-compiler/graphflow_compiler/templates/pydantic_ai_agent.py.jinja` (+25 lines)

### Frontend
1. `packages/graph-builder/src/types/runtime.ts` (+30 lines)
2. `packages/graph-builder/src/components/runtime/RunDetail.tsx` (+30 lines)
3. `packages/graph-builder/src/components/runtime/RunsList.tsx` (+20 lines)
4. `packages/graph-builder/src/components/runtime/AgentsList.tsx` (+15 lines)
5. `packages/graph-builder/src/services/runtime.ts` (+80 lines)
6. `packages/graph-builder/src/hooks/useRuntime.ts` (+100 lines)

## Estimated Effort
- **Backend**: 3-5 days
- **Frontend Core**: 3-5 days
- **Integration & Testing**: 2-3 days
- **Polish & Documentation**: 1 day
- **Total**: 9-14 days

## Success Criteria
- [ ] Can start a run in debug mode (paused before first step)
- [ ] Graph visualizes correctly with all nodes and edges
- [ ] Can set/remove breakpoints dynamically
- [ ] Step-through execution works correctly
- [ ] Memory inspector shows current state
- [ ] Can edit memory values while paused
- [ ] Node popup shows all required information
- [ ] Loop execution counts display correctly
- [ ] WebSocket provides real-time updates
- [ ] Keyboard shortcuts work (F8, F10, F9)
- [ ] Works correctly with graphs containing loops
- [ ] Handles errors and edge cases gracefully
