# Changelog

All notable changes to this project will be documented in this file.

The format is based on **Keep a Changelog**, and this project follows **Semantic Versioning**.

## [0.0.1] - 2025-11-26
### Added
- Project scaffolding and initial MVP baseline for ragcrawl.
- Initial architecture for recursive crawling, KB/RAG-ready Markdown generation, chunking, and exporters.
- Pluggable storage backends: DuckDB (default) + optional DynamoDB via PynamoDB.
- Incremental sync using conditional requests (ETag/Last-Modified), sitemap prioritization, and content-hash diffs.
- Markdown publishing formats: single-page output and multi-page output with folder structure and link rewriting.
- Centralized DuckDB storage defaulting to `~/.ragcrawl/` and CLI commands for config/listing.

### Changed
- N/A

### Fixed
- N/A