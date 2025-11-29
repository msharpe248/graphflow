"""Tests for extraction and substring steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_text.extraction import (
    SubstringStep,
    TextTruncateStep,
)


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


class TestSubstringStep:
    @pytest.mark.asyncio
    async def test_substring_start_only(self, mock_memory):
        mock_memory._data["memory.text"] = "hello world"

        step = SubstringStep(
            id="test",
            config={"input": "{memory.text}", "start": 6},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "world"

    @pytest.mark.asyncio
    async def test_substring_start_and_end(self, mock_memory):
        mock_memory._data["memory.text"] = "hello world"

        step = SubstringStep(
            id="test",
            config={"input": "{memory.text}", "start": 0, "end": 5},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello"

    @pytest.mark.asyncio
    async def test_substring_negative_index(self, mock_memory):
        mock_memory._data["memory.text"] = "hello world"

        step = SubstringStep(
            id="test",
            config={"input": "{memory.text}", "start": -5},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "world"

    @pytest.mark.asyncio
    async def test_substring_negative_end(self, mock_memory):
        mock_memory._data["memory.text"] = "hello world"

        step = SubstringStep(
            id="test",
            config={"input": "{memory.text}", "start": 0, "end": -6},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello"


class TestTextTruncateStep:
    @pytest.mark.asyncio
    async def test_truncate_with_suffix(self, mock_memory):
        mock_memory._data["memory.text"] = "This is a long sentence that needs truncating"

        step = TextTruncateStep(
            id="test",
            config={"input": "{memory.text}", "max_length": 20, "suffix": "..."},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "This is a long se..."
        assert len(mock_memory._data["memory.result"]) == 20

    @pytest.mark.asyncio
    async def test_truncate_no_truncation_needed(self, mock_memory):
        mock_memory._data["memory.text"] = "Short"

        step = TextTruncateStep(
            id="test",
            config={"input": "{memory.text}", "max_length": 20, "suffix": "..."},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Short"

    @pytest.mark.asyncio
    async def test_truncate_word_boundary(self, mock_memory):
        mock_memory._data["memory.text"] = "This is a long sentence"

        step = TextTruncateStep(
            id="test",
            config={"input": "{memory.text}", "max_length": 15, "suffix": "...", "word_boundary": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        # Should truncate at word boundary before "long"
        result = mock_memory._data["memory.result"]
        assert result.endswith("...")
        assert len(result) <= 15

    @pytest.mark.asyncio
    async def test_truncate_custom_suffix(self, mock_memory):
        mock_memory._data["memory.text"] = "This is a test string"

        step = TextTruncateStep(
            id="test",
            config={"input": "{memory.text}", "max_length": 15, "suffix": " [more]"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"].endswith(" [more]")
        assert len(mock_memory._data["memory.result"]) == 15
