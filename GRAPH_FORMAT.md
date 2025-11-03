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

The memory schema defines all data locations used by the graph. Memory is organized into four namespaces:

1. **inputs**: Data provided when the graph starts
2. **outputs**: Final results produced by the graph
3. **intermediate**: Temporary data used during execution
4. **secrets**: Sensitive data (API keys, passwords, etc.)

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
  "memory_reads": [],
  "memory_writes": ["api_response"],
  "description": "Fetch data from API"
}
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | **Yes** | Unique identifier for this step |
| `type` | string | **Yes** | Step type (e.g., `start`, `llm`, `http-get`, `transform`) |
| `config` | object | **Yes** | Configuration specific to the step type (can be empty `{}`) |
| `memory_reads` | array[string] | **Yes** | Memory keys this step reads from |
| `memory_writes` | array[string] | **Yes** | Memory keys this step writes to |
| `description` | string | No | Human-readable description of what the step does |

### Step Types

#### Built-in Step Types (graph-core)

| Type | Category | Description |
|------|----------|-------------|
| `start` | control | Entry point for the graph |
| `output` | control | Maps intermediate values to output namespace |
| `conditional` | control | Evaluates condition for branching |
| `loop` | control | Iterates over a collection |
| `join` | control | Synchronizes parallel branches |
| `llm` | ai | Calls an LLM with optional tools and structured output |
| `transform` | data | Executes Python code for data transformation |
| `read-memory` | data | Copies values from any memory section |
| `write-memory` | data | Writes values to any memory section |
| `http` | integration | Basic HTTP request |
| `db_query` | integration | Database query |
| `human_input` | human | Waits for human input/approval |

#### Plugin Step Types

Plugin steps are namespaced with the plugin name (e.g., `http.HTTPGetStep` or `http-get`). See plugin documentation for details:

- **HTTP Plugin**: 17 steps including `http-get`, `http-post`, `url-parse`, `json-parse`, `html-parse`, etc.
- **Custom Plugins**: See [Plugin Development Guide](packages/graphflow-plugin-example/README.md)

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
     "url": "https://api.example.com/users/{{user_id}}",
     "prompt": "Answer this: {{user_question}}"
   }
   ```
   - Use `{{memory_key}}` to reference memory values
   - Supports nested access: `{{user.profile.name}}`

### Example Step Configs

#### Start Step

```json
{
  "id": "start_1",
  "type": "start",
  "config": {},
  "memory_reads": [],
  "memory_writes": [],
  "description": "Entry point"
}
```

#### LLM Step

```json
{
  "id": "llm_1",
  "type": "llm",
  "config": {
    "provider": "openrouter",
    "model": "anthropic/claude-3.5-sonnet",
    "api_key_secret": "openrouter_api_key",
    "system_prompt": "You are a helpful assistant.",
    "user_prompt": "{{user_question}}",
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
  "memory_reads": ["user_question"],
  "memory_writes": ["llm_response"],
  "description": "Generate answer with LLM"
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
      "Authorization": "Bearer {{api_token}}"
    },
    "response_key": "api_data",
    "status_code_key": "api_status"
  },
  "memory_reads": ["api_token"],
  "memory_writes": ["api_data", "api_status"],
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
    "code": "return text.strip().lower()",
    "input_keys": ["text"],
    "output_key": "cleaned_text"
  },
  "memory_reads": ["text"],
  "memory_writes": ["cleaned_text"],
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
  "memory_reads": ["confidence"],
  "memory_writes": ["is_confident"],
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
  "memory_reads": ["items"],
  "memory_writes": ["current_item", "item_index", "processed_items"],
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
  "memory_reads": ["llm_response", "confidence"],
  "memory_writes": ["answer", "score"],
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

String values support `{{variable}}` template syntax for dynamic memory substitution:

