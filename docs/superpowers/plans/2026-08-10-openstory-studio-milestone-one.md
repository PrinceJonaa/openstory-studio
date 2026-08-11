# OpenStory Studio Milestone One Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Do not dispatch subagents; the user explicitly requested solo execution. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Build and prove the complete local-first mock pipeline from TXT/Markdown ingestion through temporal canon, episode scenes, storyboard panels, immutable placeholder PNGs, and a versioned export.

**Architecture:** A Python/TypeScript monorepo separates Pydantic domain state, SQLAlchemy persistence, application use cases, provider adapters, FastAPI transport, and a React/Vite workspace. SQLite and project files are authoritative; deterministic mocks make normal development and CI independent of model runtimes.

**Tech Stack:** Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy 2, SQLite, httpx, Pillow, pytest, Ruff, mypy, React, TypeScript, Vite, Vitest, Testing Library.

## Global Constraints

- The mandatory pipeline must run without downloading or starting an AI model.
- Python support starts at 3.12.
- Model-generated objects must pass Pydantic validation before persistence.
- Domain and application code cannot import provider-specific MLX, OpenAI, Qwen, FLUX, ComfyUI, or Seedance packages.
- Every CanonFact requires source_chunk_id, non-empty evidence, and confidence in [0, 1].
- SourceChunk.ordinal is project-wide and monotonically increasing in import order.
- Temporal valid_to_ordinal is inclusive.
- Allowed production transitions are draft → review, review → approved|revise, revise → draft|review, and approved → locked|revise.
- Locked artifacts reject mutation and locked panels reject regeneration.
- Rendering and export always create new version directories and never overwrite an existing artifact.
- Personally imported material stays under ignored workspaces; repository fixtures are original.
- Normal tests cannot contact external APIs or download model weights.
- UI preferences change presentation only and never modify canonical storyboard JSON.
- Implementation remains solo; no subagents or parallel agent lanes.

---

## Locked File Map

### Root and documentation

- Create pyproject.toml: Python package metadata, runtime/dev dependencies, Ruff, mypy, and pytest configuration.
- Create package.json: root npm workspace and web scripts.
- Create .gitignore: local databases, workspaces, models, environment files, caches, and builds.
- Create .env.example: text/image provider and storage configuration.
- Create README.md: install, run, test, and smoke-demo entry points.
- Create docs/architecture.md: durable layer boundaries and request flow.
- Create docs/domain-model.md: entities, facts, ordinals, statuses, and render versions.
- Create docs/local-ai.md: optional mlx_lm.server and MLX-Gen setup.
- Create docs/local-environment.md: measured Gate 0 findings.
- Create scripts/smoke_demo.sh: reproducible source-to-export API demonstration.

### Domain

- Create packages/openstory/domain/ids.py: UUID string generation.
- Create packages/openstory/domain/status.py: ProductionStatus and transition enforcement.
- Create packages/openstory/domain/project.py: Project and ProjectCreate.
- Create packages/openstory/domain/source.py: SourceDocument and SourceChunk.
- Create packages/openstory/domain/canon.py: CanonEntity, CanonFact, CanonSnapshot, extraction schemas.
- Create packages/openstory/domain/adaptation.py: Episode, Scene, and adaptation schemas.
- Create packages/openstory/domain/storyboard.py: DialogueLine, StoryboardPanel, and build schemas.
- Create packages/openstory/domain/assets.py: RenderVersion and render selection metadata.
- Create packages/openstory/domain/jobs.py: Job, JobKind, JobStatus, and generic JobRunResult.

### Application and services

- Create packages/openstory/application/create_project.py: project/workspace creation use case.
- Create packages/openstory/application/ingest_source.py: validated source import transaction.
- Create packages/openstory/application/extract_canon.py: chunk extraction and entity resolution.
- Create packages/openstory/application/adapt_episode.py: selected chunks to Episode and Scenes.
- Create packages/openstory/application/build_storyboard.py: Scene to StoryboardPanel list.
- Create packages/openstory/application/render_storyboard.py: prompt assembly and immutable render versions.
- Create packages/openstory/application/export_episode.py: versioned JSON/Markdown/image export.
- Create packages/openstory/application/run_job.py: persisted inline job state transitions.
- Create packages/openstory/services/chunking.py: Markdown, chapter, and paragraph-safe splitting.
- Create packages/openstory/services/source_reader.py: extension, UTF-8, hash, and filename validation.
- Create packages/openstory/services/json_repair.py: fenced JSON extraction and validation errors.
- Create packages/openstory/services/workspace.py: safe workspace paths and atomic file placement.

### Providers

- Create packages/openstory/providers/text/base.py: TextGenerationProvider protocol and typed error.
- Create packages/openstory/providers/text/mock.py: deterministic schema-specific mock provider.
- Create packages/openstory/providers/text/openai_compatible.py: httpx chat-completions adapter and one retry.
- Create packages/openstory/providers/image/base.py: ImageGenerationProvider protocol and result/error types.
- Create packages/openstory/providers/image/placeholder.py: deterministic Pillow PNG renderer.
- Create packages/openstory/providers/image/mlxgen.py: safe MLX-Gen subprocess adapter.
- Create packages/openstory/prompts/canon_extract.md: archivist-only extraction contract.
- Create packages/openstory/prompts/episode_adapt.md: causality and future-canon constraints.
- Create packages/openstory/prompts/storyboard_build.md: visual-beat structured-output contract.

### Persistence and API

- Create packages/openstory/persistence/db.py: Base, engine, session factory, and schema initialization.
- Create packages/openstory/persistence/models.py: SQLAlchemy records and database constraints.
- Create packages/openstory/persistence/repositories.py: domain mapping and persistence methods.
- Create apps/api/openstory_api/main.py: FastAPI assembly and CORS.
- Create apps/api/openstory_api/dependencies.py: cached settings and request-scoped dependencies.
- Create apps/api/openstory_api/routes/health.py.
- Create apps/api/openstory_api/routes/projects.py.
- Create apps/api/openstory_api/routes/sources.py.
- Create apps/api/openstory_api/routes/canon.py.
- Create apps/api/openstory_api/routes/episodes.py.
- Create apps/api/openstory_api/routes/storyboards.py.
- Create apps/api/openstory_api/routes/jobs.py.
- Create apps/api/openstory_api/routes/exports.py.

### Web

- Create apps/web/package.json, tsconfig files, vite.config.ts, index.html, and src/main.tsx.
- Create apps/web/src/app/App.tsx: navigation and project selection shell.
- Create apps/web/src/app/routes.ts: local view identifiers without a routing dependency.
- Create apps/web/src/lib/api.ts: typed fetch client.
- Create apps/web/src/lib/types.ts: API response types.
- Create apps/web/src/features/projects/ProjectOverview.tsx.
- Create apps/web/src/features/source/SourceWorkspace.tsx.
- Create apps/web/src/features/canon/CanonWorkspace.tsx.
- Create apps/web/src/features/episodes/EpisodeWorkspace.tsx.
- Create apps/web/src/features/storyboard/StoryboardDesk.tsx.
- Create apps/web/src/features/storyboard/ViewPreferences.tsx.
- Create apps/web/src/features/jobs/JobsWorkspace.tsx.
- Create apps/web/src/components/AppNav.tsx, StatusPill.tsx, EmptyState.tsx, and ActionButton.tsx.
- Create apps/web/src/styles/tokens.css, global.css, and storyboard.css.
- Create apps/web/src/test/setup.ts and focused component tests.

### Tests and fixtures

- Create tests/conftest.py: temporary database/workspace and TestClient fixtures.
- Create tests/fixtures/glass_orchard.md and glass_orchard.txt: original two-chapter source.
- Create tests/unit files aligned to each domain/service/provider.
- Create tests/integration files for each vertical slice and the full export.
- Register local_ai marker in pyproject.toml.

---

### Task 1: Repository Scaffold, Project Domain, SQLite, and API

