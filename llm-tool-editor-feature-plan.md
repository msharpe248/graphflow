# LLM Tool Editor Feature - Implementation Plan

## ✅ LLM Provider Enhancement (Completed)

Before implementing the tool editor, the LLM provider system was enhanced to support multiple providers.

### Supported Providers

| Provider | Type | base_url | api_key | Notes |
|----------|------|----------|---------|-------|
| `openai` | Native | Optional | Required | Defaults to api.openai.com. Custom base_url for Azure/custom. |
| `anthropic` | Native | - | Required | Uses `anthropic:model` in Pydantic AI |
| `ollama` | OpenAI-compat | Optional | - | Defaults to localhost:11434. Local LLM. Uses OpenAI Provider API. |
| `lmstudio` | OpenAI-compat | Optional | - | Defaults to localhost:1234/v1. Local LLM. |
| `groq` | Native | - | Required | Uses `groq:model` in Pydantic AI |
| `mistral` | Native | - | Required | Uses `mistral:model` in Pydantic AI |
| `google` | Native | - | Required | Uses `google-gla:model` in Pydantic AI |
| `openrouter` | OpenAI-compat | Fixed | Required | Fixed to openrouter.ai/api/v1 |
| `azure` | OpenAI-compat | Required | Required | Azure OpenAI deployments |
| `openai_compatible` | OpenAI-compat | Required | Required | Any OpenAI-compatible endpoint |

### Implementation Notes (Pydantic AI v1.22.0)

The Pydantic AI library v1.22.0 introduced breaking changes:
- `OpenAIModel` renamed to `OpenAIChatModel`
- `base_url` must be passed via `OpenAIProvider`, not directly to the model
- `result.data` changed to `result.output`
- Native `ollama:model` provider is broken - must use OpenAI-compatible endpoint instead

For ollama, the implementation uses:
```python
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
_provider = OpenAIProvider(base_url="http://localhost:11434/v1", api_key="ollama")
model_ref = OpenAIChatModel("llama3.1", provider=_provider)
```

### Files Modified

- `packages/graph-plugins-ai/graphflow_ai/steps.py` - Provider enum, validation, and @StepRegistry.register decorator
- `packages/graph-plugins-ai/graphflow_ai/templates/llm/pydantic_ai.jinja` - Updated for Pydantic AI v1.22.0 API
- `packages/graph-plugins-ai/graphflow_ai/templates/llm/langgraph.jinja` - LangGraph template with all providers
- `packages/graph-compiler/graphflow_compiler/generators/langgraph.py` - Fixed `_generate_llm_step_code` for all providers
- `packages/graph-compiler/graphflow_compiler/base.py` - Added `base_url` to template context
- `packages/graph-compiler/graphflow_compiler/cli.py` - Added plugin loading on startup
- `packages/graph-builder/src/utils/stepTypes.ts` - Frontend provider list

### Tested

- ✅ Pydantic AI with ollama (llama3.1)
- ✅ LangGraph with ollama (llama3.1)

---

## Overview

Create a specialized editor for LLM steps that allows defining tools by mapping existing steps to tool definitions. Users can select which properties the LLM should control and which properties should be provided by the runtime environment (from memory or constants). This enables secure, controlled tool calling where sensitive information (credentials, URLs, etc.) remains hidden from the LLM.

Tool definitions are stored in the graph JSON and compiled into framework-specific tool implementations (Pydantic AI, LangGraph/LangChain) at runtime.

## Core Concepts

### Tool Mapping
A tool is created from an existing step with:
- **LLM-visible properties**: Properties the LLM can see and control (e.g., query parameters, search terms)
- **Runtime properties**: Properties hidden from LLM, provided from memory or constants (e.g., API keys, base URLs)
- **Tool metadata**: Name, description visible to LLM

### Example Use Case
HTTP Get step → Search Tool:
- LLM sees: `query` parameter (string input)
- Runtime provides: `url` (from config), `headers` (authentication from secrets)
- Tool name: "search_web"
- Tool description: "Search the web for information"

### Step Eligibility
Not all steps should be available as tools:
- ✅ **Tool-eligible**: HTTP requests, database queries, custom code, file operations, data transformations
- ❌ **Not tools**: Control flow (if/else, loops), variable assignment, memory operations, other LLM steps

## Architecture Components

