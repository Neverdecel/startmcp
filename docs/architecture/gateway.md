
# MCP Gateway Architecture

## Overview

The **MCP Gateway** transforms startmcp from a multi-client framework into a **unified MCP server** that aggregates multiple backend MCP providers.

## Architecture Diagram

```
┌──────────────────┐
│   AI Assistant   │  (Claude Desktop, Cursor, etc.)
│   (MCP Host)     │
└────────┬─────────┘
         │ Single connection
         ▼
┌─────────────────────────────────────────────────┐
│            startmcp Gateway                      │
│         (Acts as MCP Server)                     │
│                                                   │
│  ┌─────────────────────────────────────────┐    │
│  │   Request Handler (JSON-RPC 2.0)        │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                             │
│  ┌──────────────────▼──────────────────────┐    │
│  │   Tool Aggregator                       │    │
│  │   • Collect tools from all providers    │    │
│  │   • Detect name conflicts               │    │
│  │   • Apply hybrid namespacing            │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                             │
│  ┌──────────────────▼──────────────────────┐    │
│  │   Tool Router                           │    │
│  │   • Parse tool names                    │    │
│  │   • Route to correct provider           │    │
│  │   • Handle ambiguity errors             │    │
│  └──────────────────┬──────────────────────┘    │
│                     │                             │
│  ┌──────────────────▼──────────────────────┐    │
│  │   Resource Router                       │    │
│  │   • URI-based routing                   │    │
│  │   • Provider prefix parsing             │    │
│  └──────────────────┬──────────────────────┘    │
└──────────────────────┼──────────────────────────┘
                       │
         ┌─────────────┴─────────────┬───────────────┐
         │                           │               │
         ▼                           ▼               ▼
   ┌──────────┐              ┌──────────┐      ┌──────────┐
   │Atlassian │              │  GitHub  │      │Postgres  │
   │   MCP    │              │   MCP    │      │   MCP    │
   │  Server  │              │  Server  │      │  Server  │
   └──────────┘              └──────────┘      └──────────┘
```

## Core Components

### 1. MCP Server (stdio)

**File:** `mcp/server/stdio_server.py`

**Purpose:** Accepts JSON-RPC 2.0 requests from AI assistants via stdin/stdout.

**Responsibilities:**
- Read JSON-RPC requests from stdin
- Validate request format
- Dispatch to registered handlers
- Write JSON-RPC responses to stdout
- Handle protocol errors

### 2. Gateway Orchestrator

**File:** `mcp/gateway.py`

**Purpose:** Coordinates all components and implements MCP protocol.

**Lifecycle:**
1. Load config from `config.yaml`
2. Connect to all enabled providers
3. Initialize aggregators and routers
4. Register protocol handlers
5. Serve requests from AI assistant
6. Shut down gracefully

**Key Methods:**
- `handle_tools_list()` - Return aggregated tools
- `handle_tools_call()` - Route tool execution
- `handle_resources_list()` - Return aggregated resources
- `handle_resources_read()` - Route resource reads

### 3. Tool Aggregator

**File:** `mcp/aggregator.py`

**Purpose:** Collect and merge tools from all providers.

**Hybrid Namespacing Algorithm:**

```python
# Step 1: Collect all tools
for provider in providers:
    tools = await provider.list_tools()

# Step 2: Detect conflicts
tool_counts = count_by_name(all_tools)
conflicts = {name for name, count in tool_counts.items() if count > 1}

# Step 3: Apply namespacing
for tool in all_tools:
    if tool.name in conflicts:
        # Conflict - namespace it
        tool.name = f"{provider.name}:{tool.name}"
        tool.namespace_reason = "conflict"
    else:
        # No conflict - keep natural name
        tool.namespace_reason = None
```

**Example Output:**

```python
[
    Tool(name="search_issues", provider="atlassian", namespace_reason=None),
    Tool(name="get_page", provider="atlassian", namespace_reason=None),
    Tool(name="atlassian:list_projects", provider="atlassian", namespace_reason="conflict"),
    Tool(name="github:list_projects", provider="github", namespace_reason="conflict"),
    Tool(name="create_pr", provider="github", namespace_reason=None),
]
```

### 4. Tool Router

**File:** `mcp/router.py`

**Purpose:** Route tool calls to the correct provider.

**Routing Logic:**

