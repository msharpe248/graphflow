"""Tests for Base64 encoding/decoding steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_encoding import (
    Base64EncodeStep,
    Base64DecodeStep,
    Base64URLEncodeStep,
    Base64URLDecodeStep,
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


class TestBase64EncodeStep:
    @pytest.mark.asyncio
    async def test_encode_string(self, mock_memory):
        mock_memory._data["input"] = "hello world"

        step = Base64EncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "aGVsbG8gd29ybGQ="

    @pytest.mark.asyncio
    async def test_encode_empty_string(self, mock_memory):
        mock_memory._data["input"] = ""

        step = Base64EncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ""

    @pytest.mark.asyncio
    async def test_encode_unicode(self, mock_memory):
        mock_memory._data["input"] = "héllo wörld 🌍"

        step = Base64EncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        # Should be valid Base64
        import base64
        decoded = base64.b64decode(mock_memory._data["memory.result"]).decode('utf-8')
        assert decoded == "héllo wörld 🌍"

    @pytest.mark.asyncio
    async def test_encode_bytes(self, mock_memory):
        mock_memory._data["input"] = b"\x00\x01\x02\xff"

        step = Base64EncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "AAEC/w=="


class TestBase64DecodeStep:
    @pytest.mark.asyncio
    async def test_decode_string(self, mock_memory):
        mock_memory._data["input"] = "aGVsbG8gd29ybGQ="

        step = Base64DecodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello world"

    @pytest.mark.asyncio
    async def test_decode_empty_string(self, mock_memory):
        mock_memory._data["input"] = ""

        step = Base64DecodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ""

    @pytest.mark.asyncio
    async def test_decode_as_bytes(self, mock_memory):
        mock_memory._data["input"] = "AAEC/w=="

        step = Base64DecodeStep(
            id="test",
            config={"input": "input", "as_bytes": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == b"\x00\x01\x02\xff"

    @pytest.mark.asyncio
    async def test_decode_invalid_base64(self, mock_memory):
        mock_memory._data["input"] = "not valid base64!!!"

        step = Base64DecodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="Invalid Base64"):
            await step.execute(mock_memory)


class TestBase64URLEncodeStep:
    @pytest.mark.asyncio
    async def test_encode_url_safe(self, mock_memory):
        # Content that would produce + and / in standard Base64
        mock_memory._data["input"] = "subjects?_d"

        step = Base64URLEncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        result = mock_memory._data["memory.result"]
        # URL-safe Base64 should not contain + or /
        assert "+" not in result
        assert "/" not in result

    @pytest.mark.asyncio
    async def test_encode_url_safe_roundtrip(self, mock_memory):
        mock_memory._data["input"] = "hello world"

        step = Base64URLEncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        import base64
        decoded = base64.urlsafe_b64decode(mock_memory._data["memory.result"]).decode('utf-8')
        assert decoded == "hello world"


class TestBase64URLDecodeStep:
    @pytest.mark.asyncio
    async def test_decode_url_safe(self, mock_memory):
        import base64
        encoded = base64.urlsafe_b64encode(b"hello world").decode('ascii')
        mock_memory._data["input"] = encoded

        step = Base64URLDecodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello world"

    @pytest.mark.asyncio
    async def test_decode_url_safe_as_bytes(self, mock_memory):
        import base64
        encoded = base64.urlsafe_b64encode(b"\x00\xff").decode('ascii')
        mock_memory._data["input"] = encoded

        step = Base64URLDecodeStep(
            id="test",
            config={"input": "input", "as_bytes": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == b"\x00\xff"
