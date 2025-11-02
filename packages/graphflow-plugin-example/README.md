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
        return {
            "type": "object",
            "properties": {
                "my_config": {
                    "type": "string",
                    "description": "Configuration parameter"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        # Your step logic here
        value = self.config.get("my_config")
        # ...
        if self.memory_writes:
            memory.write(self.memory_writes[0], result)
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