```python
def route_tool_call(tool_name):
    # Check if explicitly namespaced
    if ":" in tool_name:
        provider_name, actual_name = tool_name.split(":", 1)
        return route_to_provider(provider_name, actual_name)

    # Look up in aggregator
    if tool_name is unique:
        return route_to_provider(unique_provider, tool_name)
    else:
        raise AmbiguousToolError(tool_name, suggestions)
```

**Error Handling:**

When a tool is ambiguous:
```json
{
  "error": {
    "code": -32000,
    "message": "Tool 'list_projects' exists in multiple providers",
    "data": {
      "available_tools": ["atlassian:list_projects", "github:list_projects"],
      "suggestion": "Please specify provider using: atlassian:list_projects"
    }
  }
}
```

### 5. Resource Router

**File:** `mcp/router.py` (ResourceRouter class)

**Purpose:** Route resource operations based on URI scheme.

**URI Format:**
```
<provider>://<resource_path>

Examples:
  atlassian://PROJ-123
  github://owner/repo/issues/42
  postgres://database/table/row
```

**Routing:**
1. Parse URI scheme → Extract provider name
2. Validate provider is connected
3. Strip provider prefix
4. Forward to provider with original path

### 6. Conflict Resolver

**File:** `mcp/conflict_resolver.py`

**Purpose:** Generate helpful error messages for ambiguous requests.

**Features:**
- Suggest similar tool names
- List all available variants for conflicting tools
- Provide examples of correct usage
- Generate conflict summary reports

## Configuration

**config.yaml:**
```yaml
enabled_providers:
  - atlassian
  - github
  - postgres

atlassian:
  client_id: "your-client-id"

github:
  default_org: "mycompany"

postgres:
  database: "production"
```

## Usage

### Start Gateway Server

```bash
mcp serve --stdio
```

### Configure AI Assistant

**Claude Desktop config** (`~/.config/claude/config.json`):
```json
{
  "mcpServers": {
    "startmcp": {
      "command": "mcp",
      "args": ["serve", "--stdio"]
    }
  }
}
```

### AI Interaction Examples

**List all tools:**
```
AI → startmcp: tools/list
startmcp → AI: [search_issues, atlassian:list_projects, github:list_projects, ...]
```

**Call unique tool (no namespace needed):**
```
AI → startmcp: tools/call { name: "search_issues", arguments: { jql: "..." } }
startmcp → Atlassian MCP → Result
```

**Call conflicting tool (must namespace):**
```
AI → startmcp: tools/call { name: "github:list_projects", arguments: {} }
startmcp → GitHub MCP → Result
```

**Error on ambiguous call:**
```
AI → startmcp: tools/call { name: "list_projects" }
startmcp → AI: ERROR: Ambiguous. Use "atlassian:list_projects" or "github:list_projects"
```

## Performance Considerations

### Tool List Caching

Tools are aggregated once on startup and cached:
- Avoids repeated backend queries
- Fast response to `tools/list`
- Refresh on provider connection changes

### Parallel Provider Queries

When listing resources, query all providers in parallel:
```python
results = await asyncio.gather(*[p.list_resources() for p in providers])
```

### Connection Pooling

Maintain persistent connections to backend MCP servers:
- Reuse HTTP connections (for SSE providers)
- Keep stdio processes alive
- Reconnect automatically on failure

## Comparison: Gateway vs Multi-Client

### Before (Multi-Client)

**AI Assistant Config:**
```json
{
  "mcpServers": {
    "atlassian": { "command": "atlassian-mcp" },
    "github": { "command": "github-mcp" },
    "postgres": { "command": "postgres-mcp" }
  }
}
```

**Pros:**
- Simple architecture
- No aggregation overhead
- Direct provider access

**Cons:**
- AI manages 3 connections
- User configures 3 servers
- No unified tool namespace
- Possible tool name collisions

### After (Gateway)

**AI Assistant Config:**
```json
{
  "mcpServers": {
    "startmcp": { "command": "mcp serve" }
  }
}
```

**Pros:**
- Single connection
- Unified configuration
- Automatic conflict resolution
- Metadata enrichment
- Centralized auth

**Cons:**
- Additional routing layer
- Slightly more complex

## Future Enhancements

- [ ] Query routing with NLP
- [ ] Result aggregation across providers
- [ ] Provider health monitoring
- [ ] Dynamic provider loading
- [ ] WebSocket transport for remote access
- [ ] Rate limiting per provider
- [ ] Request/response logging
- [ ] Metrics and analytics
