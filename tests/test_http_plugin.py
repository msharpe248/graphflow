"""
Test HTTP plugin with memory default values.

This module tests:
1. HTTP GET step execution with default values
2. Memory initialization with schema defaults
3. Template rendering for HTTP config parameters
4. Successful HTTP request completion
"""

import json
import subprocess
import time
import requests
import pytest
from pathlib import Path


# Fixtures
@pytest.fixture
def fixtures_dir():
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def fetchurl_graph(fixtures_dir):
    """Load FetchURL graph."""
    with open(fixtures_dir / "fetchurl_graph.json") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def runtime_server(ssl_verify, runtime_protocol):
    """Start runtime server for tests with HTTPS support."""
    port = 18701  # Use non-standard port to avoid conflicts

    # Start runtime server with auto-ssl for HTTPS
    cmd = ["graphflow-runtime", "--port", str(port)]
    if runtime_protocol == "https":
        cmd.append("--auto-ssl")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait for server to start
    base_url = f"{runtime_protocol}://localhost:{port}"
    server_ready = False
    for _ in range(30):  # 30 seconds max
        time.sleep(1)
        try:
            response = requests.get(f"{base_url}/api/v1/health", timeout=2, verify=ssl_verify)
            if response.status_code == 200:
                server_ready = True
                break
        except requests.exceptions.RequestException:
            pass

    if not server_ready:
        process.terminate()
        stdout, stderr = process.communicate(timeout=5)
        pytest.fail(f"Runtime server failed to start. stdout: {stdout}, stderr: {stderr}")

    yield {"process": process, "port": port, "base_url": base_url, "verify": ssl_verify}

    # Cleanup
    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


# Test: HTTP Plugin Memory Defaults
class TestHTTPPluginMemoryDefaults:
    """Test HTTP plugin with memory default value initialization."""

    @pytest.fixture
    def fetchurl_agent(self, runtime_server, fetchurl_graph):
        """Create FetchURL test agent and clean up after."""
        base_url = runtime_server["base_url"]
        verify = runtime_server["verify"]

        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "FetchURL Test Agent",
                "description": "Test HTTP GET with memory defaults",
                "framework": "pydantic_ai",
                "graph_definition": fetchurl_graph,
            },
            timeout=30,
            verify=verify,
        )

        assert response.status_code in [200, 201], f"Failed to create agent: {response.text}"
        agent_id = response.json()["id"]

        yield {"agent_id": agent_id, "base_url": base_url, "verify": verify}

        # Cleanup
        requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10, verify=verify)

    def test_http_get_with_default_url(self, fetchurl_agent):
        """Test HTTP GET step executes successfully with default URL."""
        base_url = fetchurl_agent["base_url"]
        agent_id = fetchurl_agent["agent_id"]
        verify = fetchurl_agent["verify"]

        # Start run with default URL (http://www.google.com)
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {}},  # Use default URL from graph
            timeout=30,
            verify=verify,
        )

        assert response.status_code in [200, 201], f"Failed to start run: {response.text}"
        run_id = response.json()["id"]

        # Poll until completion
        max_attempts = 60  # 60 seconds for HTTP request
        completed = False
        final_status = None

        for attempt in range(max_attempts):
            response = requests.get(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                timeout=10,
                verify=verify,
            )
            assert response.status_code in [200, 201]
            data = response.json()
            status = data["status"]
            final_status = data

            if status in ["completed", "failed", "stopped"]:
                completed = True
                assert status == "completed", f"Run failed with status {status}. Error: {data.get('error')}"
                break

            time.sleep(1)

        assert completed, f"Run did not complete within {max_attempts} seconds. Last status: {final_status}"

        # Verify outputs
        assert "outputs" in final_status
        assert "page" in final_status["outputs"]
        assert final_status["outputs"]["page"]  # Should contain HTML content

    def test_memory_defaults_initialized(self, fetchurl_agent):
        """Test that memory defaults are properly initialized."""
        base_url = fetchurl_agent["base_url"]
        agent_id = fetchurl_agent["agent_id"]
        verify = fetchurl_agent["verify"]

        # Start run
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {}},
            timeout=30,
            verify=verify,
        )
        run_id = response.json()["id"]

        # Wait a moment for initialization
        time.sleep(2)

        # Get memory state
        response = requests.get(
            f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}/memory",
            timeout=10,
            verify=verify,
        )

        assert response.status_code in [200, 201]
        memory = response.json()

        # Verify intermediate fields have defaults
        intermediate = memory.get("intermediate", {})

        # Check timeout default
        assert "http.HTTPGetStep_2.timeout" in intermediate
        assert intermediate["http.HTTPGetStep_2.timeout"] == 30, \
            f"Expected timeout=30, got {intermediate['http.HTTPGetStep_2.timeout']}"

        # Check retries default
        assert "http.HTTPGetStep_2.retries" in intermediate
        assert intermediate["http.HTTPGetStep_2.retries"] == 2, \
            f"Expected retries=2, got {intermediate['http.HTTPGetStep_2.retries']}"

        # Check verify_ssl default
        assert "http.HTTPGetStep_2.verify_ssl" in intermediate
        assert intermediate["http.HTTPGetStep_2.verify_ssl"] is True, \
            f"Expected verify_ssl=True, got {intermediate['http.HTTPGetStep_2.verify_ssl']}"

        # Check follow_redirects default
        assert "http.HTTPGetStep_2.follow_redirects" in intermediate
        assert intermediate["http.HTTPGetStep_2.follow_redirects"] is True, \
            f"Expected follow_redirects=True, got {intermediate['http.HTTPGetStep_2.follow_redirects']}"

    def test_http_get_with_custom_url(self, fetchurl_agent):
        """Test HTTP GET step with custom URL input."""
        base_url = fetchurl_agent["base_url"]
        agent_id = fetchurl_agent["agent_id"]
        verify = fetchurl_agent["verify"]

        # Start run with custom URL
        custom_url = "https://httpbin.org/get"
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {"url": custom_url}},
            timeout=30,
            verify=verify,
        )

        assert response.status_code in [200, 201]
        run_id = response.json()["id"]

        # Wait for completion
        for _ in range(60):
            response = requests.get(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                timeout=10,
                verify=verify,
            )
            data = response.json()

            if data["status"] == "completed":
                # Verify response contains expected data from httpbin
                assert "outputs" in data
                assert "page" in data["outputs"]
                page_content = data["outputs"]["page"]

                # httpbin.org/get returns JSON, verify we got it
                assert page_content, "Response should not be empty"
                break

            elif data["status"] in ["failed", "stopped"]:
                pytest.fail(f"Run failed: {data.get('error')}")

            time.sleep(1)
        else:
            pytest.fail("Run did not complete within timeout")

    def test_http_response_status_code(self, fetchurl_agent):
        """Test that HTTP status code is written to memory."""
        base_url = fetchurl_agent["base_url"]
        agent_id = fetchurl_agent["agent_id"]
        verify = fetchurl_agent["verify"]

        # Start run with httpbin (reliable test endpoint)
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {"url": "https://httpbin.org/status/200"}},
            timeout=30,
            verify=verify,
        )
        run_id = response.json()["id"]

        # Wait for completion
        for _ in range(60):
            response = requests.get(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                timeout=10,
                verify=verify,
            )
            data = response.json()

            if data["status"] == "completed":
                # Check memory for status code
                mem_response = requests.get(
                    f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}/memory",
                    timeout=10,
                    verify=verify,
                )
                memory = mem_response.json()

                # Verify status code in intermediate memory
                intermediate = memory.get("intermediate", {})
                assert "http.HTTPGetStep_2.status_code" in intermediate
                assert intermediate["http.HTTPGetStep_2.status_code"] == 200
                break

            elif data["status"] in ["failed", "stopped"]:
                pytest.fail(f"Run failed: {data.get('error')}")

            time.sleep(1)
        else:
            pytest.fail("Run did not complete within timeout")

    def test_object_type_memory_defaults(self, fetchurl_agent):
        """Test that object-type memory fields (params, headers, auth) are initialized."""
        base_url = fetchurl_agent["base_url"]
        agent_id = fetchurl_agent["agent_id"]
        verify = fetchurl_agent["verify"]

        # Start run
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {}},
            timeout=30,
            verify=verify,
        )
        run_id = response.json()["id"]

        # Wait for initialization
        time.sleep(2)

        # Get memory state
        response = requests.get(
            f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}/memory",
            timeout=10,
            verify=verify,
        )

        memory = response.json()
        intermediate = memory.get("intermediate", {})

        # Object-type fields should be initialized to empty dict (zero value)
        # since they don't have defaults in the schema
        assert "http.HTTPGetStep_2.params" in intermediate
        assert isinstance(intermediate["http.HTTPGetStep_2.params"], dict)

        assert "http.HTTPGetStep_2.headers" in intermediate
        assert isinstance(intermediate["http.HTTPGetStep_2.headers"], dict)

        assert "http.HTTPGetStep_2.auth" in intermediate
        assert isinstance(intermediate["http.HTTPGetStep_2.auth"], dict)


