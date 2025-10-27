# startmcp

> Unified MCP gateway server that aggregates multiple backend providers into a single connection point for AI assistants.

[![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 What is startmcp?

**startmcp** is an MCP gateway server that connects AI assistants (like Claude) to multiple data sources through a single, unified interface.

### The Problem
AI assistants need to connect to multiple MCP servers (Atlassian, GitHub, databases, etc.), requiring separate configurations for each provider.

### The Solution
**startmcp** acts as a gateway that aggregates all your providers into one MCP server:

```
Before (Multiple Connections):          After (Single Gateway):
┌─────────────┐                         ┌─────────────┐
│ AI Assistant│                         │ AI Assistant│
└──────┬──────┘                         └──────┬──────┘
       │                                       │
   ┌───┴───┬───────┬───────┐                 │
   │       │       │       │                  │
┌──▼─┐  ┌─▼──┐  ┌─▼──┐  ┌─▼──┐         ┌───▼────────┐
│Atl.│  │GH  │  │ DB │  │ etc│         │  startmcp  │
│MCP │  │MCP │  │MCP │  │MCP │         │   Gateway  │
└────┘  └────┘  └────┘  └────┘         └────┬───────┘
                                             │
                                   ┌─────────┼────────┬─────┐
                                   │         │        │     │
                                ┌──▼─┐   ┌──▼──┐  ┌──▼─┐ ┌─▼──┐
                                │Atl.│   │ GH  │  │ DB │ │etc │
                                │MCP │   │ MCP │  │MCP │ │MCP │
                                └────┘   └─────┘  └────┘ └────┘
```

## ✨ Key Features

- **🎯 Single MCP Server** - One connection for all your providers
- **🔀 Smart Routing** - Tools route to the correct backend automatically
- **🏷️ Hybrid Namespacing** - Natural names when unique, prefixed only on conflicts
- **🔐 OAuth 2.1 Support** - Browser-based authentication
- **🧙 Interactive Wizard** - Beautiful CLI setup experience
- **📦 Plugin Architecture** - Easy to add custom providers
- **⚡ Near-Native Performance** - Minimal routing overhead (~5ms)

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/startmcp.git
cd startmcp

# Install with pip
pip install -e .

# Verify installation
mcp --help
```

### Setup

Run the interactive wizard:

```bash
mcp init
```

The wizard will:
1. Show available providers by category
2. Guide you through authentication (browser opens for OAuth)
3. Verify the connection works
4. Save configuration to `config.yaml`

### Start the Gateway

```bash
mcp serve --stdio
```

The gateway will:
- Load your `config.yaml`
- Connect to all enabled providers
- Aggregate tools from each provider
- Start the stdio MCP server
- Listen for requests from your AI assistant

### Connect Your AI Assistant

**For Claude Desktop**, add to `~/.config/claude/config.json`:

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

Restart Claude Desktop, and you'll have access to all your providers' tools!

## 🏗️ Architecture

startmcp implements a **gateway pattern** for MCP:

1. **Tool Aggregation** - Collects tools from all providers
2. **Conflict Detection** - Identifies tool name collisions
3. **Hybrid Namespacing** - Keeps natural names when possible:
   - `search_issues` → Routes to Atlassian (unique name)
   - `create_pr` → Routes to GitHub (unique name)
   - `atlassian:list_projects` → Explicit routing (conflict with GitHub)
   - `github:list_projects` → Explicit routing (conflict with Atlassian)
4. **Smart Routing** - Directs each tool call to the correct provider
5. **Helpful Errors** - Suggests correct tool names on ambiguity

See [Architecture Overview](docs/architecture/overview.md) for details.

## 📦 Available Providers

### 🏢 Enterprise
- **Atlassian Suite** - Jira, Confluence, Compass (OAuth via mcp-remote)

### 🚧 Coming Soon
- GitHub - Repositories, issues, PRs
- GitLab - Projects, merge requests
- PostgreSQL - Database queries
- MongoDB - Document operations
- And more...

## 🛠️ CLI Commands

```bash
# Interactive setup wizard
mcp init

# List all available providers
mcp providers list

# List only enabled providers
mcp providers list --enabled

# Start the gateway server
mcp serve --stdio

# Reconfigure setup
mcp init --reconfigure
```

## 📁 Project Structure

```
startmcp/
├── mcp/                        # Core framework
│   ├── protocol.py            # MCP protocol models
│   ├── client.py              # MCP client
│   ├── provider.py            # Provider base class
│   ├── transport/             # SSE and stdio transports
│   ├── server/                # MCP server implementation
│   ├── gateway.py             # Gateway orchestrator
│   ├── aggregator.py          # Tool aggregation
│   ├── router.py              # Tool/resource routing
│   ├── conflict_resolver.py   # Conflict detection
│   ├── registry.py            # Provider discovery
│   └── cli/                   # CLI and wizard
├── provider_mcps/             # Provider implementations
│   ├── enterprise/            # Atlassian, etc.
│   ├── dev_tools/             # GitHub, GitLab, etc.
│   ├── data/                  # Databases
│   ├── cloud/                 # AWS, GCP, Azure
│   └── web/                   # Web services
├── tests/                     # Unit and integration tests
├── docs/                      # Documentation
└── config.yaml               # Your configuration
```

## 🔧 Configuration

After running `mcp init`, your `config.yaml` will look like:

```yaml
enabled_providers:
  - atlassian

logging:
  level: INFO
  format: json

timeouts:
  connection: 30
  request: 60
```

Provider-specific settings can be added:

```yaml
atlassian:
  default_project: "PROJ"
  cloud_id: "your-cloud-id"
```

## 🧑‍💻 Creating Custom Providers

Create a new provider by extending `MCPProvider`:

```python
# provider_mcps/custom/my_provider/provider.py
from mcp.provider import MCPProvider
from mcp.categories import ProviderCategory

class MyProvider(MCPProvider):
    name = "my_provider"
    display_name = "My Custom Provider"
    category = ProviderCategory.CUSTOM
    transport_type = "sse"  # or "stdio"

    async def create_transport(self):
        # Return configured transport
        pass
```

See [Creating Providers Guide](docs/guides/creating-providers.md) for details.

## 📚 Documentation

- **Getting Started**
  - [Quick Start](docs/getting-started/quickstart.md)
  - [Installation Guide](docs/getting-started/installation.md)
- **Architecture**
  - [Overview](docs/architecture/overview.md)
  - [Gateway Design](docs/architecture/gateway.md)
  - [Tool Routing](docs/architecture/routing.md)
- **Guides**
  - [Creating Providers](docs/guides/creating-providers.md)
- **Reference**
  - [CLI Commands](docs/reference/cli.md)
- **Project Background**
  - [Problem Statement](problem-statement.md)
  - [Original Design](docs/project.md)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and release notes.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io) specification
- Atlassian provider uses [mcp-remote](https://www.npmjs.com/package/mcp-remote)
- Inspired by the need for unified AI-to-data integration

---

**Made with ❤️ for the AI engineering community**