## 1. **Step Registration: Tool Eligibility Flag**

**1.1 Update StepBase** (`packages/graph-core/graphflow_core/steps/base.py`)
Add class attribute to indicate if step can be used as a tool:

```python
class StepBase(ABC):
    """Base class for all steps"""

    # Existing attributes...

    # NEW: Indicates if this step can be wrapped as an LLM tool
    can_be_tool: bool = False

    # NEW: Human-readable reason if not eligible
    tool_ineligible_reason: Optional[str] = None
```

**1.2 Update Step Definitions**
Mark steps appropriately:

```python
# Tool-eligible steps
class HttpGetStep(StepBase):
    can_be_tool = True

class HttpPostStep(StepBase):
    can_be_tool = True

class CustomCodeStep(StepBase):
    can_be_tool = True

class DatabaseQueryStep(StepBase):
    can_be_tool = True

# NOT tool-eligible
class IfElseStep(StepBase):
    can_be_tool = False
    tool_ineligible_reason = "Control flow steps cannot be used as tools"

class SetVariableStep(StepBase):
    can_be_tool = False
    tool_ineligible_reason = "Variable assignment is not a tool operation"

class LLMStep(StepBase):
    can_be_tool = False
    tool_ineligible_reason = "LLM steps cannot call other LLM steps as tools"
```

**1.3 API Exposure** (`packages/graph-runtime/graphflow_runtime/api/routes.py`)
Include `can_be_tool` in step metadata:

```python
GET /api/v1/steps
{
  "steps": [
    {
      "type": "http_get",
      "label": "HTTP Get",
      "can_be_tool": true,
      "configSchema": {...}
    },
    {
      "type": "if_else",
      "label": "If/Else",
      "can_be_tool": false,
      "tool_ineligible_reason": "Control flow steps cannot be used as tools",
      "configSchema": {...}
    }
  ]
}
```

## 2. **Backend: Tool Definition Model**

**2.1 New Tool Schema** (NEW: `packages/graph-core/graphflow_core/models/tool.py`)
```python
from typing import Literal, Optional, List
from pydantic import BaseModel

class ToolPropertyMapping(BaseModel):
    source_property: str  # Property key from source step
    visibility: Literal['llm', 'runtime']  # Who controls this?
    runtime_value: Optional[str] = None  # If runtime: memory binding or constant
    llm_schema: Optional[dict] = None  # If LLM: JSON schema for this parameter

class ToolDefinition(BaseModel):
    id: str
    name: str  # Tool name visible to LLM (e.g., "search_web")
    description: str  # Tool description for LLM
    source_step_type: str  # e.g., 'http_get'
    property_mappings: List[ToolPropertyMapping]

    # Tool is stored in graph JSON, not as separate entity
    # Each LLM step has its own tool definitions inline
```

**2.2 Update Graph Model** (`packages/graph-core/graphflow_core/models/graph.py`)
Tools are stored in the LLM step configuration:

```python
# Example step in graph JSON
{
  "id": "llm_1",
  "type": "llm",
  "config": {
    "provider": "openai",
    "model": "gpt-4",
    "tools": [
      {
        "type": "mapped_step",
        "definition": {
          "id": "tool_search_web",
          "name": "search_web",
          "description": "Search the web for information",
          "source_step_type": "http_get",
          "property_mappings": [
            {
              "source_property": "url",
              "visibility": "runtime",
              "runtime_value": "https://api.search.com/v1/search"
            },
            {
              "source_property": "query",
              "visibility": "llm",
              "llm_schema": {
                "type": "string",
                "description": "Search query",
                "required": true
              }
            }
          ]
        }
      }
    ]
  }
}
```

## 3. **Backend: Tool Code Generation**

**3.1 Tool Compiler** (NEW: `packages/graph-compiler/graphflow_compiler/tools/compiler.py`)
Generates framework-specific tool implementations from tool definitions:

