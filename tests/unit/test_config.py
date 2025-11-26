"""Tests for configuration helpers."""

import json
from pathlib import Path

import pytest

from ragcrawl.config import user_config
from ragcrawl.config.storage_config import StorageConfig
from ragcrawl.config.user_config import UserConfigManager


def test_storage_config_helpers(tmp_path) -> None:
    """StorageConfig factories set proper backend types."""
    duck = StorageConfig.duckdb(path=tmp_path / "db.duckdb")
    assert duck.storage_type.value == "duckdb"
    assert Path(duck.backend.path) == tmp_path / "db.duckdb"

    dynamo = StorageConfig.dynamodb(region="us-west-1", table_prefix="prefix")
    assert dynamo.storage_type.value == "dynamodb"
    assert dynamo.backend.region == "us-west-1"
    assert dynamo.backend.table_prefix == "prefix"


def test_user_config_manager_load_save_and_set(tmp_path) -> None:
    """UserConfigManager saves to custom dir and validates keys."""
    mgr = UserConfigManager(config_dir=tmp_path)

    config = mgr.load()
    assert mgr.config_file.parent == tmp_path
    assert mgr.config_file.exists() is False

    # Save default config
    mgr.save(config)
    assert mgr.config_file.exists()

    # Set a valid key and persist
    mgr.set("timeout", 99)
    assert mgr.get("timeout") == 99

    # Reset to defaults creates fresh file
    mgr.reset()
    assert mgr.get("timeout") == config.timeout

    with pytest.raises(KeyError):
        mgr.get("missing")

    with pytest.raises(KeyError):
        mgr.set("does_not_exist", "value")


def test_user_config_default_helpers(monkeypatch, tmp_path) -> None:
    """Global helper functions use home directory defaults and singleton manager."""
    monkeypatch.setattr(user_config, "_config_manager", None)
    monkeypatch.setattr(user_config.Path, "home", lambda: tmp_path)

    # Default paths based on patched home
    default_dir = user_config.get_default_data_dir()
    default_db = user_config.get_default_db_path()
    assert default_dir == tmp_path / ".ragcrawl"
    assert default_db.name == "ragcrawl.duckdb"

    # Global manager uses same directory and ensures storage dir
    cfg = user_config.get_user_config()
    mgr = user_config.get_config_manager()
    assert cfg.storage_dir == default_dir
    mgr.ensure_initialized()
    assert cfg.storage_dir.exists()
    assert user_config.get_default_storage_path() == cfg.db_path
    # Cover config_file property on UserConfig
    assert cfg.config_file.name == "config.json"


def test_user_config_loads_invalid_file(monkeypatch, tmp_path) -> None:
    """Loading an invalid JSON config falls back to defaults and save handles missing config."""
    manager = UserConfigManager(config_dir=tmp_path)
    manager.config_file.parent.mkdir(parents=True, exist_ok=True)
    manager.config_file.write_text("{invalid json]")

    loaded = manager.load()
    assert loaded.db_path.name == "ragcrawl.duckdb"
    # Trigger save when _config is None
    manager._config = None  # type: ignore[attr-defined]
    manager.save()
    # storage_dir string conversion in set
    manager.set("storage_dir", tmp_path / "other")
    assert manager.get("storage_dir") == tmp_path / "other"

    # Load valid JSON with storage_dir as string
    manager._config = None  # type: ignore[attr-defined]
    manager.config_file.write_text(json.dumps({"storage_dir": str(tmp_path / "custom")}))
    loaded_custom = manager.load()
    assert loaded_custom.storage_dir == tmp_path / "custom"
    assert manager.config_dir == tmp_path

    # Separate manager to exercise storage_dir conversion branch freshly
    other_dir = tmp_path / "another"
    other_dir.mkdir(parents=True, exist_ok=True)
    second = UserConfigManager(config_dir=other_dir)
    second.config_file.write_text(json.dumps({"storage_dir": str(other_dir)}))
    second._config = None  # type: ignore[attr-defined]
    loaded_second = second.load()
    assert loaded_second.storage_dir == other_dir
