# Contributing to startmcp

Thank you for considering contributing to startmcp! This document provides guidelines for contributing to the project.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/yourusername/startmcp.git
   cd startmcp
   ```
3. **Create a virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
4. **Install in development mode**:
   ```bash
   pip install -e ".[dev]"
   ```
5. **Create a branch** for your changes:
   ```bash
   git checkout -b feature/my-feature
   ```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=mcp tests/

# Run specific test file
pytest tests/unit/test_gateway.py

# Run with verbose output
pytest -v tests/
```

### Code Style

We use standard Python tooling:

- **Black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

Run before committing:

```bash
# Format code
black mcp/ tests/

# Sort imports
isort mcp/ tests/

# Check linting
flake8 mcp/ tests/

# Type check
mypy mcp/
```

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add GitHub provider
fix: resolve tool routing issue
docs: update architecture guide
test: add aggregator unit tests
refactor: simplify conflict resolution
```

Types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `chore`

## Adding a New Provider

See [Creating Providers Guide](docs/guides/creating-providers.md) for detailed instructions.

Quick steps:

1. Create provider directory:
   ```
   provider_mcps/<category>/<provider_name>/
   ├── __init__.py
   ├── provider.py
   └── config.py
   ```

2. Implement provider class:
   ```python
   from mcp.provider import MCPProvider

   class MyProvider(MCPProvider):
       name = "my_provider"
       display_name = "My Provider"
       category = ProviderCategory.CUSTOM
       transport_type = "sse"  # or "stdio"

       async def create_transport(self):
           # Implementation
           pass
   ```

3. Add tests in `tests/unit/test_<provider_name>.py`

4. Update documentation

## Pull Request Process

1. **Update tests** - Add tests for new features
2. **Update docs** - Document new functionality
3. **Run tests** - Ensure all tests pass
4. **Update CHANGELOG.md** - Add entry under `[Unreleased]`
5. **Push changes** to your fork
6. **Create Pull Request** with:
   - Clear title and description
   - Reference to related issues
   - Screenshots (if UI changes)

### PR Review Criteria

- Tests pass
- Code follows style guidelines
- Documentation updated
- Commit messages follow convention
- No merge conflicts

## Bug Reports

When filing a bug report, include:

- **Description** - What happened vs. what should happen
- **Steps to reproduce** - Minimal example
- **Environment** - Python version, OS, dependency versions
- **Logs** - Error messages and stack traces

## Feature Requests

For feature requests, describe:

- **Use case** - What problem does it solve?
- **Proposed solution** - How should it work?
- **Alternatives** - Other approaches considered

## Code of Conduct

Be respectful and inclusive. We welcome contributions from everyone regardless of experience level.

## Questions?

- Open a [GitHub Discussion](https://github.com/yourusername/startmcp/discussions)
- Check existing issues and PRs
- Read the [documentation](docs/)

Thank you for contributing! 🎉