```python
class ToolCompiler:
    """Compiles tool definitions into executable framework-specific code"""

    def compile_tools(
        self,
        tools: List[ToolDefinition],
        framework: Literal['pydantic_ai', 'langchain']
    ) -> str:
        """Generate tool function code for the target framework"""

        if framework == 'pydantic_ai':
            return self._compile_pydantic_ai_tools(tools)
        elif framework == 'langchain':
            return self._compile_langchain_tools(tools)

    def _compile_pydantic_ai_tools(self, tools: List[ToolDefinition]) -> str:
        """
        Generate Pydantic AI tool definitions

        Example output:

        @agent.tool
        async def search_web(ctx: RunContext[Deps], query: str) -> str:
            '''Search the web for information'''
            # Get runtime properties from ctx.deps.memory
            url = "https://api.search.com/v1/search"
            headers = ctx.deps.memory.read('search_api_headers')

            # Execute HTTP Get step
            from graphflow_core.steps.http import HttpGetStep
            step = HttpGetStep(url=url, query=query, headers=headers)
            result = await step.execute(ctx.deps.memory)
            return result
        """

        code_lines = []
        for tool in tools:
            code_lines.append(self._generate_pydantic_tool(tool))
        return '\n\n'.join(code_lines)

    def _generate_pydantic_tool(self, tool: ToolDefinition) -> str:
        """Generate a single Pydantic AI tool function"""

        # Build function signature from LLM parameters
        llm_params = [
            m for m in tool.property_mappings
            if m.visibility == 'llm'
        ]
        param_sig = ', '.join([
            f"{m.source_property}: {self._py_type(m.llm_schema)}"
            for m in llm_params
        ])

        # Build runtime property resolution
        runtime_props = [
            m for m in tool.property_mappings
            if m.visibility == 'runtime'
        ]
        runtime_code = []
        for prop in runtime_props:
            if prop.runtime_value.startswith('{memory.'):
                key = prop.runtime_value[8:-1]  # Extract key from {memory.X}
                runtime_code.append(
                    f"    {prop.source_property} = ctx.deps.memory.read('{key}')"
                )
            else:
                # Constant value
                runtime_code.append(
                    f"    {prop.source_property} = {repr(prop.runtime_value)}"
                )

        # Build step execution
        step_class = self._get_step_class(tool.source_step_type)
        all_params = [m.source_property for m in tool.property_mappings]
        step_init = f"{step_class}({', '.join([f'{p}={p}' for p in all_params])})"

        return f'''
@agent.tool
async def {tool.name}(ctx: RunContext[Deps], {param_sig}) -> str:
    """{tool.description}"""
{chr(10).join(runtime_code)}

    # Execute step
    from {self._get_step_module(tool.source_step_type)} import {step_class}
    step = {step_init}
    result = await step.execute(ctx.deps.memory)
    return str(result)
'''

    def _compile_langchain_tools(self, tools: List[ToolDefinition]) -> str:
        """
        Generate LangChain tool definitions

        Example output:

        from langchain.tools import tool

        @tool
        async def search_web(query: str) -> str:
            '''Search the web for information'''
            # Similar structure but LangChain-specific
            ...
        """
        # Similar to Pydantic AI but with LangChain decorators
        pass
```

**3.2 Update Agent Template** (`packages/graph-compiler/graphflow_compiler/templates/pydantic_ai_agent.py.jinja`)
Inject compiled tool code into generated agent:

```python
# Existing imports...
from pydantic_ai import Agent, RunContext

# GENERATED TOOLS - Start
{% for tool_code in compiled_tools %}
{{ tool_code }}
{% endfor %}
# GENERATED TOOLS - End

class GeneratedAgent:
    def __init__(self, use_logging=True):
        self.memory = LoggingMemoryStore() if use_logging else MemoryStore()

        # Create agent with tools
        self.agent = Agent(
            model='{{ model }}',
            system_prompt='{{ system_prompt }}',
            # Tools are auto-registered via @agent.tool decorator
        )

    async def run(self, inputs):
        # Existing execution logic...

        # When executing LLM step, agent already has tools registered
        result = await self.agent.run(user_prompt, deps=Deps(memory=self.memory))
```

**3.3 Update Compiler** (`packages/graph-compiler/graphflow_compiler/generators/pydantic_ai.py`)
```python
class PydanticAIGenerator:
    def generate(self, graph: Graph) -> str:
        # Existing logic...

        # NEW: Extract and compile tools from LLM steps
        compiled_tools = []
        for step in graph.steps:
            if step.type == 'llm' and step.config.get('tools'):
                for tool_config in step.config['tools']:
                    if tool_config['type'] == 'mapped_step':
                        tool_def = ToolDefinition(**tool_config['definition'])
                        tool_code = ToolCompiler().compile_tools(
                            [tool_def],
                            framework='pydantic_ai'
                        )
                        compiled_tools.append(tool_code)

        # Render template with compiled tools
        return template.render(
            # Existing context...
            compiled_tools=compiled_tools
        )
```

