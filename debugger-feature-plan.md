# Debugger Feature - Implementation Plan

## Overview
Add a comprehensive debugging system with breakpoints, step-through execution, and real-time memory inspection. The debugger will integrate into the runtime view as a new tab and enhance the execution engine to support pause/resume/step control.

## Architecture Components

### 1. **Backend: Execution Control System**

**1.1 ExecutionController** (NEW: `packages/graph-runtime/graphflow_runtime/executor/execution_controller.py`)
- Manage execution state per run: `running`, `paused`, `stepping`, `stopped`
- Track current step being executed
- Store breakpoints (set of step IDs)
- Command queue for pause/resume/step operations
- Thread-safe async communication between API and executor

**1.2 Enhanced AsyncExecutor** (`packages/graph-runtime/graphflow_runtime/executor/async_executor.py`)
- Add `execution_controllers: Dict[str, ExecutionController]`
- New method: `set_breakpoint(run_id, step_id)`
- New method: `clear_breakpoint(run_id, step_id)`
- New method: `pause_execution(run_id)`
- New method: `resume_execution(run_id)`
- New method: `step_execution(run_id)` - execute next step then pause
- Modify `_execute_agent()` to check controller between steps

**1.3 Modified Code Generation** (`packages/graph-compiler/graphflow_compiler/templates/pydantic_ai_agent.py.jinja`)
- Add optional `execution_controller` parameter to `GeneratedAgent.__init__()`
- Before each step execution, check if controller signals pause
- If paused, wait on async event until resume/step signal
- After each step, update controller with current position
- Example structure:
```python
async def run(self, inputs):
    for step_id in execution_order:
        if self.execution_controller:
            await self.execution_controller.wait_if_paused(step_id)
        await self._execute_{step_id}()
        if self.execution_controller:
            self.execution_controller.step_completed(step_id)
```

**1.4 Database Schema Update** (`packages/graph-runtime/graphflow_runtime/storage/models.py`)
- Add to `AgentRun` model:
  - `current_step_id: str` (nullable) - which step is executing/paused
  - `debug_mode: bool` - whether run started in debug mode
  - `breakpoints: JSON` - array of step IDs with breakpoints

### 2. **Backend: API Enhancements**

**2.1 New REST Endpoints** (`packages/graph-runtime/graphflow_runtime/api/routes.py`)
- `POST /agents/{agent_id}/runs` - add `debug_mode: bool` parameter
- `POST /agents/{agent_id}/runs/{run_id}/pause` - pause execution
- `POST /agents/{agent_id}/runs/{run_id}/resume` - resume execution
- `POST /agents/{agent_id}/runs/{run_id}/step` - execute one step
- `POST /agents/{agent_id}/runs/{run_id}/breakpoints` - set breakpoint
- `DELETE /agents/{agent_id}/runs/{run_id}/breakpoints/{step_id}` - clear breakpoint
- `GET /agents/{agent_id}/runs/{run_id}/debug-state` - get current execution position + breakpoints

**2.2 WebSocket Support** (NEW: `packages/graph-runtime/graphflow_runtime/api/websocket.py`)
- Real-time notifications for:
  - Step started: `{type: 'step_started', step_id, timestamp}`
  - Step completed: `{type: 'step_completed', step_id, timestamp}`
  - Paused at breakpoint: `{type: 'paused', step_id, reason: 'breakpoint'}`
  - Execution resumed: `{type: 'resumed'}`
- WebSocket endpoint: `WS /agents/{agent_id}/runs/{run_id}/debug`
- Connect controller events to WebSocket broadcasts

### 3. **Frontend: Debugger UI Tab**

**3.1 New DebuggerTab Component** (NEW: `packages/graph-builder/src/components/runtime/DebuggerTab.tsx`)
- **Step List View**:
  - Show all steps in execution order
  - Highlight current step (if paused)
  - Click step to toggle breakpoint (red dot indicator)
  - Show step status: pending, completed, current, failed

- **Control Bar**:
  - Play/Pause button (pause running execution)
  - Step button (execute next step)
  - Continue button (run to next breakpoint or end)
  - Stop button (terminate execution)
  - Reset button (clear all breakpoints)

- **Memory Inspector**:
  - Live view of current memory state
  - Separate sections for inputs, outputs, intermediate, secrets
  - Highlight values that changed in last step
  - Search/filter capabilities
  - JSON tree view for complex objects

- **Execution Position Indicator**:
  - Show "Paused at: [Step Name]"
  - Display "before execution" or "after execution" state
  - Step timing information

**3.2 Updated RunDetail Component** (`packages/graph-builder/src/components/runtime/RunDetail.tsx`)
- Add 'debugger' to tab options: `'details' | 'memory' | 'execution' | 'debugger'`
- Show debugger tab when `run.debug_mode === true` or always available
- Pass run data to DebuggerTab component

**3.3 Enhanced RuntimeView** (`packages/graph-builder/src/components/runtime/RuntimeView.tsx`)
- Add "Debug" button next to "Run" button in UI
- Clicking "Debug" starts run with `debug_mode: true` and `paused: true`
- Run starts paused before first step
- Automatically switch to debugger tab when debug run created

### 4. **Frontend: Services & Hooks**

**4.1 Runtime Service Updates** (`packages/graph-builder/src/services/runtime.ts`)
- Add functions:
  - `pauseRun(agentId, runId)`
  - `resumeRun(agentId, runId)`
  - `stepRun(agentId, runId)`
  - `setBreakpoint(agentId, runId, stepId)`
  - `clearBreakpoint(agentId, runId, stepId)`
  - `getDebugState(agentId, runId)`

