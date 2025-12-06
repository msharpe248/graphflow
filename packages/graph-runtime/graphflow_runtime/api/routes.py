"""API routes for GraphFlow Runtime."""

import uuid
from datetime import datetime
from typing import Optional, List, Any
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from graphflow_core.models import GraphDefinition, ToolDefinition
from graphflow_runtime.storage.models import Agent, AgentRun
from graphflow_runtime.executor.async_executor import AsyncExecutor
from graphflow_core.plugins.manager import PluginManager
from graphflow_core.steps.registry import StepRegistry

# Router
router = APIRouter()

# Pydantic models for API
class AgentCreate(BaseModel):
    """Request to create an agent."""
    name: str = Field(..., description="Agent name")
    description: Optional[str] = Field(None, description="Agent description")
    framework: str = Field("pydantic_ai", description="Framework (pydantic_ai or langgraph)")
    graph_definition: dict = Field(..., description="Graph definition as JSON")


class AgentResponse(BaseModel):
    """Agent response."""
    id: str
    name: str
    description: Optional[str]
    framework: str
    graph_definition: dict
    created_at: datetime
    updated_at: datetime


class RunCreate(BaseModel):
    """Request to start a run."""
    inputs: dict = Field(..., description="Input values for the agent")
    run_id: Optional[str] = Field(None, description="Optional custom run ID")
    session_id: Optional[str] = Field(None, description="Session ID for conversation history (auto-generated if not provided)")
    debug_mode: bool = Field(False, description="Enable debug mode")
    breakpoints: Optional[List[str]] = Field(None, description="Initial breakpoints (list of step IDs)")


class RunResponse(BaseModel):
    """Run response."""
    id: str
    agent_id: str
    session_id: Optional[str]
    status: str
    inputs: dict
    outputs: Optional[dict]
    error: Optional[str]
    execution_log: Optional[list]
    started_at: datetime
    completed_at: Optional[datetime]
    debug_mode: Optional[bool]
    current_step_id: Optional[str]
    breakpoints: Optional[list]
    step_execution_counts: Optional[dict]
    debug_state: Optional[str]


class MemoryResponse(BaseModel):
    """Memory state response."""
    inputs: dict
    outputs: dict
    intermediate: dict
    config: dict = {}
    environment: dict = {}
    secrets: dict = {}
    execution_log: list = []


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    active_runs: int


class StepTypeResponse(BaseModel):
    """Step type metadata response."""
    type: str
    plugin: str
    plugin_version: str
    label: str
    description: str
    category: str
    config_schema: dict
    inputs_schema: dict
    outputs_schema: dict
    ui_component: Optional[str]
    can_be_tool: bool = False
    tool_ineligible_reason: Optional[str] = None


class PluginResponse(BaseModel):
    """Plugin information response."""
    name: str
    version: str
    steps: List[str]
    ui_components: dict
    has_manifest: bool


# Dependency injection
executor: Optional[AsyncExecutor] = None
plugin_manager: Optional[PluginManager] = None

def get_executor() -> AsyncExecutor:
    """Get executor instance."""
    if executor is None:
        raise HTTPException(500, "Executor not initialized")
    return executor


def get_plugin_manager() -> PluginManager:
    """Get plugin manager instance."""
    if plugin_manager is None:
        raise HTTPException(500, "Plugin manager not initialized")
    return plugin_manager


def get_db() -> Session:
    """Get database session."""
    from graphflow_runtime.storage.database import SessionLocal
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Routes
@router.get("/health", response_model=HealthResponse)
async def health_check(exec: AsyncExecutor = Depends(get_executor)):
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "active_runs": len(exec.get_active_runs())
    }


