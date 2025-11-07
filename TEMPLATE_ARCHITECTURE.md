# GraphFlow Template Architecture

## Overview

GraphFlow now uses a **step-level template system** for code generation. This architecture allows step authors to provide framework-specific code generation templates that are distributed with their step implementations.

## Key Design Principles

1. **Templates Live with Steps**: Code generation templates are co-located with step implementations, not in the compiler
2. **Smart Defaults**: Most steps are framework-agnostic and use generic execution (no custom templates needed)
3. **Framework-Specific When Needed**: Only steps that require special handling (like LLM steps) provide framework-specific templates
4. **Plugin-Friendly**: Plugin authors can distribute templates with their step packages

## Architecture Components

### 1. StepBase Methods

All steps inherit two new methods from `StepBase`:

```python
@classmethod
def get_code_template(cls, framework: str) -> Optional[str]:
    """
    Return Jinja2 template string for code generation.

    Returns:
        Template string for the framework, or None to use default
    """
    return None  # Default: use generic execution

@classmethod
def get_supported_frameworks(cls) -> List[str]:
    """
    Return list of frameworks this step supports.

    Returns:
        List of framework identifiers (e.g., ["pydantic_ai", "langgraph"])
    """
    return ["pydantic_ai", "langgraph"]  # Default: all frameworks
```

### 2. CodeGenerator Flow

The compiler now uses this flow for each step:

```python
def get_step_execution_code(self, step: Step, graph: GraphDefinition) -> str:
    # 1. Get step class from registry
    step_class = StepRegistry.get(step.type)

    # 2. Ask step for framework-specific template
    template_str = step_class.get_code_template(self.get_framework_name())

    # 3. If template provided, render it
    if template_str:
        return self._render_step_template(template_str, step, graph)

    # 4. Otherwise, use generic default
    else:
        return self._generate_generic_step_code(step)
```

### 3. Generic Default Template

For steps that don't provide custom templates, the compiler generates:

```python
# Execute {step_type} step
step_class = StepRegistry.get("{step_type}")
step = step_class(
    id="{step_id}",
    config={...},
    outputs={...}
)
await step.execute(self.memory)
```

This works for **all framework-agnostic steps** including:
- StartStep
- OutputStep
- TransformStep
- ConditionalStep
- JoinStep
- ReadMemoryStep
- WriteMemoryStep
- All HTTP plugin steps
- Any custom plugin steps

### 4. Template Context

Templates receive a rich context with helpful variables:

```python
context = {
    "step": step,                    # Step definition
    "graph": graph,                  # Full graph
    "config": step.config,           # Step config
    "outputs": step.outputs,         # Output mappings
    "memory_refs": {...},            # Extracted memory references
    "framework": "pydantic_ai",      # Target framework
    "json_type_to_python": func,     # Helper function
    # ... plus specific config values for convenience
}
```

## Example: LLM Step

The LLM step is the primary example of framework-specific templates:

### Template Location

```
packages/graph-core/
├── graphflow_core/
│   └── steps/
│       ├── llm.py                  # LLMStep class
│       └── templates/
│           └── llm/
│               ├── pydantic_ai.jinja    # Pydantic AI template
│               └── langgraph.jinja      # LangGraph template
```

### LLMStep Implementation

```python
@classmethod
def get_code_template(cls, framework: str) -> Optional[str]:
    """Load framework-specific template from package."""
    template_dir = Path(__file__).parent / "templates" / "llm"
    template_file = template_dir / f"{framework}.jinja"

    if template_file.exists():
        return template_file.read_text()

    return None
```

### Template Example (Pydantic AI)

```jinja
# LLM step using Pydantic AI

# Create Pydantic AI agent
agent = Agent(
    "{{ model }}",
{%- if system_prompt %}
    system_prompt={{ system_prompt | repr }},
{%- endif %}
    result_type=str,
)

# Run agent
result = await agent.run(user_prompt_template)

# Write response
self.memory.write("{{ output_key }}", result.data)
```