## 4. **Backend: Tool Execution at Runtime**

**4.1 Execution Flow**
Since tools are compiled into the generated agent code, execution is automatic:

1. Graph compiled → Tool definitions extracted
2. Tool functions generated for framework (Pydantic AI/LangChain)
3. Tool functions injected into agent template
4. Agent created with tools registered
5. LLM calls tool → Framework executes generated function
6. Function resolves runtime properties from memory
7. Function executes source step
8. Result returned to LLM

**No separate ToolExecutor needed** - the compiled code handles everything!

## 5. **Backend: API Enhancements**

**5.1 Step Schema API** (`packages/graph-runtime/graphflow_runtime/api/routes.py`)
```python
@app.get("/api/v1/steps")
async def list_steps():
    """List all available step types with tool eligibility"""
    steps = []
    for step_type, step_class in StepRegistry.items():
        steps.append({
            'type': step_type,
            'label': step_class.label,
            'description': step_class.description,
            'can_be_tool': step_class.can_be_tool,
            'tool_ineligible_reason': step_class.tool_ineligible_reason,
            'configSchema': step_class.config_schema,
        })
    return {'steps': steps}

@app.get("/api/v1/steps/{step_type}/schema")
async def get_step_schema(step_type: str):
    """Get detailed schema for a specific step type"""
    step_class = StepRegistry.get(step_type)
    if not step_class:
        raise HTTPException(404, f"Step type '{step_type}' not found")

    return {
        'type': step_type,
        'configSchema': step_class.config_schema,
        'inputsSchema': step_class.inputs_schema,
        'outputsSchema': step_class.outputs_schema,
        'can_be_tool': step_class.can_be_tool,
    }
```

**5.2 Tool Validation API** (NEW endpoint)
```python
@app.post("/api/v1/tools/validate")
async def validate_tool(tool: ToolDefinition):
    """Validate a tool definition"""

    # Check source step exists
    step_class = StepRegistry.get(tool.source_step_type)
    if not step_class:
        return {'valid': False, 'error': f"Step type '{tool.source_step_type}' not found"}

    # Check step can be tool
    if not step_class.can_be_tool:
        return {
            'valid': False,
            'error': step_class.tool_ineligible_reason or "This step cannot be used as a tool"
        }

    # Validate property mappings
    step_properties = set(step_class.config_schema.get('properties', {}).keys())
    mapped_properties = set(m.source_property for m in tool.property_mappings)

    missing = step_properties - mapped_properties
    if missing:
        return {
            'valid': False,
            'error': f"Missing property mappings: {', '.join(missing)}"
        }

    return {'valid': True}
```

## 6. **Frontend: Tool Builder UI**

**6.1 ToolEditor Component** (NEW: `packages/graph-builder/src/components/editors/ToolEditor.tsx`)
Main entry point - replaces the `tools` array field in LLM step config

**Layout**:
```
┌─────────────────────────────────────────┐
│ Tools (2)                    [+ Add Tool]│
├─────────────────────────────────────────┤
│ 🔧 search_web               [Edit][Delete]│
│    Search the web for info                │
│    Source: HTTP Get                       │
├─────────────────────────────────────────┤
│ 🔧 get_user_profile         [Edit][Delete]│
│    Get user profile data                  │
│    Source: HTTP Get                       │
└─────────────────────────────────────────┘
```

**Features**:
- List of configured tools (stored in step config, not separate database)
- Click "Edit" → opens ToolBuilderModal
- Click "Add Tool" → opens modal with blank tool
- Delete confirmation dialog
- Shows tool summary (name, description, source step)
- Import/Export tools as JSON (for reuse across graphs)

**6.2 ToolBuilderModal Component** (NEW: `packages/graph-builder/src/components/editors/ToolBuilderModal.tsx`)
Modal for creating/editing a single tool

**Step 1: Basic Info**
```
Tool Name: [search_web              ]
Description:
[Search the web for information      ]
[Use this when you need to find     ]
[current information online.         ]
```

