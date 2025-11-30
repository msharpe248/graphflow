"""Tests for advanced CSV steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_csv.advanced import (
    CSVFilterStep,
    CSVSelectColumnsStep,
    CSVSortStep,
    CSVGetColumnStep,
    CSVGetRowStep,
    CSVAddColumnStep,
    CSVRenameColumnsStep,
    CSVMergeStep,
    CSVGroupByStep,
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


@pytest.fixture
def sample_data():
    return [
        {"name": "Alice", "age": "30", "city": "NYC"},
        {"name": "Bob", "age": "25", "city": "LA"},
        {"name": "Charlie", "age": "35", "city": "NYC"},
    ]


class TestCSVFilterStep:
    @pytest.mark.asyncio
    async def test_filter_eq(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVFilterStep(
            id="test",
            config={"input": "{memory.rows}", "column": "city", "operator": "eq", "value": "NYC"},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert len(mock_memory._data["memory.result"]) == 2
        assert mock_memory._data["memory.count"] == 2

    @pytest.mark.asyncio
    async def test_filter_gt(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVFilterStep(
            id="test",
            config={"input": "{memory.rows}", "column": "age", "operator": "gt", "value": "28"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert len(mock_memory._data["memory.result"]) == 2  # Alice (30) and Charlie (35)

    @pytest.mark.asyncio
    async def test_filter_contains(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVFilterStep(
            id="test",
            config={"input": "{memory.rows}", "column": "name", "operator": "contains", "value": "li"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert len(mock_memory._data["memory.result"]) == 2  # Alice and Charlie


class TestCSVSelectColumnsStep:
    @pytest.mark.asyncio
    async def test_select_columns(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVSelectColumnsStep(
            id="test",
            config={"input": "{memory.rows}", "columns": ["name", "city"]},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert len(result) == 3
        assert list(result[0].keys()) == ["name", "city"]


class TestCSVSortStep:
    @pytest.mark.asyncio
    async def test_sort_string(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVSortStep(
            id="test",
            config={"input": "{memory.rows}", "column": "name"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
        assert result[2]["name"] == "Charlie"

    @pytest.mark.asyncio
    async def test_sort_numeric_descending(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVSortStep(
            id="test",
            config={"input": "{memory.rows}", "column": "age", "numeric": True, "descending": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert result[0]["age"] == "35"  # Charlie
        assert result[1]["age"] == "30"  # Alice
        assert result[2]["age"] == "25"  # Bob


class TestCSVGetColumnStep:
    @pytest.mark.asyncio
    async def test_get_column(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVGetColumnStep(
            id="test",
            config={"input": "{memory.rows}", "column": "name"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["Alice", "Bob", "Charlie"]

    @pytest.mark.asyncio
    async def test_get_column_unique(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVGetColumnStep(
            id="test",
            config={"input": "{memory.rows}", "column": "city", "unique": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert set(mock_memory._data["memory.result"]) == {"NYC", "LA"}


class TestCSVGetRowStep:
    @pytest.mark.asyncio
    async def test_get_row(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVGetRowStep(
            id="test",
            config={"input": "{memory.rows}", "index": 1},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"]["name"] == "Bob"
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_get_row_negative_index(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVGetRowStep(
            id="test",
            config={"input": "{memory.rows}", "index": -1},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"]["name"] == "Charlie"


class TestCSVAddColumnStep:
    @pytest.mark.asyncio
    async def test_add_column_constant(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVAddColumnStep(
            id="test",
            config={"input": "{memory.rows}", "column": "country", "value": "USA"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert all(row["country"] == "USA" for row in result)

    @pytest.mark.asyncio
    async def test_add_column_from_column(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVAddColumnStep(
            id="test",
            config={"input": "{memory.rows}", "column": "location", "from_column": "city"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert result[0]["location"] == "NYC"


class TestCSVRenameColumnsStep:
    @pytest.mark.asyncio
    async def test_rename_columns(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVRenameColumnsStep(
            id="test",
            config={"input": "{memory.rows}", "mapping": {"name": "full_name", "age": "years"}},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "full_name" in result[0]
        assert "years" in result[0]
        assert "name" not in result[0]


class TestCSVMergeStep:
    @pytest.mark.asyncio
    async def test_merge_append(self, mock_memory):
        mock_memory._data["memory.left"] = [{"a": 1}, {"a": 2}]
        mock_memory._data["memory.right"] = [{"a": 3}, {"a": 4}]

        step = CSVMergeStep(
            id="test",
            config={"left": "{memory.left}", "right": "{memory.right}", "mode": "append"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert len(mock_memory._data["memory.result"]) == 4

    @pytest.mark.asyncio
    async def test_merge_join(self, mock_memory):
        mock_memory._data["memory.left"] = [
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"}
        ]
        mock_memory._data["memory.right"] = [
            {"id": "1", "score": "100"},
            {"id": "2", "score": "95"}
        ]

        step = CSVMergeStep(
            id="test",
            config={"left": "{memory.left}", "right": "{memory.right}", "mode": "join", "on": "id"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[0]["score"] == "100"


class TestCSVGroupByStep:
    @pytest.mark.asyncio
    async def test_group_by(self, mock_memory, sample_data):
        mock_memory._data["memory.rows"] = sample_data

        step = CSVGroupByStep(
            id="test",
            config={"input": "{memory.rows}", "column": "city"},
            outputs={"output": "{memory.result}", "keys": "{memory.keys}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        keys = mock_memory._data["memory.keys"]

        assert set(keys) == {"NYC", "LA"}
        assert len(result["NYC"]) == 2
        assert len(result["LA"]) == 1
