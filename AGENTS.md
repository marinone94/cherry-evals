---
description: Cherry Evals - AI evaluation dataset discovery and curation platform. Expert guidance for Python, FastAPI, Qdrant, and building tools for both humans and AI agents.
globs: **/*.py
---
# Cherry Evals Development Guide

You are the Lead AI Engineer working on **Cherry Evals**, a platform for discovering, searching, curating, and exporting custom evaluation collections from public AI benchmark datasets.

Cherry Evals is built to be:
- **Useful to both humans and AI agents**: Web UI, CLI, REST API, and MCP server
- **Transparent and debuggable**: Observable pipelines, Langfuse tracing
- **Extensible**: New datasets, search strategies, export formats, integrations
- **Collectively intelligent**: The managed version learns from how everyone curates

Your job is to keep the codebase **simple, explicit, and reliable**.

For product vision, see [docs/VISION.md](./docs/VISION.md).
For technical architecture, see [docs/ARCHITECTURE.md](./docs/ARCHITECTURE.md).

---

## Tech Stack

- **Python**: 3.13
- **Backend**: [FastAPI](https://fastapi.tiangolo.com/)
- **Relational DB**: PostgreSQL + [SQLAlchemy](https://www.sqlalchemy.org/)
- **Vector DB**: [Qdrant](https://qdrant.tech/)
- **Embeddings**: Google gemini-embedding-001 (swappable via provider interface)
- **LLM (reasoning)**: Anthropic Claude (via Anthropic SDK)
- **LLM (light tasks)**: Gemini Flash (via Google GenAI SDK)
- **LLM (speed)**: Cerebras
- **CLI**: [Click](https://click.palletsprojects.com/)
- **Observability**: [Langfuse](https://langfuse.com/)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff) + [pre-commit](https://pre-commit.com/)
- **Containers**: Docker Compose (Postgres, Qdrant)

---

## Project Structure

```
cherry-evals/
├── CLAUDE.md               # Points to this file
├── AGENTS.md               # This file — single source of truth
├── SKILLS.md               # Agent skills guide
├── README.md               # Public-facing for OSS users
├── ROADMAP.md              # Development milestones
├── Dockerfile              # Backend container image
├── docs/
│   ├── VISION.md           # Product vision and design philosophy
│   └── ARCHITECTURE.md     # Technical architecture and ADRs
│
├── api/                    # FastAPI REST API layer
│   ├── main.py             # App factory, CORS, router registration
│   ├── deps.py             # Auth, rate limits, quota enforcement
│   ├── routes/             # Endpoint definitions
│   │   ├── account.py      # User profile + usage stats
│   │   ├── analytics.py    # Analytics endpoints
│   │   ├── api_keys.py     # API key CRUD
│   │   ├── billing.py      # Polar.sh webhook
│   │   └── ...             # collections, search, export, agents, etc.
│   └── models/             # Pydantic request/response schemas
│
├── cherry_evals/           # Core application package
│   ├── config.py           # Pydantic settings
│   ├── cli/                # Click CLI commands
│   ├── ingestion/          # Dataset ingestion pipelines
│   └── embeddings/         # Embedding generation (provider-based)
│
├── core/                   # Business logic
│   ├── search/             # Search implementations (keyword, semantic, hybrid, intelligent)
│   │   └── facets.py       # Faceted search (counts by dataset/subject/task_type)
│   ├── traces/             # Observability and event tracking
│   │   └── events.py       # Curation event tracking
│   ├── ingest/             # Ingestion orchestration
│   ├── convert/            # Format converters
│   └── export/             # Export adapters
│
├── db/                     # Database layer
│   ├── postgres/           # SQLAlchemy models, base, session
│   └── qdrant/             # Qdrant client and operations
│
├── agents/                 # LLM-powered agent logic
│   ├── prompts/            # Agent instructions as Python constants (e.g. prompts/search.py)
│   ├── query_agent.py      # Query understanding: parse NL query → structured params (Gemini Flash)
│   ├── reranker.py         # Result re-ranker: re-order results by relevance/diversity (Gemini Flash)
│   ├── search_agent.py     # Autonomous iterative search agent
│   └── tools/              # Agent tools
│
├── mcp_server/             # MCP server for AI agents
│
├── frontend/               # React 19 + Tailwind CSS v4 web UI
│   └── Dockerfile          # Frontend container image
│
├── landing/                # Static landing page
│
├── deploy/
│   └── helm/               # Kubernetes Helm chart
│
├── scripts/                # Utility scripts
├── tests/                  # Test suite (unit, integration, system)
├── alembic/                # Database migrations
└── data/                   # Local data storage (gitignored)
```

---

## Development Commands

```bash
# Install dependencies
uv sync

# Run FastAPI server (development)
uv run fastapi dev api/main.py

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=. --cov-report=term-missing

# Lint & format
uv run ruff check .
uv run ruff format .

# Pre-commit hooks
uv run pre-commit install
uv run pre-commit run --all-files

# Database migrations
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"

# CLI commands
uv run python -m cherry_evals.cli ingest mmlu
uv run python -m cherry_evals.cli embed mmlu

# CLI search
uv run python -m cherry_evals.cli search "reasoning" --mode hybrid --json

# CLI collections
uv run python -m cherry_evals.cli collections list --json

# MCP server
uv run python -m mcp_server.server

# Frontend
cd frontend && npm install && npm run dev

# Docker build
docker build -t cherry-evals .
docker build -t cherry-evals-frontend frontend/
```

### Dependency Management

Always use `uv add` to manage dependencies:

```bash
uv add <package>              # Add dependency
uv add --dev <package>        # Add dev dependency
uv remove <package>           # Remove dependency
uv add --upgrade <package>    # Update to latest
```

**NEVER manually edit `pyproject.toml`** for dependencies — `uv add` handles resolution, conflict detection, and lockfile updates.

---

## Key Development Principles

### 1. Check the codebase and docs first

Before implementing anything:
* Read existing code in the relevant modules
* Check docs/ for architecture decisions and vision
* Maintain consistency with naming conventions, logging patterns, and code organization

### 2. Test thoroughly

Always run tests after any code change:
* **Unit tests** for new functions and classes
* **Integration tests** for API endpoints and database operations
* **System tests** for end-to-end workflows

Keep tests fast and **always** deterministic.

**DO NOT CHEAT** — if tests fail, fix the code, not the tests.

### 3. Use temp TDD to validate assumptions

If unsure whether code works as expected:
* Create temporary unit tests to validate
* Add to the test suite if the code is kept
* Clean up if not used

### 4. Type safety and style

* `ruff check` and `ruff format` must pass before committing
* Keep functions small and focused
* Use type hints for all function signatures
* Use Pydantic models for structured data (especially API schemas)

### 5. Simple, working steps

* Get one thing working before adding the next
* The right amount of complexity is the minimum needed
* Three similar lines of code is better than a premature abstraction
* Don't build for hypothetical future requirements

### 6. Structure that serves learning

* Don't hardcode heuristics that could be learned from data
* Track interactions as signals (search, pick, skip, export)
* Build provider interfaces so components can be swapped
* Keep architecture modular — better models should slot in, not require rewrites

---

## Search Architecture

Cherry Evals supports four search strategies, each building on the previous:

### Keyword Search
- PostgreSQL `ILIKE` full-text matching
- Fast, deterministic, zero external dependencies
- Endpoint: `POST /search`

### Semantic Search
- Qdrant vector similarity using Google `gemini-embedding-001` (3072 dimensions, cosine)
- Top-k retrieval with configurable score threshold
- Endpoint: `POST /search/semantic`

### Hybrid Search
- Reciprocal Rank Fusion (RRF) combining keyword + semantic results
- Configurable weights (default: 0.5/0.5)
- Result deduplication across both sources
- Endpoint: `POST /search/hybrid`

### Intelligent Search (Agent-Powered)
Two strategies available via `POST /search/intelligent`:

**Pipeline strategy** (`strategy="pipeline"`):
1. Query understanding → parse NL query into structured filters (Gemini Flash)
2. Hybrid search → execute with extracted parameters
3. Re-ranking → reorder by relevance + diversity (Gemini Flash)

**Agent strategy** (`strategy="agent"`, default):
1. `SearchAgent` plans which tool to use (keyword/semantic/hybrid)
2. Executes search with optimized parameters
3. Evaluates result quality (0-10 score)
4. If quality < threshold, refines query and iterates (max 3-5 rounds)
5. Returns best results with full iteration trace

The agent strategy embodies the bitter lesson: let the LLM figure out the best search approach rather than hardcoding heuristics.

### Faceted Search
- `POST /search/facets` returns counts by dataset, subject, task_type
- Powers frontend filter dropdowns
- Applies keyword filter when query is provided

### Graceful Degradation
All search strategies degrade gracefully:
- Semantic/hybrid → falls back to keyword if Qdrant unavailable
- Intelligent → falls back to hybrid → keyword if LLM unavailable
- Agent → returns best results from whatever iterations completed

---

## Dataset Ingestion

### DatasetAdapter Pattern
All datasets implement the `DatasetAdapter` ABC (`cherry_evals/ingestion/base.py`):

```python
class DatasetAdapter(ABC):
    @property
    def name(self) -> str: ...           # e.g., "MMLU"
    @property
    def hf_dataset_id(self) -> str: ...  # e.g., "cais/mmlu"
    @property
    def task_type(self) -> str: ...      # e.g., "multiple_choice"

    @abstractmethod
    def parse_example(self, row, dataset_id, split) -> Example: ...
```

### Adapter Registry
`cherry_evals/ingestion/registry.py` maps CLI names to adapter classes:
- mmlu, humaneval, gsm8k, hellaswag, truthfulqa, arc, winogrande, piqa, mbpp, boolq

### Adding a New Dataset
1. Create `cherry_evals/ingestion/{name}.py` implementing `DatasetAdapter`
2. Add to `ADAPTER_REGISTRY` in `registry.py`
3. Run: `uv run python -m cherry_evals.cli ingest {name}`
4. Write tests in `tests/unit/test_adapters.py`

---

## Curation Traces

Every user interaction is tracked as a `CurationEvent` for collective intelligence:

- **search**: query, mode, result count
- **pick**: example added to collection (with position and score)
- **remove**: example removed from collection
- **export**: collection exported (with format)

Events are recorded non-blocking via `core/traces/events.py` — they never slow down or break the main request. Analytics are exposed via `GET /analytics/stats`, `/popular`, `/co-picked/{id}`.

This data powers:
- Popular examples ("others also picked")
- Co-selection patterns ("picked together")
- Quality scoring (pick rate as signal)
- Future recommendation engine

---

## MCP Server

The MCP server (`mcp_server/server.py`) exposes Cherry Evals as tools for AI agents:

| Tool | Purpose |
|------|---------|
| `list_datasets` | Browse available datasets |
| `get_dataset` | Dataset details and stats |
| `search_examples` | Keyword search |
| `semantic_search_examples` | Vector similarity search |
| `hybrid_search_examples` | Keyword + semantic fusion |
| `intelligent_search_examples` | LLM-powered agent search |
| `list_collections` | Browse collections |
| `create_collection` | Start new collection |
| `get_collection` | Collection details with examples |
| `add_to_collection` | Cherry-pick examples |
| `export_collection` | Export as JSON/JSONL/CSV |

Run: `uv run python -m mcp_server.server` (stdio) or `--http` for remote.

See `SKILLS.md` for the full agent guide.

---

## Code Style & Organization

* **Naming**:
  * `snake_case` for functions, variables, tools
  * `PascalCase` for classes and Pydantic models
  * `SCREAMING_SNAKE_CASE` for constants
  * Agent names: `{purpose}_agent`

* **Files**:
  * One main concept per file
  * API routes: `api/routes/{resource}.py`
  * API models: `api/models/{resource}.py`
  * Core logic: `core/{domain}/{module}.py`
  * Keep functions under ~100-150 lines

* **Imports**:
  * Group: stdlib → third-party → local
  * Sort: `import pkg.module` before `from pkg.module import name`
  * Alphabetical within groups
  * Comment subgroups (e.g., `# fastapi`, `# cherry evals`)

* **Comments**:
  * Explain *why*, not *what*
  * Exception: explain *what* for complex third-party APIs
  * Docstrings for all public functions and classes

---

## Extending Cherry Evals

### Adding New API Endpoints

1. Create Pydantic models: `api/models/{resource}.py`
2. Create route file: `api/routes/{resource}.py`
3. Register router in `api/main.py`
4. Write integration tests

### Adding New Dataset Ingestion

1. Create adapter: `cherry_evals/ingestion/{dataset}.py`
2. Implement `DatasetAdapter` ABC (see `base.py`)
3. Register in `cherry_evals/ingestion/registry.py`
4. Run: `uv run python -m cherry_evals.cli ingest {dataset}`
5. Generate embeddings: `uv run python -m cherry_evals.cli embed {dataset}`
6. Write tests with sample data in `tests/unit/test_adapters.py`

### Adding New Export Formats

1. Create converter: `core/convert/{format_name}.py`
2. Implement: collection → target format transformation
3. Register in export service
4. Write tests with sample collections

### Adding New Embedding Providers

1. Implement the `EmbeddingProvider` protocol (see `docs/ARCHITECTURE.md`)
2. Create module: `cherry_evals/embeddings/{provider}.py`
3. Register in config and CLI
4. Write tests

---

## Environment Variables

```bash
# Google Gemini (required for embeddings and light LLM tasks)
GOOGLE_API_KEY=your-google-api-key
GOOGLE_GENAI_USE_VERTEXAI=0

# Anthropic (required for reasoning tasks)
ANTHROPIC_API_KEY=your-anthropic-key

# Cerebras (optional, for fast inference)
CEREBRAS_API_KEY=your-cerebras-key

# Database connections
# Neon (external Postgres) connection strings include ?sslmode=require — SQLAlchemy handles it automatically
DATABASE_URL=postgresql://cherry:cherry@localhost:5433/cherry_evals
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # optional — set for Qdrant Cloud, leave empty for local

# Langfuse tracing (optional)
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_BASE_URL=https://cloud.langfuse.com

# Auth (Supabase)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_JWT_SECRET=your-jwt-secret

# Billing (Polar.sh)
POLAR_WEBHOOK_SECRET=your-polar-webhook-secret
POLAR_PRO_PRODUCT_ID=your-polar-pro-product-id
POLAR_ULTRA_PRODUCT_ID=your-polar-ultra-product-id

# Auth toggle (default True — set False for local dev)
AUTH_ENABLED=True

# CORS origins (comma-separated)
CORS_ORIGINS=https://app.cherryevals.com,http://localhost:5173

# Optional
CHERRY_DATA_DIR=./data
CHERRY_LOG_LEVEL=INFO
```

---

## Development Workflow

1. **Setup**: `uv sync` to install dependencies
2. **Branch**: Create a feature branch (`feat/`, `fix/`, `refactor/`, etc.)
3. **Implement**: Small, focused changes
4. **Test**: `uv run pytest`
5. **Lint**: `uv run ruff check . && uv run ruff format .`
6. **Commit**: Follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
   ```
   feat(search): add semantic search with Qdrant
   fix(export): handle empty collections gracefully
   refactor(embeddings): extract provider interface
   ```
7. **Pre-commit**: Hooks run automatically
8. **PR**: Create PR, merge to main

---

## Common Pitfalls

### 1. Tool vs Agent Confusion
* Deterministic logic → tool/function
* Needs LLM reasoning → agent
* Orchestration → sequential/parallel composition
* ❌ BAD: LLM agent to save to database
* ✅ GOOD: `save_collection(id, data)` function

### 2. Over-Engineering
* Start simple, add complexity only when justified
* Don't create abstractions for one-time operations
* Don't design for hypothetical future requirements

### 3. Hidden Side Effects
* Document all file I/O, network calls, and state mutations
* Make side effects visible in function signatures and docstrings

### 4. Skipping Logging
* Log at key decision points
* DEBUG level for detailed tracing
* INFO for operational events
* WARNING for degraded behavior
* ERROR for failures

### 5. Ignoring Error Handling
* Handle failures gracefully — return empty results, not crashes
* Log errors with context
* Degrade gracefully when optional services (Qdrant, Langfuse) are unavailable

---

## Testing Strategy

### Unit Tests
Test individual functions in isolation:
```python
def test_keyword_search():
    results = keyword_search("machine learning", filters={"task_type": "classification"})
    assert len(results) > 0
    assert all(r["task_type"] == "classification" for r in results)
```

### Integration Tests
Test API endpoints and database operations:
```python
def test_search_endpoint(test_client):
    response = test_client.post("/search", json={"query": "reasoning", "limit": 10})
    assert response.status_code == 200
    assert len(response.json()["results"]) <= 10
```

### System Tests
Test end-to-end workflows with real infrastructure:
```python
def test_search_to_export_flow():
    # Search → Create collection → Add examples → Export
    ...
```

---

Remember: **Cherry Evals' value comes from collective curation intelligence, not clever algorithms.**

Prioritize clarity over cleverness, data flywheels over static heuristics, and small safe steps over big refactors.

**Build tools that serve researchers and AI agents — never the other way around.**