**Step 2: Select Source Step**
```
Source Step Type:
┌─────────────────────────────────────┐
│ [Filter: ___________] [x]           │
├─────────────────────────────────────┤
│ Tool-Eligible Steps:                 │
│ ○ HTTP Get        Make HTTP request │
│ ○ HTTP Post       POST data         │
│ ○ Database Query  Query database    │
│ ● Custom Code     Run Python code   │
│                                      │
│ Not Available as Tools:              │
│ ⊘ If/Else        (Control flow)     │
│ ⊘ LLM            (Cannot nest LLMs) │
└─────────────────────────────────────┘

[< Back]  [Next >]
```

**Step 3: Configure Properties**
For selected step, show all properties with visibility toggle:

```
Configure Properties for: HTTP Get

┌────────────────────────────────────────────────┐
│ Property: url                                   │
│ ○ LLM Controls  ● Runtime Provides            │
│                                                 │
│ Runtime Value:                                 │
│ ○ Constant: [https://api.example.com/search  ]│
│ ● Memory: {memory.api_base_url               }│
│                                                 │
│ [ ] Expose to LLM (read-only)                 │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Property: query                                 │
│ ● LLM Controls  ○ Runtime Provides            │
│                                                 │
│ LLM Parameter Name: [query          ]         │
│ Description:                                    │
│ [Search query string                ]         │
│                                                 │
│ Type: string                                    │
│ [✓] Required                                   │
└────────────────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│ Property: headers                               │
│ ○ LLM Controls  ● Runtime Provides            │
│                                                 │
│ Runtime Value:                                 │
│ ● Memory: {memory.auth_headers               }│
│ ○ Constant: [{"Authorization": "Bearer ..."}]│
│                                                 │
│ [ ] Expose to LLM (read-only)                 │
└────────────────────────────────────────────────┘

[< Back]  [Save Tool]
```

**Property Configuration Options**:
- **LLM Controls**: Parameter name, description, type, required, enum values
- **Runtime Provides**:
  - Constant value (text input with type validation)
  - Memory binding (dropdown of available memory keys)
  - Option to expose to LLM as read-only context

**6.3 PropertyMappingCard Component** (NEW: `packages/graph-builder/src/components/editors/PropertyMappingCard.tsx`)
Reusable card for configuring a single property mapping

**Props**:
```typescript
interface PropertyMappingCardProps {
  propertyKey: string;
  propertySchema: any;  // From step definition
  mapping: ToolPropertyMapping;
  onChange: (mapping: ToolPropertyMapping) => void;
  availableMemory: MemorySchema;
}
```

**Features**:
- Radio buttons for LLM vs Runtime
- Conditional forms based on selection
- Memory binding autocomplete
- Type validation for constants
- Schema editor for LLM parameters (type, description, enum, required)

**6.4 Memory Binding Picker** (NEW: `packages/graph-builder/src/components/editors/MemoryBindingPicker.tsx`)
Dropdown/autocomplete for selecting memory bindings

**Features**:
- Shows available memory keys grouped by namespace (inputs, outputs, intermediate)
- Filter by type compatibility
- Shows key type and current value (if available)
- Creates binding string: `{memory.key}`

## 7. **Frontend: Enhanced LLM Step**

**7.1 Update LLM Step Schema** (`packages/graph-builder/src/utils/stepTypes.ts`)
```typescript
llm: {
  // ... existing fields ...
  configSchema: {
    // ... existing fields ...
    tools: {
      type: 'array',
      description: 'Available tools for the LLM',
      x-editor: 'tools',  // Use custom ToolEditor
      items: {
        type: 'object',
        properties: {
          type: { enum: ['function', 'mapped_step'] },
          // function: manual OpenAI-style definition
          // mapped_step: tool built from step mapping
          definition: { type: 'object' }  // ToolDefinition schema
        }
      }
    }
  }
}
```

**7.2 Tool Validation**
- Validate tool definitions before saving
- Check memory bindings exist
- Validate constant values match expected types
- Warn about missing required properties
- Show warning if source step is not tool-eligible

## 8. **Frontend: Services & Hooks**

**8.1 Step Service Updates** (`packages/graph-builder/src/services/steps.ts`)
```typescript
export const stepsService = {
  // Existing methods...

  async getStepSchema(stepType: string): Promise<StepSchema> {
    const response = await fetch(`/api/v1/steps/${stepType}/schema`);
    return response.json();
  },

  async validateTool(tool: ToolDefinition): Promise<ValidationResult> {
    const response = await fetch('/api/v1/tools/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(tool)
    });
    return response.json();
  }
}
```

