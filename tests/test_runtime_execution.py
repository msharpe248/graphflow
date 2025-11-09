"""
Test multi-graph runtime execution.

This module tests:
1. Runtime server startup
2. Agent CRUD operations
3. Running agents in the runtime
4. Memory inspection
5. Multiple concurrent agents
"""

import json
import subprocess
import time
import requests
import pytest
from pathlib import Path
import asyncio


# Fixtures
@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def simple_graph(fixtures_dir):
    """Load simple transform graph."""
    with open(fixtures_dir / "simple_transform_graph.json") as f:
        return json.load(f)


@pytest.fixture
def llm_graph(fixtures_dir):
    """Load LLM agent graph."""
    with open(fixtures_dir / "llm_agent_graph.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def runtime_server():
    """Start runtime server for tests."""
    port = 18700  # Use non-standard port

    # Start runtime server
    process = subprocess.Popen(
        ["graphflow-runtime", "--port", str(port)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to start
    base_url = f"http://localhost:{port}"
    server_ready = False
    for _ in range(30):  # 30 seconds max
        time.sleep(1)
        try:
            response = requests.get(f"{base_url}/api/v1/health", timeout=2)
            if response.status_code == 200:
                server_ready = True
                break
        except requests.exceptions.RequestException:
            pass

    if not server_ready:
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        pytest.fail(f"Runtime server failed to start. stdout: {stdout}, stderr: {stderr}")

    yield {"process": process, "port": port, "base_url": base_url}

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


# Test: Server Health
class TestRuntimeServerHealth:
    """Test runtime server health and basic endpoints."""

    def test_health_endpoint(self, runtime_server):
        """Test runtime health endpoint."""
        base_url = runtime_server["base_url"]

        response = requests.get(f"{base_url}/api/v1/health", timeout=5)
        assert response.status_code == 200

    def test_root_endpoint(self, runtime_server):
        """Test root endpoint returns API info."""
        base_url = runtime_server["base_url"]

        response = requests.get(f"{base_url}/", timeout=5)
        assert response.status_code in [200, 404]  # Depends on implementation

    def test_docs_endpoint(self, runtime_server):
        """Test OpenAPI docs endpoint."""
        base_url = runtime_server["base_url"]

        response = requests.get(f"{base_url}/docs", timeout=5)
        assert response.status_code in [200, 307]  # Redirect or direct access


# Test: Agent CRUD Operations
class TestAgentCRUD:
    """Test agent creation, reading, updating, and deletion."""

    def test_create_agent_pydantic_ai(self, runtime_server, simple_graph):
        """Test creating an agent with Pydantic AI framework."""
        base_url = runtime_server["base_url"]

        # Create agent
        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Test Agent Pydantic",
                "description": "Test agent for Pydantic AI",
                "framework": "pydantic_ai",
                "graph_definition": simple_graph,
            },
            timeout=30,
        )

        assert response.status_code == 201, f"Failed to create agent: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test Agent Pydantic"
        assert data["framework"] == "pydantic_ai"

        agent_id = data["id"]

        # Cleanup
        requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)

    def test_create_agent_langgraph(self, runtime_server, simple_graph):
        """Test creating an agent with LangGraph framework."""
        base_url = runtime_server["base_url"]

        # Create agent
        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Test Agent LangGraph",
                "description": "Test agent for LangGraph",
                "framework": "langgraph",
                "graph_definition": simple_graph,
            },
            timeout=30,
        )

        assert response.status_code == 201, f"Failed to create agent: {response.text}"
        data = response.json()
        assert data["framework"] == "langgraph"

        agent_id = data["id"]

        # Cleanup
        requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)

    def test_list_agents(self, runtime_server, simple_graph):
        """Test listing all agents."""
        base_url = runtime_server["base_url"]

        # Create a couple of agents
        agent_ids = []
        for i in range(2):
            response = requests.post(
                f"{base_url}/api/v1/agents",
                json={
                    "name": f"Test Agent {i}",
                    "framework": "pydantic_ai",
                    "graph_definition": simple_graph,
                },
                timeout=30,
            )
            assert response.status_code == 201
            agent_ids.append(response.json()["id"])

        # List agents
        response = requests.get(f"{base_url}/api/v1/agents", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2  # At least our two agents

        # Cleanup
        for agent_id in agent_ids:
            requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)

    def test_get_agent(self, runtime_server, simple_graph):
        """Test getting a specific agent."""
        base_url = runtime_server["base_url"]

        # Create agent
        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Get Test Agent",
                "framework": "pydantic_ai",
                "graph_definition": simple_graph,
            },
            timeout=30,
        )
        agent_id = response.json()["id"]

        # Get agent
        response = requests.get(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == agent_id
        assert data["name"] == "Get Test Agent"

        # Cleanup
        requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)

    def test_delete_agent(self, runtime_server, simple_graph):
        """Test deleting an agent."""
        base_url = runtime_server["base_url"]

        # Create agent
        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Delete Test Agent",
                "framework": "pydantic_ai",
                "graph_definition": simple_graph,
            },
            timeout=30,
        )
        agent_id = response.json()["id"]

        # Delete agent
        response = requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)
        assert response.status_code in [200, 204]

        # Verify deletion
        response = requests.get(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)
        assert response.status_code == 404

    def test_create_agent_with_invalid_graph(self, runtime_server):
        """Test creating agent with invalid graph definition."""
        base_url = runtime_server["base_url"]

        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Invalid Agent",
                "framework": "pydantic_ai",
                "graph_definition": {"invalid": "structure"},
            },
            timeout=30,
        )

        # Should fail
        assert response.status_code in [400, 422, 500]


