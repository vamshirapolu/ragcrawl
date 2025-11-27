# Contributing to ragcrawl

Thanks for taking the time to contribute! 🎉

## Code of Conduct

By participating in this project, you agree to follow the rules in our [Code of Conduct](code-of-conduct.md).

## How to Contribute

### Report Bugs

Open an [Issue](https://github.com/vamshirapolu/ragcrawl/issues) with:
- Reproduction steps
- Logs (redact any secrets)
- Environment details (OS, Python version, ragcrawl version)

### Request Features

Open an [Issue](https://github.com/vamshirapolu/ragcrawl/issues) describing:
- The use case and desired behavior
- Any constraints (scale, compliance, auth, JS rendering, etc.)

### Submit Pull Requests

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add/update tests
5. Update documentation
6. Open a Pull Request

## Development Setup

### Prerequisites

- Python 3.10+ (3.11 or 3.12 recommended)
- `uv` recommended (but `pip` works too)

### Setup with uv (recommended)

```bash
git clone https://github.com/vamshirapolu/ragcrawl.git
cd ragcrawl
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

### Setup with pip

```bash
git clone https://github.com/vamshirapolu/ragcrawl.git
cd ragcrawl
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -U pip
pip install -e ".[dev]"
```

## Running the Project

```bash
# Show CLI help
ragcrawl --help

# Run a simple crawl
ragcrawl crawl https://example.com --max-pages 10
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ragcrawl --cov-report=html

# Run specific test file
pytest tests/unit/test_url_normalizer.py

# Run with verbose output
pytest -v
```

## Linting and Formatting

We use **Ruff** for linting and formatting:

```bash
# Check code
ruff check .

# Format code
ruff format .

# Run both
ruff check . && ruff format .
```

## Type Checking

We use **mypy** for type checking:

```bash
mypy src/ragcrawl
```

## Documentation

We use **MkDocs** with Material theme:

```bash
# Serve docs locally
mkdocs serve

# Build docs
mkdocs build

# Deploy docs (maintainers only)
mkdocs gh-deploy
```

## Pull Request Guidelines

- **Keep PRs focused** - One feature/fix per PR when possible
- **Add/adjust tests** - When behavior changes
- **Update docs** - If you add/modify public-facing behavior
- **Backwards compatibility** - Keep it for public APIs, or clearly call out breaking changes
- **Write clear commit messages** - See guidance below

## Commit Message Guidance

We follow conventional commits (suggested):

- `feat: ...` - New feature
- `fix: ...` - Bug fix
- `docs: ...` - Documentation only
- `test: ...` - Adding or updating tests
- `refactor: ...` - Code refactoring
- `chore: ...` - Build/tooling changes

Examples:
```
feat: add support for custom user agents
fix: handle 404 errors in sync job
docs: update installation instructions
test: add tests for URL normalization
```

## Code Style

- Follow PEP 8 (enforced by Ruff)
- Use type hints for all functions
- Write docstrings in Google style
- Keep functions focused and testable
- Prefer composition over inheritance

## Testing Guidelines

- Write unit tests for new functionality
- Use pytest fixtures for common setup
- Mock external dependencies (HTTP, file system, etc.)
- Aim for high coverage, but focus on critical paths
- Add integration tests for end-to-end scenarios

## Security

Please do **not** open public issues for security vulnerabilities. See [Support](support.md) for the preferred reporting path.

## Questions?

If you have questions about contributing, feel free to:
- Open a [GitHub Discussion](https://github.com/vamshirapolu/ragcrawl/discussions) (if enabled)
- Ask in an [Issue](https://github.com/vamshirapolu/ragcrawl/issues)
- Check our [Support](support.md) page

Thank you for contributing to ragcrawl! 🚀
