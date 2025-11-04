"""API routes for GraphFlow Runtime."""

import uuid
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from graphflow_core.models import GraphDefinition
from graphflow_runtime.storage.models import Agent, AgentRun
from graphflow_runtime.executor.async_executor import AsyncExecutor
from graphflow_core.plugins.manager import PluginManager

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


class RunResponse(BaseModel):
    """Run response."""
    id: str
    agent_id: str
    status: str
    inputs: dict
    outputs: Optional[dict]
    error: Optional[str]
    execution_log: Optional[list]
    started_at: datetime
    completed_at: Optional[datetime]


class MemoryResponse(BaseModel):
    """Memory state response."""
    inputs: dict
    outputs: dict
    intermediate: dict


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
    run = AgentRun(
        id=run_id,
        agent_id=agent_id,
        status="running",
        inputs=run_data.inputs
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
    async def on_error(run_id: str, error: str):
        db_session = next(get_db())
        try:
            run_record = db_session.query(AgentRun).filter(AgentRun.id == run_id).first()
            if run_record:
                run_record.status = "failed"
                run_record.error = error
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

    # Get memory state
    memory_state = exec.get_memory_state(run_id)
    if memory_state is None:
        raise HTTPException(404, f"Memory not available (run may have completed or been released)")

    return memory_state


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