**8.2 useStepSchema Hook** (NEW: `packages/graph-builder/src/hooks/useStepSchema.ts`)
```typescript
export function useStepSchema(stepType: string | null) {
  return useQuery(
    ['stepSchema', stepType],
    () => stepsService.getStepSchema(stepType!),
    { enabled: !!stepType }
  );
}
```

**8.3 useToolValidation Hook** (NEW: `packages/graph-builder/src/hooks/useToolValidation.ts`)
```typescript
export function useToolValidation() {
  return useMutation(
    (tool: ToolDefinition) => stepsService.validateTool(tool)
  );
}
```

## 9. **Data Flow**

### Creating a Tool:
1. User clicks "Add Tool" in ToolEditor (within LLM step properties)
2. ToolBuilderModal opens (Step 1: Basic Info)
3. User enters tool name and description
4. Step 2: User selects source step type (filtered to show only `can_be_tool: true` steps)
5. Frontend fetches step schema via `getStepSchema('http_get')`
6. Step 3: For each property in schema:
   - User toggles "LLM Controls" or "Runtime Provides"
   - If Runtime: selects memory binding or enters constant
   - If LLM: configures parameter schema (name, description, type)
7. User clicks "Save Tool"
8. Frontend validates tool definition via `/api/v1/tools/validate`
9. Tool definition added to step's `config.tools` array
10. Tool appears in ToolEditor list
11. Graph saved with tool embedded in LLM step config

### Compiling a Graph with Tools:
1. User clicks "Run" on graph with LLM step containing tools
2. Backend receives graph JSON
3. Compiler extracts LLM steps with `mapped_step` tools
4. For each tool:
   - Validates source step exists and is tool-eligible
   - Generates framework-specific tool function code
5. Tool code injected into agent template
6. Complete agent code compiled and executed
7. Agent has tools registered and ready for LLM to call

### Using a Tool at Runtime:
1. LLM receives tool schema (only LLM-visible parameters)
2. LLM decides to call tool with parameters (e.g., `search_web(query="Python")`)
3. Pydantic AI/LangChain invokes generated tool function
4. Function resolves runtime properties from memory
5. Function executes source step with merged parameters
6. Result returned to LLM
7. LLM continues conversation with result

## 10. **Tool Import/Export** (Bonus Feature)

Since tools are embedded in step config, users might want to reuse tools across graphs:

**Export Tool**:
```typescript
// In ToolEditor
const exportTool = (tool: ToolDefinition) => {
  const json = JSON.stringify(tool, null, 2);
  downloadFile(`${tool.name}.tool.json`, json);
};
```

**Import Tool**:
```typescript
// In ToolEditor
const importTool = (file: File) => {
  const tool = JSON.parse(await file.text());
  // Validate tool
  const validation = await validateTool(tool);
  if (validation.valid) {
    // Add to current step's tools
    onChange([...value, { type: 'mapped_step', definition: tool }]);
  }
};
```

**Tool Library** (Future):
- Global tool registry with pre-built tools
- Share tools across projects
- Community tool marketplace

## Implementation Phases

### Phase 1: Step Eligibility & Schema API
1. Add `can_be_tool` flag to `StepBase`
2. Mark all existing steps appropriately
3. Update `/api/v1/steps` endpoint to include flag
4. Add `/api/v1/steps/{type}/schema` endpoint
5. Add `/api/v1/tools/validate` endpoint
6. Test with Postman/curl

### Phase 2: Tool Compiler
1. Create `ToolCompiler` class
2. Implement Pydantic AI tool generation
3. Implement LangChain tool generation (if needed)
4. Add unit tests for generated code
5. Test with sample tool definitions

### Phase 3: Compiler Integration
1. Update `PydanticAIGenerator` to extract tools
2. Integrate `ToolCompiler` into compilation pipeline
3. Update agent template to include tool code
4. Test end-to-end: graph with tool → compiled code → execution
5. Verify tool calling works correctly

