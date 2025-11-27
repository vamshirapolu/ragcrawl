# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Community documentation and governance files
- Comprehensive test suite for project metadata validation
- Enhanced documentation with community guidelines

## [0.0.1] - 2025-11-26

### Added
- Project scaffolding and initial MVP baseline for ragcrawl
- Initial architecture for recursive crawling, KB/RAG-ready Markdown generation, chunking, and exporters
- Pluggable storage backends: DuckDB (default) + optional DynamoDB via PynamoDB
- Incremental sync using conditional requests (ETag/Last-Modified), sitemap prioritization, and content-hash diffs
- Markdown publishing formats: single-page output and multi-page output with folder structure and link rewriting
- Centralized DuckDB storage defaulting to `~/.ragcrawl/` and CLI commands for config/listing
- Apache License 2.0 with proper SPDX identifier
- Community governance files:
  - CODE_OF_CONDUCT.md (Contributor Covenant)
  - CONTRIBUTING.md (Development setup and guidelines)
  - SUPPORT.md (Getting help and reporting issues)
  - Issue templates for bug reports and feature requests
- Comprehensive documentation site with MkDocs Material theme

### Changed
- N/A (initial release)

### Fixed
- N/A (initial release)

### Security
- N/A (initial release)

---

## Release Notes

### Version 0.0.1 - Initial Release

This is the first public release of ragcrawl, a recursive website crawler designed to produce LLM-ready knowledge base artifacts.

**Key Features:**
- Recursive crawling with pattern-based filtering
- Clean Markdown extraction optimized for RAG pipelines
- Incremental sync with change detection
- Pluggable storage (DuckDB and DynamoDB)
- Built-in chunking strategies
- CLI and Python API

**Getting Started:**
```bash
pip install ragcrawl
ragcrawl crawl https://docs.example.com --max-pages 100
```

See the [documentation](https://vamshirapolu.github.io/ragcrawl) for more details.

---

[Unreleased]: https://github.com/vamshirapolu/ragcrawl/compare/v0.0.1...HEAD
[0.0.1]: https://github.com/vamshirapolu/ragcrawl/releases/tag/v0.0.1
