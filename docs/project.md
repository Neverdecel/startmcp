# startmcp - Project Architecture

## 🏗️ System Architecture

### Overview

**startmcp** is an MCP (Model Context Protocol) client that connects to multiple MCP servers (provider-mcps). It acts as a universal adapter between AI assistants and external data sources.

```
┌─────────────────────────────────────────────────────────────┐
│                    startmcp (MCP Client)                     │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │             Interactive CLI Wizard                     │  │
│  │  • Provider selection (categorized)                    │  │
│  │  • OAuth browser flow                                  │  │
│  │  • Configuration management                            │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │             MCP Client Core                            │  │
│  │  • Protocol message handling (JSON-RPC 2.0)            │  │
│  │  • Resource/Tool/Prompt management                     │  │
│  │  • Connection lifecycle                                │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │             Transport Layer                            │  │
│  │  • SSE (Server-Sent Events) - for remote servers       │  │
│  │  • stdio - for local processes                         │  │
│  │  • Future: WebSocket support                           │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │             Authentication Layer                       │  │
│  │  • OAuth 2.1 browser flow (SSE providers)              │  │
│  │  • API key management (stdio providers)                │  │
│  │  • Token refresh & storage                             │  │
│  └────────────────────────────────────────────────────────┘  │
│                            │                                  │
│  ┌────────────────────────────────────────────────────────┐  │
│  │             Provider Manager                           │  │
│  │  • Dynamic provider loading                            │  │
│  │  • Enable/disable functionality                        │  │
│  │  • Health checks & validation                          │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
            │              │              │              │
            ▼              ▼              ▼              ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
    │  Atlassian   │ │  GitHub  │ │   AWS    │ │ Custom   │
    │     MCP      │ │   MCP    │ │   MCP    │ │   MCP    │
    │    (SSE)     │ │ (stdio)  │ │  (SSE)   │ │ (stdio)  │
    └──────────────┘ └──────────┘ └──────────┘ └──────────┘
```

---

## 📦 Core Components

### 1. **MCP Client (`mcp/client.py`)**

The core MCP protocol implementation.

**Responsibilities:**
- Send/receive JSON-RPC 2.0 messages
- Handle MCP protocol methods:
  - `resources/list` - List available data sources
  - `resources/read` - Read resource content
  - `tools/list` - List available tools
  - `tools/call` - Execute a tool
  - `prompts/list` - List available prompts
  - `prompts/get` - Get prompt template

**Key Methods:**
```python
class MCPClient:
    async def connect(self, provider: MCPProvider)
    async def list_resources(self) -> List[Resource]
    async def read_resource(self, uri: str) -> ResourceContent
    async def call_tool(self, name: str, args: dict) -> ToolResult
    async def list_prompts(self) -> List[Prompt]
```

---

### 2. **Provider Base Class (`mcp/provider.py`)**

Abstract base class for all provider-mcps.

**Interface:**
```python
class MCPProvider(ABC):
    # Metadata
    name: str                    # Unique identifier
    category: str                # Category for UI
    display_name: str            # Human-readable name
    icon: str                    # Emoji/icon
    transport_type: str          # "sse" or "stdio"
    requires_oauth: bool         # OAuth flow required?

    # Configuration
    config_class: Type[BaseModel]

    # Lifecycle
    @abstractmethod
    async def connect(self):
        """Initialize connection to MCP server"""

    @abstractmethod
    async def disconnect(self):
        """Clean up connection"""

    # MCP Protocol Methods
    @abstractmethod
    async def list_resources(self) -> List[Resource]:
        """List available resources from this provider"""

    @abstractmethod
    async def list_tools(self) -> List[Tool]:
        """List available tools from this provider"""

    # Health & Validation
    async def health_check(self) -> bool:
        """Check if provider is healthy"""

    async def validate_config(self) -> bool:
        """Validate provider configuration"""
```

---

### 3. **Transport Layer (`mcp/transport/`)**

Abstraction over different transport mechanisms.

