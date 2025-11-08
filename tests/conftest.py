"""
Shared pytest fixtures and configuration for all tests.
"""

import json
import os
import tempfile
from pathlib import Path
import pytest

# Import AI plugin to register LLM and HumanInput steps
try:
    from graphflow_ai import LLMStep, HumanInputStep
except ImportError:
    # Plugin not installed - tests requiring LLM will skip
    pass

# Configure pytest-asyncio
pytest_plugins = ("pytest_asyncio",)


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def fixtures_dir():
    """Return the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_inputs():
    """Common test inputs."""
    return {
        "user_input": "test input",
        "user_question": "What is the capital of France?",
    }


@pytest.fixture
def sample_graph_simple():
    """Minimal valid graph definition."""
    return {
        "version": "1.0",
        "metadata": {
            "name": "Simple Test Graph",
            "description": "A minimal test graph",
            "created": "2025-01-01T00:00:00Z",
            "framework_hints": ["pydantic_ai"],
            "tags": ["test"]
        },
        "memory": {
            "inputs": {
                "input": {
                    "type": "string",
                    "description": "Input value"
                }
            },
            "outputs": {
                "output": {
                    "type": "string",
                    "description": "Output value"
                }
            },
            "intermediate": {}
        },
        "steps": [
            {
                "id": "transform_1",
                "type": "transform",
                "config": {
                    "operation": "uppercase",
                    "code": "return input.upper()",
                    "input_keys": ["input"],
                    "output_key": "output"
                },
                "outputs": {
                    "result": "{memory.output}"
                }
            }
        ],
        "edges": []
    }


@pytest.fixture(autouse=True)
def reset_environment():
    """Reset environment variables before each test."""
    # Store original environment
    original_env = os.environ.copy()

    yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(autouse=True)
def isolate_test_artifacts(temp_dir, monkeypatch):
    """Isolate test artifacts from the main project."""
    # Change to temp directory for tests
    monkeypatch.chdir(temp_dir)

    yield

    # Cleanup is handled by temp_dir fixture


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "compilation: tests for graph compilation"
    )
    config.addinivalue_line(
        "markers", "standalone: tests for standalone agent execution"
    )
    config.addinivalue_line(
        "markers", "runtime: tests for multi-graph runtime"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )


def pytest_collection_modifyitems(config, items):
    """Automatically mark tests based on their location/name."""
    for item in items:
        # Mark integration tests
        if "integration" in item.nodeid or "server" in item.nodeid.lower():
            item.add_marker(pytest.mark.integration)

        # Mark by test file
        if "test_compilation" in item.nodeid:
            item.add_marker(pytest.mark.compilation)
        elif "test_standalone" in item.nodeid:
            item.add_marker(pytest.mark.standalone)
            item.add_marker(pytest.mark.integration)
        elif "test_runtime" in item.nodeid:
            item.add_marker(pytest.mark.runtime)
            item.add_marker(pytest.mark.integration)


def pytest_runtest_setup(item):
    """Setup hook called before running each test."""
    # Skip integration tests if specifically requested
    if "no_integration" in item.config.getoption("-m"):
        pytest.skip("Skipping integration tests")
