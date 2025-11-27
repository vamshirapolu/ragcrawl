# Support

## Getting Help

### Questions and How-To

- **GitHub Issues** - Open an [issue](https://github.com/vamshirapolu/ragcrawl/issues) for questions
- **GitHub Discussions** - Use [discussions](https://github.com/vamshirapolu/ragcrawl/discussions) for community Q&A (if enabled)
- **Documentation** - Check our comprehensive [documentation](../index.md)

### Bug Reports

When reporting a bug, please include:

- **OS and Python version** - e.g., "macOS 14.0, Python 3.11.5"
- **ragcrawl version** - Run `ragcrawl --version`
- **Installation method** - pip, uv, or from source
- **Command/config used** - The exact command or configuration
- **Logs** - Include relevant logs (redact any secrets/tokens)
- **Minimal reproduction steps** - Steps to reproduce the issue

Example:
```
OS: Ubuntu 22.04
Python: 3.11.5
ragcrawl: 0.0.1
Install: pip install ragcrawl

Command:
ragcrawl crawl https://example.com --max-pages 100

Error:
[paste error message here]
```

## Feature Requests

When requesting a feature, please describe:

- **User problem / use case** - What are you trying to accomplish?
- **Expected behavior** - What should happen?
- **Constraints** - Any specific requirements (scale, compliance, auth, JS rendering, etc.)
- **Alternatives considered** - What workarounds have you tried?

## Security Issues

Please do **not** open a public issue for security vulnerabilities.

Instead:
1. Use GitHub's [private vulnerability reporting](https://github.com/vamshirapolu/ragcrawl/security/advisories) (if enabled)
2. Or contact the maintainer privately via their GitHub profile

We will respond as quickly as possible and work with you to address the issue.

## Compatibility Notes

Crawling behavior depends heavily on target websites:

- **Respect robots.txt** - Honor site crawling policies
- **Respect site terms** - Follow the target site's terms of service
- **Be mindful of rate limits** - Don't overwhelm servers
- **Handle authentication properly** - Use appropriate auth methods
- **Prefer efficient strategies** - Use ETag/Last-Modified, sitemaps, conditional GET

## Common Issues

### Installation Problems

**Issue**: `pip install ragcrawl` fails

**Solution**: 
- Ensure Python 3.10+ is installed
- Try upgrading pip: `pip install --upgrade pip`
- Use a virtual environment

### Browser Mode Issues

**Issue**: Browser mode not working

**Solution**:
- Install browser dependencies: `pip install ragcrawl[browser]`
- Install Playwright browsers: `playwright install`

### DuckDB Permissions

**Issue**: Permission denied for DuckDB file

**Solution**:
- Check file permissions on `~/.ragcrawl/`
- Specify a custom path: `--storage /path/to/crawler.duckdb`

### Rate Limiting

**Issue**: Getting rate limited or blocked

**Solution**:
- Reduce concurrency: `--max-concurrency 2`
- Add delays between requests
- Check and respect robots.txt
- Use a custom user agent

## Response Times

- **Bug reports**: We aim to respond within 2-3 business days
- **Feature requests**: We review and prioritize quarterly
- **Security issues**: We respond within 24 hours

## Contributing

If you'd like to help improve ragcrawl, see our [Contributing Guide](contributing.md).

## Community

Join our community:
- Star the [GitHub repository](https://github.com/vamshirapolu/ragcrawl)
- Follow development updates
- Share your use cases and feedback