**4.2 New WebSocket Hook** (NEW: `packages/graph-builder/src/hooks/useDebugSocket.ts`)
- Custom hook: `useDebugSocket(agentId, runId)`
- Manages WebSocket connection lifecycle
- Returns: `{connected, currentStep, status, events}`
- Automatically reconnects on disconnect
- Cleans up on unmount

**4.3 Enhanced useRuntime Hook** (`packages/graph-builder/src/hooks/useRuntime.ts`)
- Add mutations:
  - `usePauseRun()`
  - `useResumeRun()`
  - `useStepRun()`
  - `useSetBreakpoint()`
  - `useClearBreakpoint()`
- Add query: `useDebugState(agentId, runId)`
- Invalidate queries on debug state changes

### 5. **Frontend: Graph Integration** (Optional Enhancement)

**5.1 Graph Canvas Updates** (`packages/graph-builder/src/components/GraphCanvas.tsx`)
- Add visual indicators to nodes:
  - Breakpoint marker (red dot on node)
  - Current step highlight (yellow/blue border)
  - Completed step checkmark
- Click node header to toggle breakpoint when in debug mode
- Sync breakpoint state with debugger tab

## Implementation Phases

### Phase 1: Core Execution Control (Backend)
1. Create `ExecutionController` class with pause/resume/step logic
2. Update `AsyncExecutor` to integrate controller
3. Modify code generation template to check controller between steps
4. Add database fields for debug state
5. Test with simple graph that pauses/resumes correctly

### Phase 2: API & WebSocket (Backend)
1. Add REST endpoints for debug control
2. Implement WebSocket support for real-time updates
3. Connect controller events to WebSocket broadcasts
4. Add breakpoint storage and checking
5. Test API with curl/Postman

### Phase 3: Debugger Tab UI (Frontend)
1. Create DebuggerTab component with step list
2. Add control buttons (pause/resume/step/stop)
3. Implement memory inspector view
4. Add breakpoint toggle functionality
5. Style with current UI theme

### Phase 4: WebSocket Integration (Frontend)
1. Create useDebugSocket hook
2. Connect WebSocket to DebuggerTab
3. Update UI in real-time as steps execute
4. Handle reconnection and errors
5. Test with real execution

### Phase 5: Graph Canvas Integration (Frontend)
1. Add breakpoint indicators to graph nodes
2. Highlight current step in graph
3. Sync breakpoint state between graph and debugger tab
4. Add click handlers to toggle breakpoints
5. Visual polish and animations

### Phase 6: Polish & Testing
1. Add "Debug" button to start runs in debug mode
2. Keyboard shortcuts (F5=continue, F10=step, F9=toggle breakpoint)
3. Persist breakpoints across sessions (localStorage)
4. Error handling and edge cases
5. End-to-end testing with complex graphs
6. Documentation and examples

## Technical Decisions & Considerations

**Before/After Step State**:
- Initially pause BEFORE step execution
- After step, pause AFTER execution (memory updated)
- This allows inspecting both pre and post state
- Implementation: two pause points per step in generated code

**Breakpoint Behavior**:
- Breakpoints pause BEFORE step execution
- If stepping through, next step pauses regardless of breakpoints
- "Continue" runs until breakpoint or completion
- Breakpoints persist across pause/resume within same run

**Memory Inspection**:
- Show live memory state from `AsyncExecutor.get_memory_state(run_id)`
- Poll every 500ms when paused, no polling when running
- Highlight changed values by comparing with previous snapshot
- Handle secrets carefully (show masked or require reveal)

**WebSocket vs Polling**:
- WebSocket for step-level events (low latency needed)
- Still use polling for memory state (simpler, less data)
- Fallback to polling if WebSocket unavailable
- WebSocket reconnection with exponential backoff

**Debug Mode Restrictions**:
- Debug mode only available for single-agent graphs initially
- Complex multi-agent orchestrations could be phase 2
- Long-running steps (LLM calls) can't be interrupted mid-step
- Timeout handling: paused runs don't timeout

## Files to Create
1. `packages/graph-runtime/graphflow_runtime/executor/execution_controller.py` (~150 lines)
2. `packages/graph-runtime/graphflow_runtime/api/websocket.py` (~200 lines)
3. `packages/graph-builder/src/components/runtime/DebuggerTab.tsx` (~400 lines)
4. `packages/graph-builder/src/hooks/useDebugSocket.ts` (~100 lines)
5. `packages/graph-builder/src/components/runtime/MemoryInspector.tsx` (~200 lines)

## Files to Modify
1. `packages/graph-runtime/graphflow_runtime/executor/async_executor.py` (+100 lines)
2. `packages/graph-runtime/graphflow_runtime/storage/models.py` (+10 lines)
3. `packages/graph-runtime/graphflow_runtime/api/routes.py` (+150 lines)
4. `packages/graph-compiler/graphflow_compiler/templates/pydantic_ai_agent.py.jinja` (+30 lines)
5. `packages/graph-builder/src/components/runtime/RunDetail.tsx` (+50 lines)
6. `packages/graph-builder/src/components/runtime/RuntimeView.tsx` (+30 lines)
7. `packages/graph-builder/src/services/runtime.ts` (+60 lines)
8. `packages/graph-builder/src/hooks/useRuntime.ts` (+80 lines)

## Estimated Effort
- **Backend**: 2-3 days
- **Frontend Core**: 2-3 days
- **Integration & Testing**: 1-2 days
- **Polish & Documentation**: 1 day
- **Total**: 6-9 days
