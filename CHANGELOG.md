# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

#### Core Framework
- MCP gateway server with tool aggregation and routing
- JSON-RPC 2.0 protocol implementation
- MCP protocol models (Resource, Tool, Prompt, etc.)
- SSE and stdio transport layers
- MCP client with full protocol support
- Provider base class and plugin architecture
- Dynamic provider registry with auto-discovery
- OAuth 2.1 with PKCE authentication
- Configuration management (YAML + environment variables)

#### Gateway Features
- Tool aggregation from multiple providers
- Hybrid namespacing (natural names when unique, prefixed on conflicts)
- Smart tool routing to correct backend
- Resource routing with provider-prefixed URIs
- Conflict detection and resolution
- Helpful error messages with suggestions

#### Server
- stdio MCP server implementation
- Background request/response handling
- Graceful subprocess management
- Proper cleanup and shutdown

#### CLI & UX
- Interactive setup wizard with rich formatting
- Provider selection by category
- Browser-based OAuth flow during setup
- Connection verification
- Commands: `init`, `serve`, `providers list`

#### Providers
- Atlassian Suite provider (Jira, Confluence, Compass)
  - Integration with official mcp-remote proxy
  - Automatic OAuth via browser
  - 27 tools for Jira and Confluence operations
  - stdio transport with subprocess management

#### Testing
- Comprehensive unit tests (protocol, client, config, provider, aggregator, router)
- Integration tests (end-to-end gateway functionality)
- Test fixtures and mocking utilities

#### Documentation
- README with gateway architecture overview
- Getting started guides
- Architecture documentation
- Tool routing guide
- Contributing guidelines
- Changelog (this file)

### Fixed
- Tool schema parsing: accept both `inputSchema` (camelCase) and `input_schema` (snake_case)
- Tool schema made optional (defaults to empty dict)
- Subprocess cleanup: graceful stdin close before termination
- Import compatibility: renamed `provider-mcps/` to `provider_mcps/` for Python imports

### Technical Details
- Python 3.12+ required
- Dependencies: pydantic, httpx, typer, questionary, rich, authlib, pytest
- 6,900+ lines of code
- 39 Python modules
- 9 test files

## [0.1.0] - TBD

Initial development release.

---

[Unreleased]: https://github.com/yourusername/startmcp/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/yourusername/startmcp/releases/tag/v0.1.0