# Test: Agent Execution
class TestAgentExecution:
    """Test running agents and monitoring execution."""

    @pytest.fixture
    def test_agent(self, runtime_server, simple_graph):
        """Create a test agent and clean up after."""
        base_url = runtime_server["base_url"]

        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Execution Test Agent",
                "framework": "pydantic_ai",
                "graph_definition": simple_graph,
            },
            timeout=30,
        )
        agent_id = response.json()["id"]

        yield {"agent_id": agent_id, "base_url": base_url}

        # Cleanup
        requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)

    def test_start_run(self, test_agent):
        """Test starting an agent run."""
        base_url = test_agent["base_url"]
        agent_id = test_agent["agent_id"]

        # Start run
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {"user_input": "test input"}},
            timeout=30,
        )

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["status"] in ["pending", "running", "completed"]

    def test_monitor_run_completion(self, test_agent):
        """Test monitoring a run until completion."""
        base_url = test_agent["base_url"]
        agent_id = test_agent["agent_id"]

        # Start run
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {"user_input": "test input"}},
            timeout=30,
        )
        run_id = response.json()["id"]

        # Poll until completion
        max_attempts = 30
        for attempt in range(max_attempts):
            response = requests.get(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                timeout=10,
            )
            assert response.status_code == 200
            data = response.json()
            status = data["status"]

            if status in ["completed", "failed", "stopped"]:
                assert status == "completed", f"Run failed: {data.get('error')}"
                assert "outputs" in data
                break

            time.sleep(1)
        else:
            pytest.fail(f"Run did not complete within {max_attempts} seconds")

    def test_list_runs(self, test_agent):
        """Test listing runs for an agent."""
        base_url = test_agent["base_url"]
        agent_id = test_agent["agent_id"]

        # Start a couple of runs
        run_ids = []
        for _ in range(2):
            response = requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/runs",
                json={"inputs": {"user_input": "test"}},
                timeout=30,
            )
            run_ids.append(response.json()["id"])

        # List runs
        response = requests.get(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_stop_run(self, runtime_server):
        """Test stopping a running agent."""
        base_url = runtime_server["base_url"]

        # Create an agent with a sleep step to ensure it runs long enough to be stopped
        slow_graph = {
            "version": "1.0",
            "metadata": {"name": "Slow Test Agent", "description": "Agent with sleep for stop testing"},
            "memory": {
                "inputs": {"input": {"type": "string"}},
                "outputs": {"output": {"type": "string"}},
                "intermediate": {}
            },
            "steps": [
                {
                    "id": "sleep_1",
                    "type": "sleep",
                    "config": {"duration": 5},  # Sleep for 5 seconds
                },
                {
                    "id": "output_1",
                    "type": "output",
                    "config": {},
                    "outputs": {"output": "{memory.input}"}
                }
            ],
            "edges": [{"id": "edge_1", "from": "sleep_1", "to": "output_1"}]
        }

        # Create agent
        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Slow Test Agent",
                "framework": "pydantic_ai",
                "graph_definition": slow_graph,
            },
            timeout=30,
        )
        agent_id = response.json()["id"]

        try:
            # Start run
            response = requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/runs",
                json={"inputs": {"input": "test"}},
                timeout=30,
            )
            run_id = response.json()["id"]

            # Give it a moment to start
            time.sleep(0.5)

            # Stop run while it's sleeping
            response = requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}/stop",
                timeout=10,
            )
            assert response.status_code in [200, 204]

            # Check status
            time.sleep(1)
            response = requests.get(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                timeout=10,
            )
            data = response.json()
            # Stop is represented as "failed" status with "stopped by user" error message
            assert data["status"] in ["stopped", "completed", "failed"]
            if data["status"] == "failed":
                assert "stopped by user" in data.get("error", "").lower()
        finally:
            # Cleanup
            requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)

    def test_delete_run(self, test_agent):
        """Test deleting a run."""
        base_url = test_agent["base_url"]
        agent_id = test_agent["agent_id"]

        # Start and wait for completion
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {"user_input": "test"}},
            timeout=30,
        )
        run_id = response.json()["id"]

        # Wait for completion
        for _ in range(20):
            response = requests.get(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                timeout=10,
            )
            if response.json()["status"] in ["completed", "failed", "stopped"]:
                break
            time.sleep(1)

        # Delete run
        response = requests.delete(
            f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
            timeout=10,
        )
        assert response.status_code in [200, 204]

        # Verify deletion
        response = requests.get(
            f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
            timeout=10,
        )
        assert response.status_code == 404


