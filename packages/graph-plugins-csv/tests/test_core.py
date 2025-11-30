"""Tests for core CSV steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_csv.core import (
    CSVParseStep,
    CSVStringifyStep,
    CSVGetHeadersStep,
    CSVToJSONStep,
    JSONToCSVStep,
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


class TestCSVParseStep:
    @pytest.mark.asyncio
    async def test_parse_with_headers(self, mock_memory):
        mock_memory._data["memory.csv"] = "name,age,city\nAlice,30,NYC\nBob,25,LA"

        step = CSVParseStep(
            id="test",
            config={"input": "{memory.csv}"},
            outputs={"output": "{memory.result}", "headers": "{memory.headers}", "row_count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == [
            {"name": "Alice", "age": "30", "city": "NYC"},
            {"name": "Bob", "age": "25", "city": "LA"}
        ]
        assert mock_memory._data["memory.headers"] == ["name", "age", "city"]
        assert mock_memory._data["memory.count"] == 2

    @pytest.mark.asyncio
    async def test_parse_without_headers(self, mock_memory):
        mock_memory._data["memory.csv"] = "Alice,30\nBob,25"

        step = CSVParseStep(
            id="test",
            config={"input": "{memory.csv}", "has_header": False},
            outputs={"output": "{memory.result}", "row_count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == [
            ["Alice", "30"],
            ["Bob", "25"]
        ]
        assert mock_memory._data["memory.count"] == 2

    @pytest.mark.asyncio
    async def test_parse_with_custom_delimiter(self, mock_memory):
        mock_memory._data["memory.csv"] = "name;age\nAlice;30"

        step = CSVParseStep(
            id="test",
            config={"input": "{memory.csv}", "delimiter": ";"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == [{"name": "Alice", "age": "30"}]


class TestCSVStringifyStep:
    @pytest.mark.asyncio
    async def test_stringify_dicts(self, mock_memory):
        mock_memory._data["memory.rows"] = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]

        step = CSVStringifyStep(
            id="test",
            config={"input": "{memory.rows}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "name" in result
        assert "age" in result
        assert "Alice" in result
        assert "Bob" in result

    @pytest.mark.asyncio
    async def test_stringify_without_header(self, mock_memory):
        mock_memory._data["memory.rows"] = [
            {"name": "Alice", "age": 30}
        ]

        step = CSVStringifyStep(
            id="test",
            config={"input": "{memory.rows}", "include_header": False},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        # Should not have header row
        lines = result.strip().split("\n")
        assert len(lines) == 1


class TestCSVGetHeadersStep:
    @pytest.mark.asyncio
    async def test_get_headers(self, mock_memory):
        mock_memory._data["memory.csv"] = "name,age,city\nAlice,30,NYC"

        step = CSVGetHeadersStep(
            id="test",
            config={"input": "{memory.csv}"},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["name", "age", "city"]
        assert mock_memory._data["memory.count"] == 3


class TestCSVToJSONStep:
    @pytest.mark.asyncio
    async def test_to_json(self, mock_memory):
        mock_memory._data["memory.csv"] = "name,age\nAlice,30\nBob,25"

        step = CSVToJSONStep(
            id="test",
            config={"input": "{memory.csv}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        import json
        result = json.loads(mock_memory._data["memory.result"])
        assert result == [
            {"name": "Alice", "age": "30"},
            {"name": "Bob", "age": "25"}
        ]


class TestJSONToCSVStep:
    @pytest.mark.asyncio
    async def test_from_json(self, mock_memory):
        mock_memory._data["memory.json"] = '[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'

        step = JSONToCSVStep(
            id="test",
            config={"input": "{memory.json}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "name" in result
        assert "age" in result
        assert "Alice" in result
        assert "Bob" in result

    @pytest.mark.asyncio
    async def test_from_invalid_json(self, mock_memory):
        mock_memory._data["memory.json"] = "not json"

        step = JSONToCSVStep(
            id="test",
            config={"input": "{memory.json}"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="Invalid JSON"):
            await step.execute(mock_memory)
