"""Tests for HumanInputStep."""
import pytest
from unittest.mock import MagicMock

from graphflow_ai import HumanInputStep


@pytest.fixture
def mock_memory():
    """Create a mock memory store."""
    memory = MagicMock()
    memory._data = {}

    def read(key):
        if key in memory._data:
            return memory._data[key]
        raise KeyError(f"Key not found: {key}")

    def write(key, value):
        memory._data[key] = value

    memory.read = MagicMock(side_effect=read)
    memory.write = MagicMock(side_effect=write)
    return memory


class TestHumanInputStep:
    def test_get_type(self):
        assert HumanInputStep.get_type() == "human_input"

    def test_get_schema_has_prompt(self):
        schema = HumanInputStep.get_schema()
        assert "prompt" in schema["properties"]

    def test_get_schema_has_input_type(self):
        schema = HumanInputStep.get_schema()
        assert "input_type" in schema["properties"]
        # Should support text, choice, approval
        assert "enum" in schema["properties"]["input_type"]
        assert "text" in schema["properties"]["input_type"]["enum"]
        assert "choice" in schema["properties"]["input_type"]["enum"]
        assert "approval" in schema["properties"]["input_type"]["enum"]

    def test_get_schema_has_output_key(self):
        schema = HumanInputStep.get_schema()
        assert "output_key" in schema["properties"]

    def test_step_creation(self):
        """Test that HumanInputStep can be instantiated."""
        step = HumanInputStep(
            id="test_human",
            config={
                "prompt": "Please enter your name:",
                "input_type": "text",
                "output_key": "user_name"
            },
            outputs={}
        )

        assert step.id == "test_human"
        assert step.config["prompt"] == "Please enter your name:"
        assert step.config["input_type"] == "text"

    def test_step_with_choices(self):
        """Test HumanInputStep with choice type."""
        step = HumanInputStep(
            id="test_choice",
            config={
                "prompt": "Select an option:",
                "input_type": "choice",
                "choices": ["Option A", "Option B", "Option C"],
                "output_key": "selected_option"
            },
            outputs={}
        )

        assert step.config["input_type"] == "choice"
        assert len(step.config["choices"]) == 3

    def test_step_with_approval(self):
        """Test HumanInputStep with approval type."""
        step = HumanInputStep(
            id="test_approval",
            config={
                "prompt": "Do you approve this action?",
                "input_type": "approval",
                "output_key": "is_approved"
            },
            outputs={}
        )

        assert step.config["input_type"] == "approval"