#### **SSE Transport (`sse.py`)**
For remote MCP servers using Server-Sent Events.

```python
class SSETransport:
    async def connect(self, endpoint: str, headers: dict)
    async def send_request(self, message: dict) -> dict
    async def listen(self) -> AsyncIterator[dict]
    async def disconnect(self)
```

**Used by:** Atlassian, remote cloud services

#### **stdio Transport (`stdio.py`)**
For local MCP servers running as subprocess.

```python
class StdioTransport:
    async def connect(self, command: List[str])
    async def send_request(self, message: dict) -> dict
    async def listen(self) -> AsyncIterator[dict]
    async def disconnect(self)
```

**Used by:** Local tools, file system access, local databases

---

### 4. **Authentication Layer (`mcp/cli/auth.py`)**

Handles OAuth 2.1 browser-based authentication for SSE providers.

**OAuth Flow:**
1. Start local HTTP server on `localhost:8734`
2. Generate authorization URL with PKCE
3. Open system browser to auth page
4. Wait for callback with authorization code
5. Exchange code for access token
6. Store token securely

```python
class OAuth2BrowserFlow:
    async def authenticate(self) -> str:
        """Run OAuth flow and return access token"""

    async def refresh_token(self, refresh_token: str) -> str:
        """Refresh expired access token"""
```

---

### 5. **Interactive CLI Wizard (`mcp/cli/wizard.py`)**

User-friendly setup experience using `questionary`.

**Wizard Steps:**
1. Show categorized provider list with checkboxes
2. For each selected provider:
   - If OAuth required → launch browser flow
   - If API key required → prompt securely
   - Validate credentials
3. Generate `config.yaml` and `.env`
4. Show success summary

```python
class SetupWizard:
    async def run(self):
        """Run interactive setup wizard"""

    def select_providers(self) -> List[str]:
        """Show categorized provider selection"""

    async def configure_provider(self, provider: MCPProvider):
        """Configure individual provider"""
```

---

### 6. **Configuration System (`mcp/config.py`)**

Simple, flat configuration management.

**Files:**
- `config.yaml` - Enabled providers and settings
- `.env` - Credentials (gitignored)

```python
class Config:
    enabled_providers: List[str]
    provider_settings: Dict[str, Dict[str, Any]]

    @classmethod
    def load(cls) -> Config:
        """Load from config.yaml and .env"""

    def save(self):
        """Save to config.yaml"""
```

---

## 🔌 Provider Categories

### 🏢 **Enterprise & Collaboration** (`provider-mcps/enterprise/`)

**Purpose:** Connect to company SaaS tools

**Examples:**
- **Atlassian** - Jira tickets, Confluence pages, Compass components
- **GitHub** - Repos, issues, PRs, code search
- **GitLab** - Projects, merge requests, CI/CD
- **Slack** - Messages, channels, users

**Typical Transport:** SSE with OAuth

---

### 🛠️ **Development Tools** (`provider-mcps/dev_tools/`)

**Purpose:** AI coding assistants and code analysis

**Examples:**
- **Claude Code** - AI pair programmer
- **Cursor** - IDE integration
- **Codex** - OpenAI code model

**Typical Transport:** stdio (local process)

---

### 💾 **Data Sources** (`provider-mcps/data/`)

**Purpose:** Database and data store access

**Examples:**
- **PostgreSQL** - SQL queries
- **MongoDB** - Document queries
- **Elasticsearch** - Search and analytics
- **Redis** - Cache access

**Typical Transport:** stdio (local connection)

---

### ☁️ **Cloud Platforms** (`provider-mcps/cloud/`)

**Purpose:** Cloud resource management

**Examples:**
- **AWS** - EC2, S3, Lambda, RDS
- **Azure** - VMs, Storage, Functions
- **GCP** - Compute Engine, Cloud Storage

**Typical Transport:** SSE with OAuth or API keys

---

### 🌐 **Web Services** (`provider-mcps/web/`)

**Purpose:** Web scraping and search

