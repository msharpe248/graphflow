# GraphFlow Example Plugin

This is an example plugin package demonstrating how to create custom step types for GraphFlow.

## Features

This plugin provides two example notification steps:

- **EmailStep**: Send email notifications with template support
- **SlackNotificationStep**: Send messages to Slack channels

## Installation

Install in development mode from the GraphFlow monorepo:

```bash
cd packages/graphflow-plugin-example
pip install -e .
```

## Usage

Once installed, the plugin steps will automatically be discovered by GraphFlow at runtime. They will appear in the UI step palette under the "notification" category with namespaced types:

- `example.EmailStep`
- `example.SlackNotificationStep`

## Creating Your Own Plugin

To create your own GraphFlow plugin, follow this structure:

### 1. Package Structure

```
my-plugin/
├── pyproject.toml
├── README.md
└── my_plugin/
    ├── __init__.py
    ├── manifest.json
    └── steps.py
```

### 2. pyproject.toml

Define the entry point:

```toml
[project.entry-points."graphflow.plugins"]
myplugin = "my_plugin"
```

### 3. manifest.json

List your step types:

```json
{
  "name": "myplugin",
  "version": "0.1.0",
  "description": "My custom GraphFlow plugin",
  "steps": [
    "MyCustomStep"
  ],
  "ui_components": {}
}
```

### 4. Implement Steps

Create step classes that inherit from `StepBase`:

```python
import re
from typing import Any, Dict
from graphflow_core.steps.base import StepBase
from graphflow_core.memory.store import MemoryStore

class MyCustomStep(StepBase):
    label = "My Custom Step"
    description = "Does something custom"
    category = "general"

    @classmethod
    def get_type(cls) -> str:
        return "MyCustomStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Configuration schema - parameters that control step behavior."""
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "param": {
                    "type": "string",
                    "description": "A configuration parameter"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """Describes what this step reads from memory."""
        return {
            "type": "object",
            "properties": {
                "data": {
                    "type": "string",
                    "description": "Input data to process"
                }
            },
            "required": ["data"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """Describes what this step writes to memory."""
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "Processing result"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute step logic."""
        # Parse memory references from config
        pattern = re.compile(r'\{memory\.([^}]+)\}')

        # Read input from memory
        input_config = self.config.get("input", "")
        match = pattern.search(input_config)
        if match:
            input_key = match.group(1)
            input_value = memory.read(input_key)

        # Process data
        result = {
            "status": "success",
            "data": input_value
        }

        # Write output to memory
        if "result" in self.outputs:
            output_template = self.outputs["result"]
            match = pattern.search(output_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, result)
```

## Step Metadata

Each step class should define these class attributes for the UI:

- `label`: Display name in the UI
- `description`: Help text
- `category`: Category for grouping (control, ai, data, transform, general, notification, etc.)

## Configuration Schema

Use `get_schema()` to define the JSON schema for your step's configuration. This is used to:

- Validate configuration in graphs
- Generate auto-configured UI forms
- Provide documentation

## Testing

After installing your plugin, restart the GraphFlow runtime:

```bash
graphflow-runtime --port 8000
```

The plugin should be discovered automatically and its steps will appear in the UI.

## License

MIT
