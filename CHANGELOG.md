# Changelog

## v0.1.0 — Experimental Community Release

Initial independently distributed Apache-2.0 edition of the video-to-documentation proof of value.

### Added

- Three independent mock flags and deterministic, clearly labeled synthetic Markdown output.
- Credential-free API and CLI regression paths, including prevention of accidental offline uploads.
- Generated test-pattern video and audio fixture for actual FFmpeg decoding, timestamps and frame embedding tests.
- Literal-text preview with a bounded display length; full Markdown copy/download preserved.
- Upload filename validation and prevention of cloud fallback for unknown mock API jobs.
- Nine Python and three JavaScript regression tests and an independent Python dependency advisory scan in CI.
- Manual-only Azure deployment workflows; SHA-pinned Node.js 24-native CI actions.
- Architecture decision record and four synthetic English/French generation evaluation fixtures with a proposed human-review rubric.

### Verification

[Baseline main CI](https://github.com/kibnelbachyr/video2doc-ai-community/actions/runs/45766562173) passed all 12 tests on Python 3.11 and Node.js on the GitHub-hosted runner. The resolved API Python dependency audit reported no known vulnerabilities at the time of the scan, following remediation of 18 previous findings. Release changes require passing CI before tagging. No Azure resources were deployed or live AI services invoked during this validation.

### Limitations

- Mock output does not analyze video. Actual media decoding is tested separately using synthetic media.
- Live transcription, vision and LLM quality, multilingual fidelity, end-to-end live execution, cost and latency remain unmeasured.
- No authentication or tenant isolation, durable queue, guaranteed recovery or production resource limits. Do not expose this service publicly or use it for sensitive recordings.
- Raw Markdown downloads remain untrusted. Rich HTML preview is intentionally deferred.
- Python advisory scanning is point-in-time and does not cover all runtime, container, OS or infrastructure vulnerabilities. Full secret scanning and third-party dependency-license review remain incomplete.
- The evaluation protocol is a design, not an empirical quality result.
