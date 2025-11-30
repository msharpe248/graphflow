"""Tests for core YAML steps - parse and stringify."""
import pytest
from unittest.mock import MagicMock

from graphflow_yaml.core import YAMLParseStep, YAMLStringifyStep


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


class TestYAMLParseStep:
    @pytest.mark.asyncio
    async def test_parse_object(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "name: John\nage: 30"

        step = YAMLParseStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {"name": "John", "age": 30}

    @pytest.mark.asyncio
    async def test_parse_list(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "- apple\n- banana\n- cherry"

        step = YAMLParseStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ["apple", "banana", "cherry"]

    @pytest.mark.asyncio
    async def test_parse_nested(self, mock_memory):
        yaml_str = """
user:
  name: Alice
  roles:
    - admin
    - user
"""
        mock_memory._data["memory.yaml_string"] = yaml_str

        step = YAMLParseStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == {
            "user": {"name": "Alice", "roles": ["admin", "user"]}
        }

    @pytest.mark.asyncio
    async def test_parse_invalid_yaml(self, mock_memory):
        mock_memory._data["memory.yaml_string"] = "invalid: yaml: content:"

        step = YAMLParseStep(
            id="test",
            config={"input": "{memory.yaml_string}"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="Invalid YAML string"):
            await step.execute(mock_memory)


class TestYAMLStringifyStep:
    @pytest.mark.asyncio
    async def test_stringify_object(self, mock_memory):
        mock_memory._data["memory.obj"] = {"name": "John", "age": 30}

        step = YAMLStringifyStep(
            id="test",
            config={"input": "{memory.obj}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "name: John" in result
        assert "age: 30" in result

    @pytest.mark.asyncio
    async def test_stringify_list(self, mock_memory):
        mock_memory._data["memory.arr"] = ["a", "b", "c"]

        step = YAMLStringifyStep(
            id="test",
            config={"input": "{memory.arr}", "default_flow_style": False},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "- a" in result
        assert "- b" in result
        assert "- c" in result

    @pytest.mark.asyncio
    async def test_stringify_sorted_keys(self, mock_memory):
        mock_memory._data["memory.obj"] = {"z": 1, "a": 2, "m": 3}

        step = YAMLStringifyStep(
            id="test",
            config={"input": "{memory.obj}", "sort_keys": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        # "a" should come before "m" which should come before "z"
        assert result.index("a:") < result.index("m:") < result.index("z:")

    @pytest.mark.asyncio
    async def test_stringify_flow_style(self, mock_memory):
        mock_memory._data["memory.obj"] = {"items": [1, 2, 3]}

        step = YAMLStringifyStep(
            id="test",
            config={"input": "{memory.obj}", "default_flow_style": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        # Flow style uses inline format
        assert "[1, 2, 3]" in result or "{" in result
