"""Tests for basic string manipulation steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_text.basic import (
    StringJoinStep,
    StringSplitStep,
    StringReplaceStep,
    StringReverseStep,
    StringRepeatStep,
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


class TestStringJoinStep:
    @pytest.mark.asyncio
    async def test_join_with_separator(self, mock_memory):
        mock_memory._data["memory.items"] = ["apple", "banana", "cherry"]

        step = StringJoinStep(
            id="test",
            config={"input": "{memory.items}", "separator": ", "},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "apple, banana, cherry"

    @pytest.mark.asyncio
    async def test_join_without_separator(self, mock_memory):
        mock_memory._data["memory.items"] = ["a", "b", "c"]

        step = StringJoinStep(
            id="test",
            config={"input": "{memory.items}", "separator": ""},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "abc"

    @pytest.mark.asyncio
    async def test_join_single_item(self, mock_memory):
        mock_memory._data["memory.items"] = ["only"]

        step = StringJoinStep(
            id="test",
            config={"input": "{memory.items}", "separator": ", "},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "only"


class TestStringSplitStep:
    @pytest.mark.asyncio
    async def test_split_with_separator(self, mock_memory):
        mock_memory._data["memory.text"] = "apple,banana,cherry"

        step = StringSplitStep(
            id="test",
            config={"input": "{memory.text}", "separator": ","},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["apple", "banana", "cherry"]

    @pytest.mark.asyncio
    async def test_split_by_character(self, mock_memory):
        mock_memory._data["memory.text"] = "hello"

        step = StringSplitStep(
            id="test",
            config={"input": "{memory.text}", "separator": ""},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["h", "e", "l", "l", "o"]

    @pytest.mark.asyncio
    async def test_split_with_max(self, mock_memory):
        mock_memory._data["memory.text"] = "a-b-c-d"

        step = StringSplitStep(
            id="test",
            config={"input": "{memory.text}", "separator": "-", "max_split": 2},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["a", "b", "c-d"]


class TestStringReplaceStep:
    @pytest.mark.asyncio
    async def test_replace_all(self, mock_memory):
        mock_memory._data["memory.text"] = "hello world world"

        step = StringReplaceStep(
            id="test",
            config={"input": "{memory.text}", "old": "world", "new": "there"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello there there"

    @pytest.mark.asyncio
    async def test_replace_with_count(self, mock_memory):
        mock_memory._data["memory.text"] = "aaa"

        step = StringReplaceStep(
            id="test",
            config={"input": "{memory.text}", "old": "a", "new": "b", "count": 2},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "bba"


class TestStringReverseStep:
    @pytest.mark.asyncio
    async def test_reverse(self, mock_memory):
        mock_memory._data["memory.text"] = "hello"

        step = StringReverseStep(
            id="test",
            config={"input": "{memory.text}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "olleh"

    @pytest.mark.asyncio
    async def test_reverse_empty(self, mock_memory):
        mock_memory._data["memory.text"] = ""

        step = StringReverseStep(
            id="test",
            config={"input": "{memory.text}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ""


class TestStringRepeatStep:
    @pytest.mark.asyncio
    async def test_repeat(self, mock_memory):
        mock_memory._data["memory.text"] = "ab"

        step = StringRepeatStep(
            id="test",
            config={"input": "{memory.text}", "count": 3},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "ababab"

    @pytest.mark.asyncio
    async def test_repeat_with_separator(self, mock_memory):
        mock_memory._data["memory.text"] = "hi"

        step = StringRepeatStep(
            id="test",
            config={"input": "{memory.text}", "count": 3, "separator": "-"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hi-hi-hi"

    @pytest.mark.asyncio
    async def test_repeat_zero(self, mock_memory):
        mock_memory._data["memory.text"] = "test"

        step = StringRepeatStep(
            id="test",
            config={"input": "{memory.text}", "count": 0},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ""
