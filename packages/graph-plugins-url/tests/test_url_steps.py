"""Tests for URL manipulation steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_url import (
    URLEscapeStep,
    URLUnescapeStep,
    URLBuildStep,
    URLParseStep,
)


@pytest.fixture
def mock_memory():
    """Create a mock memory store."""
    memory = MagicMock()
    memory._data = {}

    def read(key):
        # Handle both namespaced (memory.key) and simple (key) formats
        if key.startswith("memory."):
            key = key[7:]  # Remove "memory." prefix
        if key in memory._data:
            return memory._data[key]
        # Also check with memory prefix
        if f"memory.{key}" in memory._data:
            return memory._data[f"memory.{key}"]
        raise KeyError(f"Key not found: {key}")

    def write(key, value):
        # Normalize key storage
        if key.startswith("memory."):
            memory._data[key[7:]] = value
        else:
            memory._data[key] = value

    memory.read = MagicMock(side_effect=read)
    memory.write = MagicMock(side_effect=write)
    return memory


class TestURLEscapeStep:
    @pytest.mark.asyncio
    async def test_escape_basic(self, mock_memory):
        mock_memory._data["input_text"] = "hello world"

        step = URLEscapeStep(
            id="test",
            config={"input": "{memory.input_text}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "hello%20world"

    @pytest.mark.asyncio
    async def test_escape_special_chars(self, mock_memory):
        mock_memory._data["input_text"] = "foo=bar&baz=qux"

        step = URLEscapeStep(
            id="test",
            config={"input": "{memory.input_text}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "foo%3Dbar%26baz%3Dqux"

    @pytest.mark.asyncio
    async def test_escape_with_safe_chars(self, mock_memory):
        mock_memory._data["input_text"] = "foo/bar/baz"

        step = URLEscapeStep(
            id="test",
            config={"input": "{memory.input_text}", "safe": "/"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "foo/bar/baz"

    @pytest.mark.asyncio
    async def test_escape_unicode(self, mock_memory):
        mock_memory._data["input_text"] = "héllo wörld"

        step = URLEscapeStep(
            id="test",
            config={"input": "{memory.input_text}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        # Unicode chars get percent-encoded
        assert "%C3%A9" in mock_memory._data["result"]  # é
        assert "%C3%B6" in mock_memory._data["result"]  # ö


class TestURLUnescapeStep:
    @pytest.mark.asyncio
    async def test_unescape_basic(self, mock_memory):
        mock_memory._data["input_text"] = "hello%20world"

        step = URLUnescapeStep(
            id="test",
            config={"input": "{memory.input_text}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "hello world"

    @pytest.mark.asyncio
    async def test_unescape_special_chars(self, mock_memory):
        mock_memory._data["input_text"] = "foo%3Dbar%26baz%3Dqux"

        step = URLUnescapeStep(
            id="test",
            config={"input": "{memory.input_text}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "foo=bar&baz=qux"

    @pytest.mark.asyncio
    async def test_unescape_already_decoded(self, mock_memory):
        mock_memory._data["input_text"] = "hello world"

        step = URLUnescapeStep(
            id="test",
            config={"input": "{memory.input_text}"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "hello world"


class TestURLBuildStep:
    @pytest.mark.asyncio
    async def test_build_simple(self, mock_memory):
        step = URLBuildStep(
            id="test",
            config={"host": "example.com"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "https://example.com"

    @pytest.mark.asyncio
    async def test_build_with_path(self, mock_memory):
        step = URLBuildStep(
            id="test",
            config={"host": "example.com", "path": "/api/users"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "https://example.com/api/users"

    @pytest.mark.asyncio
    async def test_build_with_port(self, mock_memory):
        step = URLBuildStep(
            id="test",
            config={"host": "localhost", "port": 8080, "scheme": "http"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "http://localhost:8080"

    @pytest.mark.asyncio
    async def test_build_with_params(self, mock_memory):
        step = URLBuildStep(
            id="test",
            config={
                "host": "example.com",
                "path": "/search",
                "params": {"q": "test", "page": "1"}
            },
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["result"]
        assert "example.com/search?" in result
        assert "q=test" in result
        assert "page=1" in result

    @pytest.mark.asyncio
    async def test_build_with_fragment(self, mock_memory):
        step = URLBuildStep(
            id="test",
            config={
                "host": "example.com",
                "path": "/docs",
                "fragment": "section1"
            },
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["result"] == "https://example.com/docs#section1"


class TestURLParseStep:
    @pytest.mark.asyncio
    async def test_parse_simple(self, mock_memory):
        mock_memory._data["url"] = "https://example.com"

        step = URLParseStep(
            id="test",
            config={"input": "url"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["result"]
        assert result["scheme"] == "https"
        assert result["host"] == "example.com"
        assert result["path"] == ""

    @pytest.mark.asyncio
    async def test_parse_with_port(self, mock_memory):
        mock_memory._data["url"] = "http://localhost:8080/api"

        step = URLParseStep(
            id="test",
            config={"input": "url"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["result"]
        assert result["scheme"] == "http"
        assert result["host"] == "localhost"
        assert result["port"] == 8080
        assert result["path"] == "/api"

    @pytest.mark.asyncio
    async def test_parse_with_query(self, mock_memory):
        mock_memory._data["url"] = "https://example.com/search?q=test&page=2"

        step = URLParseStep(
            id="test",
            config={"input": "url"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["result"]
        assert result["path"] == "/search"
        assert result["params"]["q"] == "test"
        assert result["params"]["page"] == "2"

    @pytest.mark.asyncio
    async def test_parse_with_fragment(self, mock_memory):
        mock_memory._data["url"] = "https://example.com/docs#section1"

        step = URLParseStep(
            id="test",
            config={"input": "url"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["result"]
        assert result["fragment"] == "section1"

    @pytest.mark.asyncio
    async def test_parse_complex_url(self, mock_memory):
        mock_memory._data["url"] = "https://user:pass@api.example.com:443/v1/users?id=123&active=true#results"

        step = URLParseStep(
            id="test",
            config={"input": "url"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["result"]
        assert result["scheme"] == "https"
        assert result["path"] == "/v1/users"
        assert result["params"]["id"] == "123"
        assert result["params"]["active"] == "true"
        assert result["fragment"] == "results"
