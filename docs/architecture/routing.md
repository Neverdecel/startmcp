# Tool Routing & Namespacing Guide

## Overview

The MCP Gateway uses **hybrid namespacing** to solve tool name conflicts while maintaining natural tool names when possible.

## Hybrid Namespacing Strategy

### Principle

> **Natural names for unique tools, namespaced only on conflicts**

### Algorithm

1. **Collect** all tools from all providers
2. **Detect** which tool names appear in multiple providers
3. **Namespace** only the conflicting tools with `provider:tool_name`
4. **Keep** natural names for unique tools

### Example

**Providers:**
- Atlassian: `search_issues`, `get_page`, `list_projects`
- GitHub: `create_pr`, `list_issues`, `list_projects`
- PostgreSQL: `query_table`, `get_schema`

**Conflicts:**
- `list_projects` appears in both Atlassian and GitHub

**Aggregated Tools:**
```
✓ search_issues (atlassian) - Natural name
✓ get_page (atlassian) - Natural name
✓ atlassian:list_projects (atlassian) - Namespaced due to conflict
✓ create_pr (github) - Natural name
✓ list_issues (github) - Natural name
✓ github:list_projects (github) - Namespaced due to conflict
✓ query_table (postgres) - Natural name
✓ get_schema (postgres) - Natural name
```

## Using Tools from AI

### Unique Tools (No Namespace Needed)

When a tool name is unique across all providers, use the natural name:

```json
{
  "method": "tools/call",
  "params": {
    "name": "search_issues",
    "arguments": {
      "jql": "project = DEMO AND status = Open"
    }
  }
}
```

The gateway automatically routes to the correct provider (Atlassian in this case).

### Conflicting Tools (Namespace Required)

When multiple providers have the same tool name, you **must** use the namespaced form:

```json
{
  "method": "tools/call",
  "params": {
    "name": "github:list_projects",
    "arguments": {
      "organization": "myorg"
    }
  }
}
```

### What Happens if You Use Natural Name for Conflicting Tool?

```json
{
  "method": "tools/call",
  "params": {
    "name": "list_projects"
  }
}
```

**Error Response:**
```json
{
  "error": {
    "code": -32000,
    "message": "Tool 'list_projects' exists in multiple providers",
    "data": {
      "error_type": "ambiguous_tool",
      "available_tools": [
        "atlassian:list_projects",
        "github:list_projects"
      ],
      "suggestion": "Please specify provider using one of: atlassian:list_projects, github:list_projects",
      "example": "Use 'atlassian:list_projects' instead of 'list_projects'"
    }
  }
}
```

## Tool Metadata

All tools in gateway mode include metadata to help the AI choose appropriately:

```json
{
  "name": "search_issues",
  "description": "Search Jira issues using JQL",
  "input_schema": { ... },
  "provider": "atlassian",
  "category": "enterprise",
  "namespace_reason": null
}
```

```json
{
  "name": "atlassian:list_projects",
  "description": "List all Jira projects",
  "input_schema": { ... },
  "provider": "atlassian",
  "category": "enterprise",
  "namespace_reason": "conflict"
}
```

**Metadata Fields:**
- `provider` - Provider name that owns this tool
- `category` - Provider category (enterprise, dev_tools, data, etc.)
- `namespace_reason` - Either `"conflict"` or `null`

## Resource Routing

Resources use **provider-prefixed URIs** for explicit routing:

### URI Format

```
<provider>://<resource_path>
```

### Examples

```
atlassian://PROJ-123
github://owner/repo/issues/42
postgres://database/public/users/1
firecrawl://https://example.com
```

### Reading a Resource

```json
{
  "method": "resources/read",
  "params": {
    "uri": "atlassian://PROJ-123"
  }
}
```

The gateway:
1. Parses `atlassian://` → Routes to Atlassian provider
2. Strips prefix → Passes `PROJ-123` to Atlassian MCP
3. Returns content

### Invalid URIs

```json
{
  "method": "resources/read",
  "params": {
    "uri": "PROJ-123"
  }
}
```

**Error:**
```json
{
  "error": {
    "message": "Invalid resource URI. Expected: <provider>://<path>"
  }
}
```

## Best Practices

### For AI Assistants

1. **Always check tool metadata** to understand provider ownership
2. **Use natural names when possible** for better UX
3. **Handle ambiguity errors gracefully** by retrying with namespaced form
4. **Cache conflict information** to avoid repeated errors

### Example AI Logic

```python
async def call_tool(name, args):
    try:
        # Try natural name first
        return await mcp_client.call_tool(name, args)
    except AmbiguousToolError as e:
        # Use first suggested namespaced form
        suggested = e.data["available_tools"][0]
        return await mcp_client.call_tool(suggested, args)
```

### For Provider Developers

1. **Use descriptive tool names** to minimize conflicts
2. **Document your tools clearly** in descriptions
3. **Follow naming conventions**:
   - `verb_noun` (e.g., `list_projects`, `create_issue`)
   - Avoid generic names like `search`, `get`, `list`
   - Add domain prefix when appropriate (e.g., `jira_search_issues`)

### For Users

1. **Enable only needed providers** to reduce potential conflicts
2. **Check conflict summary** after running `mcp serve`:
   ```
   ⚠ Tool conflicts detected: 3 tools have namespace prefix
   ```
3. **Use `mcp providers list`** to see which providers offer which tools

## Viewing Conflicts

### CLI Command

```bash
# Start server (shows conflicts on startup)
mcp serve --stdio
```

**Output:**
```
✓ Connected to atlassian
✓ Connected to github
✓ Gateway started with 2 providers
  Tools: 8
  Resources: 15
  ⚠ Tool conflicts detected: 1 tools have namespace prefix
```

### Programmatic Access

```python
from mcp.gateway import MCPGateway

gateway = MCPGateway(config)
await gateway.start()

# Get conflict info
conflicts = gateway.tool_aggregator.get_conflicting_tools()
# Returns: {"list_projects"}

# Get conflict summary
summary = gateway.conflict_resolver.get_conflict_summary()
# Returns detailed conflict information
```

## Future Enhancements

### Smart Routing (Planned)

Allow AI to call ambiguous tools and let gateway route based on context:

```python
# AI calls: "list_projects"
# Gateway analyzes recent context and arguments
# Routes to likely provider based on:
# - Recent provider usage
# - Argument patterns
# - User preferences
```

### Priority Configuration (Planned)

Allow users to specify default provider for ambiguous tools:

```yaml
routing_preferences:
  list_projects: atlassian  # Default to Atlassian
  search: github            # Default to GitHub
```

### Query Language (Future)

Natural language routing:

```
"list all projects in Jira" → atlassian:list_projects
"show GitHub projects" → github:list_projects
```
