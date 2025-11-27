# GraphFlow Extensibility Plan: Plugins & MCP Integration

This document outlines plans for extending GraphFlow with new plugins and MCP (Model Context Protocol) server integration.

---

## Part 1: Plugin Ideas by Category

### 1.1 Data Processing Plugin (`graph-plugins-data`)

**Purpose**: JSON manipulation, CSV handling, DataFrame operations

#### Steps to Include:

| Step | Description | Config |
|------|-------------|--------|
| `JSONPathStep` | Extract values using JSONPath expressions | `expression`, `input_key`, `output_key` |
| `JSONMergeStep` | Deep merge multiple JSON objects | `sources[]`, `output_key`, `merge_strategy` |
| `JSONSchemaValidateStep` | Validate JSON against schema | `schema`, `input_key`, `output_key`, `strict` |
| `JSONTransformStep` | Transform JSON using jq-like syntax | `transform_expr`, `input_key`, `output_key` |
| `CSVParseStep` | Parse CSV string to list of dicts | `input_key`, `output_key`, `delimiter`, `has_header` |
| `CSVStringifyStep` | Convert list of dicts to CSV | `input_key`, `output_key`, `columns[]` |
| `DataFrameLoadStep` | Load data into pandas DataFrame | `source_key`, `format`, `output_key` |
| `DataFrameQueryStep` | Query DataFrame with pandas expressions | `df_key`, `query`, `output_key` |
| `DataFrameTransformStep` | Apply transformations (filter, sort, group) | `df_key`, `operations[]`, `output_key` |
| `DataFrameToJSONStep` | Convert DataFrame to JSON | `df_key`, `orient`, `output_key` |

**Dependencies**: `pandas`, `jsonpath-ng`, `jq` (optional)

---

### 1.2 External Services Plugin (`graph-plugins-services`)

**Purpose**: Email, FTP, cloud storage, webhooks

#### Steps to Include:

| Step | Description | Config |
|------|-------------|--------|
| `SMTPSendStep` | Send email via SMTP | `host`, `port`, `username_secret`, `password_secret`, `to`, `subject`, `body`, `attachments[]` |
| `IMAPReadStep` | Read emails from IMAP server | `host`, `folder`, `filter`, `limit`, `output_key` |
| `FTPUploadStep` | Upload file to FTP server | `host`, `path`, `content_key`, `username_secret`, `password_secret` |
| `FTPDownloadStep` | Download file from FTP | `host`, `path`, `output_key` |
| `SFTPUploadStep` | Upload via SFTP (SSH) | `host`, `path`, `content_key`, `key_secret` |
| `SFTPDownloadStep` | Download via SFTP | `host`, `path`, `output_key` |
| `S3UploadStep` | Upload to AWS S3 | `bucket`, `key`, `content_key`, `credentials_secret` |
| `S3DownloadStep` | Download from S3 | `bucket`, `key`, `output_key` |
| `WebhookSendStep` | POST to webhook URL | `url`, `payload_key`, `headers`, `output_key` |
| `WebhookWaitStep` | Wait for incoming webhook | `path`, `timeout`, `output_key` |

**Dependencies**: `boto3`, `paramiko`, `aiosmtplib`, `aioimaplib`

---

### 1.3 Text & String Plugin (`graph-plugins-text`)

**Purpose**: String manipulation, regex, templating

#### Steps to Include:

| Step | Description | Config |
|------|-------------|--------|
| `StringFormatStep` | Python f-string style formatting | `template`, `output_key` |
| `StringJoinStep` | Join array of strings | `input_key`, `separator`, `output_key` |
| `StringSplitStep` | Split string into array | `input_key`, `separator`, `output_key` |
| `RegexMatchStep` | Extract regex matches | `input_key`, `pattern`, `output_key`, `groups` |
| `RegexReplaceStep` | Replace using regex | `input_key`, `pattern`, `replacement`, `output_key` |
| `TemplateRenderStep` | Jinja2 template rendering | `template`, `context_key`, `output_key` |
| `TextTruncateStep` | Truncate text to length | `input_key`, `max_length`, `suffix`, `output_key` |
| `TextCaseStep` | Change case (upper/lower/title) | `input_key`, `case`, `output_key` |
| `MarkdownToHTMLStep` | Convert markdown to HTML | `input_key`, `output_key` |
| `HTMLToMarkdownStep` | Convert HTML to markdown | `input_key`, `output_key` |

