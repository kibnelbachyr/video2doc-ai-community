# Contributing

Thank you for helping improve this experimental reference implementation.

## What to work on

- Reproducible local development, tests, documentation and small architecture improvements.
- Clearly scoped issues with expected behavior, current behavior and a minimal reproducible example.
- Synthetic or explicitly licensed fixtures only. Do not include private recordings, real account identifiers, employer/customer material or secrets.

## Workflow

1. Open an issue for significant changes; discuss the problem and acceptance criteria.
2. Create a feature branch and keep the PR focused. Describe design trade-offs, limitations, and verification.
3. Use Python 3.11 and Node.js 24; install FFmpeg for media tests.
4. Run:

   ```bash
   python -m pip install -r api/requirements.txt httpx==0.27.2
   python -m unittest discover -s tests -v
   node --test tests/test_preview.js
   ```

5. Wait for both `test` and `dependency-audit` checks to pass. Do not bypass a failing audit or trigger Azure deployment to test a PR.
6. Review generated content and AI-assisted changes yourself. Do not report unmeasured model quality, cost or security claims as facts.

Contributions are intended for distribution under the project's Apache-2.0 license. Submit only material you are authorized to contribute. Third-party material must retain required attribution and licensing.

See [engineering evidence](docs/portfolio-readiness.md), [ADR-001](docs/adr/001-execution-and-trust-boundaries.md) and [security policy](SECURITY.md).
