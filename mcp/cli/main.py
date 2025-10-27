"""Main CLI entry point for startmcp."""

import asyncio
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from mcp.config import load_config, save_config
from mcp.registry import get_registry

app = typer.Typer(
    name="mcp",
    help="startmcp - MCP client framework for connecting AI tools to your data",
    no_args_is_help=True,
)

console = Console()


@app.command()
def init(
    reconfigure: bool = typer.Option(
        False, "--reconfigure", help="Reconfigure existing setup"
    ),
) -> None:
    """Initialize startmcp with interactive wizard."""
    from mcp.cli.wizard import SetupWizard

    wizard = SetupWizard()

    try:
        asyncio.run(wizard.run(reconfigure=reconfigure))
        console.print("✓ Setup complete!", style="bold green")
    except KeyboardInterrupt:
        console.print("\n✗ Setup cancelled", style="bold red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"✗ Setup failed: {e}", style="bold red")
        raise typer.Exit(1)


# Create providers subcommand group
providers_app = typer.Typer(
    help="Manage MCP providers",
    no_args_is_help=True,
)
app.add_typer(providers_app, name="providers")


@providers_app.command("list")
def list_providers(
    enabled_only: bool = typer.Option(
        False, "--enabled", help="Show only enabled providers"
    ),
    category: Optional[str] = typer.Option(None, "--category", help="Filter by category"),
) -> None:
    """List available MCP providers."""
    config = load_config()
    registry = get_registry()

    # Discover providers
    count = registry.discover_providers()
    if count == 0:
        console.print("No providers found", style="yellow")
        return

    # Group by category
    by_category = registry.list_by_category()

    for cat, providers in by_category.items():
        # Filter by category if specified
        if category and cat.value != category:
            continue

        # Filter by enabled if requested
        if enabled_only:
            providers = [
                p for p in providers if config.is_provider_enabled(p.name)
            ]
            if not providers:
                continue

        # Display category header
        from mcp.categories import get_category_display_name, get_category_icon

        console.print(
            f"\n{get_category_icon(cat)} {get_category_display_name(cat)}",
            style="bold cyan",
        )

        # Create table
        table = Table(show_header=True, header_style="bold")
        table.add_column("Name", style="cyan")
        table.add_column("Display Name")
        table.add_column("Description")
        table.add_column("Status")

        for provider_class in providers:
            status = (
                "[green]Enabled[/green]"
                if config.is_provider_enabled(provider_class.name)
                else "[dim]Disabled[/dim]"
            )
            table.add_row(
                provider_class.name,
                provider_class.display_name,
                provider_class.description,
                status,
            )

        console.print(table)


@providers_app.command("enable")
def enable_provider(
    name: str = typer.Argument(..., help="Provider name to enable"),
) -> None:
    """Enable a provider (runs configuration wizard for that provider)."""
    from mcp.cli.wizard import SetupWizard

    wizard = SetupWizard()

    try:
        asyncio.run(wizard.configure_single_provider(name))
        console.print(f"✓ Provider '{name}' enabled!", style="bold green")
    except KeyboardInterrupt:
        console.print("\n✗ Configuration cancelled", style="bold red")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"✗ Failed to enable provider: {e}", style="bold red")
        raise typer.Exit(1)


@providers_app.command("disable")
def disable_provider(
    name: str = typer.Argument(..., help="Provider name to disable"),
) -> None:
    """Disable a provider."""
    config = load_config()

    if not config.is_provider_enabled(name):
        console.print(f"Provider '{name}' is not enabled", style="yellow")
        return

    config.disable_provider(name)
    save_config(config)

    console.print(f"✓ Provider '{name}' disabled", style="bold green")


@app.command()
def validate(
    provider: Optional[str] = typer.Option(None, "--provider", help="Validate specific provider"),
) -> None:
    """Validate configuration and test connections."""
    config = load_config()
    registry = get_registry()
    registry.discover_providers()

    if provider:
        # Validate single provider
        providers_to_check = [provider]
    else:
        # Validate all enabled providers
        providers_to_check = config.enabled_providers

    if not providers_to_check:
        console.print("No providers to validate", style="yellow")
        return

    console.print("Validating providers...\n")

    async def validate_all() -> None:
        for provider_name in providers_to_check:
            console.print(f"Checking {provider_name}...", end=" ")

            try:
                # Get provider config
                provider_config = config.get_provider_config(provider_name)

                # Create provider instance
                provider_instance = registry.create_provider(
                    provider_name, provider_config
                )

                # Validate config
                config_valid = await provider_instance.validate_config()
                if not config_valid:
                    console.print("✗ Invalid configuration", style="bold red")
                    continue

                # Health check
                healthy = await provider_instance.health_check()
                if healthy:
                    console.print("✓ OK", style="bold green")
                else:
                    console.print("✗ Health check failed", style="bold red")

            except Exception as e:
                console.print(f"✗ Error: {e}", style="bold red")

    try:
        asyncio.run(validate_all())
    except KeyboardInterrupt:
        console.print("\n✗ Validation cancelled", style="bold red")
        raise typer.Exit(1)


@app.command()
def query(
    query_text: str = typer.Argument(..., help="Query text"),
    provider: Optional[str] = typer.Option(
        None, "--provider", "-p", help="Target specific provider"
    ),
) -> None:
    """Query enabled providers (TODO: implement query routing)."""
    console.print(
        "Query functionality coming soon! This will route queries to appropriate providers.",
        style="yellow",
    )
    console.print(f"Query: {query_text}")
    if provider:
        console.print(f"Target provider: {provider}")


@app.command()
def serve(
    stdio: bool = typer.Option(True, "--stdio", help="Use stdio transport"),
    sse: bool = typer.Option(False, "--sse", help="Use SSE transport (not yet implemented)"),
) -> None:
    """Start MCP gateway server (aggregates all enabled providers)."""
    from mcp.gateway import MCPGateway
    from mcp.server.stdio_server import StdioMCPServer

    if sse:
        console.print("SSE server not yet implemented. Use --stdio instead.", style="red")
        raise typer.Exit(1)

    config = load_config()

    if not config.enabled_providers:
        console.print("No providers enabled. Run 'mcp init' first.", style="yellow")
        raise typer.Exit(1)

    async def run_server() -> None:
        # Create gateway
        gateway = MCPGateway(config)

        # Create server
        server = StdioMCPServer()

        try:
            # Start gateway (connects to all providers)
            await gateway.start()

            # Register gateway handlers with server
            gateway.register_handlers(server)

            # Start server
            await server.start()

            # Keep running until interrupted
            while server.running:
                await asyncio.sleep(1)

        except KeyboardInterrupt:
            console.print("\nShutting down...", style="yellow")
        except Exception as e:
            console.print(f"Error: {e}", style="red")
            raise typer.Exit(1)
        finally:
            await server.stop()
            await gateway.stop()

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        pass


@app.command()
def version() -> None:
    """Show version information."""
    from mcp import __version__

    console.print(f"startmcp version {__version__}", style="bold cyan")


if __name__ == "__main__":
    app()