@router.post("/agents", response_model=AgentResponse, status_code=201)
async def create_agent(
    agent_data: AgentCreate,
    db: Session = Depends(get_db)
):
    """Create a new agent."""
    # Validate graph definition
    try:
        graph = GraphDefinition(**agent_data.graph_definition)
        errors = graph.validate_graph_structure()
        if errors:
            raise HTTPException(400, f"Invalid graph: {', '.join(errors)}")
    except Exception as e:
        raise HTTPException(400, f"Invalid graph definition: {e}")

    # Create agent record
    agent_id = str(uuid.uuid4())
    agent = Agent(
        id=agent_id,
        name=agent_data.name,
        description=agent_data.description,
        framework=agent_data.framework,
        graph_definition=agent_data.graph_definition
    )

    db.add(agent)
    db.commit()
    db.refresh(agent)

    return agent


@router.get("/agents", response_model=List[AgentResponse])
async def list_agents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all agents."""
    agents = db.query(Agent).offset(skip).limit(limit).all()
    return agents


@router.get("/agents/{agent_id}", response_model=AgentResponse)
async def get_agent(agent_id: str, db: Session = Depends(get_db)):
    """Get agent by ID."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")
    return agent


@router.delete("/agents/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Delete an agent and all its runs."""
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")

    # Stop and cleanup all runs for this agent
    runs = db.query(AgentRun).filter(AgentRun.agent_id == agent_id).all()
    for run in runs:
        exec.stop_run(run.id)
        exec.release_memory(run.id)
        db.delete(run)  # Delete run from database

    db.delete(agent)
    db.commit()


@router.post("/agents/{agent_id}/runs", response_model=RunResponse, status_code=201)
async def start_run(
    agent_id: str,
    run_data: RunCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Start a new agent run."""
    # Get agent
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(404, f"Agent not found: {agent_id}")

    # Create run record
    run_id = run_data.run_id or str(uuid.uuid4())
    session_id = run_data.session_id or str(uuid.uuid4())
    run = AgentRun(
        id=run_id,
        agent_id=agent_id,
        session_id=session_id,
        status="running",
        inputs=run_data.inputs,
        debug_mode=run_data.debug_mode,
        breakpoints=run_data.breakpoints or [],
        step_execution_counts={},
        debug_state='before_start' if run_data.debug_mode else None
    )

    db.add(run)
    db.commit()
    db.refresh(run)

    # Parse graph
    graph = GraphDefinition(**agent.graph_definition)

    # Define completion callback
    async def on_complete(run_id: str, outputs: dict, execution_log: list = None):
        db_session = next(get_db())
        try:
            run_record = db_session.query(AgentRun).filter(AgentRun.id == run_id).first()
            if run_record:
                run_record.status = "completed"
                run_record.outputs = outputs
                run_record.execution_log = execution_log or []
                run_record.completed_at = datetime.utcnow()
                db_session.commit()
        finally:
            db_session.close()

    # Define error callback
    async def on_error(run_id: str, error: str, execution_log: list = None):
        db_session = next(get_db())
        try:
            run_record = db_session.query(AgentRun).filter(AgentRun.id == run_id).first()
            if run_record:
                run_record.status = "failed"
                run_record.error = error
                run_record.execution_log = execution_log or []
                run_record.completed_at = datetime.utcnow()
                db_session.commit()
        finally:
            db_session.close()

    # Start execution in background
    background_tasks.add_task(
        exec.compile_and_run,
        run_id=run_id,
        graph=graph,
        inputs=run_data.inputs,
        framework=agent.framework,
        session_id=session_id,
        debug_mode=run_data.debug_mode,
        breakpoints=run_data.breakpoints,
        on_complete=on_complete,
        on_error=on_error
    )

    return run


@router.get("/agents/{agent_id}/runs", response_model=List[RunResponse])
async def list_runs(
    agent_id: str,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List runs for an agent."""
    runs = (
        db.query(AgentRun)
        .filter(AgentRun.agent_id == agent_id)
        .order_by(AgentRun.started_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return runs


@router.get("/agents/{agent_id}/runs/{run_id}", response_model=RunResponse)
async def get_run(
    agent_id: str,
    run_id: str,
    db: Session = Depends(get_db)
):
    """Get run status."""
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")
    return run


@router.post("/agents/{agent_id}/runs/{run_id}/stop", status_code=204)
async def stop_run(
    agent_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Stop a running agent."""
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    if run.status != "running":
        raise HTTPException(400, f"Run is not running (status: {run.status})")

    # Stop execution
    if exec.stop_run(run_id):
        run.status = "stopped"
        run.completed_at = datetime.utcnow()
        db.commit()


@router.delete("/agents/{agent_id}/runs/{run_id}", status_code=204)
async def delete_run(
    agent_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Delete a run and release its memory."""
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    # Release memory
    exec.release_memory(run_id)

    # Delete from database
    db.delete(run)
    db.commit()


@router.get("/agents/{agent_id}/runs/{run_id}/memory", response_model=MemoryResponse)
async def get_memory(
    agent_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Get memory state for a run."""
    # Verify run exists
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    # Get memory store and state
    memory = exec.get_memory(run_id)
    if memory is None:
        raise HTTPException(404, f"Memory not available (run may have completed or been released)")

    memory_state = memory.to_dict()

    # Get execution log if available (LoggingMemoryStore has get_log method)
    execution_log = []
    if hasattr(memory, 'get_log'):
        execution_log = memory.get_log()

    # Flatten the nested structure from to_dict()
    # to_dict() returns: {"memory": {"inputs": ..., "outputs": ..., "intermediate": ...}, "config": ..., "environment": ..., "secrets": ...}
    # API expects: {"inputs": ..., "outputs": ..., "intermediate": ..., "config": ..., "environment": ..., "secrets": ..., "execution_log": ...}
    flattened = {
        "inputs": memory_state.get("memory", {}).get("inputs", {}),
        "outputs": memory_state.get("memory", {}).get("outputs", {}),
        "intermediate": memory_state.get("memory", {}).get("intermediate", {}),
        "config": memory_state.get("config", {}),
        "environment": memory_state.get("environment", {}),
        "secrets": memory_state.get("secrets", {}),
        "execution_log": execution_log,
    }

    return flattened


@router.get("/agents/{agent_id}/runs/{run_id}/memory/{key}")
async def get_memory_key(
    agent_id: str,
    run_id: str,
    key: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Get specific memory value."""
    # Verify run exists
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    # Get memory
    memory = exec.get_memory(run_id)
    if memory is None:
        raise HTTPException(404, f"Memory not available")

    # Read key
    try:
        value = memory.read(key)
        return {"key": key, "value": value}
    except KeyError:
        raise HTTPException(404, f"Memory key not found: {key}")


@router.get("/steps", response_model=List[StepTypeResponse])
async def list_step_types(pm: PluginManager = Depends(get_plugin_manager)):
    """
    List all available step types.

    Returns metadata for all registered step types including those from plugins.
    Each step type includes its configuration schema and optional custom UI component path.
    """
    all_steps = pm.get_all_steps()
    return list(all_steps.values())


@router.get("/plugins", response_model=List[PluginResponse])
async def list_plugins(pm: PluginManager = Depends(get_plugin_manager)):
    """
    List all loaded plugins.

    Returns information about all discovered and loaded plugins including
    their version, provided step types, and custom UI components.
    """
    return pm.get_plugin_info_dict()


# Debug endpoints

class DebugStateResponse(BaseModel):
    """Debug state response."""
    current_step_id: Optional[str]
    breakpoints: List[str]
    step_execution_counts: dict
    status: str


class BreakpointRequest(BaseModel):
    """Request to set a breakpoint."""
    step_id: str = Field(..., description="Step ID to break on")


class MemoryUpdateRequest(BaseModel):
    """Request to update memory value."""
    namespace: str = Field(..., description="Memory namespace")
    key: str = Field(..., description="Memory key")
    value: Any = Field(..., description="New value")


@router.post("/agents/{agent_id}/runs/{run_id}/debug/pause", status_code=204)
async def pause_debug_run(
    agent_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Pause a running debug session."""
    # Verify run exists and is in debug mode
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    if not run.debug_mode:
        raise HTTPException(400, "Run is not in debug mode")

    # Pause execution
    if not await exec.pause_run(run_id):
        raise HTTPException(400, "Could not pause run (already paused or stopped)")


@router.post("/agents/{agent_id}/runs/{run_id}/debug/resume", status_code=204)
async def resume_debug_run(
    agent_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Resume a paused debug session."""
    # Verify run exists and is in debug mode
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    if not run.debug_mode:
        raise HTTPException(400, "Run is not in debug mode")

    # Resume execution
    if not await exec.resume_run(run_id):
        raise HTTPException(400, "Could not resume run (not paused)")


@router.post("/agents/{agent_id}/runs/{run_id}/debug/step", status_code=204)
async def step_debug_run(
    agent_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Execute one step in debug session."""
    # Verify run exists and is in debug mode
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    if not run.debug_mode:
        raise HTTPException(400, "Run is not in debug mode")

    # Step execution
    if not await exec.step_run(run_id):
        raise HTTPException(400, "Could not step run")


@router.post("/agents/{agent_id}/runs/{run_id}/debug/breakpoints", status_code=204)
async def set_breakpoint(
    agent_id: str,
    run_id: str,
    breakpoint_data: BreakpointRequest,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Set a breakpoint on a step."""
    # Verify run exists and is in debug mode
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    if not run.debug_mode:
        raise HTTPException(400, "Run is not in debug mode")

    # Set breakpoint
    if await exec.set_breakpoint(run_id, breakpoint_data.step_id):
        # Update database
        if run.breakpoints is None:
            run.breakpoints = []
        if breakpoint_data.step_id not in run.breakpoints:
            run.breakpoints.append(breakpoint_data.step_id)
            db.commit()
    else:
        raise HTTPException(400, "Could not set breakpoint (run not found)")


@router.delete("/agents/{agent_id}/runs/{run_id}/debug/breakpoints/{step_id}", status_code=204)
async def clear_breakpoint(
    agent_id: str,
    run_id: str,
    step_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Remove a breakpoint from a step."""
    # Verify run exists and is in debug mode
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    if not run.debug_mode:
        raise HTTPException(400, "Run is not in debug mode")

    # Clear breakpoint
    if await exec.clear_breakpoint(run_id, step_id):
        # Update database
        if run.breakpoints and step_id in run.breakpoints:
            run.breakpoints.remove(step_id)
            db.commit()


@router.put("/agents/{agent_id}/runs/{run_id}/debug/memory", status_code=204)
async def update_memory(
    agent_id: str,
    run_id: str,
    memory_data: MemoryUpdateRequest,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Update a memory value while paused."""
    # Verify run exists and is in debug mode
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    if not run.debug_mode:
        raise HTTPException(400, "Run is not in debug mode")

    # Update memory
    if not exec.update_memory_value(run_id, memory_data.namespace, memory_data.key, memory_data.value):
        raise HTTPException(400, "Could not update memory (not paused, invalid namespace, or run not found)")


@router.get("/agents/{agent_id}/runs/{run_id}/debug/state", response_model=DebugStateResponse)
async def get_debug_state(
    agent_id: str,
    run_id: str,
    db: Session = Depends(get_db),
    exec: AsyncExecutor = Depends(get_executor)
):
    """Get current debug state."""
    # Verify run exists and is in debug mode
    run = (
        db.query(AgentRun)
        .filter(AgentRun.id == run_id, AgentRun.agent_id == agent_id)
        .first()
    )
    if not run:
        raise HTTPException(404, f"Run not found: {run_id}")

    if not run.debug_mode:
        raise HTTPException(400, "Run is not in debug mode")

    # Get debug state
    state = exec.get_debug_state(run_id)
    if state is None:
        raise HTTPException(404, "Debug state not available (run may have completed)")

    return state


# Tool endpoints

class ToolValidationResponse(BaseModel):
    """Response from tool validation."""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []


@router.post("/tools/validate", response_model=ToolValidationResponse)
async def validate_tool(
    tool: ToolDefinition,
    pm: PluginManager = Depends(get_plugin_manager)
):
    """
    Validate a tool definition.

    Checks:
    - Source step exists and is tool-eligible
    - All required properties are mapped
    - Memory bindings are valid syntax
    - LLM parameters have valid schemas
    """
    errors = []
    warnings = []

    # Check source step exists
    all_steps = pm.get_all_steps()
    if tool.source_step_type not in all_steps:
        errors.append(f"Source step type '{tool.source_step_type}' not found")
        return ToolValidationResponse(valid=False, errors=errors)

    step_metadata = all_steps[tool.source_step_type]

    # Check step is tool-eligible
    if not step_metadata.get("can_be_tool", False):
        reason = step_metadata.get("tool_ineligible_reason", "This step cannot be used as a tool")
        errors.append(f"Step '{tool.source_step_type}' is not tool-eligible: {reason}")
        return ToolValidationResponse(valid=False, errors=errors)

    # Get step's config schema
    config_schema = step_metadata.get("config_schema", {})
    schema_properties = config_schema.get("properties", {})
    required_properties = set(config_schema.get("required", []))

    # Check property mappings
    mapped_properties = set()
    for mapping in tool.property_mappings:
        mapped_properties.add(mapping.source_property)

        # Validate property exists in step schema
        if mapping.source_property not in schema_properties:
            warnings.append(
                f"Property '{mapping.source_property}' not found in step schema "
                f"(may be a dynamic property)"
            )

        # Validate runtime value syntax
        if mapping.visibility == "runtime":
            if mapping.runtime_value:
                # Check for valid memory binding syntax
                if mapping.runtime_value.startswith("{") and not mapping.runtime_value.startswith("{memory."):
                    if not any(mapping.runtime_value.startswith(f"{{{ns}.") for ns in ["config", "env", "secrets"]):
                        warnings.append(
                            f"Property '{mapping.source_property}' has unusual binding syntax: "
                            f"{mapping.runtime_value}"
                        )
            else:
                errors.append(
                    f"Runtime property '{mapping.source_property}' has no value specified"
                )

        # Validate LLM parameter
        if mapping.visibility == "llm":
            if not mapping.llm_description:
                warnings.append(
                    f"LLM parameter '{mapping.source_property}' has no description "
                    f"(recommended for better LLM understanding)"
                )

    # Check for unmapped required properties
    unmapped_required = required_properties - mapped_properties
    if unmapped_required:
        errors.append(
            f"Required properties not mapped: {', '.join(sorted(unmapped_required))}"
        )

    # Validate tool has at least one LLM parameter
    llm_params = [m for m in tool.property_mappings if m.visibility == "llm"]
    if not llm_params:
        warnings.append(
            "Tool has no LLM-controlled parameters. "
            "Consider if this tool needs any input from the LLM."
        )

    return ToolValidationResponse(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


@router.get("/steps/{step_type}/schema")
async def get_step_schema(
    step_type: str,
    pm: PluginManager = Depends(get_plugin_manager)
):
    """
    Get detailed schema for a specific step type.

    Useful for building tool property mappings - returns the full
    config schema so the UI can show available properties.
    """
    all_steps = pm.get_all_steps()

    if step_type not in all_steps:
        raise HTTPException(404, f"Step type '{step_type}' not found")

    step_metadata = all_steps[step_type]

    return {
        "type": step_type,
        "config_schema": step_metadata.get("config_schema", {}),
        "inputs_schema": step_metadata.get("inputs_schema", {}),
        "outputs_schema": step_metadata.get("outputs_schema", {}),
        "can_be_tool": step_metadata.get("can_be_tool", False),
        "tool_ineligible_reason": step_metadata.get("tool_ineligible_reason"),
    }


# =============================================================================
# MCP (Model Context Protocol) Endpoints
# =============================================================================


class MCPDiscoverRequest(BaseModel):
    """Request to discover tools from an MCP server."""
    transport: str = Field(..., description="Transport type: 'stdio', 'sse', or 'streamable_http'")
    command: Optional[str] = Field(None, description="Command for stdio transport")
    args: Optional[List[str]] = Field(None, description="Arguments for stdio command")
    env: Optional[dict] = Field(None, description="Environment variables for stdio")
    url: Optional[str] = Field(None, description="URL for SSE/streamable_http transport")
    headers: Optional[dict] = Field(None, description="HTTP headers for SSE/streamable_http")
    timeout: float = Field(10.0, description="Discovery timeout in seconds")


class MCPToolInfo(BaseModel):
    """Information about an MCP tool."""
    name: str
    description: str
    input_schema: dict


class MCPDiscoverResponse(BaseModel):
    """Response from MCP tool discovery."""
    success: bool
    server_info: dict = {}
    tools: List[MCPToolInfo] = []
    error: Optional[str] = None


@router.post("/mcp/discover", response_model=MCPDiscoverResponse)
async def discover_mcp_tools(request: MCPDiscoverRequest):
    """
    Connect to an MCP server and discover available tools.

    This endpoint connects to the specified MCP server, lists its tools,
    and returns the tool definitions with their input schemas.

    Supports three transport types:
    - stdio: Local process communication
    - sse: Server-Sent Events over HTTP
    - streamable_http: Streamable HTTP transport

    Example request for stdio:
    ```json
    {
        "transport": "stdio",
        "command": "uvx",
        "args": ["mcp-server-fetch"],
        "timeout": 10
    }
    ```

    Example request for SSE:
    ```json
    {
        "transport": "sse",
        "url": "http://localhost:8080/mcp",
        "timeout": 10
    }
    ```
    """
    try:
        from graphflow_core.models.tool import MCPServerConfig
        from graphflow_ai.mcp_client import discover_mcp_tools as do_discover

        # Build server config
        config = MCPServerConfig(
            transport=request.transport,
            command=request.command,
            args=request.args,
            env=request.env,
            url=request.url,
            headers=request.headers,
            timeout=request.timeout,
        )

        # Discover tools
        result = await do_discover(config)

        # Convert to response format
        tools = [
            MCPToolInfo(
                name=t["name"],
                description=t.get("description", ""),
                input_schema=t.get("input_schema", {}),
            )
            for t in result.get("tools", [])
        ]

        return MCPDiscoverResponse(
            success=result.get("success", False),
            server_info=result.get("server_info", {}),
            tools=tools,
            error=result.get("error"),
        )

    except ImportError as e:
        return MCPDiscoverResponse(
            success=False,
            error=f"MCP support not available: {str(e)}. Install with: pip install pydantic-ai[mcp]",
        )
    except Exception as e:
        return MCPDiscoverResponse(
            success=False,
            error=f"Discovery failed: {type(e).__name__}: {str(e)}",
        )


# =============================================================================
# Session Management Endpoints
# =============================================================================


class SessionListResponse(BaseModel):
    """Response for listing sessions."""
    sessions: List[str]


class SessionDeleteResponse(BaseModel):
    """Response for deleting a session."""
    deleted: bool
    session_id: str


@router.get("/sessions", response_model=SessionListResponse)
async def list_sessions():
    """
    List all active sessions.

    Returns a list of session IDs that have conversation history stored.
    Sessions are ephemeral and cleared on runtime restart.
    """
    from graphflow_runtime.session import list_sessions as get_sessions
    return SessionListResponse(sessions=get_sessions())


@router.delete("/sessions/{session_id}", response_model=SessionDeleteResponse)
async def delete_session(session_id: str):
    """
    Delete a session and all its conversation history.

    This clears all LLM step history associated with the given session ID.
    """
    from graphflow_runtime.session import clear_session
    deleted = clear_session(session_id)
    return SessionDeleteResponse(deleted=deleted, session_id=session_id)


class SessionHistoryResponse(BaseModel):
    """Response for session history."""
    session_id: str
    history: dict  # step_id -> list of messages


@router.get("/sessions/{session_id}/history", response_model=SessionHistoryResponse)
async def get_session_history_endpoint(session_id: str):
    """
    Get all conversation history for a session.

    Returns the history for all LLM steps in the session, organized by step ID.
    Each step's history contains the messages exchanged with the LLM.
    """
    from graphflow_runtime.session import get_session_history, session_exists

    if not session_exists(session_id):
        raise HTTPException(404, f"Session not found: {session_id}")

    history = get_session_history(session_id)
    return SessionHistoryResponse(session_id=session_id, history=history)
