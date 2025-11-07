"""LLM and tool-calling agent step types."""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from graphflow_core.steps.base import StepBase
from graphflow_core.steps.registry import StepRegistry
from graphflow_core.memory.store import MemoryStore


@StepRegistry.register(
    category="ai",
    description="LLM call with tool support, prompts, and structured outputs"
)
class LLMStep(StepBase):
    """
    LLM/Agent step - call an LLM with tools and structured outputs.

    This step handles calling language models with:
    - Configurable prompts (system + user)
    - Tool calling capabilities
    - Structured output schemas
    - Multiple LLM provider support

    Config:
        provider: str - LLM provider (openrouter, openai, anthropic, etc.)
        model: str - Model identifier (e.g., "gpt-4", "claude-3-5-sonnet")
        api_key_secret: str - Secret key for API key (optional, defaults to provider default)

        system_prompt: str - System prompt template (supports {{variable}} syntax)
        user_prompt: str - User prompt template (supports {{variable}} syntax)

        tools: List[str|Dict] - Tool definitions
            - String: Reference to registered tool by name
            - Dict: Inline tool definition (OpenAI function calling format)

        output_schema: Dict - Pydantic model schema for structured output
            Example: {
                "type": "object",
                "properties": {
                    "answer": {"type": "string"},
                    "confidence": {"type": "number"}
                },
                "required": ["answer"]
            }

        temperature: float - Sampling temperature (default: 0.7)
        max_tokens: int - Maximum tokens to generate
        response_format: str - "text" or "json" (default: "text")

    Memory Reads:
        - Variables referenced in system_prompt and user_prompt templates
        - Should be declared in memory_reads

    Memory Writes:
        - If output_schema is provided: writes structured dict to specified key
        - If no output_schema: writes text response to specified key
        - Optionally writes tool calls to separate key
    """

    @classmethod
    def get_type(cls) -> str:
        return "llm"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                # Provider configuration
                "provider": {
                    "type": "string",
                    "enum": ["openrouter", "openai", "anthropic", "azure", "custom"],
                    "default": "openrouter",
                    "description": "LLM provider"
                },
                "model": {
                    "type": "string",
                    "description": "Model identifier (e.g., 'gpt-4-turbo', 'anthropic/claude-3.5-sonnet')"
                },
                "api_key_secret": {
                    "type": "string",
                    "description": "Secret key for API key (references secrets in memory schema)"
                },
                "base_url": {
                    "type": "string",
                    "description": "Custom base URL for API calls (for custom providers)"
                },

                # Prompts
                "system_prompt": {
                    "type": "string",
                    "description": "System prompt template (supports {{variable}} syntax)"
                },
                "user_prompt": {
                    "type": "string",
                    "description": "User prompt template (supports {{variable}} syntax)"
                },

                # Tools
                "tools": {
                    "type": "array",
                    "items": {
                        "oneOf": [
                            {"type": "string"},  # Tool name reference
                            {"type": "object"}   # Inline tool definition
                        ]
                    },
                    "description": "List of tools available to the LLM"
                },
                "tool_choice": {
                    "type": "string",
                    "enum": ["auto", "required", "none"],
                    "default": "auto",
                    "description": "Tool calling behavior"
                },

                # Output configuration
                "output_schema": {
                    "type": "object",
                    "description": "JSON schema for structured output (Pydantic-compatible)"
                },

                # LLM parameters
                "temperature": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 2,
                    "default": 0.7,
                    "description": "Sampling temperature"
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum tokens to generate"
                },
                "top_p": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 1,
                    "description": "Nucleus sampling parameter"
                },
                "response_format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "default": "text",
                    "description": "Response format"
                },

                # Advanced options
                "streaming": {
                    "type": "boolean",
                    "default": False,
                    "description": "Enable streaming responses"
                },
                "retries": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 2,
                    "description": "Number of retries on failure"
                },
            },
            "required": ["model"]
        }

    @classmethod
    def get_inputs_schema(cls) -> Dict[str, Any]:
        """
        LLMStep reads memory keys referenced in prompt templates.
        Inputs are dynamic based on {memory.variable} syntax in prompts.
        """
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
            "description": "Reads memory keys referenced in system_prompt and user_prompt templates using {memory.variable} syntax"
        }

    @classmethod
    def get_outputs_schema(cls) -> Dict[str, Any]:
        """LLMStep writes LLM response."""
        return {
            "type": "object",
            "properties": {
                "response": {
                    "description": "LLM response (text or structured object based on output_schema)"
                },
                "tool_calls": {
                    "type": "array",
                    "description": "Tool calls made by LLM (optional)"
                }
            },
            "description": "Writes LLM response and optionally tool calls to locations specified in outputs dict"
        }

    @classmethod
    def get_code_template(cls, framework: str) -> Optional[str]:
        """
        Return framework-specific code generation template for LLM step.

        LLM steps require different implementations for different frameworks:
        - Pydantic AI: Uses Agent API with structured outputs
        - LangGraph: Uses ChatModel with message-based interface

        Args:
            framework: Target framework ('pydantic_ai' or 'langgraph')

        Returns:
            Jinja2 template string, or None if framework not supported
        """
        # Load template from package
        template_dir = Path(__file__).parent / "templates" / "llm"
        template_file = template_dir / f"{framework}.jinja"

        if template_file.exists():
            return template_file.read_text()

        # Framework not supported
        return None

    @classmethod
    def get_supported_frameworks(cls) -> List[str]:
        """LLM step supports both Pydantic AI and LangGraph."""
        return ["pydantic_ai", "langgraph"]

    def validate_config(self) -> List[str]:
        """Validate LLM step configuration."""
        errors = []

        # Check required fields
        if "model" not in self.config:
            errors.append(f"LLMStep {self.id}: 'model' is required")

        # Check at least one prompt is provided
        if not self.config.get("system_prompt") and not self.config.get("user_prompt"):
            errors.append(f"LLMStep {self.id}: at least one of 'system_prompt' or 'user_prompt' is required")

        # Validate temperature range
        temperature = self.config.get("temperature", 0.7)
        if not (0 <= temperature <= 2):
            errors.append(f"LLMStep {self.id}: temperature must be between 0 and 2")

        # Validate provider
        provider = self.config.get("provider", "openrouter")
        valid_providers = {"openrouter", "openai", "anthropic", "azure", "custom"}
        if provider not in valid_providers:
            errors.append(f"LLMStep {self.id}: invalid provider '{provider}'")

        # If custom provider, base_url is required
        if provider == "custom" and not self.config.get("base_url"):
            errors.append(f"LLMStep {self.id}: 'base_url' required for custom provider")

        # Check outputs
        if not self.outputs or 'response' not in self.outputs:
            errors.append(f"LLMStep {self.id}: outputs.response is required")

        return errors

    async def execute(self, memory: MemoryStore) -> None:
        """
        Execute LLM call.

        This is a placeholder - actual execution is framework-specific and
        will be implemented in generated code by the compiler.

        For testing purposes, this returns a mock response.
        """
        import re

        # Extract configuration
        system_prompt = self.config.get("system_prompt", "")
        user_prompt = self.config.get("user_prompt", "")

        # Render prompts with memory values
        rendered_system = self._render_template(system_prompt, memory)
        rendered_user = self._render_template(user_prompt, memory)

        # Mock response for testing
        # In real implementation (generated code), this will call the actual LLM
        if self.config.get("output_schema"):
            # Structured output
            response = {
                "answer": f"Mock response to: {rendered_user[:50]}...",
                "confidence": 0.85,
                "_meta": {
                    "model": self.config["model"],
                    "tokens": 100
                }
            }
        else:
            # Text output
            response = f"Mock LLM response. System: {rendered_system[:30]}... User: {rendered_user[:30]}..."

        # Write to outputs
        pattern = re.compile(r'\{memory\.([^}]+)\}')

        if 'response' in self.outputs:
            response_template = self.outputs['response']
            match = pattern.search(response_template)
            if match:
                output_key = match.group(1)
                memory.write(output_key, response)

        # Write tool calls if configured
        if 'tool_calls' in self.outputs:
            tool_calls_template = self.outputs['tool_calls']
            match = pattern.search(tool_calls_template)
            if match:
                tool_calls_key = match.group(1)
                memory.write(tool_calls_key, [])

    def _render_template(self, template: str, memory: MemoryStore) -> str:
        """
        Render template with memory values.

        Supports {memory.variable} and {memory.nested.path} syntax.

        Args:
            template: Template string
            memory: Memory store

        Returns:
            Rendered string
        """
        if not template:
            return ""

        import re

        # Find all {memory.variable} patterns
        pattern = r'\{memory\.([^}]+)\}'
        matches = re.findall(pattern, template)

        rendered = template
        for var_name in matches:
            var_name = var_name.strip()
            try:
                value = memory.read(var_name)
                # Convert to string
                value_str = str(value) if value is not None else ""
                rendered = rendered.replace(f"{{memory.{var_name}}}", value_str)
            except KeyError:
                # Leave placeholder if key not found
                pass

        return rendered
