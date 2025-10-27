"""Interactive setup wizard for startmcp."""

from typing import Dict, List

import questionary
from rich.console import Console

from mcp.auth.api_key import get_token_store
from mcp.categories import (
    ProviderCategory,
    get_category_description,
    get_category_display_name,
    get_category_icon,
)
from mcp.config import Config, load_config, save_config
from mcp.exceptions import ConfigurationError
from mcp.provider import MCPProvider
from mcp.registry import get_registry

console = Console()


class SetupWizard:
    """Interactive wizard for configuring startmcp."""

    def __init__(self) -> None:
        """Initialize setup wizard."""
        self.config = Config()
        self.registry = get_registry()

    async def run(self, reconfigure: bool = False) -> None:
        """
        Run the complete setup wizard.

        Args:
            reconfigure: If True, reload existing config
        """
        # Welcome message
        console.print("\n[bold cyan]Welcome to startmcp![/bold cyan]")
        console.print(
            "This wizard will help you configure MCP providers for your AI tools.\n"
        )

        # Load existing config if reconfiguring
        if reconfigure:
            try:
                self.config = load_config()
                console.print("[yellow]Reconfiguring existing setup[/yellow]\n")
            except Exception:
                pass

        # Discover available providers
        console.print("Discovering providers...")
        count = self.registry.discover_providers()
        console.print(f"Found {count} providers\n")

        if count == 0:
            console.print("[red]No providers found![/red]")
            return

        # Select providers
        selected_providers = await self._select_providers()

        if not selected_providers:
            console.print("[yellow]No providers selected[/yellow]")
            return

        # Configure each selected provider
        for provider_name in selected_providers:
            console.print(f"\n[bold]Configuring {provider_name}...[/bold]")
            await self.configure_single_provider(provider_name, add_to_config=True)

        # Save configuration
        console.print("\n[bold]Saving configuration...[/bold]")
        save_config(self.config)
        console.print("Configuration saved to config.yaml")

    async def _select_providers(self) -> List[str]:
        """
        Show categorized provider selection.

        Returns:
            List of selected provider names
        """
        by_category = self.registry.list_by_category()
        choices = []

        # Build choices grouped by category
        for category in ProviderCategory:
            providers = by_category.get(category, [])
            if not providers:
                continue

            # Add category separator
            category_name = get_category_display_name(category)
            category_icon = get_category_icon(category)
            choices.append(
                questionary.Separator(f"\n{category_icon} {category_name}")
            )

            # Add providers in this category
            for provider_class in providers:
                # Check if already enabled
                enabled = provider_class.name in self.config.enabled_providers
                label = f"{provider_class.display_name} - {provider_class.description}"
                if enabled:
                    label += " [currently enabled]"

                choices.append(
                    questionary.Choice(
                        title=label,
                        value=provider_class.name,
                        checked=enabled,
                    )
                )

        # Show checkbox prompt
        selected = await questionary.checkbox(
            "Select providers to enable:",
            choices=choices,
        ).ask_async()

        return selected or []

    async def configure_single_provider(
        self, provider_name: str, add_to_config: bool = False
    ) -> None:
        """
        Configure a single provider.

        Args:
            provider_name: Provider name
            add_to_config: If True, enable provider in config

        Raises:
            ConfigurationError: If provider not found
        """
        # Get provider class
        provider_class = self.registry.get_provider_class(provider_name)
        if not provider_class:
            raise ConfigurationError(f"Provider '{provider_name}' not found")

        # Get existing config if any
        existing_config = self.config.get_provider_config(provider_name)

        # Configure based on provider type
        if provider_class.requires_oauth:
            await self._configure_oauth_provider(provider_class, existing_config)
        else:
            await self._configure_api_key_provider(provider_class, existing_config)

        # Enable provider
        if add_to_config:
            self.config.enable_provider(provider_name, existing_config)

    async def _configure_oauth_provider(
        self, provider_class: type[MCPProvider], config: Dict
    ) -> None:
        """Configure OAuth-based provider."""

        # Special handling for providers using mcp-remote or similar proxies
        # These handle OAuth automatically - no manual setup needed
        if provider_class.name == "atlassian":
            console.print(
                f"[cyan]{provider_class.display_name} uses OAuth authentication[/cyan]"
            )
            console.print(
                "[yellow]Your browser will open for authentication...[/yellow]\n"
            )

            try:
                # Create provider instance
                provider = provider_class(config)

                # Connect to provider (this will start mcp-remote and trigger OAuth)
                console.print("Starting authentication process...")
                await provider.connect()

                # Try to list tools to verify connection
                # Use longer timeout since user needs to authenticate in browser
                console.print("Waiting for browser authentication (may take a minute)...")
                import asyncio

                tools = await asyncio.wait_for(
                    provider.list_tools(),
                    timeout=120.0  # 2 minutes for user to complete OAuth
                )

                console.print(
                    f"[green]✓ Authentication successful! Found {len(tools)} tools.[/green]\n"
                )

                # Disconnect properly and wait for cleanup
                await provider.disconnect()
                await asyncio.sleep(0.5)  # Give subprocess time to cleanup

            except asyncio.TimeoutError:
                console.print(f"[red]✗ Authentication timed out. Please try again.[/red]")
                console.print(
                    "[yellow]Make sure to complete the authentication in your browser.[/yellow]"
                )
                # Clean up
                try:
                    await provider.disconnect()
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
                raise
            except Exception as e:
                console.print(f"[red]✗ Authentication failed: {e}[/red]")
                console.print(
                    "[yellow]Note: Requires Node.js v18+ installed (npx command)[/yellow]"
                )
                # Clean up
                try:
                    await provider.disconnect()
                    await asyncio.sleep(0.5)
                except Exception:
                    pass
                raise

            return

        # Standard OAuth flow for other providers (if any exist in future)
        console.print(
            f"[yellow]{provider_class.display_name} requires OAuth authentication[/yellow]"
        )

        # Prompt for client ID if needed
        if "client_id" not in config:
            client_id = await questionary.text(
                "Enter OAuth client ID:",
                validate=lambda x: len(x) > 0 or "Client ID required",
            ).ask_async()
            config["client_id"] = client_id

        # Run OAuth flow
        console.print("Starting OAuth flow...")
        console.print("Your browser will open for authentication.")

        try:
            # Create provider instance
            provider = provider_class(config)

            # Run authentication
            if hasattr(provider, "authenticate"):
                tokens = await provider.authenticate()

                # Store tokens
                token_store = get_token_store()
                token_store.store(provider_class.name, tokens)

                console.print(
                    "[green]✓ Authentication successful![/green]",
                )

                # Update config with tokens
                config["access_token"] = tokens.get("access_token")
                config["refresh_token"] = tokens.get("refresh_token")
            else:
                console.print(
                    "[red]Provider does not implement authenticate method[/red]"
                )

        except Exception as e:
            console.print(f"[red]✗ Authentication failed: {e}[/red]")
            raise

    async def _configure_api_key_provider(
        self, provider_class: type[MCPProvider], config: Dict
    ) -> None:
        """Configure API key-based provider."""
        console.print(
            f"[yellow]{provider_class.display_name} requires API key[/yellow]"
        )

        # Prompt for API key
        api_key = await questionary.password(
            "Enter API key:",
            validate=lambda x: len(x) > 0 or "API key required",
        ).ask_async()

        config["api_key"] = api_key

        # Check for additional configuration
        # (This would be extended based on provider config_class)
        console.print("[green]✓ Configuration saved[/green]")

    async def _prompt_for_config_field(
        self, field_name: str, field_info: Dict, current_value: any = None
    ) -> any:
        """
        Prompt user for a configuration field.

        Args:
            field_name: Name of the field
            field_info: Pydantic field info
            current_value: Current value if any

        Returns:
            User input value
        """
        description = field_info.get("description", field_name)
        required = field_info.get("required", False)

        # Show current value if exists
        prompt_text = f"{description}"
        if current_value:
            prompt_text += f" (current: {current_value})"
        prompt_text += ":"

        # Determine prompt type based on field type
        field_type = field_info.get("type", "string")

        if field_type == "boolean":
            return await questionary.confirm(
                prompt_text, default=current_value or False
            ).ask_async()
        elif field_type == "integer":
            while True:
                value = await questionary.text(
                    prompt_text,
                    default=str(current_value) if current_value else "",
                ).ask_async()
                try:
                    return int(value)
                except ValueError:
                    console.print("[red]Please enter a valid integer[/red]")
        else:
            # Text input
            validator = None
            if required:
                validator = lambda x: len(x) > 0 or f"{field_name} is required"

            return await questionary.text(
                prompt_text,
                default=str(current_value) if current_value else "",
                validate=validator,
            ).ask_async()
