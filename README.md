# startmcp

> A flexible MCP (Model Context Protocol) client framework for connecting AI tools to your data and systems.

[![MCP Protocol](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

## 🎯 What is startmcp?

**startmcp** is a reusable framework that lets you quickly integrate AI assistants (Claude, Codex, etc.) with various backends (Atlassian, GitHub, databases, web services) through the [Model Context Protocol](https://modelcontextprotocol.io).

Think of it as a **universal adapter** for connecting AI tools to your data sources - just enable the providers you need through an interactive wizard.

### Key Features

- 🔌 **MCP Protocol Compliant** - Follows official specification
- 🧙 **Interactive Setup Wizard** - Beautiful CLI experience
- 🔐 **OAuth 2.1 Support** - Browser-based authentication with SSE
- 🏗️ **Modular Architecture** - Enable only what you need
- 📦 **Provider Categories** - Organized by purpose (Enterprise, Dev Tools, Data, Cloud, Web)
- 🚀 **Multi-Transport** - SSE and stdio support

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/yourusername/startmcp.git
cd startmcp
pip install -e .
```

### Initialize with Interactive Wizard

```bash
mcp init
```

The wizard will guide you through:
1. Selecting provider-mcps from categorized lists
2. Configuring OAuth flows (browser-based for services like Atlassian)
3. Setting up API keys and credentials
4. Saving configuration to `config.yaml`

### Query Your Data

```bash
# Query across all enabled providers
mcp query "show my open Jira tickets"

# List enabled providers
mcp providers list --enabled

# Validate configuration
mcp validate
```

## 📦 Available Provider-MCPs

### 🏢 Enterprise & Collaboration
- **Atlassian** - Jira, Confluence, Compass (SSE + OAuth)
- **GitHub** - Repositories, issues, pull requests
- **GitLab** - Projects, merge requests
- **Slack** - Channels, messages

### 🛠️ Development Tools
- **Claude Code** - AI coding assistant
- **Cursor** - Code editor integration
- **Codex** - OpenAI code model

### 💾 Data Sources
- **PostgreSQL** - Database queries
- **MongoDB** - Document database
- **Elasticsearch** - Search and analytics

### ☁️ Cloud Platforms
- **AWS** - EC2, S3, Lambda resources
- **Azure** - Resource management
- **GCP** - Google Cloud services

### 🌐 Web Services
- **FireCrawl** - Web scraping
- **Serper** - Search API

## 📁 Project Structure

```
startmcp/
├── mcp/                     # Core framework
│   ├── client.py           # MCP client implementation
│   ├── provider.py         # Provider base class
│   ├── cli/                # CLI and wizard
│   └── transport/          # SSE and stdio transports
├── provider-mcps/          # Available providers
│   ├── enterprise/         # Atlassian, GitHub, etc.
│   ├── dev_tools/          # AI coding tools
│   ├── data/               # Databases
│   ├── cloud/              # Cloud platforms
│   └── web/                # Web services
├── config.yaml             # Your configuration
└── .env                    # Credentials (gitignored)
```

## 🔧 Configuration

### config.yaml

```yaml
enabled_providers:
  - atlassian
  - github
  - firecrawl

atlassian:
  default_project: "PROJ"

github:
  default_org: "mycompany"
```

### .env

```bash
GITHUB_TOKEN=ghp_xxxxx
FIRECRAWL_API_KEY=xxxxx
# Atlassian uses OAuth (no manual token needed)
```

## 🛠️ CLI Commands

```bash
# Initial setup wizard
mcp init

# List all available providers
mcp providers list

# List enabled providers only
mcp providers list --enabled

# Enable a provider (runs wizard for that provider)
mcp providers enable github

# Disable a provider
mcp providers disable github

# Validate configuration and test connections
mcp validate

# Query across enabled providers
mcp query "your query here"

# Reconfigure (re-run wizard)
mcp init --reconfigure
```

## 🔌 Creating Custom Providers

See [docs/PROVIDER_GUIDE.md](docs/PROVIDER_GUIDE.md) for detailed instructions.

Quick example:

```python
# provider-mcps/custom/my_provider.py
from mcp.provider import MCPProvider
from pydantic import BaseModel

class MyProviderConfig(BaseModel):
    api_key: str

class MyProvider(MCPProvider):
    name = "my_provider"
    category = "custom"
    display_name = "My Custom Provider"
    transport_type = "sse"

    async def connect(self):
        # Your connection logic
        pass

    async def list_resources(self):
        # Return available resources
        pass
```

## 🤝 Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📚 Documentation

- [Project Architecture](docs/project.md)
- [Problem Statement](problem-statement.md)
- [Provider Development Guide](docs/PROVIDER_GUIDE.md)
- [MCP Compliance](docs/MCP_COMPLIANCE.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io) standard
- Inspired by the need for flexible AI-to-data integration

---

**Made with ❤️ for the AI engineering community**
