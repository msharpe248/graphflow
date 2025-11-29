"""Tests for formatting and case manipulation steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_text.formatting import (
    StringFormatStep,
    TextCaseStep,
    StringTrimStep,
    StringPadStep,
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


class TestStringFormatStep:
    @pytest.mark.asyncio
    async def test_format_single_variable(self, mock_memory):
        mock_memory._data["memory.name"] = "World"

        step = StringFormatStep(
            id="test",
            config={"template": "Hello, {memory.name}!"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Hello, World!"

    @pytest.mark.asyncio
    async def test_format_multiple_variables(self, mock_memory):
        mock_memory._data["memory.first"] = "John"
        mock_memory._data["memory.last"] = "Doe"

        step = StringFormatStep(
            id="test",
            config={"template": "{memory.first} {memory.last}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "John Doe"


class TestTextCaseStep:
    @pytest.mark.asyncio
    async def test_upper(self, mock_memory):
        mock_memory._data["memory.text"] = "hello world"

        step = TextCaseStep(
            id="test",
            config={"input": "{memory.text}", "case": "upper"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "HELLO WORLD"

    @pytest.mark.asyncio
    async def test_lower(self, mock_memory):
        mock_memory._data["memory.text"] = "HELLO WORLD"

        step = TextCaseStep(
            id="test",
            config={"input": "{memory.text}", "case": "lower"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello world"

    @pytest.mark.asyncio
    async def test_title(self, mock_memory):
        mock_memory._data["memory.text"] = "hello world"

        step = TextCaseStep(
            id="test",
            config={"input": "{memory.text}", "case": "title"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Hello World"

    @pytest.mark.asyncio
    async def test_capitalize(self, mock_memory):
        mock_memory._data["memory.text"] = "hello world"

        step = TextCaseStep(
            id="test",
            config={"input": "{memory.text}", "case": "capitalize"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Hello world"

    @pytest.mark.asyncio
    async def test_swapcase(self, mock_memory):
        mock_memory._data["memory.text"] = "Hello World"

        step = TextCaseStep(
            id="test",
            config={"input": "{memory.text}", "case": "swapcase"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hELLO wORLD"


class TestStringTrimStep:
    @pytest.mark.asyncio
    async def test_trim_both(self, mock_memory):
        mock_memory._data["memory.text"] = "  hello  "

        step = StringTrimStep(
            id="test",
            config={"input": "{memory.text}", "mode": "both"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello"

    @pytest.mark.asyncio
    async def test_trim_left(self, mock_memory):
        mock_memory._data["memory.text"] = "  hello  "

        step = StringTrimStep(
            id="test",
            config={"input": "{memory.text}", "mode": "left"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello  "

    @pytest.mark.asyncio
    async def test_trim_right(self, mock_memory):
        mock_memory._data["memory.text"] = "  hello  "

        step = StringTrimStep(
            id="test",
            config={"input": "{memory.text}", "mode": "right"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "  hello"

    @pytest.mark.asyncio
    async def test_trim_custom_chars(self, mock_memory):
        mock_memory._data["memory.text"] = "xxhelloxx"

        step = StringTrimStep(
            id="test",
            config={"input": "{memory.text}", "mode": "both", "chars": "x"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello"


class TestStringPadStep:
    @pytest.mark.asyncio
    async def test_pad_left(self, mock_memory):
        mock_memory._data["memory.text"] = "42"

        step = StringPadStep(
            id="test",
            config={"input": "{memory.text}", "length": 5, "char": "0", "mode": "left"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "00042"

    @pytest.mark.asyncio
    async def test_pad_right(self, mock_memory):
        mock_memory._data["memory.text"] = "hi"

        step = StringPadStep(
            id="test",
            config={"input": "{memory.text}", "length": 5, "char": ".", "mode": "right"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hi..."

    @pytest.mark.asyncio
    async def test_pad_center(self, mock_memory):
        mock_memory._data["memory.text"] = "hi"

        step = StringPadStep(
            id="test",
            config={"input": "{memory.text}", "length": 6, "char": "-", "mode": "center"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "--hi--"
