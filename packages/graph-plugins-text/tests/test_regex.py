"""Tests for regex steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_text.regex import (
    RegexMatchStep,
    RegexReplaceStep,
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


class TestRegexMatchStep:
    @pytest.mark.asyncio
    async def test_match_first(self, mock_memory):
        mock_memory._data["memory.text"] = "The quick brown fox"

        step = RegexMatchStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"\b\w{5}\b"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "quick"
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_match_all(self, mock_memory):
        mock_memory._data["memory.text"] = "The quick brown fox"

        step = RegexMatchStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"\b\w{5}\b", "find_all": True},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["quick", "brown"]
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_match_not_found(self, mock_memory):
        mock_memory._data["memory.text"] = "The quick brown fox"

        step = RegexMatchStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"\d+"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] is None
        assert mock_memory._data["memory.found"] is False

    @pytest.mark.asyncio
    async def test_match_groups(self, mock_memory):
        mock_memory._data["memory.text"] = "John Doe (john@example.com)"

        step = RegexMatchStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"(\w+)@(\w+\.\w+)", "groups": True},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["john", "example.com"]
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_match_case_insensitive(self, mock_memory):
        mock_memory._data["memory.text"] = "Hello World"

        step = RegexMatchStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"hello", "flags": "i"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Hello"
        assert mock_memory._data["memory.found"] is True


class TestRegexReplaceStep:
    @pytest.mark.asyncio
    async def test_replace_all(self, mock_memory):
        mock_memory._data["memory.text"] = "foo bar foo baz foo"

        step = RegexReplaceStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"foo", "replacement": "qux"},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "qux bar qux baz qux"
        assert mock_memory._data["memory.count"] == 3

    @pytest.mark.asyncio
    async def test_replace_with_count(self, mock_memory):
        mock_memory._data["memory.text"] = "foo bar foo baz foo"

        step = RegexReplaceStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"foo", "replacement": "qux", "count": 2},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "qux bar qux baz foo"
        assert mock_memory._data["memory.count"] == 2

    @pytest.mark.asyncio
    async def test_replace_with_groups(self, mock_memory):
        mock_memory._data["memory.text"] = "John Smith, Jane Doe"

        step = RegexReplaceStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"(\w+) (\w+)", "replacement": r"\2, \1"},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Smith, John, Doe, Jane"
        assert mock_memory._data["memory.count"] == 2

    @pytest.mark.asyncio
    async def test_replace_delete(self, mock_memory):
        mock_memory._data["memory.text"] = "hello123world456"

        step = RegexReplaceStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"\d+", "replacement": ""},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "helloworld"
        assert mock_memory._data["memory.count"] == 2

    @pytest.mark.asyncio
    async def test_replace_case_insensitive(self, mock_memory):
        mock_memory._data["memory.text"] = "Hello HELLO hello"

        step = RegexReplaceStep(
            id="test",
            config={"input": "{memory.text}", "pattern": r"hello", "replacement": "hi", "flags": "i"},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hi hi hi"
        assert mock_memory._data["memory.count"] == 3
