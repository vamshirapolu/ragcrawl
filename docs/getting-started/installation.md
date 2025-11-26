# Installation

## Requirements

- Python 3.10 or higher
- pip or uv package manager

## Installation Options

### Basic Installation

The basic installation includes DuckDB storage and HTTP-only fetching:

```bash
pip install ragcrawl
```

Or with uv:

```bash
uv pip install ragcrawl
```

### Browser Rendering Support

For JavaScript-heavy sites, install with browser support:

```bash
pip install ragcrawl[browser]
```

This installs Playwright for headless browser rendering.

After installation, set up Playwright:

```bash
playwright install chromium
```

### DynamoDB Support

For cloud deployments with AWS DynamoDB:

```bash
pip install ragcrawl[dynamodb]
```

### Full Installation

Install all optional dependencies:

```bash
pip install ragcrawl[all]
```

### Development Installation

For contributing to the project:

```bash
git clone https://github.com/your-org/ragcrawl.git
cd ragcrawl
pip install -e ".[dev]"
```

## Verifying Installation

Test your installation:

```bash
# Check CLI is available
ragcrawl --version

# Run a simple crawl
ragcrawl crawl https://example.com --max-pages 5 --output ./test-output
```

## Dependencies

### Core Dependencies

| Package | Purpose |
|---------|---------|
| crawl4ai | Web fetching and HTML-to-Markdown conversion |
| duckdb | Default local storage backend |
| httpx | Async HTTP client |
| pydantic | Data validation and configuration |
| structlog | Structured logging |
| xxhash | Fast content hashing |
| tiktoken | Token counting for chunking |
| click | Command-line interface |

### Optional Dependencies

| Package | Purpose | Extra |
|---------|---------|-------|
| playwright | Browser rendering | `[browser]` |
| pynamodb | DynamoDB ORM | `[dynamodb]` |

## Troubleshooting

### Playwright Installation Issues

If you encounter issues with Playwright:

```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt-get install libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2

# Install browsers
playwright install chromium
```

### DuckDB Permission Issues

Ensure the storage directory is writable:

```bash
# Create with proper permissions
mkdir -p ./data
chmod 755 ./data
ragcrawl crawl https://example.com --storage ./data/crawler.duckdb
```

### AWS Credentials for DynamoDB

Set up AWS credentials for DynamoDB:

```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

Or use AWS profiles:

```bash
aws configure --profile crawler
export AWS_PROFILE=crawler
```