**Files:**
- Create: pyproject.toml, package.json, .gitignore, .env.example, README.md
- Create: docs/local-environment.md
- Create: packages/openstory/domain/ids.py
- Create: packages/openstory/domain/status.py
- Create: packages/openstory/domain/project.py
- Create: packages/openstory/domain/jobs.py
- Create: packages/openstory/services/workspace.py
- Create: packages/openstory/persistence/db.py
- Create: packages/openstory/persistence/models.py
- Create: packages/openstory/persistence/repositories.py
- Create: packages/openstory/application/create_project.py
- Create: apps/api/openstory_api/main.py
- Create: apps/api/openstory_api/dependencies.py
- Create: apps/api/openstory_api/routes/health.py
- Create: apps/api/openstory_api/routes/projects.py
- Create: tests/conftest.py
- Create: tests/unit/test_project.py
- Create: tests/unit/test_status.py
- Create: tests/integration/test_health_api.py

**Interfaces:**
- Produces: new_id() -> str
- Produces: require_transition(current: ProductionStatus, target: ProductionStatus) -> None
- Produces: WorkspaceManager.create_project(project_id: str) -> Path
- Produces: OpenStoryRepository.add_project(project: Project) -> Project
- Produces: CreateProjectService.execute(command: ProjectCreate) -> Project
- Produces: create_app(settings: Settings | None = None) -> FastAPI

- [ ] **Step 1: Create dependency and tooling manifests**

Use Python project name openstory-studio, requires-python >=3.12, and Hatchling packages at packages/openstory and apps/api/openstory_api. Add runtime dependencies fastapi, uvicorn[standard], pydantic, pydantic-settings, sqlalchemy, httpx, pillow, python-multipart. Add dev dependencies pytest, pytest-asyncio, ruff, mypy, and types-Pillow.

Configure:

~~~toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["packages", "apps/api"]
asyncio_mode = "auto"
markers = ["local_ai: requires explicitly configured local model runtimes"]

[tool.ruff]
target-version = "py312"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "B", "UP", "SIM"]

[tool.mypy]
python_version = "3.12"
strict = true
packages = ["openstory", "openstory_api"]
~~~

- [ ] **Step 2: Install the Python environment**

Run: uv sync --extra dev

Expected: dependency resolution succeeds without downloading model weights.

- [ ] **Step 3: Write failing project, status, and health tests**

Use these assertions:

~~~python
def test_project_creation_creates_workspace(
    repository: OpenStoryRepository,
    workspace_manager: WorkspaceManager,
) -> None:
    project = CreateProjectService(repository, workspace_manager).execute(
        ProjectCreate(name="The Glass Orchard", target_format="storyboard")
    )
    root = workspace_manager.project_root(project.id)
    assert root.is_dir()
    assert {path.name for path in root.iterdir()} == {
        "source", "canon", "episodes", "assets", "renders", "exports"
    }


def test_locked_artifact_cannot_transition() -> None:
    with pytest.raises(LockedArtifactError):
        require_transition(ProductionStatus.LOCKED, ProductionStatus.REVISE)


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
~~~

- [ ] **Step 4: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_project.py tests/unit/test_status.py tests/integration/test_health_api.py -q

Expected: collection fails because openstory and openstory_api modules do not exist.

- [ ] **Step 5: Implement domain primitives and status transitions**

Define exact status values and transition table:

