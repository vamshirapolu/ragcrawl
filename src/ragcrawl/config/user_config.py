"""User configuration management for ragcrawl.

Manages persistent user settings stored in ~/.ragcrawl/config.json
"""

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


def get_default_data_dir() -> Path:
    """Get the default ragcrawl data directory."""
    return Path.home() / ".ragcrawl"


def get_default_db_path() -> Path:
    """Get the default DuckDB database path."""
    return get_default_data_dir() / "ragcrawl.duckdb"


class UserConfig(BaseModel):
    """User configuration settings."""

    storage_dir: Path = Field(
        default_factory=get_default_data_dir,
        description="Directory for ragcrawl data storage",
    )
    db_name: str = Field(
        default="ragcrawl.duckdb",
        description="Name of the DuckDB database file",
    )
    user_agent: str = Field(
        default="ragcrawl/0.1",
        description="Default user agent for HTTP requests",
    )
    timeout: int = Field(
        default=30,
        description="Default HTTP timeout in seconds",
    )
    max_retries: int = Field(
        default=3,
        description="Default maximum retry attempts",
    )
    default_max_pages: int = Field(
        default=100,
        description="Default maximum pages to crawl",
    )
    default_max_depth: int = Field(
        default=5,
        description="Default maximum crawl depth",
    )

    model_config = {"frozen": False}

    @property
    def db_path(self) -> Path:
        """Get the full path to the DuckDB database."""
        return self.storage_dir / self.db_name

    @property
    def config_file(self) -> Path:
        """Get the path to the config file."""
        return self.storage_dir / "config.json"

    def ensure_storage_dir(self) -> None:
        """Ensure the storage directory exists."""
        self.storage_dir.mkdir(parents=True, exist_ok=True)


class UserConfigManager:
    """Manages loading and saving user configuration."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize the config manager.

        Args:
            config_dir: Override the default config directory.
        """
        self._config_dir = config_dir or get_default_data_dir()
        self._config_file = self._config_dir / "config.json"
        self._config: UserConfig | None = None

    @property
    def config_file(self) -> Path:
        """Get the path to the config file."""
        return self._config_file

    @property
    def config_dir(self) -> Path:
        """Get the config directory."""
        return self._config_dir

    def load(self) -> UserConfig:
        """Load configuration from file, or return defaults."""
        if self._config is not None:
            return self._config

        if self._config_file.exists():
            try:
                with open(self._config_file) as f:
                    data = json.load(f)
                # Convert storage_dir back to Path
                if "storage_dir" in data:
                    data["storage_dir"] = Path(data["storage_dir"])
                self._config = UserConfig(**data)
            except (json.JSONDecodeError, ValueError):
                # Invalid config, use defaults
                self._config = UserConfig()
        else:
            self._config = UserConfig()

        return self._config

    def save(self, config: UserConfig | None = None) -> None:
        """Save configuration to file.

        Args:
            config: Configuration to save. If None, saves current config.
        """
        if config is not None:
            self._config = config

        if self._config is None:
            self._config = UserConfig()

        # Ensure directory exists
        self._config_dir.mkdir(parents=True, exist_ok=True)

        # Serialize config
        data = self._config.model_dump()
        # Convert Path to string for JSON serialization
        data["storage_dir"] = str(data["storage_dir"])

        with open(self._config_file, "w") as f:
            json.dump(data, f, indent=2)

    def get(self, key: str) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key to retrieve.

        Returns:
            The configuration value.

        Raises:
            KeyError: If key doesn't exist.
        """
        config = self.load()
        if hasattr(config, key):
            return getattr(config, key)
        raise KeyError(f"Unknown configuration key: {key}")

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key to set.
            value: Value to set.

        Raises:
            KeyError: If key doesn't exist.
            ValueError: If value is invalid.
        """
        config = self.load()
        if not hasattr(config, key):
            raise KeyError(f"Unknown configuration key: {key}")

        # Handle Path conversion for storage_dir
        if key == "storage_dir":
            value = Path(value)

        # Create new config with updated value
        data = config.model_dump()
        data[key] = value
        self._config = UserConfig(**data)
        self.save()

    def reset(self) -> None:
        """Reset configuration to defaults."""
        self._config = UserConfig()
        self.save()

    def ensure_initialized(self) -> UserConfig:
        """Ensure config is loaded and storage directory exists.

        Returns:
            The loaded configuration.
        """
        config = self.load()
        config.ensure_storage_dir()
        return config


# Global config manager instance
_config_manager: UserConfigManager | None = None


def get_config_manager() -> UserConfigManager:
    """Get the global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = UserConfigManager()
    return _config_manager


def get_user_config() -> UserConfig:
    """Get the current user configuration."""
    return get_config_manager().load()


def get_default_storage_path() -> Path:
    """Get the default storage path from user config."""
    return get_user_config().db_path
