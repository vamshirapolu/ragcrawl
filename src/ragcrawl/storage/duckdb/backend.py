"""DuckDB storage backend implementation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from ragcrawl.config.storage_config import DuckDBConfig
from ragcrawl.models.crawl_run import CrawlRun, CrawlStats, RunStatus
from ragcrawl.models.frontier_item import FrontierItem, FrontierStatus
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.models.site import Site
from ragcrawl.storage.backend import StorageBackend
from ragcrawl.storage.duckdb.schema import get_all_schemas


class DuckDBBackend(StorageBackend):
    """
    DuckDB storage backend implementation.

    Provides local file-based storage with SQL capabilities.
    """

    def __init__(self, config: DuckDBConfig) -> None:
        """
        Initialize DuckDB backend.

        Args:
            config: DuckDB configuration.
        """
        self.config = config
        self.db_path = Path(config.path)
        self._conn: duckdb.DuckDBPyConnection | None = None

    @property
    def conn(self) -> duckdb.DuckDBPyConnection:
        """Get or create database connection."""
        if self._conn is None:
            # Ensure parent directory exists
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            self._conn = duckdb.connect(
                str(self.db_path),
                read_only=self.config.read_only,
            )
        return self._conn

    def initialize(self) -> None:
        """Initialize the database schema."""
        for schema_sql in get_all_schemas():
            self.conn.execute(schema_sql)

    def close(self) -> None:
        """Close the database connection."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def health_check(self) -> bool:
        """Check if the database is accessible."""
        try:
            self.conn.execute("SELECT 1").fetchone()
            return True
        except Exception:
            return False

    # === Site operations ===

    def save_site(self, site: Site) -> None:
        """Save or update a site."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO sites (
                site_id, name, seeds, allowed_domains, allowed_subdomains,
                config, created_at, updated_at, last_crawl_at, last_sync_at,
                total_pages, total_runs, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                site.site_id,
                site.name,
                json.dumps(site.seeds),
                json.dumps(site.allowed_domains),
                site.allowed_subdomains,
                json.dumps(site.config, default=self._json_serializer),
                site.created_at,
                site.updated_at,
                site.last_crawl_at,
                site.last_sync_at,
                site.total_pages,
                site.total_runs,
                site.is_active,
            ],
        )

    def get_site(self, site_id: str) -> Site | None:
        """Get a site by ID."""
        result = self.conn.execute(
            "SELECT * FROM sites WHERE site_id = ?", [site_id]
        ).fetchone()

        if result is None:
            return None

        return self._row_to_site(result)

    def list_sites(self) -> list[Site]:
        """List all sites."""
        results = self.conn.execute(
            "SELECT * FROM sites ORDER BY created_at DESC"
        ).fetchall()

        return [self._row_to_site(row) for row in results]

    def delete_site(self, site_id: str) -> bool:
        """Delete a site and all associated data."""
        # Delete in order of dependencies
        self.conn.execute("DELETE FROM frontier_items WHERE site_id = ?", [site_id])
        self.conn.execute("DELETE FROM page_versions WHERE site_id = ?", [site_id])
        self.conn.execute("DELETE FROM pages WHERE site_id = ?", [site_id])
        self.conn.execute("DELETE FROM crawl_runs WHERE site_id = ?", [site_id])
        result = self.conn.execute("DELETE FROM sites WHERE site_id = ?", [site_id])

        return result.rowcount > 0 if hasattr(result, "rowcount") else True

    def _row_to_site(self, row: tuple[Any, ...]) -> Site:
        """Convert a database row to a Site model."""
        return Site(
            site_id=row[0],
            name=row[1],
            seeds=json.loads(row[2]) if isinstance(row[2], str) else row[2],
            allowed_domains=json.loads(row[3]) if isinstance(row[3], str) else (row[3] or []),
            allowed_subdomains=row[4],
            config=json.loads(row[5]) if isinstance(row[5], str) else (row[5] or {}),
            created_at=row[6],
            updated_at=row[7],
            last_crawl_at=row[8],
            last_sync_at=row[9],
            total_pages=row[10] or 0,
            total_runs=row[11] or 0,
            is_active=row[12],
        )

    # === CrawlRun operations ===

    def save_run(self, run: CrawlRun) -> None:
        """Save or update a crawl run."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO crawl_runs (
                run_id, site_id, status, error_message, created_at, started_at,
                completed_at, config_snapshot, seeds, is_sync, parent_run_id,
                stats, frontier_size, max_depth_reached
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                run.run_id,
                run.site_id,
                run.status.value,
                run.error_message,
                run.created_at,
                run.started_at,
                run.completed_at,
                json.dumps(run.config_snapshot, default=self._json_serializer),
                json.dumps(run.seeds),
                run.is_sync,
                run.parent_run_id,
                json.dumps(run.stats.model_dump(), default=self._json_serializer),
                run.frontier_size,
                run.max_depth_reached,
            ],
        )

    def get_run(self, run_id: str) -> CrawlRun | None:
        """Get a crawl run by ID."""
        result = self.conn.execute(
            "SELECT * FROM crawl_runs WHERE run_id = ?", [run_id]
        ).fetchone()

        if result is None:
            return None

        return self._row_to_run(result)

    def list_runs(
        self,
        site_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CrawlRun]:
        """List crawl runs for a site."""
        results = self.conn.execute(
            """
            SELECT * FROM crawl_runs
            WHERE site_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
            """,
            [site_id, limit, offset],
        ).fetchall()

        return [self._row_to_run(row) for row in results]

    def get_latest_run(self, site_id: str) -> CrawlRun | None:
        """Get the latest crawl run for a site."""
        result = self.conn.execute(
            """
            SELECT * FROM crawl_runs
            WHERE site_id = ?
            ORDER BY created_at DESC
            LIMIT 1
            """,
            [site_id],
        ).fetchone()

        if result is None:
            return None

        return self._row_to_run(result)

    def _row_to_run(self, row: tuple[Any, ...]) -> CrawlRun:
        """Convert a database row to a CrawlRun model."""
        stats_data = json.loads(row[11]) if isinstance(row[11], str) else (row[11] or {})
        # Handle set conversion for domains_crawled
        if "domains_crawled" in stats_data and isinstance(stats_data["domains_crawled"], list):
            stats_data["domains_crawled"] = set(stats_data["domains_crawled"])

        return CrawlRun(
            run_id=row[0],
            site_id=row[1],
            status=RunStatus(row[2]),
            error_message=row[3],
            created_at=row[4],
            started_at=row[5],
            completed_at=row[6],
            config_snapshot=json.loads(row[7]) if isinstance(row[7], str) else (row[7] or {}),
            seeds=json.loads(row[8]) if isinstance(row[8], str) else (row[8] or []),
            is_sync=row[9],
            parent_run_id=row[10],
            stats=CrawlStats(**stats_data),
            frontier_size=row[12] or 0,
            max_depth_reached=row[13] or 0,
        )

    # === Page operations ===

    def save_page(self, page: Page) -> None:
        """Save or update a page."""
        # Use INSERT ... ON CONFLICT instead of INSERT OR REPLACE
        # due to a DuckDB bug with boolean columns and INSERT OR REPLACE
        self.conn.execute(
            """
            INSERT INTO pages (
                page_id, site_id, url, canonical_url, current_version_id,
                content_hash, etag, last_modified, first_seen, last_seen,
                last_crawled, last_changed, depth, referrer_url, status_code,
                is_tombstone, error_count, last_error, version_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (page_id) DO UPDATE SET
                site_id = excluded.site_id,
                url = excluded.url,
                canonical_url = excluded.canonical_url,
                current_version_id = excluded.current_version_id,
                content_hash = excluded.content_hash,
                etag = excluded.etag,
                last_modified = excluded.last_modified,
                first_seen = excluded.first_seen,
                last_seen = excluded.last_seen,
                last_crawled = excluded.last_crawled,
                last_changed = excluded.last_changed,
                depth = excluded.depth,
                referrer_url = excluded.referrer_url,
                status_code = excluded.status_code,
                is_tombstone = excluded.is_tombstone,
                error_count = excluded.error_count,
                last_error = excluded.last_error,
                version_count = excluded.version_count
            """,
            [
                page.page_id,
                page.site_id,
                page.url,
                page.canonical_url,
                page.current_version_id,
                page.content_hash,
                page.etag,
                page.last_modified,
                page.first_seen,
                page.last_seen,
                page.last_crawled,
                page.last_changed,
                page.depth,
                page.referrer_url,
                page.status_code,
                page.is_tombstone,
                page.error_count,
                page.last_error,
                page.version_count,
            ],
        )

    def get_page(self, page_id: str) -> Page | None:
        """Get a page by ID."""
        result = self.conn.execute(
            "SELECT * FROM pages WHERE page_id = ?", [page_id]
        ).fetchone()

        if result is None:
            return None

        return self._row_to_page(result)

    def get_page_by_url(self, site_id: str, url: str) -> Page | None:
        """Get a page by normalized URL."""
        result = self.conn.execute(
            "SELECT * FROM pages WHERE site_id = ? AND url = ?", [site_id, url]
        ).fetchone()

        if result is None:
            return None

        return self._row_to_page(result)

    def list_pages(
        self,
        site_id: str,
        limit: int = 1000,
        offset: int = 0,
        include_tombstones: bool = False,
    ) -> list[Page]:
        """List pages for a site."""
        query = """
            SELECT * FROM pages
            WHERE site_id = ?
        """
        params: list[Any] = [site_id]

        if not include_tombstones:
            query += " AND is_tombstone = FALSE"

        query += " ORDER BY last_seen DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        results = self.conn.execute(query, params).fetchall()
        return [self._row_to_page(row) for row in results]

    def get_pages_needing_recrawl(
        self,
        site_id: str,
        max_age_hours: float | None = None,
        limit: int = 1000,
    ) -> list[Page]:
        """Get pages that need to be re-crawled."""
        query = """
            SELECT * FROM pages
            WHERE site_id = ? AND is_tombstone = FALSE
        """
        params: list[Any] = [site_id]

        if max_age_hours is not None:
            query += """
                AND (last_crawled IS NULL OR
                     last_crawled < CURRENT_TIMESTAMP - INTERVAL ? HOUR)
            """
            params.append(max_age_hours)

        query += " ORDER BY last_crawled ASC NULLS FIRST LIMIT ?"
        params.append(limit)

        results = self.conn.execute(query, params).fetchall()
        return [self._row_to_page(row) for row in results]

    def count_pages(self, site_id: str, include_tombstones: bool = False) -> int:
        """Count pages for a site."""
        query = "SELECT COUNT(*) FROM pages WHERE site_id = ?"
        params: list[Any] = [site_id]

        if not include_tombstones:
            query += " AND is_tombstone = FALSE"

        result = self.conn.execute(query, params).fetchone()
        return result[0] if result else 0

    def _row_to_page(self, row: tuple[Any, ...]) -> Page:
        """Convert a database row to a Page model."""
        return Page(
            page_id=row[0],
            site_id=row[1],
            url=row[2],
            canonical_url=row[3],
            current_version_id=row[4],
            content_hash=row[5],
            etag=row[6],
            last_modified=row[7],
            first_seen=row[8],
            last_seen=row[9],
            last_crawled=row[10],
            last_changed=row[11],
            depth=row[12],
            referrer_url=row[13],
            status_code=row[14],
            is_tombstone=row[15],
            error_count=row[16] or 0,
            last_error=row[17],
            version_count=row[18] or 0,
        )

    # === PageVersion operations ===

    def save_version(self, version: PageVersion) -> None:
        """Save a page version."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO page_versions (
                version_id, page_id, site_id, run_id, markdown, html, plain_text,
                content_hash, raw_hash, url, canonical_url, title, description,
                content_type, status_code, language, headings_outline, word_count,
                char_count, outlinks, internal_link_count, external_link_count,
                etag, last_modified, crawled_at, created_at, fetch_latency_ms,
                extraction_latency_ms, is_tombstone, extra
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                version.version_id,
                version.page_id,
                version.site_id,
                version.run_id,
                version.markdown,
                version.html,
                version.plain_text,
                version.content_hash,
                version.raw_hash,
                version.url,
                version.canonical_url,
                version.title,
                version.description,
                version.content_type,
                version.status_code,
                version.language,
                json.dumps(version.headings_outline),
                version.word_count,
                version.char_count,
                json.dumps(version.outlinks),
                version.internal_link_count,
                version.external_link_count,
                version.etag,
                version.last_modified,
                version.crawled_at,
                version.created_at,
                version.fetch_latency_ms,
                version.extraction_latency_ms,
                version.is_tombstone,
                json.dumps(version.extra),
            ],
        )

    def get_version(self, version_id: str) -> PageVersion | None:
        """Get a page version by ID."""
        result = self.conn.execute(
            "SELECT * FROM page_versions WHERE version_id = ?", [version_id]
        ).fetchone()

        if result is None:
            return None

        return self._row_to_version(result)

    def get_current_version(self, page_id: str) -> PageVersion | None:
        """Get the current version for a page."""
        result = self.conn.execute(
            """
            SELECT pv.* FROM page_versions pv
            JOIN pages p ON p.current_version_id = pv.version_id
            WHERE p.page_id = ?
            """,
            [page_id],
        ).fetchone()

        if result is None:
            return None

        return self._row_to_version(result)

    def list_versions(
        self,
        page_id: str,
        limit: int = 100,
    ) -> list[PageVersion]:
        """List versions for a page."""
        results = self.conn.execute(
            """
            SELECT * FROM page_versions
            WHERE page_id = ?
            ORDER BY crawled_at DESC
            LIMIT ?
            """,
            [page_id, limit],
        ).fetchall()

        return [self._row_to_version(row) for row in results]

    def _row_to_version(self, row: tuple[Any, ...]) -> PageVersion:
        """Convert a database row to a PageVersion model."""
        return PageVersion(
            version_id=row[0],
            page_id=row[1],
            site_id=row[2],
            run_id=row[3],
            markdown=row[4],
            html=row[5],
            plain_text=row[6],
            content_hash=row[7],
            raw_hash=row[8],
            url=row[9],
            canonical_url=row[10],
            title=row[11],
            description=row[12],
            content_type=row[13],
            status_code=row[14],
            language=row[15],
            headings_outline=json.loads(row[16]) if isinstance(row[16], str) else (row[16] or []),
            word_count=row[17] or 0,
            char_count=row[18] or 0,
            outlinks=json.loads(row[19]) if isinstance(row[19], str) else (row[19] or []),
            internal_link_count=row[20] or 0,
            external_link_count=row[21] or 0,
            etag=row[22],
            last_modified=row[23],
            crawled_at=row[24],
            created_at=row[25],
            fetch_latency_ms=row[26],
            extraction_latency_ms=row[27],
            is_tombstone=row[28],
            extra=json.loads(row[29]) if isinstance(row[29], str) else (row[29] or {}),
        )

    # === FrontierItem operations ===

    def save_frontier_item(self, item: FrontierItem) -> None:
        """Save a frontier item."""
        self.conn.execute(
            """
            INSERT OR REPLACE INTO frontier_items (
                item_id, run_id, site_id, url, normalized_url, url_hash,
                depth, referrer_url, priority, status, retry_count, last_error,
                discovered_at, scheduled_at, started_at, completed_at, domain
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                item.item_id,
                item.run_id,
                item.site_id,
                item.url,
                item.normalized_url,
                item.url_hash,
                item.depth,
                item.referrer_url,
                item.priority,
                item.status.value,
                item.retry_count,
                item.last_error,
                item.discovered_at,
                item.scheduled_at,
                item.started_at,
                item.completed_at,
                item.domain,
            ],
        )

    def get_frontier_items(
        self,
        run_id: str,
        status: str | None = None,
        limit: int = 1000,
    ) -> list[FrontierItem]:
        """Get frontier items for a run."""
        query = "SELECT * FROM frontier_items WHERE run_id = ?"
        params: list[Any] = [run_id]

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY priority DESC, discovered_at ASC LIMIT ?"
        params.append(limit)

        results = self.conn.execute(query, params).fetchall()
        return [self._row_to_frontier_item(row) for row in results]

    def update_frontier_status(
        self,
        item_id: str,
        status: str,
        error: str | None = None,
    ) -> None:
        """Update frontier item status."""
        if error:
            self.conn.execute(
                """
                UPDATE frontier_items
                SET status = ?, last_error = ?, completed_at = CURRENT_TIMESTAMP
                WHERE item_id = ?
                """,
                [status, error, item_id],
            )
        else:
            self.conn.execute(
                """
                UPDATE frontier_items
                SET status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE item_id = ?
                """,
                [status, item_id],
            )

    def clear_frontier(self, run_id: str) -> int:
        """Clear all frontier items for a run."""
        result = self.conn.execute(
            "DELETE FROM frontier_items WHERE run_id = ?", [run_id]
        )
        return result.rowcount if hasattr(result, "rowcount") else 0

    def _row_to_frontier_item(self, row: tuple[Any, ...]) -> FrontierItem:
        """Convert a database row to a FrontierItem model."""
        return FrontierItem(
            item_id=row[0],
            run_id=row[1],
            site_id=row[2],
            url=row[3],
            normalized_url=row[4],
            url_hash=row[5],
            depth=row[6],
            referrer_url=row[7],
            priority=row[8],
            status=FrontierStatus(row[9]),
            retry_count=row[10] or 0,
            last_error=row[11],
            discovered_at=row[12],
            scheduled_at=row[13],
            started_at=row[14],
            completed_at=row[15],
            domain=row[16],
        )

    # === Bulk operations ===

    def save_pages_bulk(self, pages: list[Page]) -> int:
        """Bulk save pages."""
        for page in pages:
            self.save_page(page)
        return len(pages)

    def save_versions_bulk(self, versions: list[PageVersion]) -> int:
        """Bulk save versions."""
        for version in versions:
            self.save_version(version)
        return len(versions)

    @staticmethod
    def _json_serializer(obj: Any) -> Any:
        """JSON serializer for objects not serializable by default."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj, Path):
            return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
