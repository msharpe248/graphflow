"""Tests for core HTML processing steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_xmlhtml import (
    HTMLStripStep,
    HTMLParseStep,
    HTMLFindLinksStep,
    HTMLTableExtractStep,
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


class TestHTMLStripStep:
    @pytest.mark.asyncio
    async def test_strip_basic(self, mock_memory):
        mock_memory._data["input"] = "<p>Hello <b>World</b></p>"

        step = HTMLStripStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "Hello World"

    @pytest.mark.asyncio
    async def test_strip_complex_html(self, mock_memory):
        mock_memory._data["input"] = """
        <html>
            <head><title>Test</title></head>
            <body>
                <h1>Title</h1>
                <p>Paragraph</p>
            </body>
        </html>
        """

        step = HTMLStripStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "Test" in result
        assert "Title" in result
        assert "Paragraph" in result
        assert "<" not in result  # No tags

    @pytest.mark.asyncio
    async def test_strip_with_separator(self, mock_memory):
        mock_memory._data["input"] = "<p>Line1</p><p>Line2</p>"

        step = HTMLStripStep(
            id="test",
            config={"input": "input", "separator": "\n"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert "Line1" in result
        assert "Line2" in result

    @pytest.mark.asyncio
    async def test_strip_empty_html(self, mock_memory):
        mock_memory._data["input"] = "<div></div>"

        step = HTMLStripStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ""


class TestHTMLParseStep:
    @pytest.mark.asyncio
    async def test_parse_single_selector(self, mock_memory):
        mock_memory._data["input"] = "<h1>Hello World</h1><p>Body text</p>"

        step = HTMLParseStep(
            id="test",
            config={
                "input": "input",
                "selectors": {
                    "title": {"selector": "h1", "multiple": False}
                }
            },
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"]["title"] == "Hello World"

    @pytest.mark.asyncio
    async def test_parse_multiple_selector(self, mock_memory):
        mock_memory._data["input"] = "<ul><li>One</li><li>Two</li><li>Three</li></ul>"

        step = HTMLParseStep(
            id="test",
            config={
                "input": "input",
                "selectors": {
                    "items": {"selector": "li", "multiple": True}
                }
            },
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"]["items"] == ["One", "Two", "Three"]

    @pytest.mark.asyncio
    async def test_parse_attribute(self, mock_memory):
        mock_memory._data["input"] = '<a href="http://example.com">Link</a>'

        step = HTMLParseStep(
            id="test",
            config={
                "input": "input",
                "selectors": {
                    "link": {"selector": "a", "attribute": "href", "multiple": False}
                }
            },
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"]["link"] == "http://example.com"

    @pytest.mark.asyncio
    async def test_parse_not_found(self, mock_memory):
        mock_memory._data["input"] = "<p>No heading here</p>"

        step = HTMLParseStep(
            id="test",
            config={
                "input": "input",
                "selectors": {
                    "title": {"selector": "h1", "multiple": False}
                }
            },
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"]["title"] is None


class TestHTMLFindLinksStep:
    @pytest.mark.asyncio
    async def test_find_links(self, mock_memory):
        mock_memory._data["input"] = """
        <a href="http://example.com">Link 1</a>
        <a href="/page2">Link 2</a>
        <a href="https://google.com">Link 3</a>
        """

        step = HTMLFindLinksStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert len(result) == 3
        assert "http://example.com" in result
        assert "/page2" in result
        assert "https://google.com" in result

    @pytest.mark.asyncio
    async def test_find_links_absolute_only(self, mock_memory):
        mock_memory._data["input"] = """
        <a href="http://example.com">Link 1</a>
        <a href="/page2">Link 2</a>
        <a href="https://google.com">Link 3</a>
        """

        step = HTMLFindLinksStep(
            id="test",
            config={"input": "input", "absolute_only": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert len(result) == 2
        assert "http://example.com" in result
        assert "https://google.com" in result
        assert "/page2" not in result

    @pytest.mark.asyncio
    async def test_find_links_unique(self, mock_memory):
        mock_memory._data["input"] = """
        <a href="http://example.com">Link 1</a>
        <a href="http://example.com">Link 1 again</a>
        <a href="http://other.com">Link 2</a>
        """

        step = HTMLFindLinksStep(
            id="test",
            config={"input": "input", "unique": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_find_no_links(self, mock_memory):
        mock_memory._data["input"] = "<p>No links here</p>"

        step = HTMLFindLinksStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == []


class TestHTMLTableExtractStep:
    @pytest.mark.asyncio
    async def test_extract_table_with_headers(self, mock_memory):
        mock_memory._data["input"] = """
        <table>
            <tr><th>Name</th><th>Age</th></tr>
            <tr><td>Alice</td><td>30</td></tr>
            <tr><td>Bob</td><td>25</td></tr>
        </table>
        """

        step = HTMLTableExtractStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert len(result) == 2
        assert result[0]["Name"] == "Alice"
        assert result[0]["Age"] == "30"
        assert result[1]["Name"] == "Bob"
        assert result[1]["Age"] == "25"

    @pytest.mark.asyncio
    async def test_extract_table_without_headers(self, mock_memory):
        mock_memory._data["input"] = """
        <table>
            <tr><td>Alice</td><td>30</td></tr>
            <tr><td>Bob</td><td>25</td></tr>
        </table>
        """

        step = HTMLTableExtractStep(
            id="test",
            config={"input": "input", "headers": False},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert len(result) == 2
        assert result[0] == ["Alice", "30"]
        assert result[1] == ["Bob", "25"]

    @pytest.mark.asyncio
    async def test_extract_table_with_selector(self, mock_memory):
        mock_memory._data["input"] = """
        <table id="first"></table>
        <table id="second">
            <tr><th>Col</th></tr>
            <tr><td>Value</td></tr>
        </table>
        """

        step = HTMLTableExtractStep(
            id="test",
            config={"input": "input", "table_selector": "table#second"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        assert len(result) == 1
        assert result[0]["Col"] == "Value"

    @pytest.mark.asyncio
    async def test_extract_no_table(self, mock_memory):
        mock_memory._data["input"] = "<p>No table here</p>"

        step = HTMLTableExtractStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == []
