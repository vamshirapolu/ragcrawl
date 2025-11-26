"""Storage configuration for different backends."""

from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class StorageType(str, Enum):
    """Supported storage backend types."""

    DUCKDB = "duckdb"
    DYNAMODB = "dynamodb"


def _get_default_db_path() -> Path:
    """Get the default database path from user config."""
    # Import here to avoid circular imports
    from ragcrawl.config.user_config import get_default_storage_path

    return get_default_storage_path()


class DuckDBConfig(BaseModel):
    """Configuration for DuckDB storage backend."""

    type: Literal["duckdb"] = "duckdb"
    path: str | Path = Field(
        default_factory=_get_default_db_path,
        description="Path to DuckDB database file (default: ~/.ragcrawl/ragcrawl.duckdb)",
    )
    read_only: bool = Field(default=False, description="Open database in read-only mode")

    model_config = {"frozen": False}


class DynamoDBConfig(BaseModel):
    """Configuration for DynamoDB storage backend."""

    type: Literal["dynamodb"] = "dynamodb"
    region: str = Field(default="us-east-1", description="AWS region")
    table_prefix: str = Field(
        default="ragcrawl",
        description="Prefix for DynamoDB table names",
    )
    endpoint_url: str | None = Field(
        default=None,
        description="Custom endpoint URL (for local DynamoDB)",
    )
    aws_profile: str | None = Field(
        default=None,
        description="AWS profile to use for credentials",
    )
    aws_access_key_id: str | None = Field(default=None, description="AWS access key ID")
    aws_secret_access_key: str | None = Field(default=None, description="AWS secret key")
    ttl_days: int | None = Field(
        default=None,
        description="TTL in days for records (None = no expiration)",
    )
    read_capacity_units: int = Field(default=5, description="Read capacity units")
    write_capacity_units: int = Field(default=5, description="Write capacity units")
    billing_mode: Literal["PROVISIONED", "PAY_PER_REQUEST"] = Field(
        default="PAY_PER_REQUEST",
        description="DynamoDB billing mode",
    )

    model_config = {"frozen": False}


class StorageConfig(BaseModel):
    """
    Storage configuration supporting multiple backends.

    DuckDB is the default when no configuration is provided.
    DynamoDB is enabled only when explicitly configured.
    """

    backend: DuckDBConfig | DynamoDBConfig = Field(
        default_factory=DuckDBConfig,
        description="Storage backend configuration",
    )
    fail_if_unavailable: bool = Field(
        default=False,
        description="If True, fail instead of falling back to DuckDB when primary backend unavailable",
    )

    model_config = {"frozen": False}

    @property
    def storage_type(self) -> StorageType:
        """Get the storage type."""
        if isinstance(self.backend, DynamoDBConfig):
            return StorageType.DYNAMODB
        return StorageType.DUCKDB

    @classmethod
    def duckdb(cls, path: str | Path | None = None) -> "StorageConfig":
        """Create a DuckDB storage configuration.

        Args:
            path: Path to database file. If None, uses default (~/.ragcrawl/ragcrawl.duckdb).
        """
        if path is None:
            return cls(backend=DuckDBConfig())
        return cls(backend=DuckDBConfig(path=path))

    @classmethod
    def dynamodb(
        cls,
        region: str = "us-east-1",
        table_prefix: str = "ragcrawl",
        **kwargs: str | int | None,
    ) -> "StorageConfig":
        """Create a DynamoDB storage configuration."""
        return cls(backend=DynamoDBConfig(region=region, table_prefix=table_prefix, **kwargs))
