# GraphFlow AI Plugin

AI and human interaction steps for GraphFlow.

## Installation

```bash
pip install -e packages/graph-plugins-ai
```

## Steps Provided

### LLMStep

Call language models with tool support, prompts, and structured outputs.

**Features:**
- Multiple LLM provider support (OpenAI, Anthropic, OpenRouter, Azure, custom)
- Tool calling capabilities
- Structured output schemas (Pydantic models)
- Template-based prompts with memory variable interpolation
- Framework-specific templates for Pydantic AI and LangGraph

**Example:**
```json
{
  "id": "llm_1",
  "type": "llm",
  "config": {
    "provider": "openrouter",
    "model": "anthropic/claude-3.5-sonnet",
    "system_prompt": "You are a helpful assistant.",
    "user_prompt": "Answer this question: {memory.user_question}",
    "temperature": 0.7
  },
  "outputs": {
    "response": "{memory.llm_response}"
  }
}
```

### HumanInputStep

Pause execution and wait for human input (human-in-the-loop workflows).

**Features:**
- Multiple input types (text, choice, approval)
- Template-based prompts
- Optional timeout
- Useful for review and approval workflows

**Example:**
```json
{
  "id": "human_1",
  "type": "human_input",
  "config": {
    "prompt": "Please review: {memory.data}. Approve?",
    "input_type": "approval",
    "output_key": "human_approval"
  }
}
```

## Template System

The LLMStep provides framework-specific code generation templates:

- **Pydantic AI**: Uses Agent API with structured outputs
- **LangGraph**: Uses ChatModel with message-based interface

Templates are located in `graphflow_ai/templates/llm/` and are automatically distributed with the package.

## Development

```bash
# Install in development mode
pip install -e packages/graph-plugins-ai

# Run tests
pytest packages/graph-plugins-ai/tests
```

## License

MIT
