"""Tests for advanced YAML steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_yaml.advanced import (
    YAMLParseAllStep,
    YAMLStringifyAllStep,
    YAMLValidateStep,
    YAMLToJSONStep,
    JSONToYAMLStep,
    YAMLMergeStep,
    YAMLGetStep,
    YAMLSetStep,
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


class TestYAMLParseAllStep:
    @pytest.mark.asyncio
    async def test_parse_multi_document(self, mock_memory):
        yaml_str = """---
name: doc1
---
name: doc2
---
name: doc3
"""
        mock_memory._data["memory.yaml_string"] = yaml_str

        step = YAMLParseAllStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == [
            {"name": "doc1"},
            {"name": "doc2"},
            {"name": "doc3"}
        ]
        assert mock_memory._data["memory.count"] == 3

    @pytest.mark.asyncio
    async def test_parse_single_document(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "name: only_one"

        step = YAMLParseAllStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"output": "{memory.result}", "count": "{memory.count}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == [{"name": "only_one"}]
        assert mock_memory._data["memory.count"] == 1


class TestYAMLStringifyAllStep:
    @pytest.mark.asyncio
    async def test_stringify_multi_document(self, mock_memory):
        mock_memory._data["memory.docs"] = [
            {"name": "doc1"},
            {"name": "doc2"}
        ]

        step = YAMLStringifyAllStep(
            id="test",
            config={"input": "{memory.docs}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "---" in result
        assert "name: doc1" in result
        assert "name: doc2" in result


class TestYAMLValidateStep:
    @pytest.mark.asyncio
    async def test_validate_valid(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "name: valid\nage: 30"

        step = YAMLValidateStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"valid": "{memory.valid}", "error": "{memory.error}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.valid"] is True
        assert mock_memory._data["memory.error"] is None

    @pytest.mark.asyncio
    async def test_validate_invalid(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "invalid:\n  - missing: colon\n    bad indent"

        step = YAMLValidateStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"valid": "{memory.valid}", "error": "{memory.error}"}
        )
        await step.execute(mock_memory)

        # Note: This might actually be valid YAML depending on the content
        # Let's use a definitely invalid example
        mock_memory._data["memory.yaml_string"] = "\t- invalid tab indent"
        await step.execute(mock_memory)

        assert mock_memory._data["memory.valid"] is False
        assert mock_memory._data["memory.error"] is not None

    @pytest.mark.asyncio
    async def test_validate_strict_mode(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "\t- invalid"

        step = YAMLValidateStep(
            id="test",
            config={"input": "{memory.yaml_string}", "strict": True},
            outputs={"valid": "{memory.valid}", "error": "{memory.error}"}
        )

        with pytest.raises(ValueError, match="Invalid YAML"):
            await step.execute(mock_memory)


class TestYAMLToJSONStep:
    @pytest.mark.asyncio
    async def test_convert_to_json(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "name: John\nage: 30"

        step = YAMLToJSONStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert '"name"' in result
        assert '"John"' in result
        assert '"age"' in result
        assert "30" in result

    @pytest.mark.asyncio
    async def test_convert_to_json_indented(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "a: 1"

        step = YAMLToJSONStep(
            id="test",
            config={"input": "{memory.yaml_string}", "indent": 2},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "\n" in result  # Indented output has newlines


class TestJSONToYAMLStep:
    @pytest.mark.asyncio
    async def test_convert_from_json(self, mock_memory):
        mock_memory._data["memory.json_string"] = '{"name": "John", "age": 30}'

        step = JSONToYAMLStep(
            id="test",
            config={"input": "{memory.json_string}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "name: John" in result
        assert "age: 30" in result

    @pytest.mark.asyncio
    async def test_convert_invalid_json(self, mock_memory):
        mock_memory._data["memory.json_string"] = "not valid json"

        step = JSONToYAMLStep(
            id="test",
            config={"input": "{memory.json_string}"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="Invalid JSON string"):
            await step.execute(mock_memory)


class TestYAMLMergeStep:
    @pytest.mark.asyncio
    async def test_merge_deep(self, mock_memory):
        mock_memory._data["memory.base"] = {"a": 1, "b": {"x": 1}}
        mock_memory._data["memory.overlay"] = {"b": {"y": 2}, "c": 3}

        step = YAMLMergeStep(
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

        step = YAMLMergeStep(
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

        step = YAMLMergeStep(
            id="test",
            config={"base": "{memory.base}", "overlay": "{memory.overlay}", "strategy": "append"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"items": [1, 2, 3, 4]}


class TestYAMLGetStep:
    @pytest.mark.asyncio
    async def test_get_simple(self, mock_memory):
        mock_memory._data["memory.obj"] = {"user": {"name": "Alice"}}

        step = YAMLGetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "user.name"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Alice"
        assert mock_memory._data["memory.found"] is True

    @pytest.mark.asyncio
    async def test_get_not_found_with_default(self, mock_memory):
        mock_memory._data["memory.obj"] = {"a": 1}

        step = YAMLGetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "b.c", "default": "N/A"},
            outputs={"output": "{memory.result}", "found": "{memory.found}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "N/A"
        assert mock_memory._data["memory.found"] is False


class TestYAMLSetStep:
    @pytest.mark.asyncio
    async def test_set_simple(self, mock_memory):
        mock_memory._data["memory.obj"] = {"user": {"name": "Alice"}}
        mock_memory._data["memory.new_name"] = "Bob"

        step = YAMLSetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "user.name", "value": "{memory.new_name}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"user": {"name": "Bob"}}

    @pytest.mark.asyncio
    async def test_set_create_path(self, mock_memory):
        mock_memory._data["memory.obj"] = {}

        step = YAMLSetStep(
            id="test",
            config={"input": "{memory.obj}", "path": "a.b.c", "value": "test", "create_path": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"a": {"b": {"c": "test"}}}
