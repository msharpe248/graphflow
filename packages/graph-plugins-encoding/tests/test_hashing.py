"""Tests for hashing steps."""
import pytest
from unittest.mock import MagicMock

from graphflow_encoding import (
    MD5HashStep,
    SHA1HashStep,
    SHA256HashStep,
    SHA512HashStep,
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


class TestMD5HashStep:
    @pytest.mark.asyncio
    async def test_hash_string(self, mock_memory):
        mock_memory._data["input"] = "hello"

        step = MD5HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "5d41402abc4b2a76b9719d911017c592"

    @pytest.mark.asyncio
    async def test_hash_empty_string(self, mock_memory):
        mock_memory._data["input"] = ""

        step = MD5HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "d41d8cd98f00b204e9800998ecf8427e"

    @pytest.mark.asyncio
    async def test_hash_bytes(self, mock_memory):
        mock_memory._data["input"] = b"hello"

        step = MD5HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "5d41402abc4b2a76b9719d911017c592"


class TestSHA1HashStep:
    @pytest.mark.asyncio
    async def test_hash_string(self, mock_memory):
        mock_memory._data["input"] = "hello"

        step = SHA1HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d"

    @pytest.mark.asyncio
    async def test_hash_empty_string(self, mock_memory):
        mock_memory._data["input"] = ""

        step = SHA1HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "da39a3ee5e6b4b0d3255bfef95601890afd80709"


class TestSHA256HashStep:
    @pytest.mark.asyncio
    async def test_hash_string(self, mock_memory):
        mock_memory._data["input"] = "hello"

        step = SHA256HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    @pytest.mark.asyncio
    async def test_hash_empty_string(self, mock_memory):
        mock_memory._data["input"] = ""

        step = SHA256HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert mock_memory._data["memory.result"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    @pytest.mark.asyncio
    async def test_hash_deterministic(self, mock_memory):
        """Same input should always produce same hash."""
        mock_memory._data["input"] = "test message"

        step = SHA256HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        first_hash = mock_memory._data["memory.result"]

        await step.execute(mock_memory)
        second_hash = mock_memory._data["memory.result"]

        assert first_hash == second_hash


class TestSHA512HashStep:
    @pytest.mark.asyncio
    async def test_hash_string(self, mock_memory):
        mock_memory._data["input"] = "hello"

        step = SHA512HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        expected = "9b71d224bd62f3785d96d46ad3ea3d73319bfbc2890caadae2dff72519673ca72323c3d99ba5c11d7c7acc6e14b8c5da0c4663475c2e5c3adef46f73bcdec043"
        assert mock_memory._data["memory.result"] == expected

    @pytest.mark.asyncio
    async def test_hash_empty_string(self, mock_memory):
        mock_memory._data["input"] = ""

        step = SHA512HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        expected = "cf83e1357eefb8bdf1542850d66d8007d620e4050b5715dc83f4a921d36ce9ce47d0d13c5d85f2b0ff8318d2877eec2f63b931bd47417a81a538327af927da3e"
        assert mock_memory._data["memory.result"] == expected

    @pytest.mark.asyncio
    async def test_hash_length(self, mock_memory):
        """SHA512 produces 128 character hex string."""
        mock_memory._data["input"] = "test"

        step = SHA512HashStep(
            id="test",
            config={"input": "input"},
            outputs={"output": "{memory.result}"}
        )
        await step.execute(mock_memory)

        assert len(mock_memory._data["memory.result"]) == 128