~~~python
class ProductionStatus(StrEnum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    LOCKED = "locked"
    REVISE = "revise"


ALLOWED_TRANSITIONS: dict[ProductionStatus, frozenset[ProductionStatus]] = {
    ProductionStatus.DRAFT: frozenset({ProductionStatus.REVIEW}),
    ProductionStatus.REVIEW: frozenset(
        {ProductionStatus.APPROVED, ProductionStatus.REVISE}
    ),
    ProductionStatus.APPROVED: frozenset(
        {ProductionStatus.LOCKED, ProductionStatus.REVISE}
    ),
    ProductionStatus.REVISE: frozenset(
        {ProductionStatus.DRAFT, ProductionStatus.REVIEW}
    ),
    ProductionStatus.LOCKED: frozenset(),
}
~~~

ProjectCreate normalizes a non-empty name and constrains target_format to storyboard, comic, webtoon, anime, or film. Project stores opaque ID, slug, description, target_format, created_at, and updated_at.

- [ ] **Step 6: Implement SQLite, repository, workspace, and create-project use case**

WorkspaceManager must resolve every project path beneath its configured root and create exactly six child directories. CreateProjectService must:

1. construct the domain Project;
2. create its workspace;
3. persist and commit through OpenStoryRepository;
4. remove only the newly created project directory if persistence fails.

Use a ProjectRecord with unique slug and ISO-aware datetime columns. Keep SQLAlchemy records private to persistence modules.

- [ ] **Step 7: Implement FastAPI app and routes**

Expose:

~~~text
GET  /health
POST /projects
GET  /projects
GET  /projects/{project_id}
~~~

POST /projects accepts name, description, and target_format. Return 201 with the Project schema. Return 404 for an unknown ID and 409 for a duplicate slug.

- [ ] **Step 8: Run tests and static checks**

Run: uv run pytest tests/unit/test_project.py tests/unit/test_status.py tests/integration/test_health_api.py -q

Expected: all pass.

Run: uv run ruff check packages apps tests

Expected: no findings.

Run: uv run mypy

Expected: success with no issues.

- [ ] **Step 9: Record Gate 0 findings**

Write docs/local-environment.md with Python 3.12.13, Node 24.14.0, npm 11.9.0, uv 0.11.33, unavailable localhost text server, and unavailable mlxgen command. State explicitly that mocks remain the default.

- [ ] **Step 10: Commit**

~~~bash
git add pyproject.toml package.json .gitignore .env.example README.md docs/local-environment.md packages apps tests
git commit -m "feat: scaffold project domain and api"
~~~

### Task 2: TXT and Markdown Source Ingestion

**Files:**
- Create: packages/openstory/domain/source.py
- Create: packages/openstory/services/source_reader.py
- Create: packages/openstory/services/chunking.py
- Create: packages/openstory/application/ingest_source.py
- Modify: packages/openstory/persistence/models.py
- Modify: packages/openstory/persistence/repositories.py
- Modify: apps/api/openstory_api/main.py
- Create: apps/api/openstory_api/routes/sources.py
- Create: tests/fixtures/glass_orchard.md
- Create: tests/fixtures/glass_orchard.txt
- Create: tests/unit/test_chunking.py
- Create: tests/integration/test_source_ingestion.py

**Interfaces:**
- Consumes: OpenStoryRepository.get_project(project_id: str) -> Project | None
- Consumes: WorkspaceManager.project_root(project_id: str) -> Path
- Produces: read_source(filename: str, content: bytes) -> ReadSourceResult
- Produces: chunk_source(text: str, media_type: str) -> list[ChunkDraft]
- Produces: IngestSourceService.execute(project_id: str, filename: str, content: bytes) -> tuple[SourceDocument, list[SourceChunk]]
- Produces: OpenStoryRepository.next_chunk_ordinal(project_id: str) -> int

- [ ] **Step 1: Write original story fixtures**

Create glass_orchard.md with two ATX chapters and explicit facts involving Lira, the North Gate, and a glass shard. Create glass_orchard.txt with equivalent Chapter 1 and CHAPTER II headings. Keep each fixture under 1,500 words and mark it original in a leading comment/paragraph.

- [ ] **Step 2: Write failing chunking tests**

~~~python
def test_markdown_ingestion_splits_headings() -> None:
    text = Path("tests/fixtures/glass_orchard.md").read_text()
    drafts = chunk_source(text, "text/markdown")
    assert [draft.heading for draft in drafts] == [
        "Chapter 1: The Shard",
        "Chapter 2: The Crossing",
    ]
    assert all(text[draft.start_offset:draft.end_offset] == draft.text for draft in drafts)


def test_plaintext_ingestion_detects_chapters() -> None:
    text = Path("tests/fixtures/glass_orchard.txt").read_text()
    drafts = chunk_source(text, "text/plain")
    assert len(drafts) == 2
    assert drafts[1].heading == "CHAPTER II"
~~~

Also test paragraph-safe fallback, UTF-8 failure, unsupported extension, sanitized filename, and duplicate project hash.

- [ ] **Step 3: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_chunking.py tests/integration/test_source_ingestion.py -q

Expected: failure because source domain and services do not exist.

- [ ] **Step 4: Implement source reader and chunking**

ReadSourceResult must contain filename, media_type, text, and sha256. Accept only .txt and .md, decode UTF-8 strictly, use pathlib.Path(filename).name, and reject empty text.

ChunkDraft fields are heading, text, start_offset, and end_offset. Markdown detection uses lines beginning with one to six # characters. Plain-text detection uses a case-insensitive line expression equivalent to:

~~~python
CHAPTER_PATTERN = re.compile(
    r"^(?:chapter|part)\s+(?:\d+|[ivxlcdm]+)(?:\s*[:.-]\s*.+)?$",
    re.IGNORECASE,
)
~~~

Fallback chunks target 4,000 characters and join whole paragraphs until the next paragraph would exceed the bound.

- [ ] **Step 5: Implement source persistence and ingestion transaction**

Add SourceDocumentRecord and SourceChunkRecord. Persist document SHA, copied workspace path, global ordinal, heading, text, and offsets. Enforce unique (project_id, sha256) for documents and unique (project_id, ordinal) for chunks.

IngestSourceService writes to a temporary source file, begins the database transaction, persists document/chunks with the intended final path, atomically renames the temporary file, and then commits. On any error, roll back and remove only the temporary file or the final file created by this operation.

- [ ] **Step 6: Implement source API**

Expose:

~~~text
POST /projects/{project_id}/sources
GET  /projects/{project_id}/sources
GET  /projects/{project_id}/chunks
~~~

The POST consumes one multipart file and returns document plus chunks. A second identical file in the same project returns 409.

- [ ] **Step 7: Run focused and regression tests**

Run: uv run pytest tests/unit/test_chunking.py tests/integration/test_source_ingestion.py -q

Expected: all pass.

Run: uv run pytest -q

Expected: all tests pass.

- [ ] **Step 8: Commit**

~~~bash
git add packages/openstory/domain/source.py packages/openstory/services/source_reader.py packages/openstory/services/chunking.py packages/openstory/application/ingest_source.py packages/openstory/persistence apps/api tests
git commit -m "feat: add source ingestion and chunking"
~~~

### Task 3: Structured Mock AI, Canon Extraction, Provenance, and Jobs

**Files:**
- Create: packages/openstory/domain/canon.py
- Modify: packages/openstory/domain/jobs.py
- Create: packages/openstory/providers/text/base.py
- Create: packages/openstory/providers/text/mock.py
- Create: packages/openstory/application/run_job.py
- Create: packages/openstory/application/extract_canon.py
- Create: packages/openstory/prompts/canon_extract.md
- Modify: packages/openstory/persistence/models.py
- Modify: packages/openstory/persistence/repositories.py
- Create: apps/api/openstory_api/routes/canon.py
- Create: apps/api/openstory_api/routes/jobs.py
- Modify: apps/api/openstory_api/main.py
- Create: tests/unit/test_canon.py
- Create: tests/unit/test_mock_text_provider.py
- Create: tests/integration/test_source_to_canon.py

**Interfaces:**
- Produces: TextGenerationProvider.generate_structured(system_prompt: str, user_prompt: str, schema: type[T], temperature: float = 0.2) -> T
- Produces: MockTextProvider(response_overrides: Mapping[str, Mapping[str, Any]] | None = None)
- Produces: JobRunResult[T](job: Job, result: T)
- Produces: RunJobService.run(project_id: str, kind: JobKind, operation: Callable[[], Awaitable[T]], progress_total: int | None = None) -> JobRunResult[T]
- Produces: ExtractCanonService.execute(project_id: str, chunk_ids: list[str] | None = None) -> CanonExtractionResult
- Produces: OpenStoryRepository.resolve_entity(project_id: str, candidate: ExtractedEntity) -> CanonEntity

- [ ] **Step 1: Write failing canon invariants and provider tests**

~~~python
def test_canon_fact_requires_source_chunk() -> None:
    with pytest.raises(ValidationError):
        CanonFact(
            id=new_id(),
            project_id="project",
            subject_entity_id="lira",
            predicate="carries",
            value="glass shard",
            source_chunk_id="",
            evidence="Lira carries the shard.",
            confidence=0.9,
        )


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic() -> None:
    provider = MockTextProvider()
    first = await provider.generate_structured(
        system_prompt="archivist",
        user_prompt="The Glass Orchard\nLira lifts the shard at the North Gate.",
        schema=CanonExtractionResponse,
    )
    second = await provider.generate_structured(
        system_prompt="archivist",
        user_prompt="The Glass Orchard\nLira lifts the shard at the North Gate.",
        schema=CanonExtractionResponse,
    )
    assert first == second
    assert {entity.canonical_name for entity in first.entities} >= {
        "Lira", "North Gate", "Glass Shard"
    }
~~~

- [ ] **Step 2: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_canon.py tests/unit/test_mock_text_provider.py -q

Expected: failure because canon schemas and text providers do not exist.

- [ ] **Step 3: Implement canon schemas and provider protocol**

Define ExtractedEntity with temporary ref, kind, canonical_name, aliases, summary, and attributes. Define ExtractedFact with subject_ref, predicate, optional object_ref/value, temporal ordinals, evidence, and confidence. CanonExtractionResponse contains entities, facts, and unresolved_references.

Constrain entity kind to character, location, object, faction, creature, or concept. ExtractedFact and CanonFact require at least one of object reference/ID or value.

Use a covariant protocol-independent type variable:

~~~python
T = TypeVar("T", bound=BaseModel)


class TextGenerationProvider(Protocol):
    async def generate_structured(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema: type[T],
        temperature: float = 0.2,
    ) -> T:
        raise NotImplementedError
~~~

Define JobRunResult as a generic Pydantic model with job: Job and result: T so every model-backed endpoint returns the same observable job envelope.

- [ ] **Step 4: Implement deterministic mock responses**

For CanonExtractionResponse, return the included fixture entities and evidence only when the prompt contains The Glass Orchard and its explicit evidence sentences. For other input, return empty entities/facts and one unresolved reference stating mock mode has no fixture extraction. Apply schema.model_validate to every response, including overrides.

- [ ] **Step 5: Implement persistence, conservative resolution, and jobs**

Add CanonEntityRecord, CanonFactRecord, and JobRecord. Store lists/dicts/value in JSON columns. Add check constraints for confidence and non-empty evidence/source_chunk_id.

Resolve by normalized canonical name first, then exact normalized alias. Never fuzzy-merge.

RunJobService must persist:

~~~text
queued → running → succeeded
                  ↘ failed with concise error
~~~

Commit each state transition so the Jobs view can observe failures. When progress_total is supplied, initialize progress_current to 0 and set it to progress_total only after the operation succeeds.

- [ ] **Step 6: Implement extraction service and prompt**

For each selected or all project chunks:

1. load existing entity names/aliases;
2. call the provider with the archivist system prompt;
3. resolve candidates;
4. map temporary refs to persisted IDs;
5. verify each evidence string occurs within the chunk text;
6. persist valid facts with that chunk ID;
7. preserve unresolved references in the job result metadata.

Reject provider evidence not found in the source chunk with a typed ExtractionValidationError; do not silently rewrite it.

- [ ] **Step 7: Implement canon and job routes**

Expose:

~~~text
POST /projects/{project_id}/canon/extract
GET  /projects/{project_id}/entities
GET  /projects/{project_id}/facts
GET  /projects/{project_id}/jobs
GET  /jobs/{job_id}
~~~

The extraction POST returns JobRunResult[CanonExtractionResult] in mock/inline mode.

- [ ] **Step 8: Prove source-to-canon integration**

The integration test imports glass_orchard.md, runs extraction, and asserts:

~~~python
assert lira.kind == "character"
assert gate.kind == "location"
assert shard.kind == "object"
assert ownership.source_chunk_id == chapter_one.id
assert ownership.evidence in chapter_one.text
assert ownership.confidence == pytest.approx(0.96)
~~~

Run: uv run pytest tests/unit/test_canon.py tests/unit/test_mock_text_provider.py tests/integration/test_source_to_canon.py -q

Expected: all pass.

- [ ] **Step 9: Run regression tests and commit**

Run: uv run pytest -q

Expected: all tests pass.

~~~bash
git add packages/openstory/domain packages/openstory/providers/text packages/openstory/application packages/openstory/prompts packages/openstory/persistence apps/api tests
git commit -m "feat: add structured canon extraction"
~~~

### Task 4: OpenAI-Compatible Text Provider

**Files:**
- Create: packages/openstory/services/json_repair.py
- Create: packages/openstory/providers/text/openai_compatible.py
- Modify: apps/api/openstory_api/dependencies.py
- Modify: .env.example
- Create: tests/unit/test_json_repair.py
- Create: tests/unit/test_openai_compatible_provider.py

**Interfaces:**
- Consumes: TextGenerationProvider protocol from Task 3.
- Produces: extract_json_value(text: str) -> Any
- Produces: OpenAICompatibleTextProvider(client: httpx.AsyncClient, base_url: str, api_key: str, model: str)
- Produces: build_text_provider(settings: Settings) -> TextGenerationProvider

- [ ] **Step 1: Write failing parser and HTTP adapter tests**

Use httpx.MockTransport so tests never use the network:

~~~python
@pytest.mark.asyncio
async def test_provider_validates_chat_completion_json() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": '{"entities":[],"facts":[],"unresolved_references":[]}'}}]},
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    provider = OpenAICompatibleTextProvider(
        client=client,
        base_url="http://local.test/v1",
        api_key="local",
        model="local-model",
    )
    result = await provider.generate_structured(
        system_prompt="archivist",
        user_prompt="source",
        schema=CanonExtractionResponse,
    )
    assert result.entities == []
~~~

Also test fenced JSON, surrounding prose, HTTP failure, missing choices, invalid JSON followed by one successful repair response, and two invalid responses raising TextGenerationError.

- [ ] **Step 2: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_json_repair.py tests/unit/test_openai_compatible_provider.py -q

Expected: failure because parser and adapter do not exist.

- [ ] **Step 3: Implement JSON extraction**

extract_json_value must:

1. strip whitespace and an optional json fence;
2. try json.loads on the full string;
3. if that fails, locate the first balanced object or array while respecting quoted strings and escapes;
4. parse that slice;
5. raise StructuredOutputError containing no source text beyond a 200-character diagnostic preview.

- [ ] **Step 4: Implement the HTTP adapter and one repair retry**

POST to base_url.rstrip("/") + "/chat/completions" with model, two messages, and temperature. Do not send tools or require response_format. On parse/schema failure, send one second request whose user message includes the validation error and instructs the model to return corrected JSON only. Never retry transport authentication errors.

- [ ] **Step 5: Wire provider selection**

Settings values:

~~~text
OPENSTORY_TEXT_PROVIDER=mock|openai_compatible
OPENSTORY_TEXT_BASE_URL=http://127.0.0.1:8080/v1
OPENSTORY_TEXT_API_KEY=local
OPENSTORY_TEXT_MODEL=local-model
~~~

Mock remains the default. Unknown provider names fail at application startup with a clear configuration error.

- [ ] **Step 6: Run tests, static checks, and commit**

Run: uv run pytest tests/unit/test_json_repair.py tests/unit/test_openai_compatible_provider.py -q

Expected: all pass.

Run: uv run ruff check packages apps tests

Expected: no findings.

~~~bash
git add packages/openstory/services/json_repair.py packages/openstory/providers/text/openai_compatible.py apps/api/openstory_api/dependencies.py .env.example tests/unit
git commit -m "feat: add openai compatible text provider"
~~~

### Task 5: Temporal Canon Snapshots

**Files:**
- Modify: packages/openstory/domain/canon.py
- Modify: packages/openstory/persistence/repositories.py
- Modify: apps/api/openstory_api/routes/canon.py
- Create: tests/unit/test_temporal_canon.py
- Create: tests/integration/test_canon_snapshot_api.py

**Interfaces:**
- Consumes: CanonFact and CanonEntity from Task 3.
- Produces: OpenStoryRepository.get_canon_snapshot(project_id: str, ordinal: int) -> CanonSnapshot
- Produces: GET /projects/{project_id}/canon/snapshot?ordinal={ordinal}

- [ ] **Step 1: Write failing temporal-boundary tests**

~~~python
def test_temporal_fact_active_inside_range(
    repository_with_temporal_fact: tuple[OpenStoryRepository, str],
) -> None:
    repository, project_id = repository_with_temporal_fact
    snapshot = repository.get_canon_snapshot(project_id, ordinal=10)
    assert [fact.predicate for fact in snapshot.facts] == ["owns"]


def test_temporal_fact_inactive_after_range(
    repository_with_temporal_fact: tuple[OpenStoryRepository, str],
) -> None:
    repository, project_id = repository_with_temporal_fact
    snapshot = repository.get_canon_snapshot(project_id, ordinal=18)
    assert snapshot.facts == []
~~~

The fixture fact uses valid_from_ordinal=3 and valid_to_ordinal=17. Add assertions at ordinals 2, 3, 17, and 18 to prove inclusive endpoints.

- [ ] **Step 2: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_temporal_canon.py tests/integration/test_canon_snapshot_api.py -q

Expected: failure because snapshot query is absent.

- [ ] **Step 3: Implement repository snapshot filtering**

Use one SQL predicate:

~~~python
and_(
    CanonFactRecord.project_id == project_id,
    or_(
        CanonFactRecord.valid_from_ordinal.is_(None),
        CanonFactRecord.valid_from_ordinal <= ordinal,
    ),
    or_(
        CanonFactRecord.valid_to_ordinal.is_(None),
        CanonFactRecord.valid_to_ordinal >= ordinal,
    ),
)
~~~

Load only subject/object entities referenced by active facts. CanonSnapshot stores project_id, ordinal, entities, and facts sorted deterministically by predicate then fact ID.

- [ ] **Step 4: Add range validation**

CanonFact rejects negative ordinals and rejects valid_from_ordinal greater than valid_to_ordinal. Add the equivalent SQLite check constraint for rows created outside normal domain code.

- [ ] **Step 5: Add and test the snapshot API**

The endpoint returns 404 for an unknown project and 422 for a negative ordinal. It returns an empty valid snapshot when the project exists but no facts are active.

Run: uv run pytest tests/unit/test_temporal_canon.py tests/integration/test_canon_snapshot_api.py -q

Expected: all pass.

- [ ] **Step 6: Run regressions and commit**

Run: uv run pytest -q

Expected: all tests pass.

~~~bash
git add packages/openstory/domain/canon.py packages/openstory/persistence/repositories.py apps/api/openstory_api/routes/canon.py tests
git commit -m "feat: add temporal canon snapshots"
~~~

### Task 6: Source Chunks to Episode and Scenes

**Files:**
- Create: packages/openstory/domain/adaptation.py
- Create: packages/openstory/application/adapt_episode.py
- Create: packages/openstory/prompts/episode_adapt.md
- Modify: packages/openstory/providers/text/mock.py
- Modify: packages/openstory/persistence/models.py
- Modify: packages/openstory/persistence/repositories.py
- Create: apps/api/openstory_api/routes/episodes.py
- Modify: apps/api/openstory_api/main.py
- Create: tests/unit/test_adaptation.py
- Create: tests/integration/test_source_to_episode.py

**Interfaces:**
- Consumes: TextGenerationProvider and OpenStoryRepository.get_canon_snapshot.
- Produces: EpisodeAdaptationResponse with episode: EpisodeDraft and scenes: list[SceneDraft]
- Produces: AdaptEpisodeService.execute(project_id: str, source_chunk_ids: list[str], number: int, target_format: TargetFormat) -> tuple[Episode, list[Scene]]
- Produces: OpenStoryRepository.add_episode(episode: Episode, scenes: Sequence[Scene]) -> tuple[Episode, list[Scene]]

- [ ] **Step 1: Write failing domain and integration tests**

~~~python
def test_adaptation_requires_at_least_one_source_chunk() -> None:
    with pytest.raises(ValidationError):
        AdaptEpisodeCommand(
            project_id="project",
            source_chunk_ids=[],
            number=1,
            target_format="storyboard",
        )


def test_source_to_episode_vertical_slice(
    imported_glass_orchard: ImportedStory,
    services: ServiceBundle,
) -> None:
    episode, scenes = asyncio.run(
        services.adapt_episode.execute(
            project_id=imported_glass_orchard.project.id,
            source_chunk_ids=[chunk.id for chunk in imported_glass_orchard.chunks],
            number=1,
            target_format="storyboard",
        )
    )
    assert episode.title == "The Crossing"
    assert episode.source_chunk_ids == [chunk.id for chunk in imported_glass_orchard.chunks]
    assert [scene.ordinal for scene in scenes] == list(range(1, len(scenes) + 1))
    assert all(scene.status is ProductionStatus.DRAFT for scene in scenes)
~~~

- [ ] **Step 2: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_adaptation.py tests/integration/test_source_to_episode.py -q

Expected: failure because adaptation models and service do not exist.

- [ ] **Step 3: Implement adaptation schemas**

EpisodeDraft contains title, logline, and adaptation_notes. SceneDraft contains ordinal, title, purpose, optional location_ref, character_refs, and summary. Persisted Episode and Scene add IDs, parent IDs, status, and source_chunk_ids on Episode.

Validate scene ordinals as unique contiguous integers starting at 1.

- [ ] **Step 4: Add the constrained adaptation prompt and mock response**

The prompt must include:

- source chunks in ordinal order;
- CanonSnapshot JSON at max(selected chunk ordinal);
- target format;
- explicit future-canon prohibition;
- requirement to record omissions and reorderings.

The fixture mock returns two or three scenes grounded only in the selected Glass Orchard chapters. For arbitrary sources, it deterministically creates one visual scene using the first non-heading sentence and no resolved entity refs.

- [ ] **Step 5: Implement the service and persistence transaction**

AdaptEpisodeService must verify all chunks belong to the project, preserve the caller's chunk order after sorting by narrative ordinal, load the temporal snapshot at the maximum ordinal, validate the provider response, resolve entity refs conservatively, and persist Episode plus all Scenes in one transaction.

Duplicate episode number within a project returns 409.

The route executes this service through RunJobService with kind episode_adapt and progress_total=1.

- [ ] **Step 6: Implement episode routes**

Expose:

~~~text
POST  /projects/{project_id}/episodes/adapt
GET   /projects/{project_id}/episodes
GET   /episodes/{episode_id}
PATCH /episodes/{episode_id}/status
PATCH /scenes/{scene_id}/status
~~~

The episode detail includes ordered scenes. Status endpoints accept only a target status and call require_transition before persistence.

- [ ] **Step 7: Run focused, regression, and static tests**

Run: uv run pytest tests/unit/test_adaptation.py tests/integration/test_source_to_episode.py -q

Expected: all pass.

Run: uv run pytest -q

Expected: all tests pass.

Run: uv run ruff check packages apps tests

Expected: no findings.

- [ ] **Step 8: Commit**

~~~bash
git add packages/openstory/domain/adaptation.py packages/openstory/application/adapt_episode.py packages/openstory/prompts/episode_adapt.md packages/openstory/providers/text/mock.py packages/openstory/persistence apps/api tests
git commit -m "feat: adapt source chunks into episode scenes"
~~~

### Task 7: Scene to Structured Storyboard Panels

**Files:**
- Create: packages/openstory/domain/storyboard.py
- Create: packages/openstory/application/build_storyboard.py
- Create: packages/openstory/prompts/storyboard_build.md
- Modify: packages/openstory/providers/text/mock.py
- Modify: packages/openstory/persistence/models.py
- Modify: packages/openstory/persistence/repositories.py
- Create: apps/api/openstory_api/routes/storyboards.py
- Modify: apps/api/openstory_api/main.py
- Create: tests/unit/test_storyboard.py
- Create: tests/integration/test_episode_to_storyboard.py

**Interfaces:**
- Consumes: Scene, Episode, CanonSnapshot, and TextGenerationProvider.
- Produces: DialogueLine(speaker_entity_id: str | None, speaker_name: str, text: str)
- Produces: StoryboardBuildResponse(panels: list[PanelDraft])
- Produces: BuildStoryboardService.execute(scene_id: str) -> list[StoryboardPanel]
- Produces: OpenStoryRepository.replace_draft_storyboard(scene_id: str, panels: Sequence[StoryboardPanel]) -> list[StoryboardPanel]

- [ ] **Step 1: Write failing validation and round-trip tests**

~~~python
def test_storyboard_requires_contiguous_panel_ordinals() -> None:
    with pytest.raises(ValidationError):
        StoryboardBuildResponse(
            panels=[
                panel_draft(ordinal=1),
                panel_draft(ordinal=3),
            ]
        )


def test_storyboard_panel_round_trips_through_db(
    repository: OpenStoryRepository,
    persisted_scene: Scene,
) -> None:
    panel = storyboard_panel(scene_id=persisted_scene.id)
    repository.replace_draft_storyboard(persisted_scene.id, [panel])
    restored = repository.list_storyboard_panels(persisted_scene.id)
    assert restored == [panel]
~~~

Also verify DialogueLine, character_entity_ids, referenced_asset_ids, and negative_prompt survive JSON persistence.

- [ ] **Step 2: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_storyboard.py tests/integration/test_episode_to_storyboard.py -q

Expected: failure because storyboard domain and persistence are absent.

- [ ] **Step 3: Implement storyboard schemas**

PanelDraft contains ordinal, shot_type, framing, action, visual_description, dialogue, character_refs, optional location_ref, image_prompt, and optional negative_prompt.

StoryboardPanel adds ID, scene_id, resolved entity IDs, referenced_asset_ids, render_status, and ProductionStatus. Defaults are unrendered and draft.

Validate 1–24 panels, contiguous ordinals starting at 1, non-empty action/visual_description/image_prompt, and unique ordinal per scene.

- [ ] **Step 4: Implement storyboard prompt and deterministic mock**

The prompt includes Scene JSON, Episode adaptation context, and the temporal snapshot at the Episode's highest source chunk ordinal. It instructs the provider to create 6–12 visual beats by default and not invent future facts.

The Glass Orchard mock returns six panels matching the selected design reference: gate establishing shot, Lira raising the shard, guard response, close-up, two-shot, and gate opening.

- [ ] **Step 5: Implement service, persistence, and draft replacement rules**

BuildStoryboardService resolves character/location refs, validates all provider data, and persists the panel list in one transaction.

replace_draft_storyboard may replace an existing all-draft storyboard. It must reject replacement when any existing panel is approved or locked. Revision after approval requires explicit status changes before rebuilding.

The route executes this service through RunJobService with kind storyboard_build and progress_total=1.

- [ ] **Step 6: Implement storyboard routes**

Expose:

~~~text
POST  /scenes/{scene_id}/storyboard
GET   /scenes/{scene_id}/storyboard
PATCH /panels/{panel_id}/status
~~~

Return 409 when rebuilding would replace approved or locked panels.

- [ ] **Step 7: Run tests and commit**

Run: uv run pytest tests/unit/test_storyboard.py tests/integration/test_episode_to_storyboard.py -q

Expected: all pass.

Run: uv run pytest -q

Expected: all tests pass.

~~~bash
git add packages/openstory/domain/storyboard.py packages/openstory/application/build_storyboard.py packages/openstory/prompts/storyboard_build.md packages/openstory/providers/text/mock.py packages/openstory/persistence apps/api tests
git commit -m "feat: generate structured storyboards"
~~~

### Task 8: Placeholder Rendering, Immutable Versions, and Status Safety

**Files:**
- Create: packages/openstory/domain/assets.py
- Create: packages/openstory/providers/image/base.py
- Create: packages/openstory/providers/image/placeholder.py
- Create: packages/openstory/application/render_storyboard.py
- Modify: packages/openstory/persistence/models.py
- Modify: packages/openstory/persistence/repositories.py
- Modify: apps/api/openstory_api/routes/storyboards.py
- Modify: apps/api/openstory_api/dependencies.py
- Create: tests/unit/test_placeholder_renderer.py
- Create: tests/unit/test_render_versioning.py
- Create: tests/integration/test_storyboard_render_api.py

**Interfaces:**
- Produces: ImageGenerationResult(output_path: Path, width: int, height: int, seed: int | None, provider: str, metadata: dict[str, Any])
- Produces: ImageGenerationProvider.generate(*, prompt: str, negative_prompt: str | None, width: int, height: int, seed: int | None, output_path: Path, references: list[Path] | None = None) -> ImageGenerationResult
- Produces: build_panel_render_prompt(panel: StoryboardPanel, character_names: Sequence[str], location_name: str | None) -> str
- Produces: RenderStoryboardService.render_panel(panel_id: str, width: int = 768, height: int = 1024, seed: int | None = None) -> RenderVersion
- Produces: RenderStoryboardService.render_scene(scene_id: str, width: int = 768, height: int = 1024) -> list[RenderVersion]
- Produces: OpenStoryRepository.next_render_version(panel_id: str) -> int

- [ ] **Step 1: Write failing PNG and versioning tests**

~~~python
@pytest.mark.asyncio
async def test_placeholder_renderer_creates_png(tmp_path: Path) -> None:
    output = tmp_path / "panel.png"
    result = await PlaceholderImageProvider().generate(
        prompt="PANEL 1\nSHOT: wide\nACTION: Lira approaches the gate.",
        negative_prompt=None,
        width=640,
        height=960,
        seed=7,
        output_path=output,
        references=[],
    )
    assert result.output_path == output
    with Image.open(output) as image:
        assert image.format == "PNG"
        assert image.size == (640, 960)


@pytest.mark.asyncio
async def test_regeneration_creates_next_version(rendered_panel: RenderedPanel) -> None:
    first = await rendered_panel.service.render_panel(rendered_panel.panel.id, seed=10)
    second = await rendered_panel.service.render_panel(rendered_panel.panel.id, seed=11)
    assert first.version == 1
    assert second.version == 2
    assert first.output_path != second.output_path
    assert Path(first.output_path).exists()
    assert Path(second.output_path).exists()
~~~

Also test approved versions remain unchanged and locked panels raise LockedArtifactError before invoking the provider.

- [ ] **Step 2: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_placeholder_renderer.py tests/unit/test_render_versioning.py tests/integration/test_storyboard_render_api.py -q

Expected: failure because image provider and render records do not exist.

- [ ] **Step 3: Implement provider contract and placeholder renderer**

The protocol uses references: list[Path] | None rather than a mutable list default. PlaceholderImageProvider creates an RGB canvas, draws a restrained border/header, wraps every prompt line with textwrap, and uses Pillow's bundled/default font so no system font is required.

Write to output_path.with_suffix(".tmp.png"), reopen with Pillow to verify PNG and dimensions, then os.replace into output_path.

- [ ] **Step 4: Implement structured render prompt and version paths**

build_panel_render_prompt returns:

~~~text
PANEL {ordinal}
SHOT: {shot_type} · {framing}
CHARACTERS: {comma-separated names or None}
LOCATION: {name or Unspecified}
ACTION: {action}
VISUAL: {visual_description}
IMAGE PROMPT: {image_prompt}
~~~

The workspace path is:

~~~text
renders/{scene_id}/panel-{ordinal:04d}/v{version:03d}.png
~~~

Version allocation and RenderVersion persistence occur in one database transaction protected by unique (panel_id, version). A collision retries once after re-reading the maximum.

- [ ] **Step 5: Implement render service and selection safety**

Reject locked panels before filesystem or provider work. Create a draft RenderVersion after successful output verification, set the panel render_status to rendered, and store provider metadata.

Status updates for render versions use require_transition. Existing files are never changed when status changes.

Render routes execute through RunJobService with kind image_render. A scene render supplies progress_total equal to its panel count; successful completion records progress_current equal to that total.

- [ ] **Step 6: Implement render and file routes**

Expose:

~~~text
POST  /panels/{panel_id}/render
POST  /scenes/{scene_id}/render
GET   /renders/{render_id}/file
PATCH /renders/{render_id}/status
~~~

GET /renders/{render_id}/file resolves the persisted path through WorkspaceManager, verifies it remains beneath the workspace root, and returns FileResponse with image/png.

- [ ] **Step 7: Run focused, regression, and static tests**

Run: uv run pytest tests/unit/test_placeholder_renderer.py tests/unit/test_render_versioning.py tests/integration/test_storyboard_render_api.py -q

Expected: all pass.

Run: uv run pytest -q

Expected: all tests pass.

Run: uv run ruff check packages apps tests

Expected: no findings.

- [ ] **Step 8: Commit**

~~~bash
git add packages/openstory/domain/assets.py packages/openstory/providers/image packages/openstory/application/render_storyboard.py packages/openstory/persistence apps/api tests
git commit -m "feat: render versioned storyboard placeholders"
~~~

### Task 9: Customizable Storyboard Desk Web UI

**Files:**
- Create: apps/web/package.json
- Create: apps/web/tsconfig.json
- Create: apps/web/tsconfig.app.json
- Create: apps/web/tsconfig.node.json
- Create: apps/web/vite.config.ts
- Create: apps/web/index.html
- Create: apps/web/src/main.tsx
- Create: apps/web/src/app/App.tsx
- Create: apps/web/src/app/routes.ts
- Create: apps/web/src/lib/api.ts
- Create: apps/web/src/lib/types.ts
- Create: apps/web/src/components/AppNav.tsx
- Create: apps/web/src/components/StatusPill.tsx
- Create: apps/web/src/components/EmptyState.tsx
- Create: apps/web/src/components/ActionButton.tsx
- Create: apps/web/src/features/projects/ProjectOverview.tsx
- Create: apps/web/src/features/source/SourceWorkspace.tsx
- Create: apps/web/src/features/canon/CanonWorkspace.tsx
- Create: apps/web/src/features/episodes/EpisodeWorkspace.tsx
- Create: apps/web/src/features/storyboard/StoryboardDesk.tsx
- Create: apps/web/src/features/storyboard/ViewPreferences.tsx
- Create: apps/web/src/features/jobs/JobsWorkspace.tsx
- Create: apps/web/src/styles/tokens.css
- Create: apps/web/src/styles/global.css
- Create: apps/web/src/styles/storyboard.css
- Create: apps/web/src/test/setup.ts
- Create: apps/web/src/features/storyboard/ViewPreferences.test.tsx
- Create: apps/web/src/features/storyboard/StoryboardDesk.test.tsx
- Modify: package.json
- Modify: apps/api/openstory_api/main.py

**Interfaces:**
- Consumes: REST endpoints from Tasks 1–8.
- Produces: api object with project, source, canon, episode, storyboard, render, job, and status methods.
- Produces: ViewSettings with layout: "visual" | "balanced" | "detailed", appearance: "paper" | "dark" | "system", visibleFields, and useAsProjectDefault.
- Produces: loadViewSettings(projectId: string) -> ViewSettings
- Produces: saveViewSettings(projectId: string, settings: ViewSettings) -> void
- Produces: StoryboardDesk props { projectId: string; episodeId: string; sceneId: string }.

- [ ] **Step 1: Invoke the selected visual implementation workflow**

Before editing UI files, use product-design:image-to-code with docs/superpowers/specs/assets/storyboard-desk-customizable-view.png as the source visual. Preserve its Storyboard Desk hierarchy, paper/charcoal/terracotta/teal system, selected-panel inspector, evidence region, batch actions, and open View popover.

- [ ] **Step 2: Scaffold the Vite/React package and install dependencies**

Use React, React DOM, lucide-react, TypeScript, Vite, Vitest, jsdom, Testing Library React, Testing Library user-event, and Vite React plugin. Configure npm workspaces at apps/web and root scripts:

~~~json
{
  "scripts": {
    "web:dev": "npm --workspace @openstory/web run dev",
    "web:build": "npm --workspace @openstory/web run build",
    "web:test": "npm --workspace @openstory/web run test"
  }
}
~~~

Run: npm install

Expected: package-lock.json is created at the repository root.

- [ ] **Step 3: Write failing view-preference tests**

~~~tsx
it("persists project-specific view fields without changing panel data", async () => {
  const user = userEvent.setup();
  const panel = makePanel({ action: "Lira raises the shard." });
  render(<ViewPreferencesHarness projectId="project-a" panel={panel} />);

  await user.click(screen.getByRole("button", { name: "View" }));
  await user.click(screen.getByRole("switch", { name: "Dialogue" }));
  await user.click(screen.getByRole("button", { name: "Detailed" }));

  expect(loadViewSettings("project-a").layout).toBe("detailed");
  expect(loadViewSettings("project-a").visibleFields.dialogue).toBe(true);
  expect(panel.action).toBe("Lira raises the shard.");
});
~~~

Also test independent project keys, invalid stored JSON falling back to defaults, appearance applied through document.documentElement.dataset.theme, and the view popover closing on Escape.

- [ ] **Step 4: Run UI tests and confirm the red state**

Run: npm run web:test -- --run

Expected: failure because the web package/components do not exist.

- [ ] **Step 5: Implement typed API client and app shell**

api.ts must:

- use VITE_OPENSTORY_API_URL with default http://127.0.0.1:8000;
- set JSON headers except multipart uploads;
- parse successful JSON;
- throw ApiError(status, detail) for non-2xx responses;
- expose exact methods instead of a generic request call to components.

App.tsx loads projects, shows a compact create-project form when empty, retains the last selected project in localStorage, and switches Overview, Source, Canon, Episodes, Assets, and Jobs views without a router dependency. Overview presents the next recommended milestone action; Assets uses the shared EmptyState until render versions exist, then lists those versions.

- [ ] **Step 6: Implement the milestone workflow screens**

SourceWorkspace uploads TXT/Markdown, lists chunks, previews selected text, and exposes Extract Canon.

CanonWorkspace shows Entities and Facts tabs. Selecting a fact or entity shows evidence, chunk heading, offsets, and confidence.

EpisodeWorkspace selects chunks, runs adaptation, lists scenes, and opens StoryboardDesk.

JobsWorkspace shows kind, status, progress, and concise error.

Every async action shows pending, success, empty, and failure states. Disable duplicate submissions while pending.

- [ ] **Step 7: Implement Storyboard Desk and customization**

Use the selected mock as the visual source. The balanced layout defaults to a 2×3 panel grid with a right inspector. Use real placeholder render URLs when available and an EmptyState only when a panel has no render.

ViewSettings defaults:

~~~ts
export const DEFAULT_VIEW_SETTINGS: ViewSettings = {
  layout: "balanced",
  appearance: "paper",
  visibleFields: {
    shotType: true,
    action: true,
    dialogue: false,
    characters: false,
    location: false,
    status: true,
    continuityFlags: true,
  },
  useAsProjectDefault: true,
};
~~~

Persist under openstory:view:{projectId}. Visual layout hides/shows fields only; it must never mutate fetched panels or request a panel update.

Batch approve only eligible review panels. Batch render skips locked panels and reports per-panel failures without hiding successful versions.

- [ ] **Step 8: Implement the selected visual system**

Use CSS custom properties for paper/dark/system themes. Target:

- 1487×1058 reference composition at 1440 desktop width;
- 92px collapsed navigation rail;
- three-column storyboard region with flexible grid and 286–320px inspector;
- 14–16px body typography;
- editorial serif only for scene title;
- terracotta primary action;
- teal approved state;
- thin dividers and minimal elevation.

At widths below 960px, collapse the inspector beneath the grid and retain all actions. This is responsive web behavior, not a mobile-native client.

- [ ] **Step 9: Pass component tests and production build**

Run: npm run web:test -- --run

Expected: all tests pass.

Run: npm run web:build

Expected: TypeScript compilation and Vite production build succeed.

- [ ] **Step 10: Visually verify against the selected reference**

Start API and web development servers. Open the Storyboard Desk in the cloud browser at a 1440×1024 viewport. Capture the implementation and compare it with the selected reference in one visual inspection. Fix visible hierarchy, cropping, spacing, typography, border, and state mismatches. Re-run the browser check after fixes.

Verify these interactions in the browser:

1. navigation changes views;
2. selecting a panel updates the inspector;
3. View popover toggles fields and density;
4. Paper/Dark/System changes appearance;
5. Render all placeholders calls the scene render endpoint;
6. Approve changes only review-state artifacts;
7. source evidence expands without leaving the scene.

- [ ] **Step 11: Run backend regressions and commit**

Run: uv run pytest -q

Expected: all backend tests pass.

Run: npm run web:test -- --run

Expected: all frontend tests pass.

~~~bash
git add package.json package-lock.json apps/web apps/api/openstory_api/main.py
git commit -m "feat: add production workspace web ui"
~~~

### Task 10: Optional MLX-Gen Image Provider

**Files:**
- Create: packages/openstory/providers/image/mlxgen.py
- Modify: apps/api/openstory_api/dependencies.py
- Modify: .env.example
- Create: tests/unit/test_mlxgen_provider.py
- Create: tests/local_ai/test_mlxgen_local.py

**Interfaces:**
- Consumes: ImageGenerationProvider from Task 8.
- Produces: MLXGenImageProvider(executable: str, model: str)
- Produces: MLXGenImageProvider.is_available() -> bool
- Produces: build_image_provider(settings: Settings) -> ImageGenerationProvider

- [ ] **Step 1: Write failing subprocess-construction tests**

Patch asyncio.create_subprocess_exec and assert the positional array:

~~~python
expected = (
    "mlxgen",
    "generate",
    "--model",
    "AbstractFramework/flux.2-klein-9b-8bit",
    "--prompt",
    "Lira at the North Gate",
    "--width",
    "768",
    "--height",
    "1024",
    "--seed",
    "42",
    "--output",
    str(output_path),
)
mock_subprocess.assert_awaited_once_with(
    *expected,
    stdout=asyncio.subprocess.PIPE,
    stderr=asyncio.subprocess.PIPE,
)
~~~

Also test no seed flag when seed is None, missing executable availability, non-zero exit with sanitized stderr, and zero exit without an output file.

- [ ] **Step 2: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_mlxgen_provider.py -q

Expected: failure because the adapter does not exist.

- [ ] **Step 3: Implement safe provider**

Use shutil.which for availability. Use asyncio.create_subprocess_exec with positional arguments only. Capture communicate(), check returncode, verify output_path is a readable image through Pillow, and return ImageGenerationResult with command duration and truncated stdout in metadata. Do not store API keys or full environment dumps.

- [ ] **Step 4: Wire configuration**

Settings:

~~~text
OPENSTORY_IMAGE_PROVIDER=placeholder|mlxgen
OPENSTORY_MLXGEN_EXECUTABLE=mlxgen
OPENSTORY_MLXGEN_MODEL=AbstractFramework/flux.2-klein-9b-8bit
~~~

Placeholder remains the default. Selecting mlxgen when unavailable does not prevent API startup; the provider reports unavailable and render jobs fail with a concise 503-compatible error.

- [ ] **Step 5: Add opt-in local test**

Mark the test local_ai. Skip unless OPENSTORY_RUN_LOCAL_AI=1 and MLXGenImageProvider.is_available() are both true. The test renders one 512×512 image into tmp_path and verifies it with Pillow.

- [ ] **Step 6: Run normal tests and commit**

Run: uv run pytest tests/unit/test_mlxgen_provider.py -q

Expected: all pass without mlxgen installed.

Run: uv run pytest -m "not local_ai" -q

Expected: all tests pass with no model download.

~~~bash
git add packages/openstory/providers/image/mlxgen.py apps/api/openstory_api/dependencies.py .env.example tests
git commit -m "feat: add mlxgen image backend"
~~~

### Task 11: Versioned Episode Export and Full Mock Pipeline

**Files:**
- Create: packages/openstory/application/export_episode.py
- Create: apps/api/openstory_api/routes/exports.py
- Modify: apps/api/openstory_api/main.py
- Modify: packages/openstory/persistence/repositories.py
- Create: tests/unit/test_export_episode.py
- Create: tests/integration/test_full_mock_pipeline_export.py

**Interfaces:**
- Produces: ExportManifest(version: int, episode_id: str, created_at: datetime, source_hashes: list[str], render_version_ids: list[str], files: list[str])
- Produces: ExportBundle(project: Project, source_documents: list[SourceDocument], source_chunks: list[SourceChunk], canon_snapshot: CanonSnapshot, episode: Episode, scenes: list[Scene], panels: list[StoryboardPanel], renders: list[RenderVersion])
- Produces: ExportEpisodeService.execute(project_id: str, episode_id: str) -> ExportResult
- Produces: OpenStoryRepository.select_export_render(panel_id: str) -> RenderVersion | None
- Produces: POST /projects/{project_id}/export

- [ ] **Step 1: Write failing render-selection and export tests**

~~~python
def test_export_prefers_locked_then_approved_then_latest_draft(
    repository: OpenStoryRepository,
    panel_with_versions: PanelWithVersions,
) -> None:
    selected = repository.select_export_render(panel_with_versions.panel.id)
    assert selected.id == panel_with_versions.locked.id


def test_full_mock_pipeline_export(
    vertical_slice: VerticalSliceHarness,
) -> None:
    result = vertical_slice.run()
    export_root = Path(result.export.output_path)
    assert (export_root / "episode.json").is_file()
    assert (export_root / "episode.md").is_file()
    assert (export_root / "manifest.json").is_file()
    assert len(list((export_root / "storyboard").glob("panel-*.png"))) == 6
~~~

Also test no rendered panel produces a clear export error, a second export uses v002, JSON validates back into domain schemas, and Markdown contains scene/panel ordering.

- [ ] **Step 2: Run tests and confirm the red state**

Run: uv run pytest tests/unit/test_export_episode.py tests/integration/test_full_mock_pipeline_export.py -q

Expected: failure because export service and route do not exist.

- [ ] **Step 3: Implement deterministic render selection**

Sort status priority locked > approved > review > revise > draft, then version descending within status. Only consider render records whose file exists and whose provider result succeeded.

- [ ] **Step 4: Implement atomic versioned export**

Build exports/{episode_id}/.vNNN.tmp, write:

~~~text
episode.json
episode.md
manifest.json
storyboard/panel-0001.png
storyboard/panel-0002.png
storyboard/panel-0006.png
~~~

Use Pydantic model_dump(mode="json") with stable indentation for JSON. episode.json is an ExportBundle containing Project, selected SourceDocuments and SourceChunks, the CanonSnapshot used for the Episode, Episode, ordered Scenes, ordered StoryboardPanels, and selected RenderVersions. Markdown includes episode metadata, ordered scene headings, panel shot/action/dialogue, render status, and relative image links. Copy selected PNGs without modifying originals.

Verify every manifest path exists, then os.replace the temporary directory to exports/{episode_id}/vNNN. Persist the succeeded export Job after the rename.

- [ ] **Step 5: Implement export API**

POST /projects/{project_id}/export accepts episode_id and returns 201 with JobRunResult[ExportResult]. Execute through RunJobService with kind export and progress_total equal to the panel count. Return 404 for cross-project or missing episode and 409 when required storyboard renders are missing.

- [ ] **Step 6: Prove the complete pipeline**

The integration harness performs:

~~~text
create project
→ ingest glass_orchard.md
→ extract mock canon
→ query temporal snapshot
→ adapt episode
→ build six panels
→ render six placeholders
→ export v001
~~~

Validate episode.json as ExportBundle, assert its canon_snapshot.facts contain exact source_chunk_id and evidence values, and verify every exported image as a PNG.

- [ ] **Step 7: Run all tests and commit**

Run: uv run pytest -m "not local_ai" -q

Expected: all tests pass.

Run: uv run ruff check packages apps tests

Expected: no findings.

Run: uv run mypy

Expected: success with no issues.

~~~bash
git add packages/openstory/application/export_episode.py packages/openstory/persistence/repositories.py apps/api/openstory_api/routes/exports.py apps/api/openstory_api/main.py tests
git commit -m "feat: export storyboard episode packages"
~~~

### Task 12: Reproducible Smoke Demo, Developer Documentation, and Release Verification

**Files:**
- Create: scripts/smoke_demo.sh
- Modify: README.md
- Create: docs/architecture.md
- Create: docs/domain-model.md
- Create: docs/local-ai.md
- Modify: docs/local-environment.md
- Modify: .env.example

**Interfaces:**
- Consumes: all API and package interfaces from Tasks 1–11.
- Produces: scripts/smoke_demo.sh with zero required AI runtimes.
- Produces: clean-clone commands verified in the current environment.

- [ ] **Step 1: Write the smoke demo script**

The script must:

1. create a temporary database and workspace root with mktemp -d;
2. export OPENSTORY_TEXT_PROVIDER=mock and OPENSTORY_IMAGE_PROVIDER=placeholder;
3. start uv run uvicorn openstory_api.main:app on an available fixed development port;
4. register a trap that terminates only that server PID and removes only the temporary directory;
5. wait for /health with a bounded retry loop;
6. call every pipeline endpoint using tests/fixtures/glass_orchard.md;
7. parse IDs with python3 -c and stdin JSON, not jq;
8. assert export files and six PNGs exist;
9. print the final export path and job statuses;
10. exit non-zero on the first failed command.

- [ ] **Step 2: Run the smoke demo**

Run: bash scripts/smoke_demo.sh

Expected: exits 0 and prints a versioned export containing episode.json, episode.md, manifest.json, and six PNGs.

- [ ] **Step 3: Complete architecture and domain documentation**

architecture.md documents dependency direction:

~~~text
API/UI → application → domain
              ↓
       repository/provider protocols
              ↓
      SQLite/filesystem/adapters
~~~

domain-model.md documents project-wide ordinals, inclusive temporal intervals, provenance, conservative entity resolution, exact status transitions, immutable render versions, and export selection.

- [ ] **Step 4: Complete local AI documentation**

local-ai.md includes:

- mlx_lm.server-compatible environment variables;
- curl model-list health check;
- separation of heavyweight text and image jobs on 24 GB unified memory;
- placeholder fallback;
- MLX-Gen availability check;
- local_ai pytest command;
- statement that the MLX-Gen CLI flags require target-machine verification because mlxgen is absent in Gate 0.

- [ ] **Step 5: Complete README clean-clone workflow**

README commands:

~~~bash
uv sync --extra dev
npm install
uv run uvicorn openstory_api.main:app --reload
npm run web:dev
uv run pytest -m "not local_ai" -q
npm run web:test -- --run
npm run web:build
bash scripts/smoke_demo.sh
~~~

Document that workspaces, local databases, imported stories, and model weights are ignored.

- [ ] **Step 6: Run the complete verification matrix**

Run: uv run pytest -m "not local_ai" -q

Expected: all tests pass.

Run: uv run ruff check packages apps tests

Expected: no findings.

Run: uv run mypy

Expected: success with no issues.

Run: npm run web:test -- --run

Expected: all tests pass.

Run: npm run web:build

Expected: production build succeeds.

Run: bash scripts/smoke_demo.sh

Expected: exits 0 with a valid export.

- [ ] **Step 7: Confirm repository hygiene**

Run: git status --short --ignored

Expected: source, tests, docs, and lockfiles are tracked candidates; openstory.db, .env, workspaces contents, models, caches, and build outputs are ignored.

Run: git grep -n -E "Legendary Moonlight Sculptor|commercial manga|BEGIN.*PRIVATE"

Expected: no matches.

- [ ] **Step 8: Commit**

~~~bash
git add README.md docs scripts/smoke_demo.sh .env.example
git update-index --chmod=+x scripts/smoke_demo.sh
git commit -m "docs: add reproducible end to end demo"
~~~

- [ ] **Step 9: Create and publish the public GitHub repository**

Use the authenticated GitHub account PrinceJonaa to create public repository PrinceJonaa/openstory-studio with no auto-generated README, license, or gitignore because those files already exist locally. Set description to:

~~~text
Local-first, model-agnostic narrative production state for canon, adaptation, storyboards, continuity, and reusable assets.
~~~

Then add the returned HTTPS remote as origin and push main:

~~~bash
git remote add origin https://github.com/PrinceJonaa/openstory-studio.git
git push -u origin main
~~~

Verify the remote default branch contains the full commit sequence and Apache-2.0 license. If GitHub requires interactive reauthentication, stop only this publishing step, preserve the complete local repository, and report the exact authorization blocker.

---

## Execution Order and Checkpoints

Execute Tasks 1–12 in order with superpowers:executing-plans. After each task:

1. inspect git diff --check;
2. run the task’s focused tests;
3. run the stated regression command;
4. commit only the task’s files with the exact message;
5. record the commit hash in the execution log;
6. continue immediately when checks pass.

Stop only for a failed permission/authentication boundary, a destructive ambiguity, or evidence that an approved interface cannot work with the installed dependency. Local AI unavailability is an expected condition and never blocks the mock vertical slice.
