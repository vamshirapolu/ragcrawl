"""DynamoDB storage backend for ragcrawl."""

try:
    from ragcrawl.storage.dynamodb.backend import DynamoDBBackend
    from ragcrawl.storage.dynamodb.models import (
        CrawlRunModel,
        FrontierItemModel,
        PageModel,
        PageVersionModel,
        SiteModel,
    )

    __all__ = [
        "DynamoDBBackend",
        "SiteModel",
        "CrawlRunModel",
        "PageModel",
        "PageVersionModel",
        "FrontierItemModel",
    ]
except ImportError:
    # DynamoDB dependencies not installed
    __all__ = []