**Dependencies**: `jinja2`, `markdown`, `markdownify`

---

### 1.4 Database Plugin (`graph-plugins-database`)

**Purpose**: SQL databases, NoSQL, vector stores

#### Steps to Include:

| Step | Description | Config |
|------|-------------|--------|
| `SQLQueryStep` | Execute SQL query | `connection_string_secret`, `query`, `params`, `output_key` |
| `SQLExecuteStep` | Execute SQL (INSERT/UPDATE/DELETE) | `connection_string_secret`, `query`, `params` |
| `SQLBulkInsertStep` | Bulk insert from array | `connection_string_secret`, `table`, `data_key` |
| `MongoQueryStep` | Query MongoDB collection | `uri_secret`, `database`, `collection`, `filter`, `output_key` |
| `MongoInsertStep` | Insert into MongoDB | `uri_secret`, `database`, `collection`, `document_key` |
| `RedisGetStep` | Get value from Redis | `uri_secret`, `key`, `output_key` |
| `RedisSetStep` | Set value in Redis | `uri_secret`, `key`, `value_key`, `ttl` |
| `VectorSearchStep` | Semantic search in vector DB | `connection`, `collection`, `query_key`, `top_k`, `output_key` |
| `VectorUpsertStep` | Upsert embeddings | `connection`, `collection`, `documents_key` |

**Dependencies**: `sqlalchemy`, `asyncpg`, `motor`, `redis`, `chromadb`/`pinecone`

---

### 1.5 File System Plugin (`graph-plugins-filesystem`)

**Purpose**: Local file operations

#### Steps to Include:

| Step | Description | Config |
|------|-------------|--------|
| `FileReadStep` | Read file contents | `path`, `encoding`, `output_key` |
| `FileWriteStep` | Write to file | `path`, `content_key`, `encoding` |
| `FileAppendStep` | Append to file | `path`, `content_key` |
| `FileDeleteStep` | Delete file | `path` |
| `FileListStep` | List directory contents | `path`, `pattern`, `output_key` |
| `FileCopyStep` | Copy file | `source`, `destination` |
| `FileMoveStep` | Move/rename file | `source`, `destination` |
| `ZipCreateStep` | Create ZIP archive | `files[]`, `output_path` |
| `ZipExtractStep` | Extract ZIP archive | `archive_path`, `destination` |

**Dependencies**: Built-in Python (`pathlib`, `zipfile`, `shutil`)

---

## Part 2: MCP (Model Context Protocol) Integration

### 2.1 Overview

MCP integration enables GraphFlow to connect to MCP servers and use their tools in two ways:
1. **As Steps**: Each MCP tool becomes a graph step node
2. **As LLM Tools**: MCP tools available to LLM steps during execution

### 2.2 MCP Connection Management

#### Option A: Graph-Level Configuration

MCP servers defined in graph metadata:

```json
{
  "version": "1.0",
  "metadata": {
    "name": "My Agent",
    "mcp_servers": [
      {
        "id": "filesystem",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
      },
      {
        "id": "github",
        "transport": "stdio",
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-github"],
        "env": {
          "GITHUB_TOKEN": "{secrets.github_token}"
        }
      }
    ]
  }
}
```

**Pros**: Self-contained graphs, portable, explicit dependencies
**Cons**: Server processes started per-graph, potential resource waste

#### Option B: Runtime-Level Configuration

MCP servers configured in runtime config file (`runtime_config.yaml`):

```yaml
mcp_servers:
  filesystem:
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-filesystem", "/data"]

  github:
    transport: stdio
    command: npx
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"

  custom_api:
    transport: http
    url: "http://localhost:8080/mcp"
```

**Pros**: Shared server instances, centralized management, persistent connections
**Cons**: Graphs depend on runtime environment, less portable

#### Option C: Hybrid (Recommended)

