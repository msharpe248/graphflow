"""
GraphFlow Example Plugin

Demonstrates how to create custom step types for GraphFlow.
"""

__version__ = "0.1.0"

# Import step classes to make them available
from graphflow_plugin_example.steps import EmailStep, SlackNotificationStep, EditorShowcaseStep

__all__ = ["EmailStep", "SlackNotificationStep", "EditorShowcaseStep"]
