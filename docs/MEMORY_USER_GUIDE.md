# GraphFlow Memory - User Guide

This guide explains how to use GraphFlow's memory system in the Builder UI. Whether you're building graphs visually or writing custom plugins, this guide covers everything you need to know.

## Table of Contents

- [What is Memory?](#what-is-memory)
- [Memory Namespaces](#memory-namespaces)
- [Using the Memory Schema Panel](#using-the-memory-schema-panel)
- [Memory Bindings](#memory-bindings)
- [Working with Bindings in the Properties Panel](#working-with-bindings-in-the-properties-panel)
- [Auto-Binding Behavior](#auto-binding-behavior)
- [Step Outputs](#step-outputs)
- [Supported Types](#supported-types)
- [Default Values](#default-values)
- [Environment Variables and Secrets](#environment-variables-and-secrets)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## What is Memory?

Memory is how steps in your graph share data with each other. Think of it like variables in a program, but with some special properties:

- **Visible**: You can see all memory values in the UI
- **Editable**: During debugging, you can modify values while paused
- **Organized**: Memory is split into clear namespaces (inputs, outputs, intermediate, etc.)
- **Connected**: Steps read from and write to memory using a simple syntax

### The Basic Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   INPUTS    │───▶│   MEMORY    │───▶│  OUTPUTS    │
│ (user data) │    │  (storage)  │    │  (results)  │
└─────────────┘    └─────────────┘    └─────────────┘
                          │
                    ┌─────┴─────┐
                    │           │
               ┌────▼────┐ ┌────▼────┐
               │  Step A │ │  Step B │
               │  reads  │ │  writes │
               └─────────┘ └─────────┘
```

1. **Inputs** come from whoever runs the graph (API call, chat UI, etc.)
2. **Steps** read from memory, do their work, and write results back
3. **Outputs** are the final results returned when the graph completes

---

## Memory Namespaces

GraphFlow organizes memory into six namespaces, each shown with a distinct color in the UI:

| Namespace | Color | Purpose | When to Use |
|-----------|-------|---------|-------------|
| **Inputs** | Blue | Values provided when the graph starts | User questions, IDs, configuration |
| **Intermediate** | Purple | Temporary values between steps | Step outputs, processing results |
| **Outputs** | Green | Final results returned | Answers, generated content, status |
| **Config** | Amber | System settings (read-only) | Runtime URLs, system parameters |
| **Environment** | Teal | Environment variables | API base URLs, feature flags |
| **Secrets** | Red | Sensitive values (API keys) | API keys, passwords, tokens |

### When to Use Each Namespace

**Use Inputs for:**
- Data your graph needs to start (`user_question`, `document_id`)
- Configuration options (`output_format`, `max_results`)

**Use Intermediate for:**
- Results from one step that another step needs
- Temporary processing states
- Loop variables

**Use Outputs for:**
- The final answer or result
- Status information
- Any data you want to return to the caller

**Use Environment for:**
- URLs that change between environments (dev/staging/prod)
- Feature flags
- Non-sensitive configuration

**Use Secrets for:**
- API keys (OpenAI, Anthropic, etc.)
- Passwords and tokens
- Any sensitive credentials

---

## Using the Memory Schema Panel

The Memory Schema Panel is on the right side of the Builder. It shows all memory fields organized by namespace.

### Adding a Field

1. Find the namespace section (Inputs, Intermediate, Outputs, etc.)
2. Click the **+** button on the section header
3. Enter the field name
4. Set the type (string, number, boolean, object, array, any)
5. Configure additional options based on namespace

### Field Options by Namespace

**Inputs/Intermediate/Outputs:**
- **Type**: Data type for the field
- **Required**: (Inputs only) Whether the field must be provided
- **Default**: Value to use if not provided

**Environment:**
- **Type**: Data type
- **Environment Variable**: The actual env var name (e.g., `API_BASE_URL`)
- **Required**: Whether the env var must be set

**Secrets:**
- **Provider**: Where to get the secret (`env`, `vault`, `aws_secrets`)
- **Key**: Provider-specific key (e.g., env var name `OPENAI_API_KEY`)

### Understanding "Used by" Badges

Each field shows badges indicating which steps use it:
- **"Used by: llm_1, transform_2"** - These steps reference this field
- Helps you see dependencies and avoid breaking changes

### Deleting Fields

1. Hover over the field
2. Click the **X** button
3. Note: You can't delete fields that are still being used by steps

---

## Memory Bindings

Memory bindings are the `{memory.field}` syntax you see in step configuration. They work like **macros** - text that gets replaced with actual values at runtime.

### Basic Syntax

```
{namespace.field_name}
```

### Examples

| Syntax | Reads From | Example Value |
|--------|------------|---------------|
| `{memory.user_question}` | inputs/intermediate/outputs | `"What is AI?"` |
| `{config.runtime_url}` | System config | `"http://localhost:8000"` |
| `{env.api_base}` | Environment variable | `"https://api.example.com"` |
| `{secrets.openai_key}` | Secret provider | `"sk-..."` |

### Where Bindings Work

Bindings can be used in **any text field** in step configuration:

```json
{
  "url": "https://api.example.com/users/{memory.user_id}",
  "prompt": "Answer this question: {memory.user_question}",
  "headers": {
    "Authorization": "Bearer {secrets.api_key}"
  }
}
```

### How Resolution Works

When your graph runs:
1. The system finds all `{...}` patterns
2. Each pattern is replaced with the actual value from memory
3. Missing values become empty strings (no errors)

**Example:**
```
Input:  "Hello, {memory.user_name}! Your ID is {memory.user_id}."
Memory: { user_name: "Alice", user_id: "12345" }
Output: "Hello, Alice! Your ID is 12345."
```

---

## Working with Bindings in the Properties Panel

When you select a step, the Properties Panel shows its configuration. Here's how to work with bindings:

### Recognizing Bound Fields

Fields that use memory bindings show a **"Bound to"** button:
- **Blue button** for input/config bindings
- **Green button** for output bindings
- The button shows which memory field it's bound to

### Changing a Binding

1. Click the **"Bound to {memory.field}"** button
2. The binding dialog opens
3. Search or browse for the field you want
4. Click to select it
5. The binding updates automatically

### Using the Binding Dialog

The binding dialog helps you find and select memory fields:

- **Search**: Type to filter fields by name
- **Sections**: Expandable sections for each namespace
- **Field Info**: Shows type, description, and which steps use each field
- **Create New**: Click **"+ Add"** to create a new field inline

### Editing Default Values

When a property is bound to memory, you can edit the default value:
1. The field shows the current binding
2. Below it, an editor lets you set the default value
3. This default is used if the memory field is empty

---

## Auto-Binding Behavior

The Builder automatically creates memory fields and bindings to save you time.

### When You Add a Step

1. **Memory fields are created** for each configuration property
   - Pattern: `{stepId}.{propertyName}`
   - Example: `llm_1.temperature`, `http_1.url`

2. **Bindings are set automatically**
   - Config properties bind to their auto-created fields
   - Output properties bind to auto-created output fields

### When You Delete a Step

1. **Unused fields are cleaned up**
   - Auto-created fields (with `.` in the name) are removed
   - Manually created fields are preserved

2. **Bindings are removed**
   - References to the deleted step are cleaned up

### Manual vs Auto-Created Fields

| Pattern | Example | Behavior |
|---------|---------|----------|
| Has `.` | `llm_1.temperature` | Auto-created, auto-deleted |
| No `.` | `user_question` | Manual, preserved |

### When to Rename Auto-Created Fields

Rename auto-created fields when:
- You want a cleaner name (`response` instead of `llm_1.response`)
- Multiple steps should share the same field
- You want to preserve the field if the step is deleted

---

## Step Outputs

Step outputs are values that a step produces. They're shown in the **Outputs** section of the Properties Panel.

### How Outputs Work

1. Each step type defines what outputs it produces
2. Outputs are written to memory locations you specify
3. The next step can read these values

### Binding Outputs

Outputs are bound similarly to inputs:
1. Find the output in the Properties Panel (green section)
2. Click **"Bound to {memory.field}"** to change where it writes
3. Choose an intermediate or output field

### Output Types

Each output shows its type:
- `string` - Text data
- `number` - Numeric values
- `object` - JSON objects/dictionaries
- `array` - Lists
- `any` - Variable type

### Multiple Steps Writing to Same Field

If multiple steps write to the same memory field:
- **Last write wins** - the most recently executed step's value is kept
- This is useful for conditional paths that merge

---

## Supported Types

Memory fields support six data types:

| Type | Use For | Example Values | Default Value |
|------|---------|----------------|---------------|
| `string` | Text, URLs, prompts | `"Hello"`, `"https://..."` | `""` (empty) |
| `number` | Counts, scores, IDs | `42`, `0.7`, `-1` | `0` |
| `boolean` | Flags, conditions | `true`, `false` | `false` |
| `object` | JSON data, configs | `{"key": "value"}` | `{}` |
| `array` | Lists, collections | `[1, 2, 3]`, `["a", "b"]` | `[]` |
| `any` | Mixed/unknown types | anything | `null` |

### Choosing the Right Type

- **string**: Most common. Use for text, user input, URLs, prompts
- **number**: Use for counts, scores, temperatures, numeric IDs
- **boolean**: Use for yes/no decisions, feature flags
- **object**: Use for structured data, API responses, configurations
- **array**: Use for lists of items, batch processing
- **any**: Use when the type varies or is unknown

---

## Default Values

Default values are used when a field doesn't have a value set.

### Setting Defaults

In the Memory Schema Panel:
1. Click on a field
2. Find the "Default" input
3. Enter your default value

### When Defaults Apply

| Namespace | When Default is Used |
|-----------|---------------------|
| Inputs | When the input is not provided by the caller |
| Intermediate | At graph initialization (before any step runs) |
| Outputs | At graph initialization |

### Type-Specific Defaults (Zero Values)

If you don't set a default, the system uses a "zero value":

| Type | Zero Value |
|------|-----------|
| string | `""` |
| number | `0` |
| boolean | `false` |
| object | `{}` |
| array | `[]` |
| any | `null` |

---

## Environment Variables and Secrets

### Environment Variables

Use environment variables for configuration that changes between environments:

**Setting up:**
1. Add a field to the **Environment** section
2. Set the **Key** to the actual environment variable name
3. Use `{env.field_name}` in your steps

**Example:**
```
Memory Schema:
  environment:
    api_base:
      type: string
      key: API_BASE_URL
      required: true

Step Config:
  url: "{env.api_base}/users"

Runtime:
  API_BASE_URL=https://api.production.com
  → url becomes "https://api.production.com/users"
```

### Secrets

Use secrets for sensitive values like API keys:

**Setting up:**
1. Add a field to the **Secrets** section
2. Choose a **Provider** (`env` for environment variables)
3. Set the **Key** (e.g., `OPENAI_API_KEY`)
4. Use `{secrets.field_name}` in your steps

**Example:**
```
Memory Schema:
  secrets:
    openai_key:
      provider: env
      key: OPENAI_API_KEY

Step Config (LLM):
  api_key_secret: openai_key

Runtime:
  OPENAI_API_KEY=sk-abc123...
  → API key is securely loaded
```

### Security Notes

- Secrets are **never logged** or displayed in the UI
- During debugging, secret values are hidden
- Always use secrets for API keys, never hardcode them

---

## Common Patterns

### Pattern 1: Passing LLM Output to Next Step

```
1. LLM Step writes to: {memory.llm_response}
2. Transform Step reads from: {memory.llm_response}
```

### Pattern 2: Conditional Branching

```
1. Input: {memory.user_type}
2. Conditional checks: {memory.user_type} == "admin"
3. Different paths for admin vs regular users
```

### Pattern 3: Accumulating Results in a Loop

```
1. Loop iterates over: {memory.items}
2. Each iteration writes to: {memory.current_result}
3. Results accumulated in: {memory.all_results}
```

### Pattern 4: API Call with Dynamic URL

```
url: "https://api.example.com/users/{memory.user_id}/posts/{memory.post_id}"
headers:
  Authorization: "Bearer {secrets.api_key}"
```

### Pattern 5: Chaining Multiple LLM Calls

```
LLM 1: Summarize document → {memory.summary}
LLM 2: Generate questions from {memory.summary} → {memory.questions}
LLM 3: Answer {memory.questions} → {memory.answers}
```

---

## Troubleshooting

### "Memory key not found" Error

**Cause:** A step references a memory field that doesn't exist in the schema.

**Fix:**
1. Check the field name for typos
2. Add the field to the Memory Schema Panel
3. Ensure the correct namespace (inputs vs intermediate)

### Bindings Not Resolving

**Symptoms:** `{memory.field}` appears in output instead of the value.

**Causes & Fixes:**
- **Field not initialized**: Set a default value or ensure a previous step writes to it
- **Wrong namespace**: Use `{memory.field}` not just `{field}`
- **Timing**: Ensure the step that writes runs before the step that reads

### Type Mismatches

**Symptoms:** Unexpected behavior when using values.

**Fixes:**
- Check the field type matches expected usage
- Use Transform steps to convert types
- Check if API responses are objects when you expect strings

### Debug Mode Memory Inspection

Use debug mode to inspect memory values:

1. Enable **Debug Mode** when starting a run
2. Set breakpoints on steps
3. When paused, view all memory values in the panel
4. Edit values to test different scenarios
5. Resume to continue with modified values

### Values Not Updating

**Symptoms:** Memory shows old values after steps run.

**Fixes:**
- Check the step's output binding is correct
- Verify the step actually executed (check execution log)
- Look for errors in the step execution

---

## Related Documentation

- **[Memory System Technical Reference](MEMORY_SYSTEM.md)** - Implementation details
- **[Graph Format Specification](GRAPH_FORMAT.md)** - Memory schema in JSON
- **[Plugin Development Guide](PLUGIN_DEVELOPMENT.md)** - Memory operations for plugins

---

**Version:** 1.0
**Last Updated:** 2025-12-08
