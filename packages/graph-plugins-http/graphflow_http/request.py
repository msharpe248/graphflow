"""HTTP request step implementations."""
from typing import Any, Dict

from graphflow_core.memory import MemoryStore
from .base import BaseHTTPStep


class HTTPGetStep(BaseHTTPStep):
    """HTTP GET request step."""

    name = "HTTP GET"
    label = "HTTP GET"
    description = "Perform HTTP GET request to fetch data from a URL"

    @classmethod
    def get_type(cls) -> str:
        return "http-get"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Request URL (supports {memory.variable} template syntax)"
                },
                "params": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Query parameters (key-value pairs)"
                },
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Request headers (key-value pairs)"
                },
                "auth": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["basic", "bearer"]},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "token": {"type": "string"}
                    },
                    "description": "Authentication configuration"
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 30,
                    "description": "Request timeout in seconds"
                },
                "retries": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 2,
                    "description": "Number of retry attempts on failure"
                },
                "verify_ssl": {
                    "type": "boolean",
                    "default": True,
                    "description": "Verify SSL certificates"
                },
                "follow_redirects": {
                    "type": "boolean",
                    "default": True,
                    "description": "Follow HTTP redirects"
                }
            },
            "required": ["url"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Reads memory keys referenced in url, params, and headers using {memory.variable} syntax"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "response": {
                    "description": "HTTP response body"
                },
                "status_code": {
                    "type": "integer",
                    "description": "HTTP status code"
                },
                "headers": {
                    "type": "object",
                    "description": "Response headers"
                }
            },
            "description": "Writes HTTP GET response to locations specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTTP GET request."""
        # Get and render configuration
        url = self._render_template(self.config["url"], memory)
        params = self._render_dict(self.config.get("params", {}), memory)
        headers = self._render_dict(self.config.get("headers", {}), memory)
        auth = self.config.get("auth")
        timeout = self.config.get("timeout", 30)
        retries = self.config.get("retries", 2)
        verify_ssl = self.config.get("verify_ssl", True)
        follow_redirects = self.config.get("follow_redirects", True)

        # Make request
        response = await self._make_request(
            method="GET",
            url=url,
            params=params,
            headers=headers,
            auth=auth,
            timeout=timeout,
            retries=retries,
            verify_ssl=verify_ssl,
            follow_redirects=follow_redirects,
        )

        # Parse and write response using outputs dict
        response_body = self._parse_response(response)
        self._write_output(memory, "response", response_body)
        self._write_output(memory, "status_code", response.status_code)
        self._write_output(memory, "headers", dict(response.headers))


class HTTPPostStep(BaseHTTPStep):
    """HTTP POST request step."""

    name = "HTTP POST"
    label = "HTTP POST"
    description = "Perform HTTP POST request to send data to a URL"

    @classmethod
    def get_type(cls) -> str:
        return "http-post"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Request URL (supports {memory.variable} template syntax)"
                },
                "body": {
                    "description": "Request body (JSON object, string, or template)"
                },
                "params": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Query parameters (key-value pairs)"
                },
                "headers": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Request headers (key-value pairs)"
                },
                "auth": {
                    "type": "object",
                    "properties": {
                        "type": {"type": "string", "enum": ["basic", "bearer"]},
                        "username": {"type": "string"},
                        "password": {"type": "string"},
                        "token": {"type": "string"}
                    },
                    "description": "Authentication configuration"
                },
                "timeout": {
                    "type": "integer",
                    "minimum": 1,
                    "default": 30,
                    "description": "Request timeout in seconds"
                },
                "retries": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 2,
                    "description": "Number of retry attempts on failure"
                },
                "verify_ssl": {
                    "type": "boolean",
                    "default": True,
                    "description": "Verify SSL certificates"
                },
                "follow_redirects": {
                    "type": "boolean",
                    "default": True,
                    "description": "Follow HTTP redirects"
                }
            },
            "required": ["url"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Reads memory keys referenced in url, body, params, and headers using {memory.variable} syntax"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "response": {
                    "description": "HTTP response body"
                },
                "status_code": {
                    "type": "integer",
                    "description": "HTTP status code"
                },
                "headers": {
                    "type": "object",
                    "description": "Response headers"
                }
            },
            "description": "Writes HTTP POST response to locations specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTTP POST request."""
        # Get and render configuration
        url = self._render_template(self.config["url"], memory)
        params = self._render_dict(self.config.get("params", {}), memory)
        headers = self._render_dict(self.config.get("headers", {}), memory)
        auth = self.config.get("auth")
        timeout = self.config.get("timeout", 30)
        retries = self.config.get("retries", 2)
        verify_ssl = self.config.get("verify_ssl", True)
        follow_redirects = self.config.get("follow_redirects", True)

        # Get and render body
        body = self.config.get("body")
        if body and isinstance(body, str):
            body = self._render_template(body, memory)
        elif body and isinstance(body, dict):
            body = self._render_dict(body, memory)

        # Make request
        response = await self._make_request(
            method="POST",
            url=url,
            params=params,
            headers=headers,
            body=body,
            auth=auth,
            timeout=timeout,
            retries=retries,
            verify_ssl=verify_ssl,
            follow_redirects=follow_redirects,
        )

        # Parse and write response using outputs dict
        response_body = self._parse_response(response)
        self._write_output(memory, "response", response_body)
        self._write_output(memory, "status_code", response.status_code)
        self._write_output(memory, "headers", dict(response.headers))


