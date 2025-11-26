"""CLI entry point for ragcrawl."""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import click

from ragcrawl import __version__


def get_storage_path() -> Path:
    """Get the default storage path from user config."""
    from ragcrawl.config.user_config import get_config_manager

    manager = get_config_manager()
    config = manager.ensure_initialized()
    return config.db_path


@click.group()
@click.version_option(version=__version__)
def app() -> None:
    """ragcrawl - Crawl websites and produce LLM-ready artifacts."""
    pass


# ============================================================================
# Config command group
# ============================================================================


@app.group(invoke_without_command=True)
@click.pass_context
def config(ctx: click.Context) -> None:
    """Manage ragcrawl configuration.

    Run without subcommand to open interactive TUI editor.
    """
    if ctx.invoked_subcommand is None:
        # Launch TUI when no subcommand is provided
        from ragcrawl.cli.config_tui import run_config_tui

        run_config_tui()


@config.command("show")
def config_show() -> None:
    """Show current configuration."""
    from ragcrawl.config.user_config import get_config_manager

    manager = get_config_manager()
    cfg = manager.load()

    click.echo("ragcrawl Configuration")
    click.echo("=" * 40)
    click.echo(f"Config file: {manager.config_file}")
    click.echo(f"Config exists: {manager.config_file.exists()}")
    click.echo()
    click.echo("Settings:")
    click.echo(f"  storage_dir:       {cfg.storage_dir}")
    click.echo(f"  db_name:           {cfg.db_name}")
    click.echo(f"  db_path:           {cfg.db_path}")
    click.echo(f"  user_agent:        {cfg.user_agent}")
    click.echo(f"  timeout:           {cfg.timeout}s")
    click.echo(f"  max_retries:       {cfg.max_retries}")
    click.echo(f"  default_max_pages: {cfg.default_max_pages}")
    click.echo(f"  default_max_depth: {cfg.default_max_depth}")


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value.

    KEY: Configuration key (e.g., storage_dir, user_agent, timeout)
    VALUE: Value to set
    """
    from ragcrawl.config.user_config import get_config_manager

    manager = get_config_manager()

    # Handle type conversions
    int_keys = {"timeout", "max_retries", "default_max_pages", "default_max_depth"}

    try:
        if key in int_keys:
            typed_value: str | int | Path = int(value)
        elif key == "storage_dir":
            typed_value = Path(value).expanduser().resolve()
        else:
            typed_value = value

        manager.set(key, typed_value)
        click.echo(f"Set {key} = {typed_value}")

        # Show warning if storage_dir changed
        if key == "storage_dir":
            click.echo(
                click.style(
                    "\nNote: Existing data in the old location will not be moved automatically.",
                    fg="yellow",
                )
            )
    except KeyError as e:
        click.echo(click.style(f"Error: {e}", fg="red"))
        click.echo("\nValid keys: storage_dir, db_name, user_agent, timeout, max_retries, "
                   "default_max_pages, default_max_depth")
        sys.exit(1)
    except ValueError as e:
        click.echo(click.style(f"Error: Invalid value - {e}", fg="red"))
        sys.exit(1)


@config.command("reset")
@click.confirmation_option(prompt="Are you sure you want to reset configuration to defaults?")
def config_reset() -> None:
    """Reset configuration to defaults."""
    from ragcrawl.config.user_config import get_config_manager

    manager = get_config_manager()
    manager.reset()
    click.echo("Configuration reset to defaults.")


@config.command("path")
def config_path() -> None:
    """Show the path to the configuration file."""
    from ragcrawl.config.user_config import get_config_manager

    manager = get_config_manager()
    click.echo(manager.config_file)


# ============================================================================
# List command
# ============================================================================


@app.command("list")
@click.option(
    "--storage",
    "-s",
    type=click.Path(),
    help="DuckDB storage path (default: ~/.ragcrawl/ragcrawl.duckdb).",
)
@click.option(
    "--limit",
    "-l",
    default=20,
    help="Maximum number of runs to show.",
)
@click.option(
    "--site",
    help="Filter by site ID.",
)
@click.option(
    "--status",
    type=click.Choice(["running", "completed", "partial", "failed"]),
    help="Filter by status.",
)
def list_runs(
    storage: Optional[str],
    limit: int,
    site: Optional[str],
    status: Optional[str],
) -> None:
    """List all crawl runs.

    Shows a summary of all crawls recorded in the database with useful
    information like site/seed, run ID, status, timing, and pages crawled.
    """
    from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
    from ragcrawl.storage.backend import create_storage_backend

    storage_path = Path(storage) if storage else get_storage_path()

    if not storage_path.exists():
        click.echo(f"No database found at: {storage_path}")
        click.echo("Run 'ragcrawl crawl <url>' to start crawling.")
        return

    config = StorageConfig(backend=DuckDBConfig(path=storage_path))
    backend = create_storage_backend(config)
    backend.initialize()

    # Get all sites first
    site_list = backend.list_sites()

    if not site_list:
        click.echo("No crawl data found.")
        backend.close()
        return

    # Build site lookup
    sites_by_id = {s.site_id: s for s in site_list}

    # Collect all runs
    all_runs = []
    for s in site_list:
        if site and s.site_id != site:
            continue
        runs = backend.list_runs(s.site_id, limit=limit)
        for run in runs:
            if status and run.status.value != status:
                continue
            all_runs.append((s, run))

    if not all_runs:
        click.echo("No runs found matching criteria.")
        backend.close()
        return

    # Sort by start time (newest first)
    all_runs.sort(key=lambda x: x[1].started_at or datetime.min, reverse=True)
    all_runs = all_runs[:limit]

    # Display header
    click.echo()
    click.echo(
        f"{'RUN ID':<36} {'STATUS':<10} {'SITE':<20} {'PAGES':<8} {'DURATION':<10} {'STARTED':<20}"
    )
    click.echo("-" * 110)

    for site_info, run in all_runs:
        # Format status with color
        status_colors = {
            "completed": "green",
            "partial": "yellow",
            "failed": "red",
            "running": "blue",
        }
        status_str = click.style(
            run.status.value.ljust(10),
            fg=status_colors.get(run.status.value, "white"),
        )

        # Format site (truncate if needed)
        site_name = site_info.name or site_info.site_id
        if len(site_name) > 20:
            site_name = site_name[:17] + "..."

        # Format pages
        pages_str = f"{run.stats.pages_crawled}/{run.stats.pages_failed}"

        # Format duration
        if run.duration_seconds:
            if run.duration_seconds < 60:
                duration_str = f"{run.duration_seconds:.1f}s"
            elif run.duration_seconds < 3600:
                duration_str = f"{run.duration_seconds / 60:.1f}m"
            else:
                duration_str = f"{run.duration_seconds / 3600:.1f}h"
        else:
            duration_str = "-"

        # Format started time
        if run.started_at:
            started_str = run.started_at.strftime("%Y-%m-%d %H:%M")
        else:
            started_str = "-"

        click.echo(
            f"{run.run_id:<36} {status_str} {site_name:<20} {pages_str:<8} {duration_str:<10} {started_str:<20}"
        )

    click.echo()
    click.echo(f"Total: {len(all_runs)} run(s)")

    # Show seeds for context
    if len(site_list) <= 5:
        click.echo()
        click.echo("Sites:")
        for s in site_list:
            seeds_str = ", ".join(s.seeds[:2])
            if len(s.seeds) > 2:
                seeds_str += f" (+{len(s.seeds) - 2} more)"
            click.echo(f"  {s.site_id}: {seeds_str}")

    backend.close()


# ============================================================================
# Crawl command
# ============================================================================


@app.command()
@click.argument("seeds", nargs=-1, required=True)
@click.option(
    "--max-pages",
    "-m",
    default=None,
    type=int,
    help="Maximum pages to crawl (default: from config).",
)
@click.option(
    "--max-depth",
    "-d",
    default=None,
    type=int,
    help="Maximum crawl depth (default: from config).",
)
@click.option(
    "--output",
    "-o",
    default="./output",
    help="Output directory.",
)
@click.option(
    "--output-mode",
    type=click.Choice(["single", "multi"]),
    default="multi",
    help="Output mode: single file or multi-page.",
)
@click.option(
    "--storage",
    "-s",
    type=click.Path(),
    help="DuckDB storage path (default: ~/.ragcrawl/ragcrawl.duckdb).",
)
@click.option(
    "--include",
    "-i",
    multiple=True,
    help="Include URL patterns (regex).",
)
@click.option(
    "--exclude",
    "-e",
    multiple=True,
    help="Exclude URL patterns (regex).",
)
@click.option(
    "--robots/--no-robots",
    default=True,
    help="Respect robots.txt.",
)
@click.option(
    "--js/--no-js",
    default=False,
    help="Enable JavaScript rendering.",
)
@click.option(
    "--export-json",
    type=click.Path(),
    help="Export documents to JSON file.",
)
@click.option(
    "--export-jsonl",
    type=click.Path(),
    help="Export documents to JSONL file.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output.",
)
def crawl(
    seeds: tuple[str, ...],
    max_pages: Optional[int],
    max_depth: Optional[int],
    output: str,
    output_mode: str,
    storage: Optional[str],
    include: tuple[str, ...],
    exclude: tuple[str, ...],
    robots: bool,
    js: bool,
    export_json: Optional[str],
    export_jsonl: Optional[str],
    verbose: bool,
) -> None:
    """
    Crawl websites from seed URLs.

    SEEDS: One or more URLs to start crawling from.
    """
    from ragcrawl.config.crawler_config import CrawlerConfig, FetchMode, RobotsMode
    from ragcrawl.config.output_config import OutputConfig, OutputMode
    from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
    from ragcrawl.config.user_config import get_user_config
    from ragcrawl.core.crawl_job import CrawlJob
    from ragcrawl.utils.logging import setup_logging

    import logging

    setup_logging(level=logging.DEBUG if verbose else logging.INFO)

    # Get user config for defaults
    user_cfg = get_user_config()

    # Use defaults from user config if not specified
    if max_pages is None:
        max_pages = user_cfg.default_max_pages
    if max_depth is None:
        max_depth = user_cfg.default_max_depth

    # Use centralized storage by default
    storage_path = Path(storage) if storage else user_cfg.db_path

    # Ensure storage directory exists
    storage_path.parent.mkdir(parents=True, exist_ok=True)

    # Build config
    config = CrawlerConfig(
        seeds=list(seeds),
        max_pages=max_pages,
        max_depth=max_depth,
        include_patterns=list(include),
        exclude_patterns=list(exclude),
        robots_mode=RobotsMode.STRICT if robots else RobotsMode.OFF,
        fetch_mode=FetchMode.BROWSER if js else FetchMode.HTTP,
        storage=StorageConfig(backend=DuckDBConfig(path=storage_path)),
        output=OutputConfig(
            mode=OutputMode.SINGLE if output_mode == "single" else OutputMode.MULTI,
            root_dir=output,
        ),
    )

    click.echo(f"Starting crawl of {len(seeds)} seed URL(s)...")
    click.echo(f"  Max pages: {max_pages}")
    click.echo(f"  Max depth: {max_depth}")
    click.echo(f"  Output: {output} ({output_mode} mode)")
    click.echo(f"  Storage: {storage_path}")

    # Run crawl
    job = CrawlJob(config)
    result = asyncio.run(job.run())

    if result.success:
        click.echo(click.style("\nCrawl completed successfully!", fg="green"))
        click.echo(f"  Pages crawled: {result.stats.pages_crawled}")
        click.echo(f"  Pages failed: {result.stats.pages_failed}")
        click.echo(f"  Duration: {result.duration_seconds:.1f}s")

        # Publish output
        if result.documents:
            from ragcrawl.output.multi_page import MultiPagePublisher
            from ragcrawl.output.single_page import SinglePagePublisher

            if output_mode == "single":
                publisher = SinglePagePublisher(config.output)
            else:
                publisher = MultiPagePublisher(config.output)

            files = publisher.publish(result.documents)
            click.echo(f"  Output files: {len(files)}")

        # Export if requested
        if export_json or export_jsonl:
            from ragcrawl.export.json_exporter import JSONExporter, JSONLExporter

            if export_json:
                exporter = JSONExporter()
                exporter.export_documents(result.documents, Path(export_json))
                click.echo(f"  Exported JSON: {export_json}")

            if export_jsonl:
                exporter = JSONLExporter()
                exporter.export_documents(result.documents, Path(export_jsonl))
                click.echo(f"  Exported JSONL: {export_jsonl}")

    else:
        click.echo(click.style(f"\nCrawl failed: {result.error}", fg="red"))
        sys.exit(1)


# ============================================================================
# Sync command
# ============================================================================


@app.command()
@click.argument("site_id")
@click.option(
    "--storage",
    "-s",
    type=click.Path(),
    help="DuckDB storage path (default: ~/.ragcrawl/ragcrawl.duckdb).",
)
@click.option(
    "--max-pages",
    "-m",
    type=int,
    help="Maximum pages to sync.",
)
@click.option(
    "--max-age",
    type=float,
    help="Only check pages older than N hours.",
)
@click.option(
    "--output",
    "-o",
    help="Output directory for updates.",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Verbose output.",
)
def sync(
    site_id: str,
    storage: Optional[str],
    max_pages: Optional[int],
    max_age: Optional[float],
    output: Optional[str],
    verbose: bool,
) -> None:
    """
    Sync a previously crawled site for changes.

    SITE_ID: ID of the site to sync.
    """
    from ragcrawl.config.output_config import OutputConfig
    from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
    from ragcrawl.config.sync_config import SyncConfig
    from ragcrawl.config.user_config import get_user_config
    from ragcrawl.core.sync_job import SyncJob
    from ragcrawl.utils.logging import setup_logging

    import logging

    setup_logging(level=logging.DEBUG if verbose else logging.INFO)

    # Use centralized storage by default
    user_cfg = get_user_config()
    storage_path = Path(storage) if storage else user_cfg.db_path

    # Build config
    sync_config = SyncConfig(
        site_id=site_id,
        max_pages=max_pages,
        max_age_hours=max_age,
        storage=StorageConfig(backend=DuckDBConfig(path=storage_path)),
        output=OutputConfig(root_dir=output) if output else None,
    )

    click.echo(f"Starting sync for site: {site_id}")
    click.echo(f"  Storage: {storage_path}")

    # Run sync
    job = SyncJob(sync_config)
    result = asyncio.run(job.run())

    if result.success:
        click.echo(click.style("\nSync completed successfully!", fg="green"))
        click.echo(f"  Pages checked: {result.stats.pages_crawled}")
        click.echo(f"  Pages changed: {result.stats.pages_changed}")
        click.echo(f"  Pages deleted: {result.stats.pages_deleted}")
        click.echo(f"  Duration: {result.duration_seconds:.1f}s")

        if result.changed_pages:
            click.echo("\nChanged pages:")
            for url in result.changed_pages[:10]:
                click.echo(f"  - {url}")
            if len(result.changed_pages) > 10:
                click.echo(f"  ... and {len(result.changed_pages) - 10} more")

    else:
        click.echo(click.style(f"\nSync failed: {result.error}", fg="red"))
        sys.exit(1)


# ============================================================================
# Sites command
# ============================================================================


@app.command()
@click.option(
    "--storage",
    "-s",
    type=click.Path(),
    help="DuckDB storage path (default: ~/.ragcrawl/ragcrawl.duckdb).",
)
def sites(storage: Optional[str]) -> None:
    """List all crawled sites."""
    from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
    from ragcrawl.storage.backend import create_storage_backend

    storage_path = Path(storage) if storage else get_storage_path()

    if not storage_path.exists():
        click.echo(f"No database found at: {storage_path}")
        click.echo("Run 'ragcrawl crawl <url>' to start crawling.")
        return

    config = StorageConfig(backend=DuckDBConfig(path=storage_path))
    backend = create_storage_backend(config)
    backend.initialize()

    site_list = backend.list_sites()

    if not site_list:
        click.echo("No sites found.")
        backend.close()
        return

    click.echo(f"Found {len(site_list)} site(s):\n")
    for site in site_list:
        click.echo(f"ID: {site.site_id}")
        click.echo(f"  Name: {site.name}")
        click.echo(f"  Seeds: {', '.join(site.seeds[:3])}")
        click.echo(f"  Pages: {site.total_pages}")
        click.echo(f"  Runs: {site.total_runs}")
        if site.last_crawl_at:
            click.echo(f"  Last crawl: {site.last_crawl_at.isoformat()}")
        click.echo()

    backend.close()


# ============================================================================
# Runs command
# ============================================================================


@app.command()
@click.argument("site_id")
@click.option(
    "--storage",
    "-s",
    type=click.Path(),
    help="DuckDB storage path (default: ~/.ragcrawl/ragcrawl.duckdb).",
)
@click.option(
    "--limit",
    "-l",
    default=10,
    help="Number of runs to show.",
)
def runs(site_id: str, storage: Optional[str], limit: int) -> None:
    """List crawl runs for a site."""
    from ragcrawl.config.storage_config import DuckDBConfig, StorageConfig
    from ragcrawl.storage.backend import create_storage_backend

    storage_path = Path(storage) if storage else get_storage_path()

    if not storage_path.exists():
        click.echo(f"No database found at: {storage_path}")
        return

    config = StorageConfig(backend=DuckDBConfig(path=storage_path))
    backend = create_storage_backend(config)
    backend.initialize()

    run_list = backend.list_runs(site_id, limit=limit)

    if not run_list:
        click.echo(f"No runs found for site: {site_id}")
        backend.close()
        return

    click.echo(f"Runs for site {site_id}:\n")
    for run in run_list:
        status_color = {
            "completed": "green",
            "partial": "yellow",
            "failed": "red",
            "running": "blue",
        }.get(run.status.value, "white")

        click.echo(f"Run: {run.run_id}")
        click.echo(f"  Status: " + click.style(run.status.value, fg=status_color))
        click.echo(f"  Started: {run.started_at.isoformat() if run.started_at else 'N/A'}")
        if run.duration_seconds:
            click.echo(f"  Duration: {run.duration_seconds:.1f}s")
        click.echo(f"  Pages: {run.stats.pages_crawled} crawled, {run.stats.pages_failed} failed")
        click.echo()

    backend.close()


if __name__ == "__main__":
    app()
