# Architecture Overview

startmcp implements a **gateway pattern** to aggregate multiple MCP providers into a single server.

## High-Level Architecture

```
┌─────────────────┐
│  AI Assistant   │ (Claude Desktop, etc.)
│  (MCP Client)   │
└────────┬────────┘
         │ stdio/SSE
         │
┌────────▼────────────────┐
│   startmcp Gateway      │
│                         │
│  ┌──────────────────┐  │
│  │  MCP Server      │  │ Handles JSON-RPC requests
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │  Tool Aggregator │  │ Collects tools from providers
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │  Tool Router     │  │ Routes calls to providers
│  └────────┬─────────┘  │
│           │             │
│  ┌────────▼─────────┐  │
│  │  Providers       │  │
│  │  - Atlassian     │  │
│  │  - GitHub        │  │
│  │  - PostgreSQL    │  │
│  │  - ...           │  │
│  └──────────────────┘  │
└─────────────────────────┘
         │
         │ stdio/SSE/HTTP
         ▼
┌─────────────────────┐
│  Backend MCP        │
│  Servers            │
│  (Atlassian, etc.)  │
└─────────────────────┘
```

## Core Components

### 1. MCP Server (`mcp/server/`)
- Implements stdio transport (SSE in progress)
- Handles incoming JSON-RPC requests
- Routes to appropriate gateway handlers

### 2. Tool Aggregator (`mcp/aggregator.py`)
- Collects tools from all enabled providers
- Detects name conflicts between providers
- Applies hybrid namespacing:
  - Natural names for unique tools (`search_issues`)
  - Prefixed names for conflicts (`atlassian:list_projects`, `github:list_projects`)
- Enriches tools with metadata (provider, category)

### 3. Routers (`mcp/router.py`)
- **ToolRouter**: Routes `tools/call` to correct provider
  - Parses tool names (handles `provider:tool` format)
  - Resolves provider from name mapping
  - Detects ambiguous calls
- **ResourceRouter**: Routes `resources/read` by URI scheme
  - Extracts provider from URI (`atlassian://...`)
  - Routes to appropriate provider

### 4. Conflict Resolver (`mcp/conflict_resolver.py`)
- Generates helpful error messages
- Suggests correct tool names
- Lists available providers for a tool

### 5. Gateway Orchestrator (`mcp/gateway.py`)
- Coordinates all components
- Manages provider lifecycle (connect/disconnect)
- Implements MCP protocol handlers:
  - `tools/list` → Aggregate tools from all providers
  - `tools/call` → Route to correct provider
  - `resources/list` → Aggregate resources
  - `resources/read` → Route by URI
  - `prompts/list` → Aggregate prompts
  - `prompts/get` → Route to correct provider

### 6. Provider System (`mcp/provider.py`)
- Abstract base class for all providers
- Handles transport creation
- Delegates MCP operations to client
- Lifecycle management (connect/disconnect)

### 7. Registry (`mcp/registry.py`)
- Dynamically discovers providers from `provider_mcps/`
- Loads provider classes
- Categorizes providers
- Creates provider instances

## Request Flow

### Tool Call Example

```
1. AI sends: tools/call {name: "search_issues", arguments: {...}}
   ↓
2. stdio server receives JSON-RPC request
   ↓
3. Gateway.handle_tools_call()
   ↓
4. ToolRouter.route(name="search_issues")
   ├─ Lookup in aggregated tools
   ├─ Find: "search_issues" → provider="atlassian"
   └─ Return provider instance
   ↓
5. Call provider.call_tool("search_issues", {...})
   ↓
6. Provider sends request to Atlassian MCP server
   ↓
7. Atlassian processes and returns results
   ↓
8. Gateway returns response to AI
```

## Tool Namespacing Strategy

### Hybrid Namespacing
Tools keep natural names when unique across all providers. Only conflicting tools get prefixed.

**Example:**
```yaml
Providers: Atlassian, GitHub

Unique tools (natural names):
- search_issues → Atlassian (only provider with this tool)
- create_pr → GitHub (only provider with this tool)

Conflicting tools (namespaced):
- atlassian:list_projects (conflict with GitHub)
- github:list_projects (conflict with Atlassian)
```

### Benefits
1. **Developer-friendly**: Use `search_issues` instead of `atlassian:search_issues`
2. **Explicit when needed**: Use `atlassian:list_projects` when there's a conflict
3. **Helpful errors**: If AI calls `list_projects`, get suggestion to use specific provider

## Resource URIs

All resources use provider-prefixed URIs:

```
atlassian://PROJ-123
github://owner/repo/issues/42
postgres://database/table/row
```

This ensures routing without ambiguity.

## Performance

- **Startup**: ~2-3 seconds (connects to all providers)
- **Tool List**: <100ms (cached after first call)
- **Tool Call**: Same as direct provider + ~5ms routing overhead
- **Resource Read**: Same as direct provider + URI parsing

## Configuration

```yaml
# config.yaml
enabled_providers:
  - atlassian
  - github

atlassian:
  default_project: "PROJ"

github:
  default_org: "mycompany"
```

## Extensibility

Add new providers by:
1. Creating `provider_mcps/<category>/<name>/provider.py`
2. Implementing `MCPProvider` interface
3. Defining transport type (SSE or stdio)
4. Registry auto-discovers on next run

See [Creating Providers Guide](../guides/creating-providers.md).

## Related Documentation

- [Gateway Implementation Details](gateway.md)
- [Tool Routing Deep Dive](routing.md)
- [MCP Protocol Models](../../mcp/protocol.py)
