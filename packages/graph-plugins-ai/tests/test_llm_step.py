"""Tests for LLM step."""
import pytest
from unittest.mock import MagicMock

from graphflow_ai import LLMStep


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


class TestLLMStep:
    def test_get_type(self):
        assert LLMStep.get_type() == "llm"

    def test_get_schema_has_provider(self):
        schema = LLMStep.get_schema()
        assert "provider" in schema["properties"]

    def test_get_schema_has_model(self):
        schema = LLMStep.get_schema()
        assert "model" in schema["properties"]

    def test_get_schema_has_system_prompt(self):
        schema = LLMStep.get_schema()
        assert "system_prompt" in schema["properties"]

    def test_get_schema_has_user_prompt(self):
        schema = LLMStep.get_schema()
        assert "user_prompt" in schema["properties"]

    def test_get_schema_has_temperature(self):
        schema = LLMStep.get_schema()
        assert "temperature" in schema["properties"]

    def test_get_schema_has_history_enabled(self):
        schema = LLMStep.get_schema()
        assert "history_enabled" in schema["properties"]
        assert schema["properties"]["history_enabled"]["type"] == "boolean"

    def test_step_creation(self):
        """Test that LLMStep can be instantiated."""
        step = LLMStep(
            id="test_llm",
            config={
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "system_prompt": "You are a helpful assistant.",
                "user_prompt": "Hello!"
            },
            outputs={"response": "{memory.result}"}
        )

        assert step.id == "test_llm"
        assert step.config["provider"] == "openai"
        assert step.config["model"] == "gpt-3.5-turbo"

    @pytest.mark.asyncio
    async def test_execute_with_mock(self, mock_memory):
        """Test LLM execution with built-in mock response."""
        step = LLMStep(
            id="test_llm",
            config={
                "provider": "ollama",
                "model": "llama3.2",
                "system_prompt": "You are a helpful assistant.",
                "user_prompt": "{memory.user_message}"
            },
            outputs={"response": "{memory.result}"}
        )

        mock_memory._data["user_message"] = "What is 2+2?"

        # Execute uses built-in mock response
        await step.execute(mock_memory)

        # Verify output was written
        assert "result" in mock_memory._data
        assert "Mock LLM response" in mock_memory._data["result"]

    @pytest.mark.asyncio
    async def test_history_enabled(self, mock_memory):
        """Test that history_enabled config option is supported."""
        step = LLMStep(
            id="test_llm",
            config={
                "provider": "ollama",
                "model": "llama3.2",
                "system_prompt": "You are a helpful assistant.",
                "user_prompt": "{memory.user_message}",
                "history_enabled": True
            },
            outputs={"response": "{memory.result}"}
        )

        mock_memory._data["user_message"] = "Hello"

        # Execute uses built-in mock response
        await step.execute(mock_memory)

        # Verify output was written
        assert "result" in mock_memory._data
        assert "Mock LLM response" in mock_memory._data["result"]
