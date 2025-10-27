# Quick Start Guide

## Installation

### 1. Install in Development Mode

```bash
# Install with dependencies
pip install -e ".[dev]"
```

This will:
- Install all required dependencies
- Set up the `mcp` CLI command
- Install development tools (pytest, black, ruff, mypy)

### 2. Verify Installation

```bash
# Check version
mcp version

# View help
mcp --help
```

## First Steps

### 1. Run Interactive Setup

```bash
mcp init
```

This wizard will:
1. Show available providers grouped by category
2. Let you select which providers to enable
3. Guide you through authentication (OAuth or API keys)
4. Save configuration to `config.yaml`

### 2. List Available Providers

```bash
# List all providers
mcp providers list

# List only enabled providers
mcp providers list --enabled

# Filter by category
mcp providers list --category enterprise
```

### 3. Enable a Provider

```bash
# Enable GitHub provider (example)
mcp providers enable github

# Enable Atlassian with OAuth
mcp providers enable atlassian
```

### 4. Validate Configuration

```bash
# Validate all enabled providers
mcp validate

# Validate specific provider
mcp validate --provider atlassian
```

## Configuration Files

### config.yaml

```yaml
enabled_providers:
  - atlassian
  - github

atlassian:
  default_project: "PROJ"
  endpoint: "https://mcp.atlassian.com/v1/sse"

github:
  default_org: "mycompany"

logging:
  level: "INFO"
  format: "json"

timeouts:
  connection: 30
  request: 60
```

### .env

```bash
# API keys and secrets
GITHUB_TOKEN=ghp_xxxxx
FIRECRAWL_API_KEY=xxxxx

# OAuth tokens are stored automatically
ATLASSIAN_ACCESS_TOKEN=xxxxx
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=mcp --cov-report=html

# Run specific test file
pytest tests/unit/test_client.py

# Run with verbose output
pytest -v
```

## Development Tools

### Code Formatting

```bash
# Format code with black
black mcp/ tests/

# Lint with ruff
ruff check mcp/ tests/
```

### Type Checking

```bash
# Type check with mypy
mypy mcp/
```

## Project Structure

```
startmcp/
├── mcp/                     # Core framework
│   ├── client.py           # MCP client
│   ├── provider.py         # Provider base class
│   ├── protocol.py         # JSON-RPC protocol models
│   ├── config.py           # Configuration management
│   ├── cli/                # CLI commands
│   │   ├── main.py        # Main CLI
│   │   └── wizard.py      # Setup wizard
│   ├── transport/          # Transport layer
│   │   ├── sse.py         # SSE transport
│   │   └── stdio.py       # stdio transport
│   └── auth/               # Authentication
│       ├── oauth.py       # OAuth 2.1 flow
│       └── api_key.py     # API key auth
├── provider-mcps/          # Provider implementations
│   └── enterprise/
│       └── atlassian/     # Atlassian provider
├── tests/                  # Test suite
│   ├── conftest.py        # Test fixtures
│   └── unit/              # Unit tests
├── config.yaml             # Configuration
├── .env                    # Secrets (gitignored)
└── pyproject.toml         # Project metadata
```

## Next Steps

1. **Add More Providers**: Implement additional providers in `provider-mcps/`
2. **Extend Functionality**: Add query routing and aggregation
3. **Run Examples**: Create example scripts using the client
4. **Contribute**: Submit providers or improvements!

## Troubleshooting

### OAuth Flow Issues

If OAuth authentication fails:
1. Check that port 8734 is available
2. Verify client_id is correct
3. Ensure browser can access localhost:8734

### Import Errors

If you see import errors:
```bash
# Reinstall in editable mode
pip install -e .
```

### Test Failures

If tests fail:
```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests with more output
pytest -vv
```

## Getting Help

- Check the [main README](README.md)
- Review [project architecture](docs/project.md)
- See [problem statement](problem-statement.md)
- Report issues on GitHub
