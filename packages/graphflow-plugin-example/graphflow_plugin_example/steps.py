"""
Example Custom Step Types

Demonstrates how to create custom step types for GraphFlow.
"""

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
                    "description": "Email body template (supports {{var}} syntax)"
                },
                "from_email": {
                    "type": "string",
                    "description": "Sender email address",
                    "default": "noreply@example.com"
                }
            },
            "required": ["to", "subject", "body_template"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute email sending logic.

        In a real implementation, this would send an actual email.
        For this example, we just log the action and store the result.
        """
        # Get configuration
        to = self.config.get("to", "")
        subject = self.config.get("subject", "")
        body_template = self.config.get("body_template", "")
        from_email = self.config.get("from_email", "noreply@example.com")

        # Read any required values from memory
        # (example: substitute template variables from memory)
        context = {}
        for key in self.memory_reads:
            try:
                context[key] = memory.read(key)
            except KeyError:
                pass

        # Simple template substitution
        body = body_template
        for key, value in context.items():
            body = body.replace(f"{{{{{key}}}}}", str(value))

        # In a real implementation, send the email here
        # For now, just create a result
        result = {
            "status": "sent",
            "to": to,
            "subject": subject,
            "from": from_email,
            "timestamp": "2024-01-01T00:00:00Z"  # Would use actual timestamp
        }

        # Write result to memory
        if self.memory_writes:
            memory.write(self.memory_writes[0], result)


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
                    "description": "Message template (supports {{var}} syntax)"
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

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute Slack notification logic.

        In a real implementation, this would post to Slack's API.
        For this example, we simulate the action.
        """
        # Get configuration
        channel = self.config.get("channel", "#general")
        message_template = self.config.get("message_template", "")
        username = self.config.get("username", "GraphFlow Bot")
        icon_emoji = self.config.get("icon_emoji", ":robot_face:")

        # Read context from memory
        context = {}
        for key in self.memory_reads:
            try:
                context[key] = memory.read(key)
            except KeyError:
                pass

        # Simple template substitution
        message = message_template
        for key, value in context.items():
            message = message.replace(f"{{{{{key}}}}}", str(value))

        # In a real implementation, post to Slack here
        # For now, create a result
        result = {
            "status": "sent",
            "channel": channel,
            "message": message,
            "username": username,
            "timestamp": "2024-01-01T00:00:00Z"
        }

        # Write result to memory
        if self.memory_writes:
            memory.write(self.memory_writes[0], result)