- Runtime defines **available** MCP servers
- Graphs declare which servers they **require** (by ID)
- Runtime validates requirements at graph load time

```json
// Graph metadata
{
  "mcp_requirements": ["filesystem", "github"]
}
```

### 2.3 MCP Plugin Architecture (`graph-plugins-mcp`)

#### Core Components:

```
packages/graph-plugins-mcp/
├── graphflow_mcp/
│   ├── __init__.py
│   ├── manifest.json
│   ├── client.py           # MCP client wrapper
│   ├── connection_pool.py  # Manage MCP server connections
│   ├── steps/
│   │   ├── __init__.py
│   │   ├── mcp_tool_step.py    # Generic step that calls any MCP tool
│   │   └── mcp_resource_step.py # Step to read MCP resources
│   └── tools/
│       └── mcp_tool_adapter.py  # Adapt MCP tools as LLM tools
```

#### MCPClient Class:

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class MCPClient:
    """Manages connection to a single MCP server."""

    def __init__(self, server_config: dict):
        self.config = server_config
        self.session: Optional[ClientSession] = None
        self._tools_cache: Optional[List[dict]] = None

    async def connect(self) -> None:
        """Establish connection to MCP server."""
        if self.config["transport"] == "stdio":
            params = StdioServerParameters(
                command=self.config["command"],
                args=self.config.get("args", []),
                env=self.config.get("env")
            )
            transport = await stdio_client(params).__aenter__()
            self.session = await ClientSession(*transport).__aenter__()
            await self.session.initialize()

    async def list_tools(self) -> List[dict]:
        """Get available tools from server."""
        if self._tools_cache is None:
            result = await self.session.list_tools()
            self._tools_cache = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema
                }
                for tool in result.tools
            ]
        return self._tools_cache

    async def call_tool(self, name: str, arguments: dict) -> Any:
        """Call a tool on the MCP server."""
        result = await self.session.call_tool(name, arguments)
        # Extract text content from response
        if result.content:
            return result.content[0].text
        return None
```

#### MCPToolStep (Use MCP Tools as Graph Steps):

```python
class MCPToolStep(StepBase):
    """Execute any MCP tool as a graph step."""

    label = "MCP Tool"
    description = "Call a tool from an MCP server"
    category = "mcp"

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "server_id": {
                    "type": "string",
                    "description": "MCP server identifier"
                },
                "tool_name": {
                    "type": "string",
                    "description": "Name of MCP tool to call"
                },
                "arguments": {
                    "type": "object",
                    "description": "Arguments to pass to tool",
                    "x-editor": "json"
                }
            },
            "required": ["server_id", "tool_name"]
        }

    async def execute(self, memory: MemoryStore) -> None:
        server_id = self.config["server_id"]
        tool_name = self.config["tool_name"]
        arguments = self._resolve_arguments(self.config.get("arguments", {}), memory)

        # Get MCP client from connection pool
        client = MCPConnectionPool.get_client(server_id)
        result = await client.call_tool(tool_name, arguments)

        # Write to output
        if "result" in self.outputs:
            output_key = self._extract_memory_key(self.outputs["result"])
            memory.write(output_key, result)
```

### 2.4 MCP Tools as LLM Tools

To expose MCP tools to LLM steps, we create an adapter that converts MCP tool definitions to GraphFlow's tool format.

#### MCPToolAdapter:

```python
class MCPToolAdapter:
    """Adapts MCP tools for use in LLM steps."""

    @staticmethod
    def mcp_to_tool_definition(server_id: str, mcp_tool: dict) -> ToolDefinition:
        """Convert MCP tool to GraphFlow ToolDefinition."""

        # Build property mappings from MCP inputSchema
        mappings = []
        schema = mcp_tool.get("inputSchema", {})
        properties = schema.get("properties", {})
        required = schema.get("required", [])

        for prop_name, prop_schema in properties.items():
            mappings.append(ToolPropertyMapping(
                source_property=prop_name,
                visibility="llm",
                llm_parameter_name=prop_name,
                llm_description=prop_schema.get("description", ""),
                llm_schema=prop_schema,
                required=prop_name in required
            ))

        # Add hidden server_id parameter
        mappings.append(ToolPropertyMapping(
            source_property="_mcp_server_id",
            visibility="runtime",
            runtime_value=server_id
        ))

        return ToolDefinition(
            id=f"mcp_{server_id}_{mcp_tool['name']}",
            name=mcp_tool["name"],
            description=mcp_tool.get("description", ""),
            source_step_type="mcp.MCPToolStep",
            property_mappings=mappings,
            output_key="result"
        )
