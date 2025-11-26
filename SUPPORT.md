# Support

## Getting Help
- **Questions / How-to**: Open a GitHub Issue (or GitHub Discussions if enabled).
- **Bug reports**: Use the issue template and include:
  - OS + Python version
  - command/config used
  - logs (redact secrets)
  - minimal reproduction steps

## Feature Requests
Open an Issue and describe:
- the user problem / use case
- expected behavior
- constraints (scale, compliance, auth, JS rendering, etc.)

## Security Issues
Please do **not** open a public issue for security vulnerabilities.
Instead, use GitHub’s private vulnerability reporting (Security → Advisories) if enabled,
or contact the maintainer privately via GitHub profile.

## Compatibility Notes
Crawling behavior depends heavily on target websites:
- respect robots.txt and site terms
- be mindful of rate limits and authentication
- prefer sync strategies that minimize load (ETag/Last-Modified, sitemaps, conditional GET)