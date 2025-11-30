"""Tests for advanced JSON steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_json.advanced import (
    JSONPathStep,
    JSONMergeStep,
    JSONSchemaValidateStep,
    JSONGetStep,
    JSONSetStep,
    JSONKeysStep,
    JSONValuesStep,
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


class TestJSONPathStep:
    @pytest.mark.asyncio
    async def test_path_simple(self, mock_memory):
        mock_memory._data["memory.obj"] = {"store": {"book": [{"author": "Alice"}, {"author": "Bob"}]}}

        step = JSONPathStep(
            id="test",
            config={"input": "{memory.obj}", "expression": "$.store.book[*].author"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["Alice", "Bob"]
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_path_first_only(self, mock_memory):
        mock_memory._data["memory.obj"] = {"items": [1, 2, 3]}

        step = JSONPathStep(
            id="test",
            config={"input": "{memory.obj}", "expression": "$.items[*]", "first_only": True},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == 1
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_path_not_found(self, mock_memory):
        mock_memory._data["memory.obj"] = {"a": 1}

        step = JSONPathStep(
            id="test",
            config={"input": "{memory.obj}", "expression": "$.b.c"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == []
        assert mock_memory._data["memory.found"] is False

    @pytest.mark.asyncio
    async def test_path_invalid_expression(self, mock_memory):
        mock_memory._data["memory.obj"] = {"a": 1}

        step = JSONPathStep(
            id="test",
            config={"input": "{memory.obj}", "expression": "$[invalid"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="Invalid JSONPath expression"):
            await step.execute(mock_memory)


class TestJSONMergeStep:
    @pytest.mark.asyncio
    async def test_merge_deep(self, mock_memory):
        mock_memory._data["memory.base"] = {"a": 1, "b": {"x": 1}}
        mock_memory._data["memory.overlay"] = {"b": {"y": 2}, "c": 3}

        step = JSONMergeStep(
            id="test",
            config={"base": "{memory.base}", "overlay": "{memory.overlay}", "strategy": "deep"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"a": 1, "b": {"x": 1, "y": 2}, "c": 3}

    @pytest.mark.asyncio
    async def test_merge_replace(self, mock_memory):
        mock_memory._data["memory.base"] = {"a": 1}
        mock_memory._data["memory.overlay"] = {"b": 2}

        step = JSONMergeStep(
            id="test",
            config={"base": "{memory.base}", "overlay": "{memory.overlay}", "strategy": "replace"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"b": 2}

    @pytest.mark.asyncio
    async def test_merge_append_arrays(self, mock_memory):
        mock_memory._data["memory.base"] = {"items": [1, 2]}
        mock_memory._data["memory.overlay"] = {"items": [3, 4]}

        step = JSONMergeStep(
            id="test",
            config={"base": "{memory.base}", "overlay": "{memory.overlay}", "strategy": "append"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"items": [1, 2, 3, 4]}


class TestJSONSchemaValidateStep:
    @pytest.mark.asyncio
    async def test_validate_valid(self, mock_memory):
        mock_memory._data["memory.obj"] = {"name": "John", "age": 30}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            },
            "required": ["name"]
        }

        step = JSONSchemaValidateStep(
            id="test",
            config={"input": "{memory.obj}", "schema": schema},
            outputs={"valid": "{memory.valid}", "errors": "{memory.errors}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.valid"] is True
        assert mock_memory._data["memory.errors"] == []

    @pytest.mark.asyncio
    async def test_validate_invalid(self, mock_memory):
        mock_memory._data["memory.obj"] = {"name": 123}  # name should be string
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }

        step = JSONSchemaValidateStep(
            id="test",
            config={"input": "{memory.obj}", "schema": schema},
            outputs={"valid": "{memory.valid}", "errors": "{memory.errors}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.valid"] is False
        assert len(mock_memory._data["memory.errors"]) > 0

    @pytest.mark.asyncio
    async def test_validate_strict_mode(self, mock_memory):
        mock_memory._data["memory.obj"] = {"name": 123}
        schema = {"type": "object", "properties": {"name": {"type": "string"}}}

        step = JSONSchemaValidateStep(
            id="test",
            config={"input": "{memory.obj}", "schema": schema, "strict": True},
            outputs={"valid": "{memory.valid}", "errors": "{memory.errors}"}
        )

        with pytest.raises(ValueError, match="JSON validation failed"):
            await step.execute(mock_memory)


class TestJSONGetStep:
    @pytest.mark.asyncio
    async def test_get_simple(self, mock_memory):
        mock_memory._data["memory.obj"] = {"user": {"name": "Alice"}}

        step = JSONGetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "user.name"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Alice"
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_get_array_index(self, mock_memory):
        mock_memory._data["memory.obj"] = {"items": ["a", "b", "c"]}

        step = JSONGetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "items.1"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "b"
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_get_bracket_notation(self, mock_memory):
        mock_memory._data["memory.obj"] = {"items": [{"id": 1}, {"id": 2}]}

        step = JSONGetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "items[0].id"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == 1
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_get_not_found_with_default(self, mock_memory):
        mock_memory._data["memory.obj"] = {"a": 1}

        step = JSONGetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "b.c", "default": "N/A"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "N/A"
        assert mock_memory._data["memory.found"] is False


class TestJSONSetStep:
    @pytest.mark.asyncio
    async def test_set_simple(self, mock_memory):
        mock_memory._data["memory.obj"] = {"user": {"name": "Alice"}}
        mock_memory._data["memory.new_name"] = "Bob"

        step = JSONSetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "user.name", "value": "{memory.new_name}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"user": {"name": "Bob"}}

    @pytest.mark.asyncio
    async def test_set_create_path(self, mock_memory):
        mock_memory._data["memory.obj"] = {}

        step = JSONSetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "a.b.c", "value": "test", "create_path": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"a": {"b": {"c": "test"}}}

    @pytest.mark.asyncio
    async def test_set_literal_value(self, mock_memory):
        mock_memory._data["memory.obj"] = {"count": 0}

        step = JSONSetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "count", "value": 42},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"count": 42}


class TestJSONKeysStep:
    @pytest.mark.asyncio
    async def test_keys(self, mock_memory):
        mock_memory._data["memory.obj"] = {"a": 1, "b": 2, "c": 3}

        step = JSONKeysStep(
            id="test",
            config={"input": "{memory.obj}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert set(mock_memory._data["memory.result"]) == {"a", "b", "c"}

    @pytest.mark.asyncio
    async def test_keys_empty(self, mock_memory):
        mock_memory._data["memory.obj"] = {}

        step = JSONKeysStep(
            id="test",
            config={"input": "{memory.obj}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == []

    @pytest.mark.asyncio
    async def test_keys_not_object(self, mock_memory):
        mock_memory._data["memory.obj"] = [1, 2, 3]

        step = JSONKeysStep(
            id="test",
            config={"input": "{memory.obj}"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="must be a JSON object"):
            await step.execute(mock_memory)


class TestJSONValuesStep:
    @pytest.mark.asyncio
    async def test_values(self, mock_memory):
        mock_memory._data["memory.obj"] = {"a": 1, "b": 2, "c": 3}

        step = JSONValuesStep(
            id="test",
            config={"input": "{memory.obj}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert set(mock_memory._data["memory.result"]) == {1, 2, 3}

    @pytest.mark.asyncio
    async def test_values_empty(self, mock_memory):
        mock_memory._data["memory.obj"] = {}

        step = JSONValuesStep(
            id="test",
            config={"input": "{memory.obj}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == []

    @pytest.mark.asyncio
    async def test_values_not_object(self, mock_memory):
        mock_memory._data["memory.obj"] = "not an object"

        step = JSONValuesStep(
            id="test",
            config={"input": "{memory.obj}"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="must be a JSON object"):
            await step.execute(mock_memory)
