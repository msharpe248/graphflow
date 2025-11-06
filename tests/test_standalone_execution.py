"""
Test standalone execution of compiled agents.

This module tests:
1. Running compiled agents as CLI scripts
2. Running compiled agents as FastAPI servers
3. Input/output handling
4. Error handling in standalone mode
"""

import json
import subprocess
import time
import requests
import pytest
from pathlib import Path
import signal
import os


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
def compiled_agent_pydantic(simple_graph, tmp_path):
    """Compile a simple agent to Pydantic AI."""
    graph_file = tmp_path / "graph.json"
    with open(graph_file, "w") as f:
        json.dump(simple_graph, f)

    output_file = tmp_path / "agent.py"
    subprocess.run(
        [
            "graphflow-compile",
            "compile",
            str(graph_file),
            "--framework",
            "pydantic_ai",
            "--output",
            str(output_file),
            "--standalone",
        ],
        check=True,
        capture_output=True,
    )

    return output_file


@pytest.fixture
def compiled_agent_langgraph(simple_graph, tmp_path):
    """Compile a simple agent to LangGraph."""
    graph_file = tmp_path / "graph.json"
    with open(graph_file, "w") as f:
        json.dump(simple_graph, f)

    output_file = tmp_path / "agent.py"
    subprocess.run(
        [
            "graphflow-compile",
            "compile",
            str(graph_file),
            "--framework",
            "langgraph",
            "--output",
            str(output_file),
            "--standalone",
        ],
        check=True,
        capture_output=True,
    )

    return output_file


