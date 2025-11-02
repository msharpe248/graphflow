"""Pydantic AI code generator."""

from typing import List
from graphflow_core.models import GraphDefinition, Step
from graphflow_compiler.base import CodeGenerator


class PydanticAIGenerator(CodeGenerator):
    """
    Generate Python code using Pydantic AI framework.

    Generated code uses:
    - pydantic_ai.Agent for LLM steps
    - pydantic_ai.models for structured outputs
    - Direct step execution for non-LLM steps
    """

    def get_framework_name(self) -> str:
        return "pydantic_ai"

    def _get_framework_imports(self, graph: GraphDefinition) -> List[str]:
        """Get Pydantic AI specific imports."""
        imports = []

        # Check if we need Pydantic AI (for LLM steps)
        has_llm = any(step.type == "llm" for step in graph.steps)
        if has_llm:
            imports.extend([
                "from pydantic_ai import Agent",
                "from pydantic_ai.models import Model, KnownModelName",
                "from pydantic import BaseModel",
            ])

        # Check if we need HTTP client
        has_http = any(step.type == "http" for step in graph.steps)
        if has_http:
            imports.append("import httpx")

        return imports

    def generate_agent_class(self, graph: GraphDefinition) -> str:
        """Generate the main agent class using Pydantic AI."""
        template = self.jinja_env.get_template("pydantic_ai_agent.py.jinja")

        # Prepare step execution code
        step_execution_map = {}
        for step in graph.steps:
            step_execution_map[step.id] = self.get_step_execution_code(step, graph)

        # Build execution order (simple linear for now, will add graph logic later)
        execution_order = [step.id for step in graph.steps]

        return template.render(
            graph=graph,
            step_execution_map=step_execution_map,
            execution_order=execution_order,
        )

    def _generate_llm_step_code(self, step: Step, graph: GraphDefinition) -> str:
        """Generate Pydantic AI specific LLM step code."""
        config = step.config
        provider = config.get("provider", "openrouter")
        model = config.get("model")
        system_prompt = config.get("system_prompt", "")
        user_prompt = config.get("user_prompt", "")
        output_key = config.get("output_key")
        output_schema = config.get("output_schema")
        tools = config.get("tools", [])
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens")

        lines = [
            "# LLM step using Pydantic AI",
            "",
        ]

        # Define output schema if provided
        if output_schema:
            lines.append("# Define output schema")
            lines.append(f"class LLMOutput_{step.id}(BaseModel):")
            if "properties" in output_schema:
                for prop_name, prop_def in output_schema["properties"].items():
                    prop_type = prop_def.get("type", "any")
                    type_hint = self._json_type_to_python(prop_type)
                    desc = prop_def.get("description", "")
                    lines.append(f'    {prop_name}: {type_hint}  # {desc}')
            else:
                lines.append("    pass")
            lines.append("")

        # Render prompts with memory values
        lines.append("# Render prompts")
        for key in step.memory_reads:
            var_name = key.replace('.', '_')
            lines.append(f'{var_name} = self.memory.read("{key}")')

        # Build full prompt
        lines.append("")
        lines.append("# Build prompt")

        if user_prompt:
            # Simple template rendering (replace {{var}} with values)
            lines.append(f'user_prompt_template = {repr(user_prompt)}')
            for key in step.memory_reads:
                var_name = key.replace('.', '_')
                lines.append(f'user_prompt_template = user_prompt_template.replace("{{{{{key}}}}}", str({var_name}))')
        else:
            lines.append('user_prompt_template = ""')

        lines.append("")

        # Get API key
        api_key_secret = config.get("api_key_secret")
        if api_key_secret:
            lines.append(f'api_key = self.memory.get_secret("{api_key_secret}")')
        else:
            lines.append(f'api_key = None  # Will use environment variable')

        lines.append("")

        # Create agent
        lines.append("# Create Pydantic AI agent")

        # Determine model string
        if provider == "openrouter":
            model_str = f'"openai:{model}"'  # OpenRouter uses OpenAI-compatible API
            base_url = '"https://openrouter.ai/api/v1"'
        elif provider == "anthropic":
            model_str = f'"{model}"'
            base_url = 'None'
        else:
            model_str = f'"{model}"'
            base_url = config.get("base_url", "None")
            if base_url != "None":
                base_url = f'"{base_url}"'

        result_type = f"LLMOutput_{step.id}" if output_schema else "str"

        lines.append(f"agent = Agent(")
        lines.append(f"    {model_str},")
        if system_prompt:
            lines.append(f'    system_prompt={repr(system_prompt)},')
        lines.append(f"    result_type={result_type},")
        lines.append(f")")

        # Run agent
        lines.append("")
        lines.append("# Run agent")
        lines.append(f'result = await agent.run(user_prompt_template)')

        # Extract result
        if output_schema:
            lines.append(f'response_data = result.data.model_dump()')
        else:
            lines.append(f'response_data = result.data')

        # Write to memory
        lines.append(f'self.memory.write("{output_key}", response_data)')

        # Handle tool calls if configured
        tool_calls_key = config.get("tool_calls_key")
        if tool_calls_key:
            lines.append(f'# Tool calls not yet implemented in generated code')
            lines.append(f'self.memory.write("{tool_calls_key}", [])')

        return "\n".join(lines)

    def _json_type_to_python(self, json_type: str) -> str:
        """Convert JSON schema type to Python type hint."""
        type_map = {
            "string": "str",
            "number": "float",
            "integer": "int",
            "boolean": "bool",
            "array": "list",
            "object": "dict",
            "any": "Any",
        }
        return type_map.get(json_type, "Any")
