"""Tests for compression steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_encoding import (
    GzipCompressStep,
    GzipDecompressStep,
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


class TestGzipCompressStep:
    @pytest.mark.asyncio
    async def test_compress_string(self, mock_memory):
        mock_memory._data["input"] = "hello world"

        step = GzipCompressStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        # Result should be Base64 by default
        import base64
        compressed_bytes = base64.b64decode(mock_memory._data["memory.result"])

        # Verify it's valid gzip
        import gzip
        decompressed = gzip.decompress(compressed_bytes)
        assert decompressed == b"hello world"

    @pytest.mark.asyncio
    async def test_compress_empty_string(self, mock_memory):
        mock_memory._data["input"] = ""

        step = GzipCompressStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        # Should still produce valid gzip
        import base64
        import gzip
        compressed_bytes = base64.b64decode(mock_memory._data["memory.result"])
        decompressed = gzip.decompress(compressed_bytes)
        assert decompressed == b""

    @pytest.mark.asyncio
    async def test_compress_with_level(self, mock_memory):
        mock_memory._data["input"] = "a" * 1000

        step = GzipCompressStep(
            id="test",
            config={"input": "input", "compression_level": 9},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        # Higher compression should result in smaller output
        import base64
        compressed_bytes = base64.b64decode(mock_memory._data["memory.result"])
        assert len(compressed_bytes) < 1000  # Should compress well

    @pytest.mark.asyncio
    async def test_compress_output_bytes(self, mock_memory):
        mock_memory._data["input"] = "hello"

        step = GzipCompressStep(
            id="test",
            config={"input": "input", "output_format": "bytes"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        # Result should be raw bytes
        assert isinstance(mock_memory._data["memory.result"], bytes)

        import gzip
        decompressed = gzip.decompress(mock_memory._data["memory.result"])
        assert decompressed == b"hello"


class TestGzipDecompressStep:
    @pytest.mark.asyncio
    async def test_decompress_string(self, mock_memory):
        # First compress some data
        import gzip
        import base64
        compressed = gzip.compress(b"hello world")
        mock_memory._data["input"] = base64.b64encode(compressed).decode('ascii')

        step = GzipDecompressStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "hello world"

    @pytest.mark.asyncio
    async def test_decompress_empty(self, mock_memory):
        import gzip
        import base64
        compressed = gzip.compress(b"")
        mock_memory._data["input"] = base64.b64encode(compressed).decode('ascii')

        step = GzipDecompressStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == ""

    @pytest.mark.asyncio
    async def test_decompress_as_bytes(self, mock_memory):
        import gzip
        import base64
        compressed = gzip.compress(b"\x00\xff")
        mock_memory._data["input"] = base64.b64encode(compressed).decode('ascii')

        step = GzipDecompressStep(
            id="test",
            config={"input": "input", "as_bytes": True},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == b"\x00\xff"

    @pytest.mark.asyncio
    async def test_decompress_invalid_data(self, mock_memory):
        import base64
        mock_memory._data["input"] = base64.b64encode(b"not valid gzip").decode('ascii')

        step = GzipDecompressStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )

        with pytest.raises(ValueError, match="Failed to decompress"):
            await step.execute(mock_memory)

    @pytest.mark.asyncio
    async def test_roundtrip(self, mock_memory):
        """Compress then decompress should return original."""
        original = "test message with unicode: héllo 🌍"
        mock_memory._data["input"] = original

        compress_step = GzipCompressStep(
            id="compress",
            config={"input": "input"},
            outputs={"output": "{memory.compressed}"}
        )
        await compress_step.execute(mock_memory)

        mock_memory._data["to_decompress"] = mock_memory._data["memory.compressed"]
        decompress_step = GzipDecompressStep(
            id="decompress",
            config={"input": "to_decompress"},
            outputs={"output": "{memory.decompressed}"}
        )
        await decompress_step.execute(mock_memory)

        assert mock_memory._data["memory.decompressed"] == original
