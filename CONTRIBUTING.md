# Contributing to ragcrawl

Thanks for taking the time to contribute! 🎉

## Code of Conduct
By participating in this project, you agree to follow the rules in `CODE_OF_CONDUCT.md`.

## How to Contribute
- **Report bugs**: open an Issue with reproduction steps, logs, and environment details.
- **Request features**: open an Issue describing the use case and desired behavior.
- **Submit PRs**: fork the repo, create a feature branch, and open a Pull Request.

## Development Setup

### Prerequisites
- Python 3.11+ (3.12 recommended)
- `uv` recommended (but `pip` works too)

### Setup with uv (recommended)
```bash
git clone https://github.com/vamshirapolu/ragcrawl.git
cd ragcrawl
uv venv
uv pip install -e ".[dev]"

Setup with pip

python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e ".[dev]"

Running the Project

ragcrawl --help

Running Tests

pytest -q

Linting / Formatting

If the repo uses Ruff:

ruff check .
ruff format .

If the repo uses Black:

black .

Docs (MkDocs)

mkdocs serve

Pull Request Guidelines
	•	Keep PRs focused (one feature/fix per PR when possible).
	•	Add/adjust tests when behavior changes.
	•	Update docs if you add/modify public-facing behavior.
	•	Keep backwards compatibility for public APIs, or clearly call out breaking changes.

Commit Message Guidance (suggested)
	•	feat: ... new feature
	•	fix: ... bug fix
	•	docs: ... docs-only
	•	chore: ... build/tooling

Security

Please do not open public issues for security vulnerabilities. See SUPPORT.md for the preferred reporting path.