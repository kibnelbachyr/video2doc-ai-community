# Configuration Reference

All configuration is done through environment variables. In local development
they are loaded from a `.env` file. In production they are injected by Azure
Container Apps from Key Vault secrets via the Managed Identity.

---

## Environment variables

### Azure Blob Storage

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `AZURE_STORAGE_CONNECTION_STRING` | Yes* | `DefaultEndpointsProtocol=https;AccountName=...` | Full connection string for the Storage Account. Used for job state, video blobs, and result blobs. |
| `AZURE_STORAGE_INPUT_CONTAINER` | No | `video-input` | CLI-only (`pipeline.py --upload`). Container for the uploaded video. The API doesn't use this — it stores everything under `jobs/{id}/`. |
| `AZURE_STORAGE_OUTPUT_CONTAINER` | No | `doc-output` | CLI-only (`pipeline.py --upload`). Container for the generated Markdown. Same API caveat as above. |

\* Not required when `MOCK_TRANSCRIPTION=true AND MOCK_VISION=true` (both together
trigger in-memory storage mode, bypassing Blob Storage entirely).

---

### Azure AI Speech

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `AZURE_SPEECH_KEY` | Yes* | `abc123...` | Primary key of the Azure AI Speech resource. |
| `AZURE_SPEECH_REGION` | Yes* | `francecentral` | Region of the Speech resource. Used to construct the REST endpoint URL: `https://{region}.stt.speech.microsoft.com/...` |
| `SPEECH_LANGUAGE` | No | `en-US` | BCP-47 recognition language of the video's audio (e.g. `fr-FR` for a French training video). Must match the spoken language or transcription quality degrades sharply. |

\* Not required when `MOCK_TRANSCRIPTION=true`.

---

### Azure AI Vision

| Variable | Required | Example | Description |
|----------|----------|---------|-------------|
| `AZURE_VISION_ENDPOINT` | Yes* | `https://vision-v2doc-abc123.cognitiveservices.azure.com/` | Endpoint URL of the Azure AI Vision resource. |
| `AZURE_VISION_KEY` | Yes* | `abc123...` | Primary key of the Vision resource. |

\* Not required when `MOCK_VISION=true`.

---

### Azure AI Foundry (GPT-4.1)

| Variable | Required | Default | Example | Description |
|----------|----------|---------|---------|-------------|
| `AZURE_OPENAI_ENDPOINT` | Live generation only | — | `https://aif-v2doc-abc123.cognitiveservices.azure.com/` | Endpoint of the AIServices account. Note: ends with `.cognitiveservices.azure.com/`, not `.openai.azure.com/`. |
| `AZURE_OPENAI_KEY` | Live generation only | — | `abc123...` | Primary key of the AIServices account. |
| `AZURE_OPENAI_DEPLOYMENT` | No | `gpt-4.1` | `gpt-4.1` | Name of the model deployment inside Azure AI Foundry. Must match the deployment name in `main.bicep`. |
| `AZURE_OPENAI_API_VERSION` | No | `2025-04-01-preview` | `2025-04-01-preview` | Azure OpenAI API version. Required for the GPT-4.1 model. |

---

### Pipeline behaviour

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `MOCK_TRANSCRIPTION` | No | `false` | Set to `true` to skip all Azure AI Speech calls and return a hard-coded transcript. Useful during development. |
| `MOCK_VISION` | No | `false` | Set to `true` to skip ffmpeg frame extraction and Azure AI Vision calls, returning hard-coded frame analysis results. |
| `MOCK_GENERATION` | No | `false` | Set to `true` for fixed, labelled synthetic Markdown; skips Azure OpenAI. |
| `FRAMES_PER_MINUTE` | No | `12` | Number of frames to extract per minute of video (1 every 5s by default). Controls the rate passed to ffmpeg (`fps=1/interval`). Higher values produce richer, more synchronized documentation at the cost of Vision API spend and pipeline duration. |

---

## Mock mode combinations

The three flags independently control speech, vision/frame extraction and generation. When transcription and vision are both mocked, API storage is in memory. All three must be true for a credential-free run; if generation is false, Foundry credentials are required. The CLI rejects `--upload` when all three flags are true. Mock generation returns a fixed fictional document and does not analyze real input.

---

## Production environment (Container App)

In production, secrets are stored in Key Vault and injected automatically
by Container Apps. The Bicep template maps them:

```bicep
env: [
  { name: 'AZURE_SPEECH_KEY',              secretRef: 'speech-key'   }
  { name: 'AZURE_SPEECH_REGION',           value: location            }
  { name: 'SPEECH_LANGUAGE',               value: speechLanguage      }
  { name: 'AZURE_VISION_ENDPOINT',         value: visionService.properties.endpoint }
  { name: 'AZURE_VISION_KEY',              secretRef: 'vision-key'   }
  { name: 'AZURE_OPENAI_ENDPOINT',         value: aiFoundry.properties.endpoint }
  { name: 'AZURE_OPENAI_KEY',              secretRef: 'openai-key'   }
  { name: 'AZURE_OPENAI_DEPLOYMENT',       value: 'gpt-4.1'          }
  { name: 'AZURE_OPENAI_API_VERSION',      value: '2025-04-01-preview' }
  { name: 'AZURE_STORAGE_CONNECTION_STRING', secretRef: 'storage-conn' }
  { name: 'FRAMES_PER_MINUTE',             value: '12'               }
  { name: 'MOCK_TRANSCRIPTION',            value: 'false'            }
  { name: 'MOCK_VISION',                   value: 'false'            }
]
```

`secretRef` values are resolved at runtime by the Container Apps platform
from the Key Vault references defined in the `configuration.secrets` block.
No credentials ever appear in plain text in the Bicep template or the
Container App configuration UI.

---

## `.env` file (local development)

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

`.env` is listed in `.gitignore` and must never be committed. All variables
in `.env.example` correspond directly to the table above.

Example minimal `.env` for fully synthetic local development:

```dotenv
MOCK_TRANSCRIPTION=true
MOCK_VISION=true
MOCK_GENERATION=true
```

No Azure credentials are required for these three flags. Use one API worker. For live generation, set MOCK_GENERATION=false and configure Foundry. For real media analysis, disable the relevant media mocks and configure the corresponding services; the CLI upload option requires Blob credentials.
