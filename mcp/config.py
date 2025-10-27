"""Configuration management for startmcp."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from mcp.exceptions import ConfigurationError


class GlobalConfig(BaseModel):
    """Global configuration settings."""

    logging_level: str = Field(default="INFO", description="Logging level")
    logging_format: str = Field(default="json", description="Logging format")
    connection_timeout: int = Field(
        default=30, description="Connection timeout in seconds"
    )
    request_timeout: int = Field(default=60, description="Request timeout in seconds")


class Config(BaseModel):
    """Main configuration for startmcp."""

    enabled_providers: List[str] = Field(
        default_factory=list, description="List of enabled provider names"
    )
    provider_settings: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Provider-specific settings"
    )
    global_settings: GlobalConfig = Field(
        default_factory=GlobalConfig, description="Global settings"
    )

    @classmethod
    def load(
        cls, config_path: Optional[Path] = None, env_path: Optional[Path] = None
    ) -> "Config":
        """
        Load configuration from files.

        Args:
            config_path: Path to config.yaml (defaults to ./config.yaml)
            env_path: Path to .env file (defaults to ./.env)

        Returns:
            Loaded configuration

        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Load environment variables
        if env_path is None:
            env_path = Path(".env")
        if env_path.exists():
            load_dotenv(env_path)

        # Load YAML config
        if config_path is None:
            config_path = Path("config.yaml")

        if not config_path.exists():
            # Return default config if file doesn't exist
            return cls()

        try:
            with open(config_path, "r") as f:
                yaml_data = yaml.safe_load(f) or {}

            # Extract global settings
            global_settings = {}
            if "logging" in yaml_data:
                global_settings["logging_level"] = yaml_data["logging"].get(
                    "level", "INFO"
                )
                global_settings["logging_format"] = yaml_data["logging"].get(
                    "format", "json"
                )
            if "timeouts" in yaml_data:
                global_settings["connection_timeout"] = yaml_data["timeouts"].get(
                    "connection", 30
                )
                global_settings["request_timeout"] = yaml_data["timeouts"].get(
                    "request", 60
                )

            # Extract provider settings
            enabled_providers = yaml_data.get("enabled_providers", [])
            provider_settings = {}

            for provider_name in enabled_providers:
                if provider_name in yaml_data:
                    provider_settings[provider_name] = yaml_data[provider_name]

            # Create config object
            config = cls(
                enabled_providers=enabled_providers,
                provider_settings=provider_settings,
                global_settings=GlobalConfig(**global_settings),
            )

            return config

        except yaml.YAMLError as e:
            raise ConfigurationError(f"Failed to parse config.yaml: {e}")
        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def save(self, config_path: Optional[Path] = None) -> None:
        """
        Save configuration to file.

        Args:
            config_path: Path to config.yaml (defaults to ./config.yaml)

        Raises:
            ConfigurationError: If save fails
        """
        if config_path is None:
            config_path = Path("config.yaml")

        try:
            # Build YAML structure
            yaml_data = {
                "enabled_providers": self.enabled_providers,
                "logging": {
                    "level": self.global_settings.logging_level,
                    "format": self.global_settings.logging_format,
                },
                "timeouts": {
                    "connection": self.global_settings.connection_timeout,
                    "request": self.global_settings.request_timeout,
                },
            }

            # Add provider-specific settings
            for provider_name, settings in self.provider_settings.items():
                yaml_data[provider_name] = settings

            # Write to file
            with open(config_path, "w") as f:
                yaml.dump(yaml_data, f, default_flow_style=False, sort_keys=False)

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration: {e}")

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific provider.

        Args:
            provider_name: Provider name

        Returns:
            Provider configuration dict
        """
        config = self.provider_settings.get(provider_name, {})

        # Add environment variables (prefixed with PROVIDER_NAME_)
        env_prefix = f"{provider_name.upper()}_"
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # Convert PROVIDER_NAME_SOME_KEY to some_key
                config_key = key[len(env_prefix) :].lower()
                config[config_key] = value

        return config

    def is_provider_enabled(self, provider_name: str) -> bool:
        """
        Check if a provider is enabled.

        Args:
            provider_name: Provider name

        Returns:
            True if enabled
        """
        return provider_name in self.enabled_providers

    def enable_provider(
        self, provider_name: str, settings: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Enable a provider.

        Args:
            provider_name: Provider name
            settings: Optional provider settings
        """
        if provider_name not in self.enabled_providers:
            self.enabled_providers.append(provider_name)

        if settings:
            self.provider_settings[provider_name] = settings

    def disable_provider(self, provider_name: str) -> None:
        """
        Disable a provider.

        Args:
            provider_name: Provider name
        """
        if provider_name in self.enabled_providers:
            self.enabled_providers.remove(provider_name)


# Helper functions


def load_config(
    config_path: Optional[Path] = None, env_path: Optional[Path] = None
) -> Config:
    """
    Load configuration from files.

    Args:
        config_path: Path to config.yaml
        env_path: Path to .env file

    Returns:
        Loaded configuration
    """
    return Config.load(config_path, env_path)


def save_config(config: Config, config_path: Optional[Path] = None) -> None:
    """
    Save configuration to file.

    Args:
        config: Configuration object
        config_path: Path to config.yaml
    """
    config.save(config_path)