### Phase 4: Frontend Tool Builder UI
1. Create `ToolEditor` component (list view)
2. Create `ToolBuilderModal` skeleton (3 steps)
3. Implement Step 1: Basic Info form
4. Implement Step 2: Step type selector (with eligibility filtering)
5. Implement Step 3: Property mapping interface
6. Style with existing UI theme

### Phase 5: Frontend Property Mapping
1. Create `PropertyMappingCard` component
2. Implement LLM vs Runtime toggle
3. Add memory binding picker
4. Add constant value input with validation
5. Add LLM parameter schema editor
6. Test with various step types

### Phase 6: Integration & Services
1. Create `useStepSchema` hook
2. Create `useToolValidation` hook
3. Connect ToolEditor to real API
4. Register `ToolEditor` in EditorRegistry
5. Update LLM step schema to use custom editor
6. Test in PropertiesPanel

### Phase 7: Testing & Polish
1. End-to-end test: create tool → compile → execute → LLM calls tool
2. Test with multiple frameworks (Pydantic AI, LangChain)
3. Error handling and validation
4. Tool import/export functionality
5. Documentation and examples
6. UI polish and animations

## Technical Decisions & Considerations

### Tool Storage
- **No separate database**: Tools are stored inline in graph JSON
- **Embedded in step config**: Each LLM step has its own tools
- **Reusability via export/import**: Users can share tools as JSON files
- **Future**: Optional global tool library for common patterns

### Memory Binding Resolution
- Runtime bindings resolved at execution time within generated tool function
- If memory key doesn't exist → error with helpful message
- Support default values for optional runtime properties
- Validate binding exists at compile time (warning, not error)

### Security
- Runtime properties NEVER sent to LLM in tool schema
- Tool definitions sanitized before LLM sees them
- Validate all user inputs (prevent injection)
- Secrets handled via existing secrets system
- Generated code runs in same sandbox as regular steps

### Type Safety
- Validate runtime constant values match expected types
- Type checking for memory bindings (warn if types mismatch)
- LLM parameter schemas must match source property types
- Generated code includes type hints for IDE support

### Framework Support
- **Phase 1**: Pydantic AI (primary framework)
- **Phase 2**: LangChain/LangGraph (if needed)
- **Extensible**: Easy to add new framework generators
- Framework detected from graph configuration or step config

### Code Generation Strategy
- Tools compiled into agent code (not runtime interpreted)
- Generated code is human-readable for debugging
- Include comments in generated code explaining mappings
- Failed compilation shows helpful error messages

### Step Eligibility Guidelines
Steps that should be tools:
- External API calls (HTTP, database, file system)
- Data transformations (format, parse, transform)
- Custom code execution
- Retrieval operations (search, query)

Steps that should NOT be tools:
- Control flow (if/else, loops, switches)
- Memory operations (set variable, clear memory)
- Other LLM steps (no nested LLM calls)
- Graph control (wait, timeout, error handling)

### Advanced Features (Future)
- **Tool composition**: Multi-step tools (chain steps)
- **Conditional properties**: Show/hide based on other values
- **Response transformation**: Map step output to LLM-friendly format
- **Tool categories**: Organize tools by function
- **Tool templates**: Pre-built tools for common use cases
- **Tool versioning**: Track changes to tool definitions

## Files to Create

**Backend** (~700 lines total):
1. `packages/graph-compiler/graphflow_compiler/tools/__init__.py` (boilerplate)
2. `packages/graph-compiler/graphflow_compiler/tools/compiler.py` (~300 lines)
3. `packages/graph-core/graphflow_core/models/tool.py` (~100 lines)
4. `packages/graph-compiler/graphflow_compiler/tools/pydantic_ai_generator.py` (~200 lines)
5. `packages/graph-compiler/graphflow_compiler/tools/langchain_generator.py` (~100 lines) - optional

**Frontend** (~1200 lines total):
1. `packages/graph-builder/src/components/editors/ToolEditor.tsx` (~200 lines)
2. `packages/graph-builder/src/components/editors/ToolBuilderModal.tsx` (~400 lines)
3. `packages/graph-builder/src/components/editors/PropertyMappingCard.tsx` (~250 lines)
4. `packages/graph-builder/src/components/editors/MemoryBindingPicker.tsx` (~150 lines)
5. `packages/graph-builder/src/hooks/useStepSchema.ts` (~50 lines)
6. `packages/graph-builder/src/hooks/useToolValidation.ts` (~50 lines)
7. `packages/graph-builder/src/types/tool.ts` (~100 lines)

