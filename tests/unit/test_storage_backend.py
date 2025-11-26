"""Tests for storage backend factory behavior."""

import sys
import types

import pytest

from ragcrawl.config.storage_config import DynamoDBConfig, StorageConfig
from ragcrawl.storage import backend as backend_module


def _install_dummy_duckdb(monkeypatch, tmp_path):
    """Install dummy DuckDBBackend and DuckDBConfig to avoid real DB interactions."""
    class DummyDuckDBBackend:
        def __init__(self, config) -> None:
            self.config = config

        def __repr__(self) -> str:  # pragma: no cover - debugging helper
            return f"DummyDuckDBBackend({self.config})"

    class DummyDuckDBConfig:
        def __init__(self, path=None) -> None:
            self.path = path or tmp_path / "fallback.duckdb"

    monkeypatch.setitem(
        sys.modules,
        "ragcrawl.storage.duckdb.backend",
        types.SimpleNamespace(DuckDBBackend=DummyDuckDBBackend),
    )
    monkeypatch.setattr(backend_module, "DuckDBConfig", DummyDuckDBConfig)


def test_create_storage_backend_uses_dynamodb_when_available(monkeypatch, tmp_path) -> None:
    """When DynamoDB is healthy, the factory returns that backend."""
    _install_dummy_duckdb(monkeypatch, tmp_path)

    class HealthyDynamo:
        def __init__(self, config) -> None:
            self.config = config
            self.initialized = True

        def health_check(self) -> bool:
            return True

    monkeypatch.setitem(
        sys.modules,
        "ragcrawl.storage.dynamodb.backend",
        types.SimpleNamespace(DynamoDBBackend=HealthyDynamo),
    )

    config = StorageConfig(backend=DynamoDBConfig(region="us-west-2"))
    backend = backend_module.create_storage_backend(config)
    assert isinstance(backend, HealthyDynamo)
    assert backend.config.region == "us-west-2"


def test_create_storage_backend_falls_back_to_duckdb(monkeypatch, tmp_path) -> None:
    """When DynamoDB is unavailable and fail_if_unavailable=False, fallback to DuckDB."""
    _install_dummy_duckdb(monkeypatch, tmp_path)

    class UnhealthyDynamo:
        def __init__(self, config) -> None:
            self.config = config

        def health_check(self) -> bool:
            return False

    monkeypatch.setitem(
        sys.modules,
        "ragcrawl.storage.dynamodb.backend",
        types.SimpleNamespace(DynamoDBBackend=UnhealthyDynamo),
    )

    config = StorageConfig(backend=DynamoDBConfig(), fail_if_unavailable=False)
    backend = backend_module.create_storage_backend(config)
    # Factory should return dummy DuckDB backend
    assert backend.__class__.__name__ == "DummyDuckDBBackend"
    assert str(backend.config.path).endswith("fallback.duckdb")


def test_create_storage_backend_raises_when_fail_if_unavailable(monkeypatch, tmp_path) -> None:
    """fail_if_unavailable=True propagates DynamoDB failures."""
    _install_dummy_duckdb(monkeypatch, tmp_path)

    class BrokenDynamo:
        def __init__(self, config) -> None:
            raise RuntimeError("boom")

    monkeypatch.setitem(
        sys.modules,
        "ragcrawl.storage.dynamodb.backend",
        types.SimpleNamespace(DynamoDBBackend=BrokenDynamo),
    )

    config = StorageConfig(backend=DynamoDBConfig(), fail_if_unavailable=True)
    with pytest.raises(RuntimeError):
        backend_module.create_storage_backend(config)
