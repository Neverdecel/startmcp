"""Provider registry for dynamic discovery and loading."""

import importlib
import pkgutil
from pathlib import Path
from typing import Dict, List, Optional, Type

from mcp.categories import ProviderCategory
from mcp.provider import MCPProvider


class ProviderRegistry:
    """Registry for discovering and managing MCP providers."""

    def __init__(self) -> None:
        """Initialize provider registry."""
        self._providers: Dict[str, Type[MCPProvider]] = {}
        self._instances: Dict[str, MCPProvider] = {}

    def register(self, provider_class: Type[MCPProvider]) -> None:
        """
        Register a provider class.

        Args:
            provider_class: Provider class to register
        """
        if not provider_class.name:
            raise ValueError(f"Provider {provider_class} must have a 'name' attribute")
        self._providers[provider_class.name] = provider_class

    def get_provider_class(self, name: str) -> Optional[Type[MCPProvider]]:
        """
        Get provider class by name.

        Args:
            name: Provider name

        Returns:
            Provider class or None if not found
        """
        return self._providers.get(name)

    def list_providers(
        self, category: Optional[ProviderCategory] = None
    ) -> List[Type[MCPProvider]]:
        """
        List all registered providers, optionally filtered by category.

        Args:
            category: Optional category filter

        Returns:
            List of provider classes
        """
        providers = list(self._providers.values())
        if category:
            providers = [p for p in providers if p.category == category]
        return providers

    def create_provider(self, name: str, config: Optional[Dict] = None) -> MCPProvider:
        """
        Create a provider instance.

        Args:
            name: Provider name
            config: Provider configuration

        Returns:
            Provider instance

        Raises:
            ValueError: If provider not found
        """
        provider_class = self.get_provider_class(name)
        if not provider_class:
            raise ValueError(f"Provider '{name}' not found in registry")

        # Create and cache instance
        instance = provider_class(config)
        self._instances[name] = instance
        return instance

    def get_instance(self, name: str) -> Optional[MCPProvider]:
        """
        Get cached provider instance.

        Args:
            name: Provider name

        Returns:
            Provider instance or None
        """
        return self._instances.get(name)

    def discover_providers(self, search_path: Optional[Path] = None) -> int:
        """
        Discover and register providers from a directory.

        Args:
            search_path: Path to search for providers (defaults to provider-mcps/)

        Returns:
            Number of providers discovered
        """
        if search_path is None:
            # Default to provider_mcps/ directory
            search_path = Path(__file__).parent.parent / "provider_mcps"

        if not search_path.exists():
            return 0

        count = 0

        # Walk through subdirectories
        for category_dir in search_path.iterdir():
            if not category_dir.is_dir() or category_dir.name.startswith("_"):
                continue

            # Iterate through provider modules
            for importer, modname, ispkg in pkgutil.iter_modules([str(category_dir)]):
                if ispkg:
                    # Load provider.py from package
                    try:
                        module = importlib.import_module(
                            f"provider_mcps.{category_dir.name}.{modname}.provider"
                        )
                        # Look for provider class
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (
                                isinstance(attr, type)
                                and issubclass(attr, MCPProvider)
                                and attr != MCPProvider
                            ):
                                self.register(attr)
                                count += 1
                    except Exception as e:
                        print(f"Failed to load provider {modname}: {e}")
                        continue

        return count

    def list_by_category(self) -> Dict[ProviderCategory, List[Type[MCPProvider]]]:
        """
        Get providers grouped by category.

        Returns:
            Dict mapping category to list of providers
        """
        result: Dict[ProviderCategory, List[Type[MCPProvider]]] = {}
        for provider_class in self._providers.values():
            category = provider_class.category
            if category not in result:
                result[category] = []
            result[category].append(provider_class)
        return result


# Global registry instance
_global_registry = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    """Get the global provider registry."""
    return _global_registry
