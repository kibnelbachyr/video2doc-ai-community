---
marp: true
theme: default
paginate: true
size: 16:9
---

# video2doc-ai

### From screen recording to structured documentation — automatically

**Experimental community edition · v0.1.0**

Offline and synthetic media components verified; live AI quality and production deployment unvalidated.

---

## The problem

- Product demos, training sessions, and technical walkthroughs get **recorded constantly** — and then forgotten in a video library
- Turning a video into documentation today means **manual transcription + manual writing**: slow, expensive, inconsistent across authors
- Multilingual teams duplicate the effort per language
- By the time the doc is written, the product has often already changed again

---

## The solution

> Give it **one video file**. Generate **draft documentation** for human review, with French and English as target languages.

- Input: a product demo, training, or walkthrough recording
- Output: structured draft Markdown with referenced screenshots embedded when available
- Designed to reduce manual transcription and screenshotting; human review remains necessary

---

## How it works — 5 steps

1. **Upload** — the browser sends the video to the API
2. **Transcribe** — Azure AI Speech converts narration into a timestamped transcript
3. **Extract frames** — key screenshots are sampled from the video
4. **Analyze** — Azure AI Vision captions each frame and reads on-screen text (OCR)
5. **Generate** — Azure AI Foundry (GPT-4.1) writes the documentation, placing the right screenshot next to the right paragraph

All five steps run automatically; the user just uploads and waits.

---

## The key idea: one shared timeline

```
Transcript   [02:15] "...then click Export Wizard..."
Frame        [02:18] frame_000027.png  →  Export dialog on screen
```

Narration and visuals are **aligned by timestamp**, not just concatenated.
The model is instructed to place screenshots near related narration; placement accuracy remains unevaluated.

---

## Key capabilities

- **Bilingual target** — French and English outputs are intended; language fidelity is not yet measured
- **Diátaxis structure** — the generation prompt requests Tutorial, How-to Guide, Reference and Explanation sections
- **Timestamped context** — intended to support relevant screenshot placement
- **Fidelity goal** — preserve source terminology and avoid invented steps; evaluation pending
- **Self-contained output** — available referenced frames can be embedded in Markdown
- **Limited retry handling** — generation retries rate-limit errors; no durable recovery guarantee

---

## What makes the pipeline "smart"

- **Silence-aware audio chunking** — prefers natural pauses and falls back to fixed-duration splits
- **Timestamp-precision alignment** — transcript segments and sampled frames use a shared rounded `[MM:SS]` timeline
- **Tunable visual density** — configurable frame sampling rate, defaults to one frame every 5 seconds for thorough coverage
- **Smart frame selection by the model** — generation instructions request representative frames; actual selection quality remains unverified

---

## Architecture

```
Browser (Static Web App)
   │  upload video / poll status / fetch result
   ▼
FastAPI  (Container App)
   │
   ├── Azure AI Speech    → transcription
   ├── ffmpeg              → frame extraction
   ├── Azure AI Vision    → caption + OCR per frame
   └── Azure AI Foundry   → GPT-4.1 documentation generation
                               │
                               ▼
                      Azure Blob Storage
                      (job state + result)
```

**PoV execution model** — live API state is persisted in Blob Storage, but daemon-thread processing is not durable across restarts. Offline state is process-local.

---

## Technical stack

| Layer | Technology |
|---|---|
| Frontend | Vanilla JS SPA — Azure Static Web Apps |
| Backend | FastAPI (Python) — Azure Container Apps |
| Speech-to-text | Azure AI Speech (REST API) |
| Visual analysis | Azure AI Vision 4.0 (caption + OCR) |
| Document generation | Azure AI Foundry — GPT-4.1 |
| Storage | Azure Blob Storage |
| Secrets | Azure Key Vault + Managed Identity |
| Infrastructure as Code | Bicep — single template, one-command deploy |
| CI/CD | GitHub Actions (build, infra, deploy) |

---

## Security & cost model

- **Secret handling design** — Key Vault references and managed identity are intended to avoid embedding service credentials in images or source
- **No admin passwords** — container registry pulls and secret access are both RBAC-based
- **Cost model** — consumption-oriented compute with additional service/storage charges; actual costs are unmeasured
- **Target regions** — France Central and West Europe; GlobalStandard inference may route elsewhere. Residency is not established by this template.

---

## Current scope (PoV) → production path

| Today (Proof of Value) | Production upgrade |
|---|---|
| Daemon thread per accepted job; no concurrency cap | Worker queue, concurrent processing |
| ~10 min practical video length | Azure Batch Transcription API for longer videos |
| Open API, no authentication | Azure AD auth via Static Web Apps |
| Uniform time-based frame sampling | Scene-change / diversity-based key-frame detection |
| Manual AI quota tuning | Provisioned-throughput GPT deployment |

---

## Business value

- Turns **idle video assets** (demos, trainings, recordings) into reusable, structured documentation
- Potential reduction in drafting time; no measured time savings yet
- **Consistent structure** is a design goal
- **French/English support** is intended; quality assessment pending
- **Source fidelity** is an evaluation goal, not a measured advantage

---

## Try it

1. Follow the credential-free quick start in README.md.
2. Upload a harmless placeholder named demo.mp4 and observe job completion.
3. Copy or download the clearly labeled fixed synthetic Markdown. This does not analyze the video.

---

## Next steps

- Evaluate fictional French/English cases and non-sensitive, authorized synthetic recordings before considering a pilot
- Validate output quality against the current documentation review process
- Prioritize production hardening items from the upgrade path above based on pilot feedback

---

# Questions?
