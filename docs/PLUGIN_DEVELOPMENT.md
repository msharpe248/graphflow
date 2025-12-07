# GraphFlow Plugin Development Guide

This guide explains how to create custom step packages for GraphFlow, allowing you to extend the platform with your own step types that integrate seamlessly with the visual graph builder and runtime.

## Table of Contents

- [Overview](#overview)
- [Plugin Architecture](#plugin-architecture)
- [Creating a Plugin Package](#creating-a-plugin-package)
- [Step Implementation](#step-implementation)
- [Plugin Manifest](#plugin-manifest)
- [Installation and Testing](#installation-and-testing)
- [Advanced Topics](#advanced-topics)
- [Best Practices](#best-practices)

## Overview

GraphFlow's plugin system allows you to:

- Create custom step types as pip-installable packages
- Distribute steps independently from the core platform
- Automatically integrate with the UI without rebuilding
- Share steps across projects and teams
- Version and manage step implementations separately

Plugins are discovered automatically via Python entry points when the GraphFlow runtime starts.

## Plugin Architecture

### How Plugins Work

1. **Discovery**: On startup, GraphFlow scans for packages registered under the `graphflow.plugins` entry point group
2. **Loading**: Plugin modules are imported and their manifest files are read
3. **Registration**: Step classes are registered with namespaced type identifiers (e.g., `myplugin.CustomStep`)
4. **API Exposure**: Step metadata is exposed via REST endpoints for the UI to consume
5. **UI Integration**: The frontend fetches step types dynamically and displays them in the step palette

### Plugin Components

A complete plugin package consists of:

```
my-plugin/
├── pyproject.toml          # Package metadata and entry point
├── README.md               # Documentation
├── LICENSE                 # License file
└── my_plugin/              # Python package
    ├── __init__.py         # Module initialization
    ├── manifest.json       # Plugin metadata
    └── steps.py            # Step implementations
```

## Creating a Plugin Package

### Step 1: Initialize Package Structure

Create the basic directory structure:

```bash
mkdir -p my-graphflow-plugin/my_plugin
cd my-graphflow-plugin
```

### Step 2: Create pyproject.toml

Define your package metadata and register the entry point:

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-graphflow-plugin"
version = "0.1.0"
description = "Custom GraphFlow steps for [your use case]"
readme = "README.md"
requires-python = ">=3.11"
authors = [
    {name = "Your Name", email = "you@example.com"}
]
dependencies = [
    "graphflow-core",
    # Add any additional dependencies your steps need
]

# IMPORTANT: Register the entry point
[project.entry-points."graphflow.plugins"]
myplugin = "my_plugin"
```

**Key Points:**

- The entry point name (`myplugin`) becomes the namespace for your steps
- Keep it short and descriptive (e.g., `slack`, `email`, `database`)
- The value (`my_plugin`) should point to your Python package

### Step 3: Create Package __init__.py

```python
"""
My GraphFlow Plugin

Description of what your plugin provides.
"""

__version__ = "0.1.0"

# Import step classes to make them available
from my_plugin.steps import MyCustomStep, AnotherStep

__all__ = ["MyCustomStep", "AnotherStep"]
```

### Step 4: Create manifest.json

The manifest file declares your plugin's metadata:

```json
{
  "name": "myplugin",
  "version": "0.1.0",
  "description": "Description of your plugin",
  "steps": [
    "MyCustomStep",
    "AnotherStep"
  ],
  "ui_components": {}
}
```

**Fields:**

- `name`: Must match the entry point name
- `version`: Plugin version (should match pyproject.toml)
- `description`: User-facing description
- `steps`: List of step class names to register
- `ui_components`: (Optional) Map of custom React components for step configuration

## Step Implementation

### Basic Step Structure

Create your step classes in `steps.py`:

```python
from typing import Any, Dict
from graphflow_core.steps.base import StepBase
from graphflow_core.memory.store import MemoryStore


class MyCustomStep(StepBase):
    """
    Description of what this step does.

    This docstring is for developers. Use the 'description'
    class attribute for user-facing documentation.
    """

    # UI Metadata
    label = "My Custom Step"
    description = "User-facing description shown in the UI"
    category = "general"  # control, ai, data, transform, general, etc.

    @classmethod
    def get_type(cls) -> str:
        """Return the step type identifier."""
        return "MyCustomStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Define the JSON schema for step configuration.

        This schema is used to:
        - Validate configuration in graphs
        - Generate auto-configured UI forms
        - Provide parameter documentation
        """
        return {
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of parameter",
                    "default": "default_value"
                },
                "param2": {
                    "type": "number",
                    "description": "Numeric parameter",
                    "minimum": 0,
                    "maximum": 100
                },
                "param3": {
                    "type": "boolean",
                    "description": "Boolean flag"
                }
            },
            "required": ["param1"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute the step logic.

        Args:
            memory: Memory store for reading/writing values

        Note:
            - self.memory_reads: Auto-extracted from {memory.*} in config
            - self.memory_writes: Auto-extracted from {memory.*} in outputs
        """
        # 1. Get configuration
        param1 = self.config.get("param1")
        param2 = self.config.get("param2", 50)

        # 2. Read from memory if needed
        # Memory references in config are automatically parsed
        input_data = None
        for key in self.memory_reads:
            try:
                input_data = memory.read(key)
                break
            except KeyError:
                pass

        # 3. Perform your step logic
        result = self._do_work(param1, param2, input_data)

        # 4. Write results to memory
        # Extract actual memory key from outputs dictionary
        if "result" in self.outputs:
            # Parse {memory.key} from output template
            import re
            pattern = re.compile(r'\{memory\.([^}]+)\}')
            match = pattern.search(self.outputs["result"])
            if match:
                output_key = match.group(1)
                memory.write(output_key, result)

    def _do_work(self, param1, param2, input_data):
        """Your custom logic here."""
        # Implement your step's functionality
        return {"status": "success", "data": "..."}
```

### Step Metadata

#### Class Attributes

- **`label`** (required): Display name in the UI
- **`description`** (required): Help text shown to users
- **`category`** (required): Grouping category for the step palette

**Standard Categories:**

- `control`: Control flow (conditionals, loops, joins)
- `ai`: AI/LLM operations
- `data`: Data fetching and storage
- `transform`: Data transformation
- `general`: General purpose or uncategorized

You can also define custom categories for domain-specific groupings.

### Configuration Schema

The `get_schema()` method should return a JSON Schema (draft 7) defining your step's configuration parameters.

**Supported Types:**

```python
{
    "type": "object",
    "properties": {
        "string_param": {
            "type": "string",
            "description": "String parameter",
            "default": "default",
            "enum": ["option1", "option2"]  # Optional dropdown
        },
        "number_param": {
            "type": "number",
            "description": "Numeric parameter",
            "default": 42,
            "minimum": 0,
            "maximum": 100
        },
        "boolean_param": {
            "type": "boolean",
            "description": "Boolean flag",
            "default": true
        },
        "array_param": {
            "type": "array",
            "description": "List of items",
            "items": {
                "type": "string"
            }
        },
        "object_param": {
            "type": "object",
            "description": "Nested object",
            "properties": {
                "nested_key": {"type": "string"}
            }
        }
    },
    "required": ["string_param"]  # Required fields
}
```

### Memory Operations

Steps interact with shared memory to pass data between nodes:

```python
async def execute(self, memory: MemoryStore) -> None:
    # Read from memory
    value = memory.read("key_name")  # Raises KeyError if not found

    # Check if key exists
    if memory.exists("key_name"):
        value = memory.read("key_name")

    # Write to memory
    memory.write("output_key", {"result": "data"})

    # Update existing value
    memory.update("key_name", new_value)

    # Get all memory state
    state = memory.get_state()  # Returns {inputs, outputs, intermediate}
```

**Memory Scopes:**

- **Inputs**: Initial values provided when starting a graph run
- **Outputs**: Final results returned to the caller
- **Intermediate**: Temporary values passed between steps

> **Note on Debugging:** When running in debug mode, users can edit memory values while execution is paused. Your step may receive modified or unexpected values. Implement defensive validation to handle this gracefully.

**Automatic Memory Tracking:**

GraphFlow automatically tracks memory reads and writes by parsing your step configuration:

- **Memory Reads**: Extracted from `{memory.*}` references in the `config` dictionary
- **Memory Writes**: Extracted from `{memory.*}` references in the `outputs` dictionary

Example in graph definition:

```json
{
    "id": "step1",
    "type": "myplugin.MyCustomStep",
    "config": {
        "input_field": "{memory.input_data}"
    },
    "outputs": {
        "result": "{memory.processed_data}"
    }
}
```

The framework will automatically:
1. Set `self.memory_reads = ["input_data"]`
2. Set `self.memory_writes = ["processed_data"]`
3. Make these available as properties on your step instance

**Helper Pattern for Writing Outputs:**

Since extracting memory keys from outputs is common, consider this reusable pattern:

```python
import re

def _write_output(self, memory: MemoryStore, output_name: str, value: any) -> None:
    """
    Helper to write an output value to memory.

    Args:
        memory: Memory store
        output_name: Name of the output in self.outputs dict
        value: Value to write
    """
    if output_name in self.outputs:
        pattern = re.compile(r'\{memory\.([^}]+)\}')
        match = pattern.search(self.outputs[output_name])
        if match:
            memory_key = match.group(1)
            memory.write(memory_key, value)

# Usage in execute():
async def execute(self, memory: MemoryStore) -> None:
    result = {"status": "success", "data": "..."}
    self._write_output(memory, "result", result)
```

## Complete Example

Here's a complete example plugin that integrates with an external API:

```python
from typing import Any, Dict
import httpx
from graphflow_core.steps.base import StepBase
from graphflow_core.memory.store import MemoryStore


class WeatherLookupStep(StepBase):
    """Fetch weather data from an external API."""

    label = "Weather Lookup"
    description = "Fetch current weather for a location"
    category = "data"

    @classmethod
    def get_type(cls) -> str:
        return "WeatherLookupStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or zip code"
                },
                "api_key": {
                    "type": "string",
                    "description": "Weather API key (or use secrets)"
                },
                "units": {
                    "type": "string",
                    "description": "Temperature units",
                    "enum": ["celsius", "fahrenheit"],
                    "default": "celsius"
                }
            },
            "required": ["location", "api_key"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        # Get configuration
        location = self.config["location"]
        api_key = self.config["api_key"]
        units = self.config.get("units", "celsius")

        # Make API request
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.weather.example.com/current",
                params={
                    "location": location,
                    "units": units,
                    "key": api_key
                }
            )
            response.raise_for_status()
            weather_data = response.json()

        # Write to memory
        # Extract memory key from outputs dictionary
        if "result" in self.outputs:
            import re
            pattern = re.compile(r'\{memory\.([^}]+)\}')
            match = pattern.search(self.outputs["result"])
            if match:
                output_key = match.group(1)
                memory.write(output_key, weather_data)
```

## Installation and Testing

### Development Installation

Install your plugin in development mode for testing:

```bash
cd my-graphflow-plugin
pip install -e .
```

### Verify Installation

Check that your plugin is discoverable:

```python
from importlib.metadata import entry_points

eps = entry_points()
if hasattr(eps, "select"):
    plugins = eps.select(group="graphflow.plugins")
else:
    plugins = eps.get("graphflow.plugins", [])

for ep in plugins:
    print(f"Found plugin: {ep.name} -> {ep.value}")
```

### Test with GraphFlow

1. **Restart the runtime** to discover the plugin:

```bash
graphflow-runtime --port 8000
```

You should see: `✓ Loaded N plugin(s)`

2. **Check the API** to verify your steps are available:

```bash
curl http://localhost:8000/api/v1/plugins
curl http://localhost:8000/api/v1/steps | jq '.[] | select(.plugin=="myplugin")'
```

3. **Open the UI** and look for your steps in the palette under their category

### Distribution

To distribute your plugin:

1. **Build the package:**

```bash
pip install build
python -m build
```

2. **Publish to PyPI:**

```bash
pip install twine
twine upload dist/*
```

3. **Install from PyPI:**

```bash
pip install my-graphflow-plugin
```

## Advanced Topics

### Debugging Support

GraphFlow includes a built-in debugger that allows users to:
- Set breakpoints before and after step execution
- Step through graph execution one node at a time
- Pause/resume execution
- Inspect and edit memory values while paused

**Good news:** This is completely transparent to plugin developers. The debugging infrastructure wraps your step's `execute()` method automatically - you don't need to add any debugging hooks or special code.

**What you should know:**
- Your step may pause mid-execution if the user sets a breakpoint
- Memory values may be modified by users during debugging (see Input Validation best practices)
- Execution timing may be affected during debug runs

### Error Handling

Implement robust error handling in your steps:

```python
async def execute(self, memory: MemoryStore) -> None:
    import re

    try:
        # Your logic here
        result = await self._do_api_call()

        # Write success result
        if "result" in self.outputs:
            pattern = re.compile(r'\{memory\.([^}]+)\}')
            match = pattern.search(self.outputs["result"])
            if match:
                output_key = match.group(1)
                memory.write(output_key, result)

    except httpx.HTTPError as e:
        # Log the error
        logger.error(f"API call failed: {e}")

        # Optionally write error state
        if "result" in self.outputs:
            pattern = re.compile(r'\{memory\.([^}]+)\}')
            match = pattern.search(self.outputs["result"])
            if match:
                output_key = match.group(1)
                memory.write(output_key, {
                    "error": str(e),
                    "status": "failed"
                })
        # Re-raise to stop graph execution
        raise
```

### Validation

Add custom validation logic:

```python
def validate_config(self) -> List[str]:
    """
    Validate step configuration.

    Returns:
        List of error messages (empty if valid)
    """
    errors = []

    if "api_key" in self.config:
        if not self.config["api_key"].startswith("sk-"):
            errors.append("API key must start with 'sk-'")

    if "timeout" in self.config:
        if self.config["timeout"] < 0:
            errors.append("Timeout must be positive")

    return errors
```

### Async Operations

Steps should use async/await for I/O operations:

```python
async def execute(self, memory: MemoryStore) -> None:
    # Good: Non-blocking I/O
    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    # Good: Concurrent operations
    results = await asyncio.gather(
        self._fetch_data_1(),
        self._fetch_data_2(),
        self._fetch_data_3()
    )
```

### Custom UI Components (Future)

The plugin system supports custom React components for step configuration:

```json
{
    "ui_components": {
        "MyCustomStep": "components/MyStepConfig.tsx"
    }
}
```

This feature is planned for future releases.

## Best Practices

### Naming Conventions

- **Plugin name**: Use kebab-case (e.g., `graphflow-slack-integration`)
- **Python package**: Use snake_case (e.g., `graphflow_slack_integration`)
- **Entry point**: Use lowercase, no separators (e.g., `slack`)
- **Step classes**: Use PascalCase with "Step" suffix (e.g., `SendMessageStep`)

### Step Design

1. **Single Responsibility**: Each step should do one thing well
2. **Configurability**: Make steps flexible through configuration
3. **Error Messages**: Provide clear, actionable error messages
4. **Documentation**: Document all configuration parameters
5. **Idempotency**: Where possible, make steps idempotent

### Performance

- Use async/await for I/O operations
- Avoid blocking operations in execute()
- Clean up resources properly
- Consider timeouts for external API calls

### Security

- Never hardcode secrets in step code
- Use the secrets system for sensitive configuration
- Validate all user inputs
- Sanitize data from external sources

### Input Validation

Always validate data read from memory, especially since:
- Memory values can be edited by users during debugging
- Previous steps may fail or produce unexpected output
- Type coercion may be needed for robustness

```python
async def execute(self, memory: MemoryStore) -> None:
    # Read and validate
    value = memory.read("input_data")

    # Type checking
    if not isinstance(value, str):
        raise ValueError(f"Expected string, got {type(value).__name__}")

    # Range validation
    if len(value) > 1000:
        raise ValueError("Input too large (max 1000 characters)")

    # Process validated data
    result = self._process(value)
```

### Testing

Create unit tests for your steps:

```python
import pytest
from graphflow_core.memory.store import MemoryStore
from my_plugin.steps import MyCustomStep

@pytest.mark.asyncio
async def test_my_custom_step():
    # Create step
    step = MyCustomStep(
        id="test",
        config={"param1": "value"},
        outputs={"result": "{memory.output}"}
    )

    # Create memory store
    memory = MemoryStore()
    memory.write("input", "test data")

    # Execute step
    await step.execute(memory)

    # Assert results
    result = memory.read("output")
    assert result["status"] == "success"
```

## Examples

See the `graphflow-plugin-example` package in the GraphFlow repository for a complete working example with:

- Email notification step
- Slack notification step
- Proper package structure
- Full documentation

## Support

- **Documentation**: https://docs.graphflow.dev (coming soon)
- **Issues**: https://github.com/msharpe248/graphflow/issues
- **Discussions**: https://github.com/msharpe248/graphflow/discussions

## License

Plugin packages can use any license. We recommend MIT for maximum compatibility.
