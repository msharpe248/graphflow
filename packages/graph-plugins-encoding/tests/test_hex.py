"""Tests for hex encoding/decoding steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_encoding import (
    HexEncodeStep,
    HexDecodeStep,
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


class TestHexEncodeStep:
    @pytest.mark.asyncio
    async def test_encode_string(self, mock_memory):
        mock_memory._data["input"] = "hello"

        step = HexEncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "68656c6c6f"

    @pytest.mark.asyncio
    async def test_encode_empty_string(self, mock_memory):
        mock_memory._data["input"] = ""

        step = HexEncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ""

    @pytest.mark.asyncio
    async def test_encode_uppercase(self, mock_memory):
        mock_memory._data["input"] = "hello"

        step = HexEncodeStep(
            id="test",
            config={"input": "input", "uppercase": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "68656C6C6F"

    @pytest.mark.asyncio
    async def test_encode_bytes(self, mock_memory):
        mock_memory._data["input"] = b"\x00\xff"

        step = HexEncodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "00ff"


class TestHexDecodeStep:
    @pytest.mark.asyncio
    async def test_decode_string(self, mock_memory):
        mock_memory._data["input"] = "68656c6c6f"

        step = HexDecodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello"

    @pytest.mark.asyncio
    async def test_decode_uppercase(self, mock_memory):
        mock_memory._data["input"] = "68656C6C6F"

        step = HexDecodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello"

    @pytest.mark.asyncio
    async def test_decode_as_bytes(self, mock_memory):
        mock_memory._data["input"] = "00ff"

        step = HexDecodeStep(
            id="test",
            config={"input": "input", "as_bytes": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == b"\x00\xff"

    @pytest.mark.asyncio
    async def test_decode_invalid_hex(self, mock_memory):
        mock_memory._data["input"] = "xyz"

        step = HexDecodeStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="Invalid hexadecimal"):
            await step.execute(mock_memory)

    @pytest.mark.asyncio
    async def test_roundtrip(self, mock_memory):
        """Encode then decode should return original."""
        original = "test message"
        mock_memory._data["input"] = original

        encode_step = HexEncodeStep(
            id="encode",
            config={"input": "input"},
            outputs={"output": "{memory.encoded}"}
        )
        await encode_step.execute(mock_memory)

        mock_memory._data["to_decode"] = mock_memory._data["memory.encoded"]
        decode_step = HexDecodeStep(
            id="decode",
            config={"input": "to_decode"},
            outputs={"output": "{memory.decoded}"}
        )
        await decode_step.execute(mock_memory)

        assert mock_memory._data["memory.decoded"] == original
