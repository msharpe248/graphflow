# GraphFlow Graph Definition Format

This document provides the complete specification for the GraphFlow graph definition JSON format. This format is used to:

1. **Save graphs** created in the visual graph builder UI
2. **Compile graphs** into executable Python code via `graphflow-compile`
3. **Execute graphs** in the GraphFlow runtime
4. **Share and version** workflow definitions

## Table of Contents

- [Overview](#overview)
- [Top-Level Structure](#top-level-structure)
- [Metadata](#metadata)
- [Memory Schema](#memory-schema)
- [Steps](#steps)
- [Edges](#edges)
- [Configuration Conventions](#configuration-conventions)
- [Complete Examples](#complete-examples)

---

## Overview

A GraphFlow graph is a JSON document that defines:

- **Control flow**: How steps connect via edges
- **Data flow**: How data moves through memory
- **Step configuration**: Parameters for each step
- **Memory schema**: Input/output/intermediate data structures

**Key Principles:**
- **Version 1.0** is currently the only supported version
- **Step IDs must be unique** within a graph
- **Edge IDs must be unique** within a graph
- **Memory keys** must be declared in the memory schema before use
- **Control flow** is defined by edges
- **Data flow** is defined by memory reads/writes

---

## Top-Level Structure

```json
{
  "version": "1.0",
  "metadata": { ... },
  "memory": { ... },
  "steps": [ ... ],
  "edges": [ ... ]
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `version` | string | **Yes** | Graph format version. Must be `"1.0"` |
| `metadata` | object | **Yes** | Graph metadata (name, description, tags, etc.) |
| `memory` | object | **Yes** | Memory schema defining data structures |
| `steps` | array | **Yes** | List of step definitions (nodes in the graph) |
| `edges` | array | **Yes** | List of edge definitions (connections between steps) |

---

## Metadata

Metadata provides descriptive information about the graph.

### Structure

```json
{
  "metadata": {
    "name": "My Agent Name",
    "description": "What this agent does",
    "created": "2025-11-02T00:00:00Z",
    "framework_hints": ["pydantic_ai", "langgraph"],
    "tags": ["example", "production", "api"]
  }
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Human-readable name for the graph |
| `description` | string | No | Detailed description of the graph's purpose |
| `created` | string (ISO 8601) | No | Creation timestamp |
| `framework_hints` | array[string] | No | Suggested compilation targets (`pydantic_ai`, `langgraph`) |
| `tags` | array[string] | No | Tags for categorization and search |

---

## Memory Schema

The memory schema defines all data locations used by the graph. Memory is organized into six namespaces.

> **Related Documentation:**
> - [Memory User Guide](MEMORY_USER_GUIDE.md) - How to use memory in the Builder UI
> - [Memory System Technical Reference](MEMORY_SYSTEM.md) - Implementation details

1. **inputs**: Data provided when the graph starts
2. **outputs**: Final results produced by the graph
3. **intermediate**: Temporary data used during execution
4. **secrets**: Sensitive data (API keys, passwords, etc.)
5. **config**: Configuration values (runtime parameters)
6. **environment**: Environment variable references

### Structure

```json
{
  "memory": {
    "inputs": {
      "user_question": {
        "type": "string",
        "description": "Question from user",
        "required": true
      }
    },
    "outputs": {
      "answer": {
        "type": "string",
        "description": "Generated answer"
      }
    },
    "intermediate": {
      "processed_text": {
        "type": "string",
        "description": "Intermediate processed text"
      }
    },
    "secrets": {
      "api_key": {
        "provider": "env",
        "key": "OPENAI_API_KEY",
        "description": "API key for OpenAI"
      }
    },
    "config": {
      "max_retries": {
        "type": "number",
        "description": "Maximum number of retries for API calls"
      }
    },
    "environment": {
      "api_url": {
        "type": "string",
        "key": "API_BASE_URL",
        "description": "Base URL for API",
        "required": true
      }
    }
  }
}
```

### Field Definition

Each field in `inputs`, `outputs`, or `intermediate` has:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | **Yes** | Data type: `string`, `number`, `boolean`, `object`, `array`, `any` |
| `description` | string | No | Human-readable description |
| `required` | boolean | No | Whether the field is required (default: `true` for inputs, `false` otherwise) |
| `default` | any | No | Default value if not provided |

### Secret Definition

Each field in `secrets` has:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `provider` | string | **Yes** | Where to retrieve secret: `env`, `vault`, `aws_secrets` |
| `key` | string | **Yes** | Key name in the secret provider |
| `description` | string | No | Human-readable description |

### Config Definition

Each field in `config` has:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | **Yes** | Data type: `string`, `number`, `boolean` |
| `description` | string | No | Human-readable description |

### Environment Definition

Each field in `environment` has:

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | **Yes** | Data type: `string`, `number`, `boolean` |
| `key` | string | **Yes** | Environment variable name |
| `description` | string | No | Human-readable description |
| `required` | boolean | No | Whether the environment variable is required (default: `true`) |

### Memory Key Naming

- Use `snake_case` for memory keys
- Keys can be referenced with dot notation for nested access: `object.field.subfield`
- Memory keys must be declared before use in steps
- Input keys are automatically available to all steps
- Output keys should only be written by `output` steps or final steps

---

## Steps

Steps are the nodes in your graph. Each step represents a unit of work.

### Structure

```json
{
  "id": "fetch_data",
  "type": "http-get",
  "config": {
    "url": "https://api.example.com/data",
    "response_key": "api_response"
  },
  "description": "Fetch data from API"
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique identifier for this step |
| `type` | string | **Yes** | Step type (e.g., `start`, `llm`, `http-get`, `transform`) |
| `config` | object | **Yes** | Configuration specific to the step type (can be empty `{}`) |
| `outputs` | object | No | Maps output names to memory locations using `{memory.field}` syntax |
| `description` | string | No | Human-readable description of what the step does |

### Step Types

#### Built-in Step Types (graph-core)

| Type | Category | Description |
|------|----------|-------------|
| `start` | control | Entry point for the graph |
| `output` | control | Maps intermediate values to output namespace |
| `conditional` | control | Evaluates condition for branching |
| `join` | control | Synchronizes parallel branches |
| `sleep` | control | Sleep/delay for a specified duration |
| `loop` | control | Iterates over a collection |
| `transform` | data | Executes Python code for data transformation |
| `read-memory` | data | Copies values from any memory section |
| `write-memory` | data | Writes values to any memory section |

#### Plugin Step Types

Plugin steps are namespaced with the plugin name (e.g., `http.HTTPGetStep`, `ai.LLMStep`). See plugin documentation for details:

- **HTTP Plugin**: HTTP requests (`http.HTTPGetStep`, `http.HTTPPostStep`, etc.)
- **URL Plugin**: URL parsing and manipulation (`url.URLParseStep`, `url.URLBuildStep`, etc.)
- **XML/HTML Plugin**: HTML/XML processing (`xmlhtml.HTMLParseStep`, `xmlhtml.XMLToJSONStep`, etc.)
- **Encoding Plugin**: Base64, Hex, Hashing, Gzip (`encoding.Base64EncodeStep`, `encoding.SHA256HashStep`, etc.)
- **AI Plugin**: LLM and human interaction steps (`ai.LLMStep`, `ai.HumanInputStep`)
- **Custom Plugins**: See [Plugin Development Guide](../packages/graphflow-plugin-example/README.md)

### Config Object

The `config` object is step-type specific. Each step type defines its own configuration schema.

#### Common Config Patterns

1. **Output Key Pattern** (used by many steps):
   ```json
   {
     "response_key": "api_response",
     "status_code_key": "status"
   }
   ```
   - Fields ending in `_key` specify WHERE to write outputs
   - The output schema describes WHAT is written (without `_key` suffix)
   - Example: `response_key` → writes to memory location, `response` in output schema

2. **Input Key Pattern**:
   ```json
   {
     "input_key": "raw_data",
     "output_key": "processed_data"
   }
   ```

3. **Template Syntax** (for string substitution):
   ```json
   {
     "url": "https://api.example.com/users/{memory.user_id}",
     "prompt": "Answer this: {memory.user_question}"
   }
   ```
   - Use `{memory.memory_key}` to reference memory values
   - Supports nested access: `{memory.user.profile.name}`

### Example Step Configs

#### Start Step

```json
{
  "id": "start_1",
  "type": "start",
  "config": {},
  "description": "Entry point"
}
```

#### LLM Step

```json
{
  "id": "llm_1",
  "type": "llm",
  "config": {
    "provider": "ollama",
    "model": "llama3.1",
    "system_prompt": "You are a helpful assistant.",
    "user_prompt": "{memory.user_question}",
    "output_schema": {
      "type": "object",
      "properties": {
        "answer": {"type": "string"},
        "confidence": {"type": "number"}
      },
      "required": ["answer"]
    },
    "output_key": "llm_response",
    "temperature": 0.7,
    "max_tokens": 2000
  },
  "description": "Generate answer with LLM"
}
```

**Supported Providers:**
| Provider | Config | API Key |
|----------|--------|---------|
| `ollama` | `base_url` (default: http://localhost:11434) | None (local) |
| `lmstudio` | `base_url` (default: http://localhost:1234/v1) | None (local) |
| `openrouter` | - | `api_key_secret` → env var |
| `anthropic` | - | `api_key_secret` → env var |
| `openai` | - | `api_key_secret` → env var |

#### LLM Step with Tools

LLM steps can have tools that the model can call during execution:

```json
{
  "id": "llm_1",
  "type": "llm",
  "config": {
    "provider": "ollama",
    "model": "llama3.1",
    "user_prompt": "{memory.user_request}",
    "output_key": "response",
    "tools": [
      {
        "type": "mapped_step",
        "definition": {
          "id": "fetch_tool",
          "name": "fetch_url",
          "description": "Fetch content from a URL",
          "source_step_type": "http.HTTPGetStep",
          "property_mappings": [
            {
              "source_property": "url",
              "visibility": "llm",
              "llm_parameter_name": "url",
              "llm_description": "The URL to fetch",
              "llm_schema": {"type": "string"},
              "required": true
            }
          ],
          "output_key": "response"
        }
      }
    ]
  },
  "description": "LLM with URL fetch tool"
}
```

#### HTTP GET Step

```json
{
  "id": "fetch_api",
  "type": "http-get",
  "config": {
    "url": "https://api.example.com/data",
    "headers": {
      "Authorization": "Bearer {memory.api_token}"
    },
    "response_key": "api_data",
    "status_code_key": "api_status"
  },
  "description": "Fetch data from API"
}
```

#### Transform Step

```json
{
  "id": "process_data",
  "type": "transform",
  "config": {
    "operation": "clean_text",
    "code": "return {memory.text}.strip().lower()"
  },
  "outputs": {
    "result": "{memory.cleaned_text}"
  },
  "description": "Clean and normalize text"
}
```

#### Conditional Step

```json
{
  "id": "check_score",
  "type": "conditional",
  "config": {
    "condition": "confidence > 0.8",
    "result_key": "is_confident"
  },
  "description": "Check if confidence is high"
}
```

#### Loop Step

```json
{
  "id": "process_items",
  "type": "loop",
  "config": {
    "collection_key": "items",
    "item_key": "current_item",
    "index_key": "item_index",
    "max_iterations": 100,
    "results_key": "processed_items"
  },
  "description": "Process each item"
}
```

#### Output Step

```json
{
  "id": "final_output",
  "type": "output",
  "config": {
    "mapping": {
      "answer": "llm_response.answer",
      "score": "confidence"
    }
  },
  "description": "Map to outputs"
}
```

---

## Edges

Edges define the control flow between steps. They determine the execution order.

### Structure

```json
{
  "id": "edge_1",
  "from": "start_1",
  "to": "llm_1",
  "condition": null,
  "description": "Start to LLM"
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique identifier for this edge |
| `from` | string | **Yes** | Source step ID |
| `to` | string | **Yes** | Target step ID |
| `condition` | string | No | Python expression for conditional edges (null for unconditional) |
| `description` | string | No | Human-readable description |

### Conditional Edges

Conditional edges are used with `conditional` steps to create branching logic:

```json
[
  {
    "id": "e1",
    "from": "check_confidence",
    "to": "high_confidence_path",
    "condition": "is_confident == True"
  },
  {
    "id": "e2",
    "from": "check_confidence",
    "to": "low_confidence_path",
    "condition": "is_confident == False"
  }
]
```

### Loop Back Edges

Edges can point back to earlier steps to create loops:

```json
{
  "id": "loop_back",
  "from": "check_done",
  "to": "loop_body",
  "condition": "not is_done"
}
```

### Join Points

Multiple edges can target the same step to create join points:

```json
[
  {
    "id": "e1",
    "from": "branch_a",
    "to": "join_1"
  },
  {
    "id": "e2",
    "from": "branch_b",
    "to": "join_1"
  }
]
```

---

## Configuration Conventions

### The `_key` Suffix Convention

Many steps use a configuration pattern where fields ending in `_key` specify memory locations for outputs:

**In Config (JSON):**
```json
{
  "response_key": "api_data",
  "status_code_key": "http_status"
}
```

**In Output Schema:**
```json
{
  "properties": {
    "response": {
      "description": "HTTP response body"
    },
    "status_code": {
      "type": "integer",
      "description": "HTTP status code"
    }
  }
}
```

**Why this matters:**
- The UI displays outputs with clean names (without `_key`)
- The config specifies WHERE to write (with `_key`)
- The output schema describes WHAT is written (without `_key`)

### Template Syntax

String values support `{memory.variable}` template syntax for dynamic memory substitution:

```json
{
  "url": "https://api.example.com/users/{memory.user_id}/posts/{memory.post_id}",
  "prompt": "Summarize this: {memory.document.content}",
  "headers": {
    "Authorization": "Bearer {memory.api_token}"
  }
}
```

**Features:**
- Supports nested access with dot notation: `{memory.user.profile.name}`
- Works in strings, URLs, headers, prompts, etc.
- Replaced at runtime with actual memory values

### Memory Reads and Writes

Memory access is automatically tracked by parsing `{memory.field}` references in your step configuration and outputs:

**How it works:**
1. Memory reads are extracted from any `{memory.field}` references in the `config` object
2. Memory writes are extracted from any `{memory.field}` references in the `outputs` object
3. The compiler and runtime automatically detect these references - no manual tracking needed
4. Ensure all referenced memory keys are declared in the memory schema

### Step ID Naming

**Recommendations:**
- Use descriptive names: `fetch_user_data` instead of `step_1`
- Use `snake_case` for consistency
- Include type hints: `llm_1`, `http_get_1`, `transform_cleanup`
- Keep IDs unique and meaningful

---

## Complete Examples

### Minimal Example

```json
{
  "version": "1.0",
  "metadata": {
    "name": "Echo Agent",
    "description": "Simply echoes the input"
  },
  "memory": {
    "inputs": {
      "message": {
        "type": "string",
        "required": true
      }
    },
    "outputs": {
      "echo": {
        "type": "string"
      }
    },
    "intermediate": {},
    "secrets": {}
  },
  "steps": [
    {
      "id": "start",
      "type": "start",
      "config": {},
    },
    {
      "id": "output",
      "type": "output",
      "config": {
        "mapping": {
          "echo": "message"
        }
      },
    }
  ],
  "edges": [
    {
      "id": "e1",
      "from": "start",
      "to": "output"
    }
  ]
}
```

### API Workflow Example

```json
{
  "version": "1.0",
  "metadata": {
    "name": "API Data Fetcher",
    "description": "Fetches and processes API data",
    "tags": ["api", "http", "processing"]
  },
  "memory": {
    "inputs": {
      "user_id": {
        "type": "string",
        "description": "User ID to fetch",
        "required": true
      }
    },
    "outputs": {
      "user_profile": {
        "type": "object",
        "description": "Processed user profile"
      }
    },
    "intermediate": {
      "api_response": {
        "type": "object",
        "description": "Raw API response"
      },
      "processed_data": {
        "type": "object",
        "description": "Cleaned data"
      }
    },
    "secrets": {
      "api_key": {
        "provider": "env",
        "key": "API_KEY",
        "description": "API authentication key"
      }
    }
  },
  "steps": [
    {
      "id": "start",
      "type": "start",
      "config": {},
    },
    {
      "id": "fetch_user",
      "type": "http-get",
      "config": {
        "url": "https://api.example.com/users/{memory.user_id}",
        "headers": {
          "Authorization": "Bearer {memory.api_key}"
        },
        "response_key": "api_response"
      },
    },
    {
      "id": "process_data",
      "type": "transform",
      "config": {
        "operation": "extract_profile",
        "code": "return {'name': {memory.api_response}['name'], 'email': {memory.api_response}['email']}"
      },
      "outputs": {
        "result": "{memory.processed_data}"
      },
    },
    {
      "id": "output",
      "type": "output",
      "config": {
        "mapping": {
          "user_profile": "processed_data"
        }
      },
    }
  ],
  "edges": [
    {
      "id": "e1",
      "from": "start",
      "to": "fetch_user"
    },
    {
      "id": "e2",
      "from": "fetch_user",
      "to": "process_data"
    },
    {
      "id": "e3",
      "from": "process_data",
      "to": "output"
    }
  ]
}
```

### LLM with Conditional Logic

```json
{
  "version": "1.0",
  "metadata": {
    "name": "Smart Responder",
    "description": "Routes to LLM or canned response based on complexity"
  },
  "memory": {
    "inputs": {
      "question": {
        "type": "string",
        "required": true
      }
    },
    "outputs": {
      "answer": {
        "type": "string"
      }
    },
    "intermediate": {
      "is_complex": {
        "type": "boolean"
      },
      "llm_answer": {
        "type": "string"
      },
      "simple_answer": {
        "type": "string"
      }
    },
    "secrets": {
      "openai_key": {
        "provider": "env",
        "key": "OPENAI_API_KEY"
      }
    }
  },
  "steps": [
    {
      "id": "start",
      "type": "start",
      "config": {},
    },
    {
      "id": "check_complexity",
      "type": "conditional",
      "config": {
        "condition": "len(question) > 50",
        "result_key": "is_complex"
      },
    },
    {
      "id": "llm_path",
      "type": "llm",
      "config": {
        "provider": "openai",
        "model": "gpt-4",
        "api_key_secret": "openai_key",
        "user_prompt": "{memory.question}",
        "output_key": "llm_answer"
      },
    },
    {
      "id": "simple_path",
      "type": "transform",
      "config": {
        "code": "return 'Thanks for your question!'"
      },
      "outputs": {
        "result": "{memory.simple_answer}"
      },
    },
    {
      "id": "merge_llm",
      "type": "output",
      "config": {
        "mapping": {"answer": "llm_answer"}
      },
    },
    {
      "id": "merge_simple",
      "type": "output",
      "config": {
        "mapping": {"answer": "simple_answer"}
      },
    }
  ],
  "edges": [
    {
      "id": "e1",
      "from": "start",
      "to": "check_complexity"
    },
    {
      "id": "e2",
      "from": "check_complexity",
      "to": "llm_path",
      "condition": "is_complex == True"
    },
    {
      "id": "e3",
      "from": "check_complexity",
      "to": "simple_path",
      "condition": "is_complex == False"
    },
    {
      "id": "e4",
      "from": "llm_path",
      "to": "merge_llm"
    },
    {
      "id": "e5",
      "from": "simple_path",
      "to": "merge_simple"
    }
  ]
}
```

---

## Validation

The GraphFlow compiler validates graphs before compilation:

```bash
graphflow-compile validate my_graph.json
```

**Common Validation Errors:**

1. **Invalid step references in edges**: Ensure all `from` and `to` values match step IDs
2. **Duplicate step IDs**: Each step must have a unique ID
3. **Duplicate edge IDs**: Each edge must have a unique ID
4. **Undeclared memory keys**: All keys in memory references in config and outputs must be in memory schema
5. **Invalid version**: Only `"1.0"` is supported
6. **Invalid field types**: Memory field types must be valid (`string`, `number`, `boolean`, `object`, `array`, `any`)

---

## Best Practices

1. **Use descriptive names** for steps, edges, and memory keys
2. **Document your graph** with descriptions in metadata and steps
3. **Declare all memory upfront** in the memory schema
4. **Use intermediate memory** for temporary data, not outputs
5. **Keep secrets in the secrets namespace** and reference by name
6. **Use template syntax** for dynamic values instead of hardcoding
7. **Validate graphs** before deploying to catch errors early
8. **Version your graphs** using tags or separate files
9. **Test with simple inputs** before complex scenarios
10. **Use the UI** to build graphs visually, then export to JSON

---

## Related Documentation

**Memory System:**
- **[Memory User Guide](MEMORY_USER_GUIDE.md)** - How to use memory bindings and namespaces
- **[Memory System Technical Reference](MEMORY_SYSTEM.md)** - Implementation details

**Plugins:**
- **[HTTP Plugin](../packages/graph-plugins-http/README.md)** - HTTP requests
- **[URL Plugin](../packages/graph-plugins-url/README.md)** - URL parsing and manipulation
- **[XML/HTML Plugin](../packages/graph-plugins-xmlhtml/README.md)** - HTML/XML processing
- **[Encoding Plugin](../packages/graph-plugins-encoding/README.md)** - Base64, Hex, Hashing, Gzip
- **[Plugin Development](PLUGIN_DEVELOPMENT.md)** - Creating custom step types

**Core:**
- **[Core Library](../packages/graph-core/README.md)** - Built-in step types
- **[Compiler](../packages/graph-compiler/README.md)** - Compiling graphs to Python code
- **[Runtime API](http://localhost:8000/docs)** - REST API for running graphs

---

**Version:** 1.0
**Last Updated:** 2025-12-06
