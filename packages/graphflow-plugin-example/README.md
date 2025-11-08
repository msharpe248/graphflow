# GraphFlow Example Plugin

This is an example plugin package demonstrating how to create custom step types for GraphFlow.

## Features

This plugin provides three example steps:

- **EmailStep**: Send email notifications with template support
- **SlackNotificationStep**: Send messages to Slack channels
- **EditorShowcaseStep**: Demonstrates all 11 available custom editors

## Installation

Install in development mode from the GraphFlow monorepo:

```bash
cd packages/graphflow-plugin-example
pip install -e .
```

## Usage

Once installed, the plugin steps will automatically be discovered by GraphFlow at runtime. They will appear in the UI step palette with namespaced types:

- `example.EmailStep` - notification category
- `example.SlackNotificationStep` - notification category
- `example.EditorShowcaseStep` - example category

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

**IMPORTANT**: The manifest.json file is **required** and is the **only** way to register plugin steps. Steps not listed in the manifest will not be registered, even if they are properly imported in `__init__.py`.

**Do NOT use decorators** like `@StepRegistry.register()` for plugin steps. All registration happens through the manifest.

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

The `steps` array must contain the class names of all steps you want to expose. When you add a new step class:
1. Create the step class in your steps module
2. Import it in `__init__.py`
3. **Add the class name to the manifest.json `steps` array**
4. Restart the GraphFlow runtime for changes to take effect

Your step will appear in the UI with a namespaced type: `myplugin.MyCustomStep`

### 4. Implement Steps

Create step classes that inherit from `StepBase`. Steps are registered via the manifest.json file (not decorators) and will appear in the UI with namespaced types like `myplugin.MyCustomStep`.

**Important**: Each step class must define:
- `label` (str): Display name in the UI (e.g., "My Custom Step")
- `description` (str): Help text shown in the UI
- `get_type()` method: Returns a simple identifier (used internally, not shown in UI)

```python
import re
from typing import Any, Dict
from graphflow_core.steps.base import StepBase
from graphflow_core.memory.store import MemoryStore

class MyCustomStep(StepBase):
    """
    Example custom step.

    This step will appear in the UI as 'myplugin.MyCustomStep'.
    """

    # Required class attributes for UI display
    label = "My Custom Step"
    description = "Does something custom"

    @classmethod
    def get_type(cls) -> str:
        """Internal type identifier (not shown in UI)."""
        return "custom"

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

## Step Naming and Display

### How Steps Appear in the UI

When you create a plugin step, it will be displayed with a **namespaced type**:

- **Type in API/graphs**: `pluginname.ClassName` (e.g., `example.EmailStep`)
- **Display name in UI**: Uses the `label` attribute (e.g., "Send Email")
- **Description**: Uses the `description` attribute

### Required Class Attributes

Each step class **must** define these class attributes:

- `label` (str): **Required**. Display name in the UI (e.g., "Send Email", "HTTP GET")
- `description` (str): **Required**. Help text shown in the step palette (e.g., "Send email notifications with template support")

### Optional Class Attributes

- `category` (str): Category for grouping steps in the UI. If not specified, steps use their plugin's category. Common categories:
  - `control` - Flow control (conditional, loop, etc.)
  - `ai` - AI/LLM operations
  - `data` - Data manipulation
  - `transform` - Data transformation
  - `notification` - Alerts and notifications
  - `http` - HTTP/web operations
  - `general` - General purpose

### Example

```python
class EmailStep(StepBase):
    label = "Send Email"  # Required - shown in UI
    description = "Send email notifications with template support"  # Required
    # category not specified - will use plugin's category

    @classmethod
    def get_type(cls) -> str:
        return "email"  # Internal identifier (not shown in UI)
