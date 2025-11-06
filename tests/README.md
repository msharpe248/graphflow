# GraphFlow Test Suite

Comprehensive test suite for verifying GraphFlow functionality across all execution modes.

## Test Structure

```
tests/
├── fixtures/                           # Test data and example graphs
│   ├── simple_transform_graph.json    # Basic transformation pipeline
│   └── llm_agent_graph.json           # LLM-based agent
├── test_compilation.py                 # Graph compilation tests
├── test_standalone_execution.py        # Standalone agent execution tests
├── test_runtime_execution.py           # Multi-graph runtime tests
├── pytest.ini                          # Pytest configuration
└── README.md                           # This file
```

## Test Categories

### 1. Compilation Tests (`test_compilation.py`)

Tests graph compilation to different frameworks:

- **Pydantic AI Compilation**: Verify graphs compile to Pydantic AI agents
- **LangGraph Compilation**: Verify graphs compile to LangGraph agents
- **Standalone vs Runtime Mode**: Test both compilation modes
- **Code Validation**: Ensure generated code is valid Python
- **Error Handling**: Test compilation with invalid graphs

**Run compilation tests:**
```bash
pytest tests/test_compilation.py -v
```

### 2. Standalone Execution Tests (`test_standalone_execution.py`)

Tests running compiled agents standalone (without runtime server):

- **CLI Execution**: Run agents as command-line scripts
- **Server Mode**: Run agents as FastAPI servers
- **Input/Output Handling**: Verify data flow through agents
- **Performance**: Test execution time and server startup
- **Error Handling**: Test with invalid inputs

**Run standalone tests:**
```bash
pytest tests/test_standalone_execution.py -v
```

**Note:** These tests start FastAPI servers on non-standard ports (18765+) to avoid conflicts.

### 3. Runtime Execution Tests (`test_runtime_execution.py`)

Tests the full multi-graph runtime system:

- **Server Health**: Verify runtime server starts correctly
- **Agent CRUD**: Create, read, update, delete agents
- **Agent Execution**: Run agents and monitor status
- **Memory Inspection**: Inspect agent memory during/after execution
- **Concurrent Execution**: Multiple agents and runs simultaneously

**Run runtime tests:**
```bash
pytest tests/test_runtime_execution.py -v
```

**Note:** These tests start a runtime server on port 18700.

## Running Tests

### Run All Tests
```bash
# From project root
pytest tests/ -v

# With coverage
pytest tests/ --cov=graphflow_core --cov=graphflow_compiler --cov=graphflow_runtime

# Parallel execution (if pytest-xdist installed)
pytest tests/ -n auto
```

### Run Specific Test Categories
```bash
# Compilation only
pytest tests/test_compilation.py

# Standalone execution only
pytest tests/test_standalone_execution.py

# Runtime execution only
pytest tests/test_runtime_execution.py
```

### Run Specific Tests
```bash
# Run a specific test class
pytest tests/test_compilation.py::TestPydanticAICompilation -v

# Run a specific test method
pytest tests/test_compilation.py::TestPydanticAICompilation::test_compile_simple_graph_pydantic_ai -v

# Run tests matching a pattern
pytest tests/ -k "pydantic" -v
```

### Run with Markers
```bash
# Run only integration tests
pytest tests/ -m integration

# Skip slow tests
pytest tests/ -m "not slow"
```

## Prerequisites

### Required Dependencies
```bash
pip install pytest pytest-asyncio httpx requests
```

### Optional Dependencies
```bash
# For coverage reports
pip install pytest-cov

# For parallel execution
pip install pytest-xdist

# For timeout enforcement
pip install pytest-timeout
```

### Environment Setup

Some tests require environment variables:

```bash
# For LLM tests (optional)
export OPENAI_API_KEY="sk-..."

# For custom runtime port
export GRAPHFLOW_RUNTIME_PORT="18700"
```

## Test Data

Test fixtures are located in `tests/fixtures/`:

- **simple_transform_graph.json**: Basic graph with transform steps
- **llm_agent_graph.json**: Graph with LLM step (requires API key for full testing)

Add custom test graphs to this directory for additional test scenarios.

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -e packages/graph-core
        pip install -e packages/graph-compiler
        pip install -e packages/graph-runtime
        pip install pytest pytest-asyncio httpx requests pytest-cov

    - name: Run tests
      run: pytest tests/ -v --cov

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Writing New Tests

### Test File Naming
- Test files must start with `test_` (e.g., `test_my_feature.py`)
- Test functions must start with `test_` (e.g., `def test_something():`)
- Test classes must start with `Test` (e.g., `class TestMyFeature:`)

### Using Fixtures
```python
import pytest

@pytest.fixture
def my_fixture():
    """Reusable test data or setup."""
    return {"key": "value"}

def test_using_fixture(my_fixture):
    """Test that uses the fixture."""
    assert my_fixture["key"] == "value"
```

### Marking Tests
```python
import pytest

@pytest.mark.slow
def test_slow_operation():
    """This test takes a long time."""
    pass

@pytest.mark.integration
def test_external_service():
    """This test requires external services."""
    pass
```

### Testing Async Code
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    """Test async functions."""
    result = await some_async_function()
    assert result is not None
```

## Troubleshooting

### Tests Hang or Timeout
- Check if servers are already running on test ports (18700, 18765, etc.)
- Increase timeout values in test code
- Run tests with `-s` flag to see output: `pytest tests/ -s`

### Port Already in Use
```bash
# Find process using port
lsof -i :18700

# Kill process
kill -9 <PID>
```

### Import Errors
Ensure packages are installed in development mode:
```bash
pip install -e packages/graph-core
pip install -e packages/graph-compiler
pip install -e packages/graph-runtime
```

### Server Won't Start
- Check logs in test output with `-s` flag
- Verify runtime dependencies are installed
- Try running server manually: `graphflow-runtime --port 18700`

## Coverage Reports

### Generate HTML Coverage Report
```bash
pytest tests/ --cov --cov-report=html
open htmlcov/index.html
```

### Coverage Thresholds
Current targets:
- **graph-core**: 80%+
- **graph-compiler**: 75%+
- **graph-runtime**: 70%+

## Performance Benchmarking

### Measure Test Execution Time
```bash
pytest tests/ --durations=10
```

### Profile Tests
```bash
pytest tests/ --profile
```

## Contributing

When adding new features:

1. **Write tests first** (TDD approach recommended)
2. **Add fixtures** for reusable test data
3. **Mark tests appropriately** (slow, integration, etc.)
4. **Document test purpose** with clear docstrings
5. **Ensure tests are deterministic** (no random failures)
6. **Clean up resources** (servers, files, database entries)

## Related Documentation

- [GraphFlow Documentation](../README.md)
- [Compilation Guide](../packages/graph-compiler/README.md)
- [Runtime Guide](../packages/graph-runtime/README.md)
- [Core Concepts](../packages/graph-core/README.md)
