# Installation Guide

## Prerequisites

- Python 3.12 or higher
- pip (Python package installer)
- Git

## Installation Steps

### 1. Install in Development Mode

From the project root directory:

```bash
pip install -e .
```

This installs startmcp in "editable" mode, making the `mcp` command available.

### 2. Install with Development Tools

For development (includes pytest, black, ruff, mypy):

```bash
pip install -e ".[dev]"
```

### 3. Verify Installation

Run the verification script:

```bash
python verify_install.py
```

Or manually check:

```bash
# Check the command is available
mcp --help

# Check version
mcp version
```

## Expected Output

After successful installation, you should see:

```
$ mcp --help

 Usage: mcp [OPTIONS] COMMAND [ARGS]...

 startmcp - MCP client framework for connecting AI tools to your data

╭─ Options ─────────────────────────────────────────╮
│ --help          Show this message and exit.       │
╰───────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────╮
│ init        Initialize startmcp with interactive  │
│             wizard.                                │
│ providers   Manage MCP providers                  │
│ query       Query enabled providers               │
│ validate    Validate configuration and test       │
│             connections.                           │
│ version     Show version information.             │
╰───────────────────────────────────────────────────╯
```

## Troubleshooting

### Command Not Found

If `mcp` command is not found:

```bash
# Reinstall with verbose output
pip install -e . -v

# Check if it's in your PATH
which mcp

# Try using python -m
python -m mcp.cli.main --help
```

### Import Errors

If you see import errors:

```bash
# Ensure all dependencies are installed
pip install -r requirements.txt

# Or reinstall
pip uninstall startmcp
pip install -e .
```

### Python Version Issues

Check your Python version:

```bash
python --version

# If too old, use python3.12 explicitly
python3.12 -m pip install -e .
```

### Virtual Environment (Recommended)

Use a virtual environment to avoid conflicts:

```bash
# Create venv
python3.12 -m venv venv

# Activate
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install
pip install -e ".[dev]"
```

## Next Steps

After successful installation:

1. Read [QUICKSTART.md](QUICKSTART.md) for usage guide
2. Run `mcp init` to set up providers
3. Check [BUILD_SUMMARY.md](BUILD_SUMMARY.md) for architecture overview

## Uninstallation

To remove startmcp:

```bash
pip uninstall startmcp
```

## Development Installation

For contributors:

```bash
# Clone repository
git clone https://github.com/yourusername/startmcp.git
cd startmcp

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black mcp/ tests/
ruff check mcp/ tests/

# Type check
mypy mcp/
```

## Docker Installation (Future)

Docker support coming in Phase 2:

```bash
# Build image
docker build -t startmcp .

# Run
docker run -it startmcp mcp init
```
