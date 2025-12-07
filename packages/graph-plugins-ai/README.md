# GraphFlow AI Plugin

AI and human interaction steps for GraphFlow.

## Installation

```bash
pip install -e packages/graph-plugins-ai
```

## Steps Provided

### LLMStep

Call language models with tool support, prompts, structured outputs, and conversation history.

**Features:**
- Multiple LLM provider support (OpenAI, Anthropic, OpenRouter, Ollama, LM Studio)
- Tool calling capabilities with MappedStepTools
- Structured output schemas (Pydantic models)
- Template-based prompts with memory variable interpolation
- **Chat History / Sessions**: Maintain conversation context across multiple LLM calls
- Framework-specific templates for Pydantic AI and LangGraph

**Basic Example:**
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

## Chat History / Sessions

LLM steps can maintain conversation history across multiple calls, enabling multi-turn conversations and context-aware responses.

**Configuration:**
- `history_memory_key` - Memory key to store/retrieve chat history (e.g., `"chat_history"`)

When `history_memory_key` is set:
1. Previous messages are loaded from memory before the LLM call
2. The new user message and assistant response are appended to history
3. Updated history is saved back to memory after each call

**Example - Multi-turn Chat:**
```json
{
  "id": "chat_llm",
  "type": "llm",
  "config": {
    "provider": "ollama",
    "model": "llama3.2",
    "system_prompt": "You are a helpful assistant.",
    "user_prompt": "{memory.user_message}",
    "history_memory_key": "chat_history"
  },
  "outputs": {
    "response": "{memory.assistant_response}"
  }
}
```

**How it works:**
1. First call: Empty history, LLM sees only the system prompt and user message
2. Second call: History contains previous exchange, LLM has full context
3. Each subsequent call builds on the conversation

**Use Cases:**
- Chatbots with memory of previous exchanges
- Multi-step reasoning where context matters
- Agents that need to remember previous tool calls
- Conversational workflows with human-in-the-loop

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
