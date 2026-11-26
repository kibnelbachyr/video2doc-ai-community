# Security policy

## Scope

This repository is an experimental proof of value, not a supported production service. No guaranteed security maintenance or response-time commitment is offered. The API has no authenticated job ownership or tenant isolation. Run it on localhost with synthetic data. Do not expose it publicly, process confidential recordings or deploy it to shared environments without a separate security review.

Generated Markdown, transcript text and OCR output are untrusted. The included browser preview uses literal text; other viewers may interpret HTML, links and images.

## Reporting a vulnerability

Do not publish exploit details, credentials, personal information or customer data in a public issue. If GitHub private vulnerability reporting is enabled, use the repository's Security tab and Report a vulnerability. Otherwise request a private reporting channel from the maintainer via a minimal issue with no sensitive details. Include an affected commit/version, impact, safe synthetic reproduction and suggested mitigation in the private report.

## Verification and boundaries

CI runs Python/JavaScript regression checks and a Python dependency advisory scan. A clean scan is point-in-time evidence, not proof of security. Dependency licensing, container/OS advisories, secret detection and production controls require additional review.

See [ADR-001](docs/adr/001-execution-and-trust-boundaries.md) for known trust boundaries and [release notes](CHANGELOG.md) for scope.
