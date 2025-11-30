"""LangGraph/LangChain code generator."""

import re
from typing import List
from graphflow_core.models import GraphDefinition, Step
from graphflow_compiler.base import CodeGenerator


class LangGraphGenerator(CodeGenerator):
    """
    Generate Python code using LangGraph framework.

    Generated code uses:
    - langgraph.StateGraph for graph structure
    - langchain for LLM integration
    - State-based execution model
    """

    def get_framework_name(self) -> str:
        return "langgraph"

    def _get_framework_imports(self, graph: GraphDefinition) -> List[str]:
        """Get LangGraph specific imports."""
        imports = [
            "from typing import TypedDict, Annotated",
            "from langgraph.graph import StateGraph, END",
            "from langgraph.graph.message import add_messages",
        ]

        # Check if we need LangChain (for LLM steps)
        has_llm = any(step.type == "llm" for step in graph.steps)
        if has_llm:
            imports.append("from langchain_core.messages import HumanMessage, SystemMessage")

            # Check which providers are used and add appropriate imports
            providers_used = {
                step.config.get("provider", "ollama")
                for step in graph.steps
                if step.type == "llm"
            }

            # OpenAI-compatible providers (openai, openrouter, azure, openai_compatible, lmstudio)
            openai_compatible_providers = {"openai", "openrouter", "azure", "openai_compatible", "lmstudio"}
            if providers_used & openai_compatible_providers:
                imports.append("from langchain_openai import ChatOpenAI")

            if "anthropic" in providers_used:
                imports.append("from langchain_anthropic import ChatAnthropic")

            if "ollama" in providers_used:
                imports.append("from langchain_ollama import ChatOllama")

            if "groq" in providers_used:
                imports.append("from langchain_groq import ChatGroq")

            if "mistral" in providers_used:
                imports.append("from langchain_mistralai import ChatMistralAI")

            if "google" in providers_used:
                imports.append("from langchain_google_genai import ChatGoogleGenerativeAI")

        # Check if we need HTTP client
        has_http = any(step.type == "http" for step in graph.steps)
        if has_http:
            imports.append("import httpx")

        return imports

    def generate_agent_class(self, graph: GraphDefinition) -> str:
        """Generate the main agent class using LangGraph."""
        template = self.jinja_env.get_template("langgraph_agent.py.jinja")

        # Prepare step execution code
        step_execution_map = {}
        for step in graph.steps:
            step_execution_map[step.id] = self.get_step_execution_code(step, graph)

        # Build state schema
        state_fields = self._build_state_fields(graph)

        # Build graph structure
        graph_edges = self._build_graph_edges(graph)

        return template.render(
            graph=graph,
            step_execution_map=step_execution_map,
            state_fields=state_fields,
            graph_edges=graph_edges,
            steps=graph.steps,
        )

    def _build_state_fields(self, graph: GraphDefinition) -> List[dict]:
        """Build state schema fields for LangGraph."""
        fields = []

        # Add all memory fields to state
        for key, field in graph.memory.inputs.items():
            fields.append({
                "name": key,
                "type": self._json_type_to_python(field.type),
                "section": "input"
            })

        for key, field in graph.memory.intermediate.items():
            fields.append({
                "name": key,
                "type": self._json_type_to_python(field.type),
                "section": "intermediate"
            })

        for key, field in graph.memory.outputs.items():
            fields.append({
                "name": key,
                "type": self._json_type_to_python(field.type),
                "section": "output"
            })

        return fields

    def _build_graph_edges(self, graph: GraphDefinition) -> List[dict]:
        """Build graph edges for LangGraph."""
        edges = []
        for edge in graph.edges:
            edges.append({
                "source": edge.source,
                "target": edge.target,
                "condition": edge.condition
            })
        return edges

    def _generate_llm_step_code(self, step: Step, graph: GraphDefinition) -> str:
        """Generate LangGraph specific LLM step code."""
        config = step.config
        provider = config.get("provider", "ollama")
        model = config.get("model")
        system_prompt = config.get("system_prompt", "")
        user_prompt = config.get("user_prompt", "")
        temperature = config.get("temperature", 0.7)
        base_url = config.get("base_url")

        # Extract output key from outputs dict
        output_key = None
        pattern = re.compile(r'\{memory\.([^}]+)\}')
        for key in ["response", "result"]:
            if key in step.outputs:
                match = pattern.search(step.outputs[key])
                if match:
                    output_key = match.group(1)
                    break

        lines = [
            "# LLM step using LangChain",
            "",
        ]

        # Render prompts with state values
        lines.append("# Render prompts from state")
        memory_refs = set()
        for prompt in [system_prompt, user_prompt]:
            if prompt:
                memory_refs.update(pattern.findall(prompt))

        for key in sorted(memory_refs):
            var_name = key.replace('.', '_')
            lines.append(f'{var_name} = state.get("{key}", "")')

        lines.append("")

        # Build prompt
        if user_prompt:
            lines.append(f'user_prompt_template = {repr(user_prompt)}')
            for key in sorted(memory_refs):
                var_name = key.replace('.', '_')
                lines.append(f'user_prompt_template = user_prompt_template.replace("{{memory.{key}}}", str({var_name}))')
        else:
            lines.append('user_prompt_template = ""')

        lines.append("")

        # Get API key from environment or state
        api_key_secret = config.get("api_key_secret")
        if api_key_secret:
            lines.append('# API key from environment')
            lines.append('import os')
            lines.append(f'api_key = os.getenv("{api_key_secret.upper()}", "")')
        else:
            lines.append('api_key = None')

        lines.append("")

        # Create LLM based on provider
        lines.append("# Create LangChain LLM")
        if provider == "openai":
            if base_url:
                lines.append(f'llm = ChatOpenAI(model="{model}", temperature={temperature}, base_url="{base_url}", api_key=api_key)')
            else:
                lines.append(f'llm = ChatOpenAI(model="{model}", temperature={temperature})')
        elif provider == "anthropic":
            lines.append(f'llm = ChatAnthropic(model="{model}", temperature={temperature})')
        elif provider == "ollama":
            ollama_url = base_url or "http://localhost:11434"
            lines.append(f'llm = ChatOllama(model="{model}", temperature={temperature}, base_url="{ollama_url}")')
        elif provider == "groq":
            lines.append(f'llm = ChatGroq(model="{model}", temperature={temperature})')
        elif provider == "mistral":
            lines.append(f'llm = ChatMistralAI(model="{model}", temperature={temperature})')
        elif provider == "google":
            lines.append(f'llm = ChatGoogleGenerativeAI(model="{model}", temperature={temperature})')
        elif provider == "lmstudio":
            lmstudio_url = base_url or "http://localhost:1234/v1"
            lines.append(f'llm = ChatOpenAI(model="{model}", temperature={temperature}, base_url="{lmstudio_url}", api_key="lm-studio")')
        elif provider == "openrouter":
            lines.append(f'llm = ChatOpenAI(model="{model}", temperature={temperature}, base_url="https://openrouter.ai/api/v1", api_key=api_key)')
        elif provider in ["azure", "openai_compatible"]:
            lines.append(f'llm = ChatOpenAI(model="{model}", temperature={temperature}, base_url="{base_url}", api_key=api_key)')
        else:
            # Default: treat as OpenAI
            lines.append(f'llm = ChatOpenAI(model="{model}", temperature={temperature})')

        lines.append("")

        # Build messages
        lines.append("# Build messages")
        lines.append("messages = []")
        if system_prompt:
            lines.append(f'messages.append(SystemMessage(content={repr(system_prompt)}))')
        lines.append("messages.append(HumanMessage(content=user_prompt_template))")

        lines.append("")

        # Invoke LLM
        lines.append("# Invoke LLM")
        lines.append("response = await llm.ainvoke(messages)")

        # Handle structured output if configured
        output_schema = config.get("output_schema")
        if output_schema:
            lines.append("")
            lines.append("# Parse structured output (placeholder)")
            lines.append("# In production, use with_structured_output()")
            lines.append('response_data = {"answer": response.content, "confidence": 0.85}')
            lines.append(f'state["{output_key}"] = response_data')
        else:
            lines.append(f'state["{output_key}"] = response.content')

        # Handle tool calls
        tool_calls_key = config.get("tool_calls_key")
        if tool_calls_key:
            lines.append("")
            lines.append("# Extract tool calls if any")
            lines.append("if hasattr(response, 'tool_calls'):")
            lines.append(f'    state["{tool_calls_key}"] = response.tool_calls')
            lines.append("else:")
            lines.append(f'    state["{tool_calls_key}"] = []')

        lines.append("")
        lines.append("return state")

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

    def get_step_execution_code(self, step: Step, graph: GraphDefinition) -> str:
        """
        Generate execution code for a specific step (LangGraph state-based).

        Overrides base method to use state dict instead of memory store.
        For LLM steps with tools (especially MCP tools), uses templates.
        """
        if step.type == "start":
            return "# Start step - no operation\nreturn state"

        elif step.type == "output":
            return self._generate_output_step_code_langgraph(step)

        elif step.type == "transform":
            return self._generate_transform_step_code_langgraph(step)

        elif step.type == "conditional":
            return self._generate_conditional_step_code_langgraph(step)

        elif step.type == "llm":
            # Check if the LLM step has tools - if so, use template system
            tools_config = step.config.get("tools", [])
            has_tools = len(tools_config) > 0
            if has_tools:
                # Use template system for steps with tools (supports MCP tools)
                from graphflow_core.steps.registry import StepRegistry
                try:
                    step_class = StepRegistry.get(step.type)
                    template_str = step_class.get_code_template(self.get_framework_name())
                    if template_str:
                        return self._render_step_template(template_str, step, graph)
                except (KeyError, ValueError):
                    pass
            # Fall back to built-in generation for simple LLM steps
            return self._generate_llm_step_code(step, graph)

        elif step.type == "http":
            return self._generate_http_step_code_langgraph(step)

        elif step.type == "join":
            return "# Join step - synchronization handled by graph\nreturn state"

        else:
            # Generic step execution
            return f"# Generic step: {step.type}\nreturn state"

    def _generate_output_step_code_langgraph(self, step: Step) -> str:
        """Generate code for output step (LangGraph version)."""
        mapping = step.config.get("mapping", {})
        lines = ["# Output step - map to outputs"]
        for output_key, source_key in mapping.items():
            lines.append(f'state["{output_key}"] = state.get("{source_key}", "")')
        lines.append("return state")
        return "\n".join(lines)

    def _generate_transform_step_code_langgraph(self, step: Step) -> str:
        """Generate code for transform step (LangGraph version)."""
        code = step.config.get("code", "")

        # Extract output key from outputs dict
        output_key = None
        # Check both "result" and "response" keys
        for key in ["result", "response"]:
            if key in step.outputs:
                pattern = re.compile(r'\{memory\.([^}]+)\}')
                match = pattern.search(step.outputs[key])
                if match:
                    output_key = match.group(1)
                    break

        # Extract memory references from code using {memory.*} syntax
        pattern = re.compile(r'\{memory\.([^}]+)\}')
        memory_refs = set(pattern.findall(code))

        # Build context - extract variables from state
        context_lines = ["# Transform step"]
        adjusted_code = code

        for memory_key in sorted(memory_refs):
            # Prefix with _mem_ to avoid shadowing Python built-ins
            var_name = '_mem_' + memory_key.replace('.', '_')
            context_lines.append(f'{var_name} = state.get("{memory_key}", "")')
            # Replace {memory.variable} with var_name in code
            adjusted_code = adjusted_code.replace(f'{{memory.{memory_key}}}', var_name)

        # Execute transform
        context_lines.append("def _transform():")
        for line in adjusted_code.split('\n'):
            context_lines.append(f"    {line}")

        context_lines.append(f'_result = _transform()')
        context_lines.append(f'state["{output_key}"] = _result')
        context_lines.append("return state")

        return "\n".join(context_lines)

    def _generate_conditional_step_code_langgraph(self, step: Step) -> str:
        """Generate code for conditional step (LangGraph version)."""
        condition = step.config.get("condition")
        result_key = step.config.get("result_key")

        lines = ["# Conditional step"]

        # Extract memory references from condition
        pattern = re.compile(r'\{memory\.([^}]+)\}')
        memory_refs = set(pattern.findall(condition or ""))

        for key in sorted(memory_refs):
            var_name = key.replace('.', '_')
            lines.append(f'{var_name} = state.get("{key}", "")')

        # Adjust condition to use local variables
        adjusted_condition = condition
        for key in sorted(memory_refs):
            var_name = key.replace('.', '_')
            adjusted_condition = adjusted_condition.replace(f'{{memory.{key}}}', var_name)

        lines.append(f'_condition_result = {adjusted_condition}')
        lines.append(f'state["{result_key}"] = bool(_condition_result)')
        lines.append("return state")

        return "\n".join(lines)

    def _generate_http_step_code_langgraph(self, step: Step) -> str:
        """Generate code for HTTP step (LangGraph version)."""
        return """# HTTP step
import httpx
async with httpx.AsyncClient() as client:
    response = await client.request(
        method="{method}",
        url=state.get("url", "{url}"),
        headers={headers},
        json={body}
    )
    state["{response_key}"] = response.json()
return state
""".format(
            method=step.config.get("method", "GET"),
            url=step.config.get("url", ""),
            headers=repr(step.config.get("headers", {})),
            body=repr(step.config.get("body", {})),
            response_key=step.config.get("response_key")
        )