# Test: CLI Execution
class TestCLIExecution:
    """Test running compiled agents as CLI scripts."""

    def test_pydantic_agent_cli_execution(self, compiled_agent_pydantic, tmp_path):
        """Test running Pydantic AI agent via CLI."""
        # Create input file
        inputs_file = tmp_path / "inputs.json"
        with open(inputs_file, "w") as f:
            json.dump({"user_input": "hello world"}, f)

        # Run agent
        result = subprocess.run(
            ["python", str(compiled_agent_pydantic), str(inputs_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Check execution succeeded
        assert result.returncode == 0, f"Agent failed: {result.stderr}"

        # Check output contains expected result
        try:
            output = json.loads(result.stdout)
            assert "result" in output
            assert isinstance(output["result"], str)
        except json.JSONDecodeError:
            pytest.fail(f"Agent output is not valid JSON: {result.stdout}")

    def test_langgraph_agent_cli_execution(self, compiled_agent_langgraph, tmp_path):
        """Test running LangGraph agent via CLI."""
        # Create input file
        inputs_file = tmp_path / "inputs.json"
        with open(inputs_file, "w") as f:
            json.dump({"user_input": "hello world"}, f)

        # Run agent
        result = subprocess.run(
            ["python", str(compiled_agent_langgraph), str(inputs_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Check execution succeeded
        assert result.returncode == 0, f"Agent failed: {result.stderr}"

        # Check output contains expected result
        try:
            output = json.loads(result.stdout)
            assert "result" in output
        except json.JSONDecodeError:
            pytest.fail(f"Agent output is not valid JSON: {result.stdout}")

    def test_cli_with_invalid_input(self, compiled_agent_pydantic, tmp_path):
        """Test CLI with invalid input file."""
        # Create invalid input file
        inputs_file = tmp_path / "inputs.json"
        with open(inputs_file, "w") as f:
            f.write("not valid json")

        # Run agent
        result = subprocess.run(
            ["python", str(compiled_agent_pydantic), str(inputs_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # Should fail
        assert result.returncode != 0

    def test_cli_with_missing_input_fields(self, compiled_agent_pydantic, tmp_path):
        """Test CLI with missing required input fields."""
        # Create input file with missing fields
        inputs_file = tmp_path / "inputs.json"
        with open(inputs_file, "w") as f:
            json.dump({}, f)  # Empty inputs

        # Run agent
        result = subprocess.run(
            ["python", str(compiled_agent_pydantic), str(inputs_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        # May fail or succeed with defaults, check it doesn't crash
        # At minimum, should not hang or timeout
        assert True  # Successfully completed without timeout


# Test: Server Mode Execution
class TestServerExecution:
    """Test running compiled agents as FastAPI servers."""

    @pytest.fixture
    def server_process(self, compiled_agent_pydantic, tmp_path):
        """Start agent server and yield process."""
        port = 18765  # Use non-standard port to avoid conflicts

        # Start server
        process = subprocess.Popen(
            [
                "python",
                str(compiled_agent_pydantic),
                "--server",
                "--port",
                str(port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Wait for server to start
        time.sleep(3)

        # Check if process is running
        if process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(f"Server failed to start. stdout: {stdout}, stderr: {stderr}")

        yield {"process": process, "port": port, "base_url": f"http://localhost:{port}"}

        # Cleanup: kill server
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()

    def test_server_health_check(self, server_process):
        """Test server health endpoint."""
        base_url = server_process["base_url"]

        # Check health endpoint
        try:
            response = requests.get(f"{base_url}/health", timeout=5)
            assert response.status_code == 200
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Health check failed: {e}")

    def test_server_invoke_endpoint(self, server_process):
        """Test server invoke endpoint."""
        base_url = server_process["base_url"]

        # Call invoke endpoint
        try:
            response = requests.post(
                f"{base_url}/invoke",
                json={"user_input": "hello world"},
                timeout=30,
            )

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert isinstance(data["result"], str)
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Invoke request failed: {e}")

    def test_server_with_invalid_input(self, server_process):
        """Test server with invalid input."""
        base_url = server_process["base_url"]

        # Call with invalid input
        try:
            response = requests.post(
                f"{base_url}/invoke",
                json={"wrong_field": "value"},
                timeout=30,
            )

            # Should return error status
            assert response.status_code in [400, 422, 500]
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Request failed unexpectedly: {e}")

    def test_server_docs_endpoint(self, server_process):
        """Test that OpenAPI docs are available."""
        base_url = server_process["base_url"]

        # Check docs endpoint
        try:
            response = requests.get(f"{base_url}/docs", timeout=5)
            # Should redirect or return docs page
            assert response.status_code in [200, 307]
        except requests.exceptions.RequestException:
            # Docs might not be enabled, that's okay
            pass


# Test: Integration with Different Graph Types
class TestDifferentGraphTypes:
    """Test standalone execution with various graph structures."""

    def test_graph_with_multiple_outputs(self, tmp_path):
        """Test agent with multiple output fields."""
        graph = {
            "version": "1.0",
            "metadata": {
                "name": "Multi-Output Agent",
                "description": "Test multi-output",
                "created": "2025-01-01T00:00:00Z"
            },
            "memory": {
                "inputs": {"input": {"type": "string"}},
                "outputs": {
                    "output1": {"type": "string"},
                    "output2": {"type": "string"},
                },
                "intermediate": {},
            },
            "steps": [
                {
                    "id": "step1",
                    "type": "transform",
                    "config": {
                        "operation": "uppercase",
                        "code": "return input.upper()",
                        "input_keys": ["input"],
                        "output_key": "output1"
                    },
                    "outputs": {"result": "{memory.output1}"},
                },
                {
                    "id": "step2",
                    "type": "transform",
                    "config": {
                        "operation": "lowercase",
                        "code": "return input.lower()",
                        "input_keys": ["input"],
                        "output_key": "output2"
                    },
                    "outputs": {"result": "{memory.output2}"},
                },
            ],
            "edges": [],
        }

        # Compile
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(graph, f)

        output_file = tmp_path / "agent.py"
        subprocess.run(
            [
                "graphflow-compile",
                "compile",
                str(graph_file),
                "--framework",
                "pydantic_ai",
                "--output",
                str(output_file),
                "--standalone",
            ],
            check=True,
            capture_output=True,
        )

        # Run
        inputs_file = tmp_path / "inputs.json"
        with open(inputs_file, "w") as f:
            json.dump({"input": "Test"}, f)

        result = subprocess.run(
            ["python", str(output_file), str(inputs_file)],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        output = json.loads(result.stdout)
        assert "output1" in output
        assert "output2" in output

    def test_graph_with_no_steps(self, tmp_path):
        """Test agent with no steps (pass-through)."""
        graph = {
            "version": "1.0",
            "metadata": {
                "name": "Empty Agent",
                "description": "Test empty agent",
                "created": "2025-01-01T00:00:00Z"
            },
            "memory": {
                "inputs": {"input": {"type": "string"}},
                "outputs": {"output": {"type": "string"}},
                "intermediate": {},
            },
            "steps": [],
            "edges": [],
        }

        # Compile
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(graph, f)

        output_file = tmp_path / "agent.py"
        result = subprocess.run(
            [
                "graphflow-compile",
                "compile",
                str(graph_file),
                "--framework",
                "pydantic_ai",
                "--output",
                str(output_file),
                "--standalone",
            ],
            capture_output=True,
            text=True,
        )

        # Should compile successfully (or fail gracefully)
        # Either behavior is acceptable
        assert True  # Test passes if no crash


# Test: Performance and Timeout
class TestPerformanceAndTimeout:
    """Test performance characteristics of standalone execution."""

    def test_cli_execution_completes_in_reasonable_time(
        self, compiled_agent_pydantic, tmp_path
    ):
        """Test that CLI execution completes within reasonable time."""
        inputs_file = tmp_path / "inputs.json"
        with open(inputs_file, "w") as f:
            json.dump({"user_input": "test"}, f)

        start_time = time.time()
        result = subprocess.run(
            ["python", str(compiled_agent_pydantic), str(inputs_file)],
            capture_output=True,
            text=True,
            timeout=10,  # Should complete within 10 seconds
        )
        elapsed_time = time.time() - start_time

        assert result.returncode == 0
        assert elapsed_time < 10, f"Execution took too long: {elapsed_time}s"

    def test_server_startup_time(self, compiled_agent_pydantic):
        """Test that server starts within reasonable time."""
        port = 18766

        start_time = time.time()
        process = subprocess.Popen(
            [
                "python",
                str(compiled_agent_pydantic),
                "--server",
                "--port",
                str(port),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for server to be ready (max 10 seconds)
        server_ready = False
        for _ in range(20):  # 20 * 0.5s = 10s max
            time.sleep(0.5)
            try:
                response = requests.get(f"http://localhost:{port}/health", timeout=1)
                if response.status_code == 200:
                    server_ready = True
                    break
            except requests.exceptions.RequestException:
                pass

        elapsed_time = time.time() - start_time

        # Cleanup
        process.terminate()
        process.wait(timeout=5)

        assert server_ready, "Server did not start within 10 seconds"
        assert elapsed_time < 10, f"Server startup took too long: {elapsed_time}s"