```json
{
  "url": "https://api.example.com/users/{{user_id}}/posts/{{post_id}}",
  "prompt": "Summarize this: {{document.content}}",
  "headers": {
    "Authorization": "Bearer {{api_token}}"
  }
}
```

**Features:**
- Supports nested access with dot notation: `{{user.profile.name}}`
- Works in strings, URLs, headers, prompts, etc.
- Replaced at runtime with actual memory values

### Memory Reads and Writes

The `memory_reads` and `memory_writes` arrays must accurately reflect what the step accesses:

**Best Practices:**
1. List all memory keys the step reads in `memory_reads`
2. List all memory keys the step writes in `memory_writes`
3. Include base keys for nested access: for `user.name`, include `user`
4. Ensure all keys are declared in the memory schema

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
      "memory_reads": [],
      "memory_writes": []
    },
    {
      "id": "output",
      "type": "output",
      "config": {
        "mapping": {
          "echo": "message"
        }
      },
      "memory_reads": ["message"],
      "memory_writes": ["echo"]
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
      "memory_reads": [],
      "memory_writes": []
    },
    {
      "id": "fetch_user",
      "type": "http-get",
      "config": {
        "url": "https://api.example.com/users/{{user_id}}",
        "headers": {
          "Authorization": "Bearer {{api_key}}"
        },
        "response_key": "api_response"
      },
      "memory_reads": ["user_id", "api_key"],
      "memory_writes": ["api_response"]
    },
    {
      "id": "process_data",
      "type": "transform",
      "config": {
        "operation": "extract_profile",
        "code": "return {'name': api_response['name'], 'email': api_response['email']}",
        "input_keys": ["api_response"],
        "output_key": "processed_data"
      },
      "memory_reads": ["api_response"],
      "memory_writes": ["processed_data"]
    },
    {
      "id": "output",
      "type": "output",
      "config": {
        "mapping": {
          "user_profile": "processed_data"
        }
      },
      "memory_reads": ["processed_data"],
      "memory_writes": ["user_profile"]
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
      "memory_reads": [],
      "memory_writes": []
    },
    {
      "id": "check_complexity",
      "type": "conditional",
      "config": {
        "condition": "len(question) > 50",
        "result_key": "is_complex"
      },
      "memory_reads": ["question"],
      "memory_writes": ["is_complex"]
    },
    {
      "id": "llm_path",
      "type": "llm",
      "config": {
        "provider": "openai",
        "model": "gpt-4",
        "api_key_secret": "openai_key",
        "user_prompt": "{{question}}",
        "output_key": "llm_answer"
      },
      "memory_reads": ["question"],
      "memory_writes": ["llm_answer"]
    },
    {
      "id": "simple_path",
      "type": "transform",
      "config": {
        "code": "return 'Thanks for your question!'",
        "output_key": "simple_answer"
      },
      "memory_reads": [],
      "memory_writes": ["simple_answer"]
    },
    {
      "id": "merge_llm",
      "type": "output",
      "config": {
        "mapping": {"answer": "llm_answer"}
      },
      "memory_reads": ["llm_answer"],
      "memory_writes": ["answer"]
    },
    {
      "id": "merge_simple",
      "type": "output",
      "config": {
        "mapping": {"answer": "simple_answer"}
      },
      "memory_reads": ["simple_answer"],
      "memory_writes": ["answer"]
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
4. **Undeclared memory keys**: All keys in `memory_reads`/`memory_writes` must be in memory schema
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

- **[HTTP Plugin](packages/graph-plugins-http/README.md)** - HTTP step types and configuration
- **[Plugin Development](packages/graphflow-plugin-example/README.md)** - Creating custom step types
- **[Core Library](packages/graph-core/README.md)** - Built-in step types
- **[Compiler](packages/graph-compiler/README.md)** - Compiling graphs to Python code
- **[Runtime API](http://localhost:8000/docs)** - REST API for running graphs

---

**Version:** 1.0
**Last Updated:** 2025-11-02