```

#### Usage in LLM Step:

```json
{
  "id": "llm_1",
  "type": "llm",
  "config": {
    "provider": "ollama",
    "model": "llama3.1",
    "user_prompt": "{memory.user_request}",
    "mcp_tools": {
      "servers": ["filesystem", "github"],
      "include_patterns": ["*"],
      "exclude_patterns": ["dangerous_*"]
    }
  }
}
```

The compiler would:
1. Connect to specified MCP servers
2. List their tools
3. Convert to ToolDefinitions via MCPToolAdapter
4. Include in compiled LLM step code

### 2.5 Dynamic Tool Discovery

For runtime-level MCP servers, we need dynamic tool discovery:

```python
class MCPConnectionPool:
    """Singleton managing all MCP server connections."""

    _instance = None
    _clients: Dict[str, MCPClient] = {}

    @classmethod
    async def initialize(cls, config: dict) -> None:
        """Initialize connections from runtime config."""
        for server_id, server_config in config.get("mcp_servers", {}).items():
            client = MCPClient(server_config)
            await client.connect()
            cls._clients[server_id] = client

    @classmethod
    def get_client(cls, server_id: str) -> MCPClient:
        if server_id not in cls._clients:
            raise ValueError(f"MCP server '{server_id}' not configured")
        return cls._clients[server_id]

    @classmethod
    async def get_all_tools(cls) -> Dict[str, List[dict]]:
        """Get tools from all connected servers."""
        result = {}
        for server_id, client in cls._clients.items():
            result[server_id] = await client.list_tools()
        return result
```

### 2.6 API Endpoints for MCP

Add REST endpoints for MCP management:

```
GET  /api/v1/mcp/servers           # List configured MCP servers
GET  /api/v1/mcp/servers/{id}      # Get server details
GET  /api/v1/mcp/servers/{id}/tools # List tools from server
POST /api/v1/mcp/servers/{id}/connect # Connect to server
POST /api/v1/mcp/servers/{id}/disconnect # Disconnect
```

### 2.7 UI Integration

**Step Palette Changes:**
- New "MCP" category showing connected servers
- Expandable server nodes showing available tools
- Drag MCP tool → creates MCPToolStep with tool pre-configured

**LLM Step Tool Panel:**
- "Add MCP Tools" button
- Server/tool selector dialog
- Pattern-based filtering (include/exclude)

---

## Part 3: Implementation Roadmap

### Phase 1: MCP Foundation
1. Create `graph-plugins-mcp` package
2. Implement MCPClient and MCPConnectionPool
3. Add runtime config support for MCP servers
4. Add basic MCPToolStep

### Phase 2: MCP as LLM Tools
1. Implement MCPToolAdapter
2. Update LLM step templates for MCP tools
3. Add `mcp_tools` config to LLM step schema
4. Update tool compiler for MCP tools

### Phase 3: UI Integration
1. Add MCP server management to runtime view
2. Add MCP tools to step palette
3. Add MCP tool selector to LLM step properties

### Phase 4: Additional Plugins
- Pick plugins based on user demand
- Each plugin follows established patterns
- ~1-2 days per plugin for core steps

---

## Key Files Reference

| File | Purpose |
|------|---------|
| `packages/graph-core/graphflow_core/steps/base.py` | StepBase class to extend |
| `packages/graph-core/graphflow_core/models/tool.py` | ToolDefinition models |
| `packages/graph-compiler/graphflow_compiler/tools/compiler.py` | Tool code generation |
| `packages/graph-runtime/graphflow_runtime/config.py` | Runtime configuration |
| `packages/graphflow-plugin-example/` | Plugin template to copy |

---

**Last Updated:** 2025-11-27
