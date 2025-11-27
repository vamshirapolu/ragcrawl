# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.0.2] - 2025-11-27

### Added
- Enhanced documentation with community guidelines and contribution guide
- Markdown extraction configuration reference and README coverage for `MarkdownConfig`
- CLI support for `--markdown-config` (TOML/JSON) and docs showing how to invoke it

### Changed
- Tuned default Markdown extraction for doc-like sites (pruning threshold 0.55, min words 15, text block threshold 15)

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