```

Result in UI:
- Type: `example.EmailStep`
- Display: "Send Email"
- Help text: "Send email notifications with template support"

## Configuration Schema

Use `get_schema()` to define the JSON schema for your step's configuration. This is used to:

- Validate configuration in graphs
- Generate auto-configured UI forms
- Provide documentation

## Custom Editors

GraphFlow provides 11 specialized editors that you can use for step properties. By default, properties use editors based on their JSON Schema type (string, number, boolean, object, array). You can request specific editors using the `x-editor` field in your property schema.

### Available Editors

#### Inline Editors (displayed directly in the form)

1. **String Editor** (default for `type: "string"`)
   ```json
   {
     "type": "string",
     "description": "A text input"
   }
   ```

2. **Number Editor** (default for `type: "number"` or `type: "integer"`)
   ```json
   {
     "type": "number",
     "description": "A numeric input"
   }
   ```

3. **Boolean Editor** (default for `type: "boolean"`)
   ```json
   {
     "type": "boolean",
     "description": "A toggle switch",
     "default": false
   }
   ```

4. **Date Picker**
   ```json
   {
     "type": "string",
     "x-editor": "date",
     "description": "Date selection in YYYY-MM-DD format"
   }
   ```

5. **Time Editor**
   ```json
   {
     "type": "string",
     "x-editor": "time",
     "description": "Time selection in HH:MM format (24-hour)"
   }
   ```

6. **DateTime Picker**
   ```json
   {
     "type": "string",
     "x-editor": "datetime",
     "description": "Date and time in ISO 8601 format"
   }
   ```

#### Modal Editors (opened in a dedicated modal dialog)

7. **JSON Editor** (default for `type: "object"` or `type: "array"`)
   ```json
   {
     "type": "object",
     "x-editor": "json",
     "description": "Structured JSON data with syntax highlighting"
   }
   ```

8. **Key-Value Editor**
   ```json
   {
     "type": "object",
     "x-editor": "keyvalue",
     "description": "Simple key-value pairs (e.g., HTTP headers, environment variables)"
   }
   ```

9. **Color Picker**
   ```json
   {
     "type": "string",
     "x-editor": "color",
     "description": "Visual color picker",
     "default": "#3b82f6"
   }
   ```

10. **Table Editor**
    ```json
    {
      "type": "object",
      "x-editor": "table",
      "description": "Tabular data with custom columns",
      "x-editor-config": {
        "columns": [
          {"key": "name", "label": "Name", "placeholder": "Enter name"},
          {"key": "value", "label": "Value", "placeholder": "Enter value"}
        ],
        "initialRows": 2,
        "addRowLabel": "Add Row",
        "emptyMessage": "No rows defined"
      }
    }
    ```

11. **Markdown Editor**
    ```json
    {
      "type": "string",
      "x-editor": "markdown",
      "description": "Markdown content with live preview"
    }
    ```

### Editor Configuration

Some editors support additional configuration via `x-editor-config`:

- **Table Editor**: Define columns, initial rows, labels, and messages
- Future editors may support additional configuration options

### Example: Using Custom Editors

```python
@classmethod
def get_schema(cls) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            # Inline editors
            "api_key": {
                "type": "string",
                "description": "API key for authentication"
            },
            "timeout": {
                "type": "number",
                "description": "Timeout in seconds",
                "default": 30
            },
            "enabled": {
                "type": "boolean",
                "description": "Enable this feature",
                "default": True
            },
            "schedule_date": {
                "type": "string",
                "x-editor": "date",
                "description": "When to run this task"
            },

            # Modal editors
            "headers": {
                "type": "object",
                "x-editor": "keyvalue",
                "description": "HTTP headers to send"
            },
            "theme_color": {
                "type": "string",
                "x-editor": "color",
                "description": "Brand color",
                "default": "#3b82f6"
            },
            "description": {
                "type": "string",
                "x-editor": "markdown",
                "description": "Step documentation"
            },
            "mapping": {
                "type": "object",
                "x-editor": "table",
                "description": "Field mappings",
                "x-editor-config": {
                    "columns": [
                        {"key": "source", "label": "Source Field", "placeholder": "e.g., user_id"},
                        {"key": "target", "label": "Target Field", "placeholder": "e.g., id"}
                    ],
                    "initialRows": 3,
                    "addRowLabel": "Add Mapping",
                    "emptyMessage": "No mappings defined"
                }
            }
        },
        "required": []
    }
```

See the `EditorShowcaseStep` in this plugin for a complete working example of all 11 editors.

## Testing

After installing your plugin, restart the GraphFlow runtime:

```bash
graphflow-runtime --port 8000
```

The plugin should be discovered automatically and its steps will appear in the UI.

## License

MIT
