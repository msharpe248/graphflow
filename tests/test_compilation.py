"""
Test graph compilation to different frameworks.

This module tests:
1. Compilation to Pydantic AI
2. Compilation to LangGraph
3. Validation of generated code
4. Standalone vs runtime mode compilation
"""

import json
import subprocess
import tempfile
from pathlib import Path
import pytest


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


# Test: Pydantic AI Compilation
class TestPydanticAICompilation:
    """Test compilation to Pydantic AI framework."""

    def test_compile_simple_graph_pydantic_ai(self, simple_graph, tmp_path):
        """Test compiling a simple graph to Pydantic AI."""
        # Write graph to temp file
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(simple_graph, f)

        # Compile
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
            ],
            capture_output=True,
            text=True,
        )

        # Check compilation succeeded
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        assert output_file.exists(), "Output file was not created"

        # Check generated code contains expected elements
        code = output_file.read_text()
        assert "class GeneratedAgent:" in code
        assert "async def run(" in code
        assert "from graphflow_core.memory import MemoryStore" in code
        assert "MEMORY_SCHEMA" in code

    def test_compile_llm_graph_pydantic_ai(self, llm_graph, tmp_path):
        """Test compiling an LLM graph to Pydantic AI."""
        # Write graph to temp file
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(llm_graph, f)

        # Compile
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
            ],
            capture_output=True,
            text=True,
        )

        # Check compilation succeeded
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        assert output_file.exists(), "Output file was not created"

        # Check generated code contains Pydantic AI specific elements
        code = output_file.read_text()
        assert "from pydantic_ai" in code or "pydantic_ai" in code
        assert "Agent(" in code or "agent =" in code

    def test_compile_standalone_mode(self, simple_graph, tmp_path):
        """Test compilation with standalone mode (default)."""
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(simple_graph, f)

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

        assert result.returncode == 0
        code = output_file.read_text()

        # Should include CLI and server wrappers
        assert 'if __name__ == "__main__"' in code
        assert "def main_cli" in code or "def create_fastapi_app" in code

    def test_compile_no_standalone_mode(self, simple_graph, tmp_path):
        """Test compilation without standalone wrappers."""
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(simple_graph, f)

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
                "--no-standalone",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0
        code = output_file.read_text()

        # Should NOT include CLI wrappers
        assert 'if __name__ == "__main__"' not in code

    def test_validate_only_mode(self, simple_graph, tmp_path):
        """Test validation without code generation."""
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(simple_graph, f)

        result = subprocess.run(
            [
                "graphflow-compile",
                "compile",
                str(graph_file),
                "--validate-only",
            ],
            capture_output=True,
            text=True,
        )

        # Should validate successfully and not create output file
        assert result.returncode == 0
        assert "valid" in result.stdout.lower() or result.returncode == 0


# Test: LangGraph Compilation
class TestLangGraphCompilation:
    """Test compilation to LangGraph framework."""

    def test_compile_simple_graph_langgraph(self, simple_graph, tmp_path):
        """Test compiling a simple graph to LangGraph."""
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(simple_graph, f)

        output_file = tmp_path / "agent.py"
        result = subprocess.run(
            [
                "graphflow-compile",
                "compile",
                str(graph_file),
                "--framework",
                "langgraph",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        # Check compilation succeeded
        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        assert output_file.exists(), "Output file was not created"

        # Check generated code contains LangGraph elements
        code = output_file.read_text()
        assert "class GeneratedAgent:" in code
        assert "StateGraph" in code or "from langgraph" in code
        assert "AgentState" in code or "TypedDict" in code

    def test_compile_llm_graph_langgraph(self, llm_graph, tmp_path):
        """Test compiling an LLM graph to LangGraph."""
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(llm_graph, f)

        output_file = tmp_path / "agent.py"
        result = subprocess.run(
            [
                "graphflow-compile",
                "compile",
                str(graph_file),
                "--framework",
                "langgraph",
                "--output",
                str(output_file),
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Compilation failed: {result.stderr}"
        assert output_file.exists()

        code = output_file.read_text()
        assert "langgraph" in code.lower() or "StateGraph" in code


# Test: Code Validation
class TestCodeValidation:
    """Test that generated code is syntactically valid Python."""

    def test_generated_code_is_valid_python_pydantic(self, simple_graph, tmp_path):
        """Test that generated Pydantic AI code is valid Python."""
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
            ],
            check=True,
        )

        # Try to compile the Python code
        result = subprocess.run(
            ["python", "-m", "py_compile", str(output_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Generated code has syntax errors: {result.stderr}"

    def test_generated_code_is_valid_python_langgraph(self, simple_graph, tmp_path):
        """Test that generated LangGraph code is valid Python."""
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
            ],
            check=True,
        )

        # Try to compile the Python code
        result = subprocess.run(
            ["python", "-m", "py_compile", str(output_file)],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"Generated code has syntax errors: {result.stderr}"


# Test: Error Handling
class TestCompilationErrors:
    """Test error handling during compilation."""

    def test_invalid_graph_structure(self, tmp_path):
        """Test compilation fails gracefully with invalid graph."""
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump({"invalid": "structure"}, f)

        result = subprocess.run(
            [
                "graphflow-compile",
                "compile",
                str(graph_file),
                "--framework",
                "pydantic_ai",
            ],
            capture_output=True,
            text=True,
        )

        # Should fail with non-zero exit code
        assert result.returncode != 0

    def test_nonexistent_file(self, tmp_path):
        """Test compilation fails with nonexistent file."""
        result = subprocess.run(
            [
                "graphflow-compile",
                "compile",
                str(tmp_path / "nonexistent.json"),
                "--framework",
                "pydantic_ai",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0

    def test_invalid_framework(self, simple_graph, tmp_path):
        """Test compilation fails with invalid framework."""
        graph_file = tmp_path / "graph.json"
        with open(graph_file, "w") as f:
            json.dump(simple_graph, f)

        result = subprocess.run(
            [
                "graphflow-compile",
                "compile",
                str(graph_file),
                "--framework",
                "invalid_framework",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
