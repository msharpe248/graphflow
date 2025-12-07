"""Tests for XML processing steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_xmlhtml import (
    XMLParseStep,
    XMLToJSONStep,
    JSONToXMLStep,
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


class TestXMLParseStep:
    @pytest.mark.asyncio
    async def test_parse_basic(self, mock_memory):
        mock_memory._data["input"] = """
        <root>
            <item>Value 1</item>
            <item>Value 2</item>
        </root>
        """

        step = XMLParseStep(
            id="test",
            config={"input": "input", "xpath": "//item/text()"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "Value 1" in result
        assert "Value 2" in result

    @pytest.mark.asyncio
    async def test_parse_attribute(self, mock_memory):
        mock_memory._data["input"] = '<root><item id="1"/><item id="2"/></root>'

        step = XMLParseStep(
            id="test",
            config={"input": "input", "xpath": "//item/@id"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "1" in result
        assert "2" in result


class TestXMLToJSONStep:
    @pytest.mark.asyncio
    async def test_convert_simple(self, mock_memory):
        mock_memory._data["input"] = "<root><name>Test</name><value>123</value></root>"

        step = XMLToJSONStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert result["root"]["name"] == "Test"
        assert result["root"]["value"] == "123"

    @pytest.mark.asyncio
    async def test_convert_with_attributes(self, mock_memory):
        mock_memory._data["input"] = '<root id="1"><name>Test</name></root>'

        step = XMLToJSONStep(
            id="test",
            config={"input": "input", "attr_prefix": "@"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert result["root"]["@id"] == "1"
        assert result["root"]["name"] == "Test"


class TestJSONToXMLStep:
    @pytest.mark.asyncio
    async def test_convert_dict(self, mock_memory):
        mock_memory._data["input"] = {
            "root": {
                "name": "Test",
                "value": "123"
            }
        }

        step = JSONToXMLStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "<root>" in result
        assert "<name>Test</name>" in result
        assert "<value>123</value>" in result
        assert "</root>" in result

    @pytest.mark.asyncio
    async def test_roundtrip(self, mock_memory):
        """JSON to XML to JSON should preserve data."""
        original = {"root": {"item": "value"}}
        mock_memory._data["input"] = original

        # Convert to XML
        to_xml_step = JSONToXMLStep(
            id="to_xml",
            config={"input": "input"},
            outputs={"output": "{memory.xml}"}
        )
        await to_xml_step.execute(mock_memory)

        # Convert back to JSON
        mock_memory._data["xml_input"] = mock_memory._data["memory.xml"]
        to_json_step = XMLToJSONStep(
            id="to_json",
            config={"input": "xml_input"},
            outputs={"output": "{memory.json}"}
        )
        await to_json_step.execute(mock_memory)

        result = mock_memory._data["memory.json"]
        assert result["root"]["item"] == "value"
