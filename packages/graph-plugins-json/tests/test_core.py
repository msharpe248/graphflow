"""Tests for core JSON steps - parse and stringify."""
import pytest
from unittest.mock import MagicMock

from graphflow_json.core import JSONParseStep, JSONStringifyStep


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


class TestJSONParseStep:
    @pytest.mark.asyncio
    async def test_parse_object(self, mock_memory):
        mock_memory._data["memory.json_string"] = '{"name": "John", "age": 30}'

        step = JSONParseStep(
            id="test",
            config={"input": "{memory.json_string}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_parse_array(self, mock_memory):
        mock_memory._data["memory.json_string"] = '[1, 2, 3]'

        step = JSONParseStep(
            id="test",
            config={"input": "{memory.json_string}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == [1, 2, 3]

    @pytest.mark.asyncio
    async def test_parse_nested(self, mock_memory):
        mock_memory._data["memory.json_string"] = '{"user": {"name": "Alice", "roles": ["admin", "user"]}}'

        step = JSONParseStep(
            id="test",
            config={"input": "{memory.json_string}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {
            "user": {"name": "Alice", "roles": ["admin", "user"]}
        }

    @pytest.mark.asyncio
    async def test_parse_invalid_json(self, mock_memory):
        mock_memory._data["memory.json_string"] = 'not valid json'

        step = JSONParseStep(
            id="test",
            config={"input": "{memory.json_string}"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="Invalid JSON string"):
            await step.execute(mock_memory)


class TestJSONStringifyStep:
    @pytest.mark.asyncio
    async def test_stringify_object(self, mock_memory):
        mock_memory._data["memory.obj"] = {"name": "John", "age": 30}

        step = JSONStringifyStep(
            id="test",
            config={"input": "{memory.obj}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert '"name"' in result
        assert '"John"' in result
        assert '"age"' in result
        assert '30' in result

    @pytest.mark.asyncio
    async def test_stringify_array(self, mock_memory):
        mock_memory._data["memory.arr"] = [1, 2, 3]

        step = JSONStringifyStep(
            id="test",
            config={"input": "{memory.arr}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "[1, 2, 3]"

    @pytest.mark.asyncio
    async def test_stringify_with_indent(self, mock_memory):
        mock_memory._data["memory.obj"] = {"a": 1}

        step = JSONStringifyStep(
            id="test",
            config={"input": "{memory.obj}", "indent": 2},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "\n" in result  # Pretty printed

    @pytest.mark.asyncio
    async def test_stringify_sorted_keys(self, mock_memory):
        mock_memory._data["memory.obj"] = {"z": 1, "a": 2, "m": 3}

        step = JSONStringifyStep(
            id="test",
            config={"input": "{memory.obj}", "sort_keys": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        # "a" should come before "m" which should come before "z"
        assert result.index('"a"') < result.index('"m"') < result.index('"z"')

    @pytest.mark.asyncio
    async def test_stringify_unicode(self, mock_memory):
        mock_memory._data["memory.obj"] = {"greeting": "Hello, World!"}

        step = JSONStringifyStep(
            id="test",
            config={"input": "{memory.obj}", "ensure_ascii": False},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert "Hello, World!" in mock_memory._data["memory.result"]
