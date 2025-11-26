"""ragcrawl - Recursive website crawler producing LLM-ready knowledge base artifacts."""

from ragcrawl.config.crawler_config import CrawlerConfig
from ragcrawl.config.output_config import OutputConfig, OutputMode
from ragcrawl.config.storage_config import DuckDBConfig, DynamoDBConfig, StorageConfig
from ragcrawl.config.sync_config import SyncConfig, SyncStrategy
from ragcrawl.core.crawl_job import CrawlJob, CrawlResult
from ragcrawl.core.sync_job import SyncJob, SyncResult
from ragcrawl.models.chunk import Chunk
from ragcrawl.models.crawl_run import CrawlRun, RunStatus
from ragcrawl.models.document import Document
from ragcrawl.models.page import Page
from ragcrawl.models.page_version import PageVersion
from ragcrawl.models.site import Site

__version__ = "0.1.0"

__all__ = [
    # Version
    "__version__",
    # Config
    "CrawlerConfig",
    "SyncConfig",
    "SyncStrategy",
    "StorageConfig",
    "DuckDBConfig",
    "DynamoDBConfig",
    "OutputConfig",
    "OutputMode",
    # Jobs
    "CrawlJob",
    "CrawlResult",
    "SyncJob",
    "SyncResult",
    # Models
    "Document",
    "Page",
    "PageVersion",
    "CrawlRun",
    "RunStatus",
    "Site",
    "Chunk",
]
