# Bilingual generation evaluation protocol (v1)

Status: synthetic fixture specification and offline evaluator self-test. No live LLM runs, scores or independent human review are claimed.

The four cases in [cases-v1.json](cases-v1.json) are fictional English/French timestamped transcript and vision-context pairs, including missing-information cases. They assess the generation stage only, not speech or visual recognition. Frame names are synthetic context references; no binary screenshots are included. Evaluate image placement from the supplied timestamps and captions, not actual image pixels.

## Procedure

1. Pin code commit, system prompt digest, model deployment/version, API version and generation parameters. Obtain owner approval for any live calls and budget. Never send customer media.
2. Run each case separately using the generation function with MOCK_GENERATION=false. Store raw Markdown and run metadata in a non-public evaluation workspace until reviewed. Capture elapsed time, token usage where available, errors and retries.
3. A human reviewer compares each output with the fixture, recording supporting excerpts and ratings from the rubric. Ideally use a second reviewer for disagreement resolution; report who authored and reviewed fixtures.
4. Repeat three times per case to capture nondeterminism, report all runs and failure cases, do not cherry-pick.

## Rubric (0–2 points each)

| Dimension | 0 | 1 | 2 |
| --- | --- | --- | --- |
| Factual fidelity | Material incorrect claim | Minor inaccuracy | All claims supported |
| Completeness | Multiple required facts missing | One required fact missing | All required facts included |
| Language consistency | Wrong language | Mixed language beyond names/terms | Correct language throughout |
| Structure | Multiple missing Diátaxis sections | One missing or poorly separated | Four coherent sections |
| Frame alignment | Invented or materially misplaced frame | Existing frame omitted or weakly placed | Only supplied frame references, context-aligned |
| Unsupported claims/uncertainty | Invents missing procedure or contradicts evidence | Ambiguity not made explicit | Missing information acknowledged without invention |

Proposed acceptance: each run scores at least 10/12, no zero on any dimension, no unsupported material claim and no invented frame. This threshold is a proposed engineering criterion, not a benchmark established from empirical results.

Record case ID, repeat, commit, prompt hash, model/version, parameters, reviewer, dimension scores, supporting evidence, latency, token usage and any failure. Report pass rate and distribution over all attempted runs. Do not equate four authored cases with representative production coverage. Actual end-to-end media and real model quality require separately approved experiments.

## Offline evaluator self-test

Run `python -m evals.run_offline --output evaluation-report.json` from the repository root. The standard-library runner uses four unchanged fixtures, each with one constructed reference and four deliberately corrupted variants. It verifies exact section order, required literal presence, absence of selected unsupported literals and a frame-name allowlist. Expected and actual Boolean checks, fixture and output digests, and deterministic aggregate counts are recorded. Twenty expected-outcome executions are not twenty model runs. The reference is derived from its own fixture; this tests the evaluator, not the model. Literal checks cannot detect semantic paraphrases, negation, hallucinations beyond the enumerated phrases, linguistic fidelity or frame placement quality. Human review and live-model quality remain null. No network or provider calls.
