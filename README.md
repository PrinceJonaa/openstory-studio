# OpenStory Studio

OpenStory Studio is a local-first, model-agnostic narrative production system. It turns
TXT or Markdown source material into evidence-backed canon, episode scenes, structured
storyboards, immutable render versions, and portable production packages.

The durable product is the story and production state above replaceable AI models. The
complete first milestone works with deterministic mocks and does not download model
weights.

```text
source → temporal canon → episode → scenes → panels → renders → export
```

## Milestone-one capabilities

- Imports `.txt` and `.md`, detects chapters or headings, and persists normalized chunks.
- Extracts characters, locations, objects, and facts with exact source evidence.
- Queries canon through inclusive narrative intervals so future facts do not leak backward.
- Adapts selected chunks into an episode and ordered scenes.
- Builds validated storyboard-panel JSON and renders legitimate placeholder PNGs.
- Keeps production artifacts in `draft → review → approved → locked` workflows.
- Creates a new immutable render version on every regeneration.
- Exports versioned JSON, Markdown, a manifest, and storyboard images.
- Optionally talks to an OpenAI-compatible local text server and the MLX-Gen CLI.
- Includes a React production workspace with customizable density, fields, and appearance.

## Requirements

- Python 3.12 or newer
- [uv](https://docs.astral.sh/uv/)
- Node.js 20 or newer and npm

## Install from a clean clone

```bash
uv sync --extra dev
npm install
```

Copy `.env.example` to `.env` only when you want to override the mock defaults. Local
stories, databases, workspaces, model weights, and `.env` files are ignored by Git.

## Run locally

Start the API:

```bash
uv run uvicorn openstory_api.main:app --reload
```

In a second terminal, start the web workspace:

```bash
npm run web:dev
```

Vite proxies `/api` to the local FastAPI process. Open the URL printed by Vite.

## Prove the entire mock pipeline

The smoke demo creates an isolated temporary database and workspace, runs every endpoint,
checks the six generated PNGs and export package, then cleans up only its own temporary
files and API process.

```bash
bash scripts/smoke_demo.sh
```

It exercises:

```text
create project
→ import tests/fixtures/glass_orchard.md
→ extract mock canon
→ query a temporal snapshot
→ adapt an episode
→ build six panels
→ render six placeholders
→ export v001
```

The included Glass Orchard fixture is original demo material and is safe for repository
history.

## Test and build

```bash
uv run pytest -m "not local_ai" -q
uv run ruff check packages apps tests
uv run mypy apps packages
npm run web:test
npm run web:build
```

Normal tests never download or require AI models. Optional hardware-backed proofs are
marked `local_ai`; see [Local AI](docs/local-ai.md).

## Configuration

| Variable | Default | Purpose |
| --- | --- | --- |
| `OPENSTORY_DATABASE_URL` | `sqlite:///./openstory.db` | SQLite connection URL |
| `OPENSTORY_WORKSPACE_ROOT` | `./workspaces` | Project files, renders, and exports |
| `OPENSTORY_TEXT_PROVIDER` | `mock` | `mock` or `openai_compatible` |
| `OPENSTORY_TEXT_BASE_URL` | `http://127.0.0.1:8080/v1` | OpenAI-compatible text endpoint |
| `OPENSTORY_TEXT_MODEL` | `local-model` | Configured text model name |
| `OPENSTORY_IMAGE_PROVIDER` | `placeholder` | `placeholder` or `mlxgen` |
| `OPENSTORY_MLXGEN_EXECUTABLE` | `mlxgen` | MLX-Gen CLI executable |
| `OPENSTORY_MLXGEN_MODEL` | Flux example | MLX-Gen model identifier |

Provider-specific code stays behind explicit text and image interfaces. Selecting MLX-Gen
does not prevent API startup when the executable is absent; render jobs fail clearly while
the rest of the product remains available.

## Repository map

| Path | Responsibility |
| --- | --- |
| `packages/openstory/domain` | Validated story and production state |
| `packages/openstory/application` | Independently testable use cases |
| `packages/openstory/providers` | Replaceable model adapters |
| `packages/openstory/persistence` | SQLite records and repositories |
| `apps/api/openstory_api` | FastAPI transport and dependency wiring |
| `apps/web` | React/Vite production workspace |
| `tests` | Unit, integration, and opt-in local-AI proofs |

Read [Architecture](docs/architecture.md), [Domain model](docs/domain-model.md), and
[Local environment](docs/local-environment.md) for implementation details.

## Scope

Milestone one intentionally excludes video, voices, music, LoRA training, PDF OCR,
advanced EPUB parsing, vector databases, autonomous agent swarms, authentication, cloud
deployment, and advanced page-layout editing. Continuity validation and reusable asset
versions are the next product layer.

## License

Apache License 2.0. See [LICENSE](LICENSE).
