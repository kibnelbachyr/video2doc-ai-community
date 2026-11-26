# Portfolio readiness and evidence

This is a proof-of-value project, not a production-ready service. This checklist defines the public engineering evidence required before calling it a reproducible reference implementation. It complements the existing [production readiness plan](production-readiness-plan.md); it does not replace it.

## Release gates

| Gate | Acceptance evidence | Status |
| --- | --- | --- |
| P0 — Publication boundary | Owner confirms rights to publish code, documentation and examples; review current and historical content for customer material, secrets and personal data; decide licensing explicitly | Open |
| P1 — Reproducible local run | CI-verified credential-free synthetic API and CLI run; no real media is decoded in mock mode. Real synthetic-video decoding remains unverified | Offline baseline verified; real-media run open |
| P2 — Automated verification | CI runs formatting/lint, unit tests and offline smoke test on pull requests; dependency and secret scans enabled; failures block release | Open |
| P3 — Architectural evidence | Document job lifecycle, trust boundaries, failure modes, retry and idempotency decisions, and deployment assumptions; link ADRs from architecture docs | Open |
| P4 — AI evaluation | Version a synthetic French/English fixture set and rubric; evaluate factual fidelity, completeness, language consistency, image alignment and unsupported claims; record model/prompt versions and human review | Open |
| P5 — Operational evidence | Publish reproducible latency, failure-rate and cost-per-video measurements with assumptions; document remaining gaps and teardown steps | Open |

## Initial work sequence

1. Confirm P0 before further public examples or releases. No license is implied by public visibility.
2. Validate local setup and mock mode in a clean environment. Add a synthetic fixture and a deterministic generation stub if the current mock path requires a live model.
3. Add a minimal PR-only CI workflow, without cloud deployments or secrets. Start with timestamp utilities, job state transitions and an end-to-end offline smoke test.
4. Record architecture decisions: background thread vs durable queue, job storage, model output handling and access boundaries.
5. Establish a small evaluation baseline and cost measurement protocol. Do not publish performance or quality claims without measurements.

## Evidence policy

- Use synthetic, self-authored or explicitly licensed fixtures only.
- Never commit credentials, private customer recordings, tenant identifiers or generated documents containing sensitive material.
- Separate measured results from estimates; record environment, sample size, model version and test date.
- Treat generated output as untrusted until reviewed. A passing evaluation is not a security guarantee.
- Label releases accurately; a portfolio-ready demo is not equivalent to enterprise production readiness.

## Definition of done

P0–P5 have documented evidence, known limitations are explicit, and a new reader can reproduce the baseline without relying on private infrastructure. The existing production readiness plan remains the source of truth for enterprise deployment milestones.

## Verified offline baseline

[Initial CI run](https://github.com/kibnelbachyr/video2doc-ai-community/actions/runs/45763217620) passed five tests on Python 3.11, with Python socket connections and Blob calls guarded during tests. Dependency installation is online. This is not a real-media, LLM-quality or production-security validation. [Hardening CI run](https://github.com/kibnelbachyr/video2doc-ai-community/actions/runs/45763474700) passed six Python tests and three Node preview tests. The preview is literal text, not browser-sanitized rich HTML. Deployment workflows are manual-only.

## Media and dependency evidence increment

The synthetic-media tests create a three-second local test-pattern video and sine-wave audio using FFmpeg; no customer media or model calls are involved. They check actual frame extraction, audio decoding/chunking, timestamp formatting and embedding of extracted images. They do not measure real speech recognition, image understanding, translation or documentation quality. CI installs FFmpeg and dependencies over the network, then runs the tests locally. The separate dependency-audit job resolves the API requirements in a clean virtual environment and runs pip-audit against the resolved packages. Any findings or scanner failure must be reviewed before release; a clean Python advisory scan does not cover OS, browser or infrastructure risks. Results for this increment are pending CI.

## Dependency remediation

[Media and dependency CI run](https://github.com/kibnelbachyr/video2doc-ai-community/actions/runs/45763652369) passed the nine Python tests and JavaScript preview checks, but pip-audit reported 18 advisories affecting four installed packages: Starlette 0.37.2 (7), python-multipart 0.0.9 (7), requests 2.31.0 (3), python-dotenv 1.0.1 (1). The media PR was merged before the audit passed. Publication remains blocked. Candidate remediation pins FastAPI 0.165.0 (requires Starlette >=1.6.0), Starlette 1.10.0, python-multipart 0.0.34, requests 2.34.2 and python-dotenv 1.2.4. Shared CLI requirements are updated consistently. No advisory exemptions, disabled checks or continue-on-error settings. Compatibility and remediation must be verified by fresh successful CI, including dependency audit; no claim that these pins resolve all known issues until that evidence exists. No Azure operations.
