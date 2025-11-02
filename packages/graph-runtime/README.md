# graphflow-runtime

Runtime manager for GraphFlow agents - FastAPI service for executing and managing agents.

## Features

- **Agent Management**: Upload and manage agent definitions
- **Execution Engine**: Run agents with async background execution
- **Memory Inspection**: Query memory state during execution
- **Lifecycle Management**: Start, stop, and monitor agent runs
- **REST API**: Complete API for all operations
- **Auto-compilation**: Compile graphs on-the-fly or use pre-compiled agents

## Installation

```bash
pip install -e .
```

## Quick Start

### Start the Server

```bash
# Start on default port (8000)
graphflow-runtime

# Start on custom port
graphflow-runtime --port 9000

# Development mode with auto-reload
graphflow-runtime --reload
```

### API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Agent Management
- `POST /api/v1/agents` - Create new agent
- `GET /api/v1/agents` - List all agents
- `GET /api/v1/agents/{agent_id}` - Get agent details
- `DELETE /api/v1/agents/{agent_id}` - Delete agent

### Execution
- `POST /api/v1/agents/{agent_id}/runs` - Start new run
- `GET /api/v1/agents/{agent_id}/runs` - List runs
- `GET /api/v1/agents/{agent_id}/runs/{run_id}` - Get run status
- `POST /api/v1/agents/{agent_id}/runs/{run_id}/stop` - Stop running agent
- `DELETE /api/v1/agents/{agent_id}/runs/{run_id}` - Delete run

### Memory Inspection
- `GET /api/v1/agents/{agent_id}/runs/{run_id}/memory` - Get memory state
- `GET /api/v1/agents/{agent_id}/runs/{run_id}/memory/{key}` - Get specific value

### Health
- `GET /api/v1/health` - Health check

## Example Usage

### Create and Run an Agent

```python
import requests

# Create agent
response = requests.post("http://localhost:8000/api/v1/agents", json={
    "name": "My Agent",
    "framework": "pydantic_ai",
    "graph_definition": {
        # Graph definition JSON
    }
})
agent_id = response.json()["id"]

# Start run
response = requests.post(
    f"http://localhost:8000/api/v1/agents/{agent_id}/runs",
    json={"inputs": {"user_question": "Hello"}}
)
run_id = response.json()["id"]

# Check status
response = requests.get(
    f"http://localhost:8000/api/v1/agents/{agent_id}/runs/{run_id}"
)
print(response.json())

# Get memory state
response = requests.get(
    f"http://localhost:8000/api/v1/agents/{agent_id}/runs/{run_id}/memory"
)
print(response.json())
```

## Architecture

- **FastAPI**: Modern async web framework
- **SQLAlchemy**: Database ORM for agent/run persistence
- **AsyncExecutor**: Background task execution
- **Dynamic Compilation**: Compile graphs to Python on-the-fly

## Development

Run tests:
```bash
pytest
```

Run with auto-reload:
```bash
graphflow-runtime --reload
```