# Test: Memory Inspection
class TestMemoryInspection:
    """Test inspecting agent memory during and after execution."""

    @pytest.fixture
    def completed_run(self, runtime_server, simple_graph):
        """Create and complete a run."""
        base_url = runtime_server["base_url"]

        # Create agent
        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Memory Test Agent",
                "framework": "pydantic_ai",
                "graph_definition": simple_graph,
            },
            timeout=30,
        )
        agent_id = response.json()["id"]

        # Start run
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {"user_input": "hello"}},
            timeout=30,
        )
        run_id = response.json()["id"]

        # Wait for completion
        for _ in range(20):
            response = requests.get(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                timeout=10,
            )
            if response.json()["status"] == "completed":
                break
            time.sleep(1)

        yield {"agent_id": agent_id, "run_id": run_id, "base_url": base_url}

        # Cleanup
        requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)

    def test_get_memory_state(self, completed_run):
        """Test getting complete memory state."""
        base_url = completed_run["base_url"]
        agent_id = completed_run["agent_id"]
        run_id = completed_run["run_id"]

        response = requests.get(
            f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}/memory",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert "inputs" in data
        assert "outputs" in data
        assert "intermediate" in data

    def test_get_specific_memory_value(self, completed_run):
        """Test getting a specific memory value."""
        base_url = completed_run["base_url"]
        agent_id = completed_run["agent_id"]
        run_id = completed_run["run_id"]

        response = requests.get(
            f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}/memory/user_input",
            timeout=10,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["value"] == "hello"


# Test: Concurrent Execution
class TestConcurrentExecution:
    """Test running multiple agents concurrently."""

    def test_multiple_agents_concurrent_execution(self, runtime_server, simple_graph):
        """Test running multiple agents at the same time."""
        base_url = runtime_server["base_url"]

        # Create multiple agents
        agent_ids = []
        for i in range(3):
            response = requests.post(
                f"{base_url}/api/v1/agents",
                json={
                    "name": f"Concurrent Agent {i}",
                    "framework": "pydantic_ai",
                    "graph_definition": simple_graph,
                },
                timeout=30,
            )
            agent_ids.append(response.json()["id"])

        # Start runs for all agents
        run_data = []
        for agent_id in agent_ids:
            response = requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/runs",
                json={"inputs": {"user_input": f"test for {agent_id}"}},
                timeout=30,
            )
            run_data.append({"agent_id": agent_id, "run_id": response.json()["id"]})

        # Wait for all to complete
        for data in run_data:
            for _ in range(30):
                response = requests.get(
                    f"{base_url}/api/v1/agents/{data['agent_id']}/runs/{data['run_id']}",
                    timeout=10,
                )
                if response.json()["status"] == "completed":
                    break
                time.sleep(1)
            else:
                pytest.fail(f"Run {data['run_id']} did not complete")

        # Cleanup
        for agent_id in agent_ids:
            requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)

    def test_same_agent_multiple_runs(self, runtime_server, simple_graph):
        """Test multiple concurrent runs of the same agent."""
        base_url = runtime_server["base_url"]

        # Create agent
        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "Multi-Run Agent",
                "framework": "pydantic_ai",
                "graph_definition": simple_graph,
            },
            timeout=30,
        )
        agent_id = response.json()["id"]

        # Start multiple runs
        run_ids = []
        for i in range(3):
            response = requests.post(
                f"{base_url}/api/v1/agents/{agent_id}/runs",
                json={"inputs": {"user_input": f"run {i}"}},
                timeout=30,
            )
            run_ids.append(response.json()["id"])

        # Wait for all to complete
        for run_id in run_ids:
            for _ in range(30):
                response = requests.get(
                    f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                    timeout=10,
                )
                if response.json()["status"] == "completed":
                    break
                time.sleep(1)
            else:
                pytest.fail(f"Run {run_id} did not complete")

        # Cleanup
        requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10)
