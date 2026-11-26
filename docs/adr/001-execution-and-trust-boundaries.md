# ADR-001 — Execution and trust boundaries

Status: Accepted for experimental reference scope; not production approval.

## Context and decision

The proof of value uses FastAPI, a daemon thread per accepted job, local temporary media processing, Azure AI providers and Blob-backed state. Keep this simple execution model for local experiments rather than introduce a managed queue or cloud resources before validating the need. Retain the three mock controls and literal-text preview; deploy manually only. This decision prioritizes low-cost reproducibility and explicit limitations, not availability or multi-tenant isolation.

## Current job lifecycle

1. POST /api/jobs validates filename/extension; live mode reads the upload, creates a pending state and uploads the file. The two media mock flags instead use in-memory state and discard the body.
2. A background daemon thread marks processing and records transcription, frame extraction, vision analysis and document generation steps.
3. The runner persists Markdown before setting status done. In media mock mode, state and results are process-local; use one worker.
4. The polling client retrieves state and, when done, retrieves the full Markdown. The preview assigns literal text, and copy/download preserve raw output.
5. Exceptions attempt to mark failed. Temporary local files are removed in the runner finally block; Blob cleanup is not guaranteed by this logic.

## Boundaries and failure modes

| Boundary | Current behavior | Residual risk / future decision |
| --- | --- | --- |
| Browser -> API | Filename and extension checks; live size check after reading | No authenticated job ownership; CORS permissive; proxy/parser and resource exhaustion limits not established |
| API -> worker | Daemon thread; no durable queue | Crash or restart can leave pending/processing jobs; no recovery, lease or concurrency cap |
| Worker -> state/result | Blob overwrite or process-local dictionaries | No compare-and-swap, deduplication, transactional commit or enforced transition table; retrying submission may create duplicate jobs |
| Media -> providers | Transcripts, frame captions and OCR sent to generation | Untrusted input, privacy/residency review, prompt injection and unsupported claims; model prompt alone is not a security boundary |
| Provider failures | Generation retries rate limits; other failures propagate to job failure | No complete retry taxonomy, end-to-end deadline or guaranteed failure-state write |
| Generated output -> browser | Literal-text preview; bounded display; raw download | External Markdown viewers may render dangerous content; no rich-preview sanitization assurance |
| Logging and retention | Errors and filenames can enter logs/state; local temp cleanup | Raw exceptions may disclose sensitive details; no retention/erasure guarantees for Blob data |
| Deployment | Manual workflow dispatch; infrastructure template exists | No deployed security or cost evidence; live configuration and authorization must be separately reviewed |

## Alternatives considered

- Durable queue and isolated workers: preferred when reliable replay, bounded concurrency and recovery are required; deferred.
- Rich Markdown preview with maintained sanitizer: possible later with strict image/link policy, CSP and real browser tests; deferred in favor of literal text.
- Always-live provider workflow: rejected for regression CI because it requires credentials, spend and nondeterministic model outputs.

## Production prerequisites

Authenticated job ownership, bounded uploads and worker resources, durable queue with idempotent jobs and lease-based recovery, sanitized error handling, retention/cleanup, least-privilege storage, private networking where appropriate, provider timeout/retry budgets, prompt/output evaluation and operating metrics. Revisit this ADR before any shared or customer-facing deployment. A passing offline test is not a production security boundary.
