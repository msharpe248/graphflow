# GraphFlow Examples

This directory contains example graph definitions demonstrating various features of GraphFlow.

## Examples

### simple_agent.json
A basic agent that demonstrates:
- Linear flow (start → transform → transform → output)
- Memory reads and writes
- Transform steps with Python code
- Input/output mapping

**Usage:**
```bash
graphflow-compile validate simple_agent.json
```

### conditional_agent.json
A more complex agent demonstrating:
- Conditional branching based on input values
- Multiple execution paths
- Join step for synchronization
- Conditional edges
- Dynamic message selection

**Usage:**
```bash
graphflow-compile validate conditional_agent.json
```

### llm_agent.json
An LLM-powered agent demonstrating:
- LLM step with OpenRouter provider
- Structured output with JSON schema
- System and user prompts with memory templating
- Tool integration (inline function tools)

**Usage:**
```bash
graphflow-compile compile llm_agent.json --framework pydantic_ai --output agent.py
```

### ollama_tool_agent.json
An Ollama-based agent with tool calling:
- Local LLM using Ollama provider (llama3.1)
- MappedStepTool wrapping http.HTTPGetStep as a URL fetcher
- Tool parameter visibility control (LLM vs runtime)
- Tool error handling (errors returned to LLM for adaptive behavior)

**Usage:**
```bash
# Requires Ollama running locally with llama3.1
graphflow-compile compile ollama_tool_agent.json --framework pydantic_ai --output agent.py
python agent.py '{"user_request": "Fetch the Python homepage"}'
```

### advanced_research_agent.json
A complex multi-step research agent demonstrating:
- Loop iterations over search results
- HTTP requests to external APIs
- LLM summarization steps
- Human review gates
- Conditional quality checks

## Validating Examples

To validate all examples:
```bash
graphflow-compile validate *.json
```

To validate a specific example:
```bash
graphflow-compile validate simple_agent.json
```

## Graph Definition Structure

Each graph JSON file contains:
- **version**: Schema version (currently "1.0")
- **metadata**: Name, description, tags, etc.
- **memory**: Schema for inputs, outputs, intermediate, config, environment, and secrets
- **steps**: Array of step definitions (nodes in the graph)
- **edges**: Array of edge definitions (control flow)

## Creating Your Own

To create your own graph definition:

1. Use the visual graph builder at http://localhost:3000 (recommended)
2. Or copy one of the examples and modify
3. Validate using `graphflow-compile validate`
4. Test execution by uploading to runtime or compiling to standalone

## Step Types Available

### Control Flow
- **start**: Entry point (no operation)
- **output**: Map intermediate values to outputs
- **conditional**: Evaluate conditions for branching
- **join**: Synchronization point for multiple branches
- **loop**: Iterate over collections
- **sleep**: Delay execution for specified duration

### Data Manipulation
- **transform**: Execute Python code to transform data
- **read-memory**: Copy values between memory namespaces
- **write-memory**: Write values to memory

### AI
- **ai.LLMStep**: LLM call with multi-provider support (Ollama, LM Studio, OpenRouter, Anthropic, OpenAI)
- **ai.HumanInputStep**: Wait for human review/input

### HTTP (from graph-plugins-http)
- **http.HTTPGetStep**, **http.HTTPPostStep**, etc.: HTTP requests
- **http.URLParseStep**, **http.URLBuildStep**: URL manipulation
- **http.JSONParseStep**, **http.JSONStringifyStep**: JSON handling
- **http.HTMLParseStep**, **http.HTMLStripStep**: HTML processing

See the [main README](../README.md) for complete documentation.
