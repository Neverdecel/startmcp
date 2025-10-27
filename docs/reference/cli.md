# CLI Reference

Complete reference for the `mcp` command-line interface.

## Global Options

```bash
mcp --help     # Show help message
mcp --version  # Show version
```

## Commands

### `mcp init`

Run the interactive setup wizard to configure providers.

**Usage:**
```bash
mcp init [OPTIONS]
```

**Options:**
- `--reconfigure` - Reconfigure existing setup (default: false)

**Examples:**
```bash
# First-time setup
mcp init

# Reconfigure (keeps existing config as defaults)
mcp init --reconfigure
```

**What it does:**
1. Discovers available providers
2. Shows categorized provider selection
3. Guides through authentication (OAuth, API keys)
4. Verifies connections
5. Saves configuration to `config.yaml`

---

### `mcp serve`

Start the MCP gateway server.

**Usage:**
```bash
mcp serve [OPTIONS]
```

**Options:**
- `--stdio` - Use stdio transport (default: true)
- `--sse` - Use SSE transport (not yet implemented)

**Examples:**
```bash
# Start server with stdio (for Claude Desktop, etc.)
mcp serve --stdio

# Server runs in foreground - press Ctrl+C to stop
```

**What it does:**
1. Loads `config.yaml`
2. Connects to all enabled providers
3. Aggregates tools and resources
4. Starts MCP server
5. Listens for JSON-RPC requests

**Output:**
```
Loading configuration...
Connecting to providers...
  ✓ atlassian (27 tools)
Starting MCP gateway server...
Server ready. Listening on stdio...
```

---

### `mcp providers list`

List available MCP providers.

**Usage:**
```bash
mcp providers list [OPTIONS]
```

**Options:**
- `--enabled` - Show only enabled providers
- `--category <CATEGORY>` - Filter by category

**Examples:**
```bash
# List all providers
mcp providers list

# List only enabled providers
mcp providers list --enabled

# List providers in specific category
mcp providers list --category enterprise
```

**Output:**
```
🏢 Enterprise & Collaboration

Name        Display Name      Description                           Status
─────────────────────────────────────────────────────────────────────────────
atlassian   Atlassian Suite   Connect to Jira, Confluence, Compass  ✓ Enabled

🛠️ Development Tools

Name        Display Name      Description                           Status
─────────────────────────────────────────────────────────────────────────────
github      GitHub            Repositories, issues, pull requests   Disabled
```

---

## Configuration File

The `config.yaml` file is created by `mcp init` and can be edited manually.

**Location:** `./config.yaml` (in current directory)

**Format:**
```yaml
enabled_providers:
  - atlassian
  - github

logging:
  level: INFO
  format: json

timeouts:
  connection: 30
  request: 60

# Provider-specific settings
atlassian:
  default_project: "PROJ"
  cloud_id: "your-cloud-id"

github:
  default_org: "mycompany"
  api_url: "https://api.github.com"
```

## Environment Variables

Provider credentials can be set via environment variables:

```bash
# Format: <PROVIDER_NAME>_<KEY>
export GITHUB_TOKEN=ghp_xxxxx
export FIRECRAWL_API_KEY=xxxxx

# Override config values
export ATLASSIAN_DEFAULT_PROJECT=PROJ
```

Environment variables take precedence over `config.yaml`.

## Exit Codes

- `0` - Success
- `1` - Error (check stderr for details)

## Logging

Configure logging in `config.yaml`:

```yaml
logging:
  level: DEBUG    # DEBUG, INFO, WARNING, ERROR
  format: json    # json or text
```

Or via environment:
```bash
export MCP_LOG_LEVEL=DEBUG
export MCP_LOG_FORMAT=text
```

## Examples

### Complete Setup Workflow

```bash
# 1. First-time setup
mcp init
# ... follow wizard prompts ...

# 2. Verify configuration
cat config.yaml

# 3. Test providers
mcp providers list --enabled

# 4. Start gateway
mcp serve --stdio

# ... in another terminal ...

# 5. Configure AI assistant (Claude Desktop)
cat > ~/.config/claude/config.json <<EOF
{
  "mcpServers": {
    "startmcp": {
      "command": "mcp",
      "args": ["serve", "--stdio"]
    }
  }
}
EOF
```

### Adding a New Provider

```bash
# 1. Enable new provider
mcp init --reconfigure

# 2. Select additional provider from wizard
# ... complete OAuth/API key setup ...

# 3. Restart gateway
# (if already running, stop with Ctrl+C first)
mcp serve --stdio
```

### Troubleshooting

```bash
# Enable debug logging
export MCP_LOG_LEVEL=DEBUG
mcp serve --stdio

# Check provider discovery
mcp providers list

# Verify config file
cat config.yaml

# Test connection to specific provider
# (via provider's health check)
python -c "
from mcp.registry import get_registry
from mcp.config import load_config

config = load_config()
registry = get_registry()
registry.discover_providers()

provider = registry.create_provider('atlassian', config.get_provider_config('atlassian'))

import asyncio
asyncio.run(provider.health_check())
"
```

## Integration with AI Assistants

### Claude Desktop

Add to `~/.config/claude/config.json`:
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

### Other MCP Clients

Any MCP-compatible client can connect to startmcp using stdio transport.

Provide:
- **Command**: `mcp`
- **Args**: `["serve", "--stdio"]`
- **Working Directory**: Directory containing `config.yaml`

## See Also

- [Getting Started Guide](../getting-started/quickstart.md)
- [Architecture Overview](../architecture/overview.md)
- [Creating Providers](../guides/creating-providers.md)