# Test: HTTP Plugin Error Handling
class TestHTTPPluginErrorHandling:
    """Test HTTP plugin error handling."""

    @pytest.fixture
    def fetchurl_agent(self, runtime_server, fetchurl_graph):
        """Create FetchURL test agent."""
        base_url = runtime_server["base_url"]
        verify = runtime_server["verify"]

        response = requests.post(
            f"{base_url}/api/v1/agents",
            json={
                "name": "FetchURL Error Test Agent",
                "framework": "pydantic_ai",
                "graph_definition": fetchurl_graph,
            },
            timeout=30,
            verify=verify,
        )
        agent_id = response.json()["id"]

        yield {"agent_id": agent_id, "base_url": base_url, "verify": verify}

        # Cleanup
        requests.delete(f"{base_url}/api/v1/agents/{agent_id}", timeout=10, verify=verify)

    def test_http_get_invalid_url(self, fetchurl_agent):
        """Test HTTP GET with invalid URL."""
        base_url = fetchurl_agent["base_url"]
        agent_id = fetchurl_agent["agent_id"]
        verify = fetchurl_agent["verify"]

        # Start run with invalid URL
        response = requests.post(
            f"{base_url}/api/v1/agents/{agent_id}/runs",
            json={"inputs": {"url": "not-a-valid-url"}},
            timeout=30,
            verify=verify,
        )
        run_id = response.json()["id"]

        # Wait for completion or failure
        for _ in range(30):
            response = requests.get(
                f"{base_url}/api/v1/agents/{agent_id}/runs/{run_id}",
                timeout=10,
                verify=verify,
            )
            data = response.json()

            if data["status"] in ["failed", "completed", "stopped"]:
                # Should fail with invalid URL
                assert data["status"] == "failed", "Expected run to fail with invalid URL"
                assert "error" in data or "message" in data
                break

            time.sleep(1)
        else:
            pytest.fail("Run did not complete within timeout")
