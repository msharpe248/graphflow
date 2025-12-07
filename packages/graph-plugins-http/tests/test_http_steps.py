"""Tests for HTTP request steps."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from graphflow_http import (
    HTTPGetStep,
    HTTPPostStep,
    HTTPPutStep,
    HTTPPatchStep,
    HTTPDeleteStep,
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


@pytest.fixture
def mock_response():
    """Create a mock HTTP response."""
    response = MagicMock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/json"}
    response.text = '{"message": "success"}'
    response.json.return_value = {"message": "success"}
    return response


class TestHTTPGetStep:
    def test_get_type(self):
        assert HTTPGetStep.get_type() == "http.HTTPGetStep"

    def test_get_schema_has_url(self):
        schema = HTTPGetStep.get_schema()
        assert "url" in schema["properties"]
        assert "url" in schema["required"]

    def test_get_schema_has_headers(self):
        schema = HTTPGetStep.get_schema()
        assert "headers" in schema["properties"]

    def test_get_schema_has_timeout(self):
        schema = HTTPGetStep.get_schema()
        assert "timeout" in schema["properties"]
        assert schema["properties"]["timeout"]["default"] == 30

    def test_get_schema_has_retries(self):
        schema = HTTPGetStep.get_schema()
        assert "retries" in schema["properties"]
        assert schema["properties"]["retries"]["default"] == 2

    @pytest.mark.asyncio
    async def test_execute_get_json(self, mock_memory, mock_response):
        step = HTTPGetStep(
            id="test",
            config={"url": "https://api.example.com/data"},
            outputs={"response": "{memory.result}", "status_code": "{memory.status}"}
        )

        with patch.object(step, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            mock_response.headers = {"content-type": "application/json"}
            mock_response.json.return_value = {"message": "success"}

            await step.execute(mock_memory)

            mock_request.assert_called_once()
            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == "GET"
            assert call_kwargs["url"] == "https://api.example.com/data"

    @pytest.mark.asyncio
    async def test_execute_get_with_params(self, mock_memory, mock_response):
        step = HTTPGetStep(
            id="test",
            config={
                "url": "https://api.example.com/search",
                "params": {"q": "test", "page": "1"}
            },
            outputs={"response": "{memory.result}"}
        )

        with patch.object(step, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await step.execute(mock_memory)

            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["params"] == {"q": "test", "page": "1"}

    @pytest.mark.asyncio
    async def test_execute_get_with_headers(self, mock_memory, mock_response):
        step = HTTPGetStep(
            id="test",
            config={
                "url": "https://api.example.com/data",
                "headers": {"Authorization": "Bearer token123"}
            },
            outputs={"response": "{memory.result}"}
        )

        with patch.object(step, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await step.execute(mock_memory)

            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["headers"]["Authorization"] == "Bearer token123"


class TestHTTPPostStep:
    def test_get_type(self):
        assert HTTPPostStep.get_type() == "http.HTTPPostStep"

    def test_get_schema_has_body(self):
        schema = HTTPPostStep.get_schema()
        assert "body" in schema["properties"]

    @pytest.mark.asyncio
    async def test_execute_post_with_body(self, mock_memory, mock_response):
        step = HTTPPostStep(
            id="test",
            config={
                "url": "https://api.example.com/users",
                "body": {"name": "Test User", "email": "test@example.com"}
            },
            outputs={"response": "{memory.result}"}
        )

        with patch.object(step, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response
            mock_response.status_code = 201

            await step.execute(mock_memory)

            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == "POST"
            assert call_kwargs["body"]["name"] == "Test User"


class TestHTTPPutStep:
    def test_get_type(self):
        assert HTTPPutStep.get_type() == "http.HTTPPutStep"

    @pytest.mark.asyncio
    async def test_execute_put(self, mock_memory, mock_response):
        step = HTTPPutStep(
            id="test",
            config={
                "url": "https://api.example.com/users/123",
                "body": {"name": "Updated User"}
            },
            outputs={"response": "{memory.result}"}
        )

        with patch.object(step, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await step.execute(mock_memory)

            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == "PUT"


class TestHTTPPatchStep:
    def test_get_type(self):
        assert HTTPPatchStep.get_type() == "http.HTTPPatchStep"

    @pytest.mark.asyncio
    async def test_execute_patch(self, mock_memory, mock_response):
        step = HTTPPatchStep(
            id="test",
            config={
                "url": "https://api.example.com/users/123",
                "body": {"email": "new@example.com"}
            },
            outputs={"response": "{memory.result}"}
        )

        with patch.object(step, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_request.return_value = mock_response

            await step.execute(mock_memory)

            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == "PATCH"


class TestHTTPDeleteStep:
    def test_get_type(self):
        assert HTTPDeleteStep.get_type() == "http.HTTPDeleteStep"

    @pytest.mark.asyncio
    async def test_execute_delete(self, mock_memory, mock_response):
        step = HTTPDeleteStep(
            id="test",
            config={"url": "https://api.example.com/users/123"},
            outputs={"response": "{memory.result}"}
        )

        with patch.object(step, '_make_request', new_callable=AsyncMock) as mock_request:
            mock_response.status_code = 204
            mock_response.text = ""
            mock_request.return_value = mock_response

            await step.execute(mock_memory)

            call_kwargs = mock_request.call_args[1]
            assert call_kwargs["method"] == "DELETE"
