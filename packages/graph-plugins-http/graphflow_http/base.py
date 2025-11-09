"""Base HTTP client functionality for GraphFlow HTTP plugin."""
import asyncio
import re
from typing import Any, Dict, Optional
from abc import ABC

import httpx

from graphflow_core.steps.base import StepBase
from graphflow_core.memory import MemoryStore


class BaseHTTPStep(StepBase, ABC):
    """Base class for HTTP steps with shared functionality."""

    category = "http"

    def _render_template(self, template: str, memory: MemoryStore) -> str:
        """
        Render template string with memory values.

        Supports namespaced syntax:
        - {memory.variable}
        - {config.variable}
        - {env.variable}
        - {secrets.variable}
        """
        if not template:
            return ""

        # Find all {namespace.variable} patterns
        pattern = r'\{(memory|config|env|secrets)\.(\w+(?:\.\w+)*)\}'
        matches = re.findall(pattern, template)

        result = template
        for namespace, field in matches:
            # Create the full namespaced key
            full_key = f"{namespace}.{field}"

            # Try to read from memory using namespaced key
            try:
                value = memory.read(full_key)
            except KeyError:
                value = None

            # Replace in template
            if value is not None:
                result = result.replace(f'{{{full_key}}}', str(value))

        return result

    def _render_dict(self, data: Dict[str, Any], memory: MemoryStore) -> Dict[str, Any]:
        """Render all string values in a dict through template engine."""
        if not data:
            return {}

        # If data is a string (memory template), render it first
        if isinstance(data, str):
            rendered = self._render_template(data, memory)
            # If the rendered value is not a dict, return empty dict
            if not isinstance(rendered, dict):
                return {}
            data = rendered

        result = {}
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._render_template(value, memory)
            elif isinstance(value, dict):
                result[key] = self._render_dict(value, memory)
            else:
                result[key] = value

        return result

    async def _make_request(
        self,
        method: str,
        url: str,
        *,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Any] = None,
        timeout: int = 30,
        retries: int = 2,
        verify_ssl: bool = True,
        follow_redirects: bool = True,
        auth: Optional[Dict[str, str]] = None,
    ) -> httpx.Response:
        """
        Make HTTP request with retry logic.

        Args:
            method: HTTP method (GET, POST, etc.)
            url: Request URL
            params: Query parameters
            headers: Request headers
            body: Request body (for POST, PUT, PATCH)
            timeout: Request timeout in seconds
            retries: Number of retry attempts
            verify_ssl: Verify SSL certificates
            follow_redirects: Follow HTTP redirects
            auth: Authentication dict with 'type' and credentials

        Returns:
            httpx.Response object

        Raises:
            httpx.HTTPError: On request failure after retries
        """
        # Build auth
        auth_obj = None
        if auth:
            auth_type = auth.get('type', '').lower()
            if auth_type == 'basic':
                auth_obj = httpx.BasicAuth(
                    username=auth.get('username', ''),
                    password=auth.get('password', '')
                )
            elif auth_type == 'bearer':
                if not headers:
                    headers = {}
                headers['Authorization'] = f"Bearer {auth.get('token', '')}"

        # Build client config
        client_config = {
            'timeout': timeout,
            'verify': verify_ssl,
            'follow_redirects': follow_redirects,
        }

        if auth_obj:
            client_config['auth'] = auth_obj

        last_exception = None

        for attempt in range(retries + 1):
            try:
                async with httpx.AsyncClient(**client_config) as client:
                    # Build request kwargs
                    request_kwargs = {
                        'url': url,
                        'params': params,
                        'headers': headers,
                    }

                    # Add body for methods that support it
                    if body is not None and method.upper() in ['POST', 'PUT', 'PATCH']:
                        if isinstance(body, (dict, list)):
                            request_kwargs['json'] = body
                        else:
                            request_kwargs['content'] = str(body)

                    # Make request
                    response = await client.request(method, **request_kwargs)
                    response.raise_for_status()

                    return response

            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as e:
                last_exception = e

                if attempt < retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                else:
                    raise

        # Should not reach here, but just in case
        if last_exception:
            raise last_exception

        raise httpx.HTTPError("Request failed with unknown error")

    def _parse_response(self, response: httpx.Response) -> Any:
        """
        Parse response body based on content type.

        Returns:
            Parsed response body (dict for JSON, str for text, bytes for binary)
        """
        content_type = response.headers.get('content-type', '').lower()

        try:
            if 'application/json' in content_type:
                return response.json()
            elif 'text/' in content_type or 'application/xml' in content_type:
                return response.text
            else:
                return response.content
        except Exception:
            # Fallback to text
            return response.text

    def _write_output(self, memory: MemoryStore, output_name: str, value: Any) -> None:
        """
        Write a value to memory using the outputs dict.

        Args:
            memory: Memory store
            output_name: Name of the output in the outputs dict
            value: Value to write
        """
        if output_name not in self.outputs:
            return

        output_template = self.outputs[output_name]
        # Support all namespaces: {memory.*}, {config.*}, {env.*}, {secrets.*}
        pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')
        match = pattern.search(output_template)

        if match:
            namespace = match.group(1)
            field_key = match.group(2)
            # Write with full namespaced key
            memory.write(f"{namespace}.{field_key}", value)