**Examples:**
- **FireCrawl** - Web scraping API
- **Serper** - Google Search API
- **Brave Search** - Privacy-focused search

**Typical Transport:** stdio with API keys

---

## 🔄 MCP Protocol Flow

### Example: Querying Jira Tickets

```
User: "Show my open Jira tickets"
  │
  ▼
┌─────────────────────────────────────┐
│  startmcp CLI                       │
│  mcp query "show my open tickets"   │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│  Query Router                       │
│  • Determines relevant providers    │
│  • Routes to Atlassian provider     │
└─────────────────────────────────────┘
  │
  ▼
┌─────────────────────────────────────┐
│  Atlassian Provider                 │
│  • Formats MCP request              │
│  • Sends via SSE transport          │
└─────────────────────────────────────┘
  │
  │ JSON-RPC 2.0 over SSE
  │
  ▼
┌─────────────────────────────────────┐
│  Atlassian MCP Server               │
│  https://mcp.atlassian.com/v1/sse   │
│  • Authenticates via OAuth token    │
│  • Queries Jira API                 │
│  • Returns resources                │
└─────────────────────────────────────┘
  │
  │ Response
  │
  ▼
┌─────────────────────────────────────┐
│  startmcp CLI                       │
│  • Formats response                 │
│  • Displays to user                 │
└─────────────────────────────────────┘
```

**JSON-RPC Message Example:**

Request:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "search_issues",
    "arguments": {
      "jql": "assignee=currentUser() AND status='Open'"
    }
  }
}
```

Response:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "result": {
    "content": [
      {
        "type": "text",
        "text": "Found 5 open tickets:\n- PROJ-123: Fix login bug\n- PROJ-124: Add export feature\n..."
      }
    ]
  }
}
```

---

## 🧩 Extension Points

### Adding New Provider Categories

1. Create directory: `provider-mcps/new_category/`
2. Add category metadata to `mcp/categories.py`
3. Providers automatically discovered

### Custom Transport Types

Implement `Transport` interface in `mcp/transport/base.py`:

```python
class CustomTransport(Transport):
    async def connect(self, config: dict)
    async def send_request(self, message: dict) -> dict
    async def disconnect(self)
```

### Custom Authentication Methods

Extend `AuthHandler` in `mcp/cli/auth.py`:

```python
class APIKeyAuth(AuthHandler):
    async def authenticate(self) -> str:
        # Custom auth logic
        pass
```

---

## 📊 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| CLI | `typer`, `questionary`, `rich` | Interactive CLI |
| HTTP | `httpx`, `aiohttp` | SSE connections |
| Protocol | `pydantic` | Message validation |
| Config | `pyyaml`, `python-dotenv` | Configuration |
| Testing | `pytest`, `pytest-asyncio` | Test framework |

---

## 🔐 Security Considerations

1. **Credentials Storage**
   - `.env` file gitignored by default
   - OAuth tokens stored encrypted (future)
   - API keys never logged

2. **OAuth Security**
   - PKCE (Proof Key for Code Exchange) used
   - State parameter for CSRF protection
   - Local callback server on `localhost` only

3. **Transport Security**
   - TLS 1.2+ required for SSE
   - Certificate validation enforced
   - Timeout on all network operations

---

## 🚀 Performance Optimizations

1. **Connection Pooling** - Reuse HTTP connections
2. **Lazy Loading** - Load providers only when needed
3. **Caching** - Cache provider metadata and auth tokens
4. **Async I/O** - All I/O operations async
5. **Rate Limiting** - Respect provider rate limits

---

## 📈 Future Enhancements

- [ ] WebSocket transport support
- [ ] Provider dependency resolution
- [ ] Query result caching
- [ ] Multi-provider query aggregation
- [ ] Plugin marketplace
- [ ] Web UI for configuration
- [ ] Docker containerization
- [ ] Provider health monitoring dashboard

---

## 🤝 Contributing

See provider development guide: [PROVIDER_GUIDE.md](PROVIDER_GUIDE.md)