## Files to Modify

**Backend** (~250 lines changes):
1. `packages/graph-core/graphflow_core/steps/base.py` (+20 lines) - Add `can_be_tool` flag
2. `packages/graph-core/graphflow_core/steps/*.py` (+5 lines each × ~15 steps) - Mark eligibility
3. `packages/graph-runtime/graphflow_runtime/api/routes.py` (+100 lines) - New endpoints
4. `packages/graph-compiler/graphflow_compiler/generators/pydantic_ai.py` (+50 lines) - Tool integration
5. `packages/graph-compiler/graphflow_compiler/templates/pydantic_ai_agent.py.jinja` (+30 lines) - Tool injection
6. `packages/graph-core/graphflow_core/steps/llm.py` (+50 lines) - Update tool handling

**Frontend** (~150 lines changes):
1. `packages/graph-builder/src/components/editors/EditorRegistry.ts` (+10 lines)
2. `packages/graph-builder/src/components/editors/index.ts` (+10 lines)
3. `packages/graph-builder/src/utils/stepTypes.ts` (+30 lines)
4. `packages/graph-builder/src/services/steps.ts` (+50 lines)
5. `packages/graph-builder/src/types/graph.ts` (+50 lines)

## Estimated Effort
- **Backend Core (Compiler)**: 3-4 days
- **Backend API & Integration**: 2-3 days
- **Frontend UI**: 4-5 days
- **Integration & Testing**: 2-3 days
- **Documentation**: 1 day
- **Total**: 12-16 days

## Example End Result

### User Creates a Tool (Stored in Graph JSON):
```json
{
  "id": "llm_1",
  "type": "llm",
  "config": {
    "provider": "openai",
    "model": "gpt-4",
    "tools": [
      {
        "type": "mapped_step",
        "definition": {
          "id": "tool_search",
          "name": "search_web",
          "description": "Search the web for current information",
          "source_step_type": "http_get",
          "property_mappings": [
            {
              "source_property": "url",
              "visibility": "runtime",
              "runtime_value": "https://api.search.com/v1/search"
            },
            {
              "source_property": "query",
              "visibility": "llm",
              "llm_schema": {
                "type": "string",
                "description": "Search query",
                "required": true
              }
            },
            {
              "source_property": "headers",
              "visibility": "runtime",
              "runtime_value": "{memory.search_api_headers}"
            }
          ]
        }
      }
    ]
  }
}
```

### Generated Code (Pydantic AI):
```python
from pydantic_ai import Agent, RunContext

# GENERATED TOOLS - Start
@agent.tool
async def search_web(ctx: RunContext[Deps], query: str) -> str:
    """Search the web for current information"""
    # Runtime properties from config/memory
    url = "https://api.search.com/v1/search"
    headers = ctx.deps.memory.read('search_api_headers')

    # Execute source step
    from graphflow_core.steps.http import HttpGetStep
    step = HttpGetStep(url=url, query=query, headers=headers)
    result = await step.execute(ctx.deps.memory)
    return str(result)
# GENERATED TOOLS - End

class GeneratedAgent:
    def __init__(self):
        self.memory = MemoryStore()
        self.agent = Agent(
            model='openai:gpt-4',
            system_prompt='You are a helpful assistant.'
        )

    async def run(self, inputs):
        # Agent has search_web tool available
        result = await self.agent.run(
            "Search for Python tutorials",
            deps=Deps(memory=self.memory)
        )
        return result
```

### What LLM Sees:
```json
{
  "type": "function",
  "function": {
    "name": "search_web",
    "description": "Search the web for current information",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "Search query"
        }
      },
      "required": ["query"]
    }
  }
}
```

### Runtime Execution:
```python
# LLM calls: search_web(query="Python tutorials")
# Framework executes generated function:
await search_web(ctx, query="Python tutorials")

# Inside function:
# - url = "https://api.search.com/v1/search" (from config)
# - query = "Python tutorials" (from LLM)
# - headers = {"Authorization": "Bearer xyz"} (from memory)
#
# HttpGetStep executes with all parameters
# Result returned to LLM
```

---

This plan now fully accounts for code generation, framework integration, and step eligibility. The tools are compiled into the agent code rather than executed through a separate runtime system, which is cleaner and more performant.
