"""URL manipulation step implementations."""
import re
from typing import Any, Dict
from urllib.parse import quote, unquote, urlparse, urlunparse, parse_qs, urlencode

from graphflow_core.memory import MemoryStore
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry

# Pattern for extracting memory references
pattern = re.compile(r'\{(memory|config|env|secrets)\.([^}]+)\}')


@StepRegistry.register(step_type="url.URLEscapeStep", category="url", description="URL encode a string", plugin="url")
class URLEscapeStep(StepBase):
    """URL encode/escape string step."""

    name = "URL Escape"
    label = "URL Escape"
    description = "URL encode a string for safe use in URLs"
    category = "url"

    @classmethod
    def get_type(cls) -> str:
        return "url.URLEscapeStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                },
                "safe": {
                    "type": "string",
                    "default": "",
                    "description": "Characters that should not be encoded (default: empty)"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "String to URL encode"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "URL encoded string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute URL escape."""
        # Extract input from config
        input_template = self.config.get("input", "")
        mem_pattern = re.compile(r'\{memory\.([^}]+)\}')
        match = mem_pattern.search(input_template)
        if match:
            input_key = match.group(1)
            input_value = memory.read(input_key)
        else:
            raise ValueError(f"{self.__class__.__name__} {self.id}: Invalid input reference")
        safe_chars = self.config.get("safe", "")

        # Convert to string if needed
        input_str = str(input_value) if input_value is not None else ""

        # URL encode
        encoded = quote(input_str, safe=safe_chars)

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = mem_pattern.search(output_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, encoded)


@StepRegistry.register(step_type="url.URLUnescapeStep", category="url", description="URL decode a string", plugin="url")
class URLUnescapeStep(StepBase):
    """URL decode/unescape string step."""

    name = "URL Unescape"
    label = "URL Unescape"
    description = "URL decode a percent-encoded string"

    @classmethod
    def get_type(cls) -> str:
        return "url.URLUnescapeStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "URL encoded string to decode"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "output": {
                    "type": "string",
                    "description": "Decoded string"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute URL unescape."""
        # Extract input from config
        input_template = self.config.get("input", "")
        mem_pattern = re.compile(r'\{memory\.([^}]+)\}')
        match = mem_pattern.search(input_template)
        if match:
            input_key = match.group(1)
            input_value = memory.read(input_key)
        else:
            raise ValueError(f"{self.__class__.__name__} {self.id}: Invalid input reference")

        # Convert to string if needed
        input_str = str(input_value) if input_value is not None else ""

        # URL decode
        decoded = unquote(input_str)

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = mem_pattern.search(output_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, decoded)


@StepRegistry.register(step_type="url.URLBuildStep", category="url", description="Build a URL from components", plugin="url")
class URLBuildStep(StepBase):
    """Build URL from components step."""

    name = "URL Build"
    label = "URL Build"
    description = "Construct a URL from components (scheme, host, path, params, etc.)"

    @classmethod
    def get_type(cls) -> str:
        return "url.URLBuildStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "scheme": {
                    "type": "string",
                    "default": "https",
                    "description": "URL scheme (http, https, etc.)"
                },
                "host": {
                    "type": "string",
                    "description": "Hostname (e.g., api.example.com)"
                },
                "port": {
                    "type": "integer",
                    "description": "Port number (optional)"
                },
                "path": {
                    "type": "string",
                    "default": "",
                    "description": "URL path (e.g., /api/users)"
                },
                "params": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Query parameters as key-value pairs"
                },
                "fragment": {
                    "type": "string",
                    "description": "URL fragment/anchor (optional)"
                }
            },
            "required": ["host"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Can read scheme, host, port, path, params, fragment from memory if specified as keys"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Constructed URL"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute URL build."""
        scheme = self.config.get("scheme", "https")
        host = self.config["host"]
        port = self.config.get("port")
        path = self.config.get("path", "")
        params = self.config.get("params", {})
        fragment = self.config.get("fragment", "")

        # Build netloc (host:port)
        if port:
            netloc = f"{host}:{port}"
        else:
            netloc = host

        # Encode query parameters
        query = urlencode(params) if params else ""

        # Construct URL using urlunparse
        url = urlunparse((scheme, netloc, path, "", query, fragment))

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, url)


@StepRegistry.register(step_type="url.URLParseStep", category="url", description="Parse URL into components", plugin="url")
class URLParseStep(StepBase):
    """Parse URL into components step."""

    name = "URL Parse"
    label = "URL Parse"
    description = "Extract components from a URL (scheme, host, path, params, etc.)"

    @classmethod
    def get_type(cls) -> str:
        return "url.URLParseStep"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input value using {memory.variable} syntax"
                }
            },
            "required": ["input"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to parse"
                }
            },
            "required": ["url"]
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "components": {
                    "type": "object",
                    "properties": {
                        "scheme": {"type": "string"},
                        "netloc": {"type": "string"},
                        "host": {"type": "string"},
                        "port": {"type": "integer"},
                        "path": {"type": "string"},
                        "params": {"type": "object"},
                        "query": {"type": "string"},
                        "fragment": {"type": "string"}
                    },
                    "description": "Parsed URL components"
                }
            }
        }

    async def execute(self, memory: MemoryStore) -> None:
        """Execute URL parse."""
        url = memory.read(self.config["input"])

        # Parse URL
        parsed = urlparse(str(url))

        # Extract host and port from netloc
        netloc = parsed.netloc
        host = netloc
        port = None

        if ':' in netloc:
            host, port_str = netloc.rsplit(':', 1)
            try:
                port = int(port_str)
            except ValueError:
                host = netloc  # Not a valid port, keep full netloc

        # Parse query parameters
        params = {}
        if parsed.query:
            # parse_qs returns lists for each value, simplify to single values
            parsed_params = parse_qs(parsed.query)
            params = {k: v[0] if len(v) == 1 else v for k, v in parsed_params.items()}

        # Build components dict
        components = {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "host": host,
            "port": port,
            "path": parsed.path,
            "params": params,
            "query": parsed.query,
            "fragment": parsed.fragment,
        }

        # Write output
        if "output" in self.outputs:
            output_template = self.outputs["output"]
            match = pattern.search(output_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, components)
