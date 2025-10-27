"""Tests for configuration system."""

from pathlib import Path

import pytest
import yaml

from mcp.config import Config, load_config, save_config


def test_default_config() -> None:
    """Test default configuration."""
    config = Config()

    assert config.enabled_providers == []
    assert config.provider_settings == {}
    assert config.global_settings.logging_level == "INFO"


def test_enable_disable_provider() -> None:
    """Test enabling and disabling providers."""
    config = Config()

    # Enable provider
    config.enable_provider("test", {"api_key": "test123"})
    assert config.is_provider_enabled("test")
    assert config.provider_settings["test"]["api_key"] == "test123"

    # Disable provider
    config.disable_provider("test")
    assert not config.is_provider_enabled("test")


def test_get_provider_config() -> None:
    """Test getting provider configuration."""
    config = Config(
        provider_settings={
            "test": {"endpoint": "http://localhost:8080"}
        }
    )

    provider_config = config.get_provider_config("test")
    assert provider_config["endpoint"] == "http://localhost:8080"


def test_save_and_load_config(temp_config_dir: Path) -> None:
    """Test saving and loading configuration."""
    config_path = temp_config_dir / "config.yaml"

    # Create and save config
    config = Config(
        enabled_providers=["test1", "test2"],
        provider_settings={
            "test1": {"api_key": "key1"},
            "test2": {"endpoint": "http://localhost"},
        },
    )
    save_config(config, config_path)

    # Load config
    loaded_config = load_config(config_path)

    assert loaded_config.enabled_providers == ["test1", "test2"]
    assert loaded_config.provider_settings["test1"]["api_key"] == "key1"


def test_load_nonexistent_config() -> None:
    """Test loading nonexistent config returns defaults."""
    config = load_config(Path("nonexistent.yaml"))

    assert config.enabled_providers == []
    assert config.provider_settings == {}


def test_config_yaml_format(temp_config_dir: Path) -> None:
    """Test that saved config has correct YAML format."""
    config_path = temp_config_dir / "config.yaml"

    config = Config(enabled_providers=["test"])
    save_config(config, config_path)

    # Read and verify YAML structure
    with open(config_path) as f:
        yaml_data = yaml.safe_load(f)

    assert "enabled_providers" in yaml_data
    assert "logging" in yaml_data
    assert "timeouts" in yaml_data