## Benefits

### For Step Authors

✅ **Full Control**: Complete control over code generation for your step
✅ **Framework Optimization**: Optimize for each framework's strengths
✅ **Distribution**: Templates distributed with step package via pip
✅ **Testing**: Test templates with actual generated code

### For Plugin Developers

✅ **Simple by Default**: Most plugins don't need templates at all
✅ **Custom When Needed**: Add templates only for complex steps
✅ **Self-Contained**: Everything in one package
✅ **Documented**: Clear examples in LLMStep

### For Compiler Maintainers

✅ **Separation of Concerns**: Compiler doesn't know about step internals
✅ **Extensibility**: New frameworks just need new templates
✅ **Maintainability**: Less hardcoded logic in compiler
✅ **Backwards Compatible**: Existing steps work without changes

## Package Distribution

### pyproject.toml Configuration

To distribute templates with your package:

```toml
[tool.setuptools.package-data]
your_package = ["steps/templates/**/*.jinja"]
```

### Directory Structure for Plugins

```
my-plugin/
├── my_plugin/
│   ├── __init__.py
│   ├── steps.py
│   └── templates/          # Optional
│       └── custom-step/
│           ├── pydantic_ai.jinja
│           └── langgraph.jinja
├── pyproject.toml
└── manifest.json
```

## Migration Status

### ✅ Completed

- StepBase infrastructure (get_code_template, get_supported_frameworks)
- CodeGenerator refactored to use templates
- LLMStep templates for both frameworks
- Package configuration for template distribution
- All tests passing (25/25)

### 🎯 Framework Support

| Step Type | Pydantic AI | LangGraph | Uses Custom Template |
|-----------|-------------|-----------|---------------------|
| start | ✅ | ✅ | No (generic) |
| output | ✅ | ✅ | No (generic) |
| transform | ✅ | ✅ | No (generic) |
| conditional | ✅ | ✅ | No (generic) |
| join | ✅ | ✅ | No (generic) |
| read-memory | ✅ | ✅ | No (generic) |
| write-memory | ✅ | ✅ | No (generic) |
| **llm** | ✅ | ✅ | **Yes (framework-specific)** |
| http-* (plugin) | ✅ | ✅ | No (generic) |

### 🔮 Future Enhancements

- Template inheritance/composition
- Template validation at registration time
- Template testing utilities
- More template helpers/filters
- Template documentation generator

## Creating Custom Templates

### When to Use Custom Templates

Create custom templates when your step:

1. **Uses framework-specific APIs** (like LLM libraries)
2. **Requires special initialization** that differs per framework
3. **Benefits from framework optimizations**
4. **Has complex code generation logic**

### When to Use Generic Execution

Use the default generic execution when your step:

1. **Only uses memory operations** (read/write)
2. **Works the same** across all frameworks
3. **Uses standard Python libraries** (httpx, json, etc.)
4. **Follows simple patterns**

### Template Best Practices

1. **Keep it Simple**: Templates should be readable
2. **Use Context Variables**: Leverage provided context helpers
3. **Handle Edge Cases**: Check for None values, empty lists, etc.
4. **Test Generated Code**: Verify syntax and execution
5. **Document Variables**: Comment what context vars you use

## Testing Templates

To test your templates:

```python
# test_my_step_templates.py
def test_my_step_template_pydantic_ai():
    step_class = MyStep
    template = step_class.get_code_template("pydantic_ai")

    assert template is not None
    assert "await" in template  # Check for async
    # ... verify template content
```

## Summary

The template architecture provides:

- **Flexibility**: Steps control their code generation
- **Simplicity**: Default works for most cases
- **Maintainability**: Clear separation of concerns
- **Extensibility**: Easy to add new frameworks or steps

This design enables GraphFlow to support diverse step types and frameworks while keeping the compiler clean and maintainable.
