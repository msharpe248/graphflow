"""
Example Custom Step Types

Demonstrates how to create custom step types for GraphFlow.
"""

import re
from typing import Any, Dict
from graphflow_core.steps.base import StepBase
from graphflow_core.memory.store import MemoryStore


class EmailStep(StepBase):
    """
    Example step that sends an email.

    This is a demonstration step showing how to create custom actions.
    In a real implementation, this would integrate with an email service.
    """

    # Step metadata for UI
    label = "Send Email"
    description = "Send an email notification"
    category = "notification"

    @classmethod
    def get_type(cls) -> str:
        return "EmailStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "to": {
                    "type": "string",
                    "description": "Recipient email address"
                },
                "subject": {
                    "type": "string",
                    "description": "Email subject"
                },
                "body_template": {
                    "type": "string",
                    "description": "Email body template (supports {memory.var} syntax)"
                },
                "from_email": {
                    "type": "string",
                    "description": "Sender email address",
                    "default": "noreply@example.com"
                }
            },
            "required": ["to", "subject", "body_template"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "description": "This step can reference any memory variables in its config fields using {memory.var} syntax",
            "properties": {}
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "Email sending result with status, timestamp, and details"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute email sending logic.

        In a real implementation, this would send an actual email.
        For this example, we just log the action and store the result.
        """
        # Parse memory references
        pattern = re.compile(r'\{memory\.([^}]+)\}')

        # Get configuration and resolve memory references
        to = self.config.get("to", "")
        subject = self.config.get("subject", "")
        body_template = self.config.get("body_template", "")
        from_email = self.config.get("from_email", "noreply@example.com")

        # Resolve memory references in config fields
        def resolve_memory_refs(value: str) -> str:
            """Replace {memory.var} references with actual values."""
            if not isinstance(value, str):
                return value

            def replacer(match):
                key = match.group(1)
                try:
                    return str(memory.read(key))
                except KeyError:
                    return match.group(0)  # Keep original if not found

            return pattern.sub(replacer, value)

        # Resolve all config values
        to = resolve_memory_refs(to)
        subject = resolve_memory_refs(subject)
        body = resolve_memory_refs(body_template)
        from_email = resolve_memory_refs(from_email)

        # In a real implementation, send the email here
        # For now, just create a result
        result = {
            "status": "sent",
            "to": to,
            "subject": subject,
            "from": from_email,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }

        # Write output to memory
        if "result" in self.outputs:
            output_template = self.outputs["result"]
            match = pattern.search(output_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, result)


class SlackNotificationStep(StepBase):
    """
    Example step that sends a Slack notification.

    Demonstrates integrating with an external service.
    """

    # Step metadata for UI
    label = "Slack Notification"
    description = "Send a message to Slack"
    category = "notification"

    @classmethod
    def get_type(cls) -> str:
        return "SlackNotificationStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "channel": {
                    "type": "string",
                    "description": "Slack channel (e.g., #general)"
                },
                "message_template": {
                    "type": "string",
                    "description": "Message template (supports {memory.var} syntax)"
                },
                "webhook_url": {
                    "type": "string",
                    "description": "Slack webhook URL (or use secret)"
                },
                "username": {
                    "type": "string",
                    "description": "Bot username",
                    "default": "GraphFlow Bot"
                },
                "icon_emoji": {
                    "type": "string",
                    "description": "Bot icon emoji",
                    "default": ":robot_face:"
                }
            },
            "required": ["channel", "message_template"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "description": "This step can reference any memory variables in its config fields using {memory.var} syntax",
            "properties": {}
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "result": {
                    "type": "object",
                    "description": "Slack notification result with status, timestamp, and details"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute Slack notification logic.

        In a real implementation, this would post to Slack's API.
        For this example, we simulate the action.
        """
        # Parse memory references
        pattern = re.compile(r'\{memory\.([^}]+)\}')

        # Get configuration
        channel = self.config.get("channel", "#general")
        message_template = self.config.get("message_template", "")
        username = self.config.get("username", "GraphFlow Bot")
        icon_emoji = self.config.get("icon_emoji", ":robot_face:")

        # Resolve memory references in config fields
        def resolve_memory_refs(value: str) -> str:
            """Replace {memory.var} references with actual values."""
            if not isinstance(value, str):
                return value

            def replacer(match):
                key = match.group(1)
                try:
                    return str(memory.read(key))
                except KeyError:
                    return match.group(0)  # Keep original if not found

            return pattern.sub(replacer, value)

        # Resolve all config values
        channel = resolve_memory_refs(channel)
        message = resolve_memory_refs(message_template)
        username = resolve_memory_refs(username)
        icon_emoji = resolve_memory_refs(icon_emoji)

        # In a real implementation, post to Slack here
        # For now, create a result
        result = {
            "status": "sent",
            "channel": channel,
            "message": message,
            "username": username,
            "timestamp": "2024-01-01T00:00:00Z"
        }

        # Write output to memory
        if "result" in self.outputs:
            output_template = self.outputs["result"]
            match = pattern.search(output_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, result)


class EditorShowcaseStep(StepBase):
    """
    Showcase step demonstrating all available custom editors.

    This step does nothing but provides examples of all editor types
    for documentation and testing purposes.
    """

    # Step metadata for UI
    label = "Editor Showcase"
    description = "Demonstrates all available custom editors (no-op step for documentation)"
    category = "example"

    @classmethod
    def get_type(cls) -> str:
        return "EditorShowcaseStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                # String editor (default)
                "text_field": {
                    "type": "string",
                    "description": "Simple text input (string editor)"
                },
                # Number editor
                "number_field": {
                    "type": "number",
                    "description": "Numeric input (number editor)"
                },
                # Boolean editor (checkbox)
                "boolean_field": {
                    "type": "boolean",
                    "description": "Toggle switch (boolean editor)",
                    "default": False
                },
                # JSON editor
                "json_field": {
                    "type": "object",
                    "description": "JSON data (json editor - modal)",
                    "x-editor": "json"
                },
                # Key-Value editor
                "keyvalue_field": {
                    "type": "object",
                    "description": "Key-value pairs (keyvalue editor - modal)",
                    "x-editor": "keyvalue"
                },
                # Color picker
                "color_field": {
                    "type": "string",
                    "description": "Color selection (color picker - modal)",
                    "x-editor": "color",
                    "default": "#3b82f6"
                },
                # Table editor
                "table_field": {
                    "type": "object",
                    "description": "Tabular data (table editor - modal)",
                    "x-editor": "table",
                    "x-editor-config": {
                        "columns": [
                            {"key": "name", "label": "Name", "placeholder": "Item name"},
                            {"key": "value", "label": "Value", "placeholder": "Item value"}
                        ],
                        "initialRows": 2,
                        "addRowLabel": "Add Item",
                        "emptyMessage": "No items defined"
                    }
                },
                # Markdown editor
                "markdown_field": {
                    "type": "string",
                    "description": "Markdown content (markdown editor - modal)",
                    "x-editor": "markdown"
                },
                # Date picker
                "date_field": {
                    "type": "string",
                    "description": "Date selection (date picker - inline)",
                    "x-editor": "date"
                },
                # Time picker
                "time_field": {
                    "type": "string",
                    "description": "Time selection (time editor - inline)",
                    "x-editor": "time"
                },
                # DateTime picker
                "datetime_field": {
                    "type": "string",
                    "description": "Date and time selection (datetime picker - inline)",
                    "x-editor": "datetime"
                }
            },
            "required": []
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "description": "No inputs required - this is a showcase step",
            "properties": {}
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "showcase_data": {
                    "type": "object",
                    "description": "All configured editor values (for testing)"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """
        No-op execution - just collects all editor values for output.

        This step doesn't perform any real action, it's purely for
        showcasing the different editor types available.
        """
        # Collect all config values
        showcase_data = {
            "text_field": self.config.get("text_field"),
            "number_field": self.config.get("number_field"),
            "boolean_field": self.config.get("boolean_field"),
            "json_field": self.config.get("json_field"),
            "keyvalue_field": self.config.get("keyvalue_field"),
            "color_field": self.config.get("color_field"),
            "table_field": self.config.get("table_field"),
            "markdown_field": self.config.get("markdown_field"),
            "date_field": self.config.get("date_field"),
            "time_field": self.config.get("time_field"),
            "datetime_field": self.config.get("datetime_field"),
        }

        # Write output to memory if configured
        if "showcase_data" in self.outputs:
            output_template = self.outputs["showcase_data"]
            pattern = re.compile(r'\{memory\.([^}]+)\}')
            match = pattern.search(output_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, showcase_data)