class HTTPPutStep(BaseHTTPStep):
    """HTTP PUT request step."""

    name = "HTTP PUT"
    label = "HTTP PUT"
    description = "Perform HTTP PUT request to update resource at URL"

    @classmethod
    def get_type(cls) -> str:
        return "http-put"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        # Same schema as POST
        schema = HTTPPostStep.get_schema()
        return schema

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return HTTPPostStep.get_inputs_schema()

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "response": {
                    "description": "HTTP response body "
                },
                "status_code": {
                    "type": "integer",
                    "description": "HTTP status code "
                },
                "headers": {
                    "type": "object",
                    "description": "Response headers "
                }
            },
            "description": "Writes HTTP PUT response to locations specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTTP PUT request."""
        # Get and render configuration (same as POST)
        url = self._render_template(self.config["url"], memory)
        params = self._render_dict(self.config.get("params", {}), memory)
        headers = self._render_dict(self.config.get("headers", {}), memory)
        auth = self.config.get("auth")
        timeout = self.config.get("timeout", 30)
        retries = self.config.get("retries", 2)
        verify_ssl = self.config.get("verify_ssl", True)
        follow_redirects = self.config.get("follow_redirects", True)

        # Get and render body
        body = self.config.get("body")
        if body and isinstance(body, str):
            body = self._render_template(body, memory)
        elif body and isinstance(body, dict):
            body = self._render_dict(body, memory)

        # Make request
        response = await self._make_request(
            method="PUT",
            url=url,
            params=params,
            headers=headers,
            body=body,
            auth=auth,
            timeout=timeout,
            retries=retries,
            verify_ssl=verify_ssl,
            follow_redirects=follow_redirects,
        )

        # Parse and write response
        response_body = self._parse_response(response)
        self._write_output(memory, "response", response_body)

        # Write optional outputs
        self._write_output(memory, "status_code", response.status_code)

        self._write_output(memory, "headers", dict(response.headers))


class HTTPPatchStep(BaseHTTPStep):
    """HTTP PATCH request step."""

    name = "HTTP PATCH"
    label = "HTTP PATCH"
    description = "Perform HTTP PATCH request for partial resource updates"

    @classmethod
    def get_type(cls) -> str:
        return "http-patch"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        # Same schema as POST
        return HTTPPostStep.get_schema()

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return HTTPPostStep.get_inputs_schema()

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "response": {
                    "description": "HTTP response body "
                },
                "status_code": {
                    "type": "integer",
                    "description": "HTTP status code "
                },
                "headers": {
                    "type": "object",
                    "description": "Response headers "
                }
            },
            "description": "Writes HTTP PATCH response to locations specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTTP PATCH request."""
        # Get and render configuration (same as POST)
        url = self._render_template(self.config["url"], memory)
        params = self._render_dict(self.config.get("params", {}), memory)
        headers = self._render_dict(self.config.get("headers", {}), memory)
        auth = self.config.get("auth")
        timeout = self.config.get("timeout", 30)
        retries = self.config.get("retries", 2)
        verify_ssl = self.config.get("verify_ssl", True)
        follow_redirects = self.config.get("follow_redirects", True)

        # Get and render body
        body = self.config.get("body")
        if body and isinstance(body, str):
            body = self._render_template(body, memory)
        elif body and isinstance(body, dict):
            body = self._render_dict(body, memory)

        # Make request
        response = await self._make_request(
            method="PATCH",
            url=url,
            params=params,
            headers=headers,
            body=body,
            auth=auth,
            timeout=timeout,
            retries=retries,
            verify_ssl=verify_ssl,
            follow_redirects=follow_redirects,
        )

        # Parse and write response
        response_body = self._parse_response(response)
        self._write_output(memory, "response", response_body)

        # Write optional outputs
        self._write_output(memory, "status_code", response.status_code)

        self._write_output(memory, "headers", dict(response.headers))


class HTTPDeleteStep(BaseHTTPStep):
    """HTTP DELETE request step."""

    name = "HTTP DELETE"
    label = "HTTP DELETE"
    description = "Perform HTTP DELETE request to remove resource at URL"

    @classmethod
    def get_type(cls) -> str:
        return "http-delete"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        # Similar to GET, but without body
        return HTTPGetStep.get_schema()

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return HTTPGetStep.get_inputs_schema()

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "response": {
                    "description": "HTTP response body "
                },
                "status_code": {
                    "type": "integer",
                    "description": "HTTP status code "
                },
                "headers": {
                    "type": "object",
                    "description": "Response headers "
                }
            },
            "description": "Writes HTTP DELETE response to locations specified in outputs dict"
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute HTTP DELETE request."""
        # Get and render configuration (same as GET)
        url = self._render_template(self.config["url"], memory)
        params = self._render_dict(self.config.get("params", {}), memory)
        headers = self._render_dict(self.config.get("headers", {}), memory)
        auth = self.config.get("auth")
        timeout = self.config.get("timeout", 30)
        retries = self.config.get("retries", 2)
        verify_ssl = self.config.get("verify_ssl", True)
        follow_redirects = self.config.get("follow_redirects", True)

        # Make request
        response = await self._make_request(
            method="DELETE",
            url=url,
            params=params,
            headers=headers,
            auth=auth,
            timeout=timeout,
            retries=retries,
            verify_ssl=verify_ssl,
            follow_redirects=follow_redirects,
        )

        # Parse and write response
        response_body = self._parse_response(response)
        self._write_output(memory, "response", response_body)

        # Write optional outputs
        self._write_output(memory, "status_code", response.status_code)

        self._write_output(memory, "headers", dict(response.headers))
