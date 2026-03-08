# Cherry Evals — Architecture

## Tech Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| Language | Python 3.13 | Ecosystem, type safety, async support |
| Backend | FastAPI | Async, auto-docs, Pydantic integration |
| Relational DB | PostgreSQL + SQLAlchemy | Robust, full-text search, JSON support |
| Vector DB | Qdrant | Purpose-built, rich filtering, good Python client |
| Embeddings | Google gemini-embedding-001 (swappable) | 3072 dims, good quality, available API key |
| LLM (reasoning) | Anthropic Claude | Best reasoning quality, available key |
| LLM (light tasks) | Gemini Flash | Fast, cheap, available key |
| LLM (speed) | Cerebras | Ultra-fast inference, available key |
| Observability | Langfuse | Agent tracing, cost tracking |
| Package manager | uv | Fast, reliable, lockfile |
| Lint/format | Ruff + pre-commit | Fast, comprehensive |
| Containers | Docker Compose | Local dev (Postgres, Qdrant) |
| CLI | Click | Simple, composable |

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Web UI   │  │   CLI    │  │ MCP Server│  │REST API│ │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───┬────┘ │
│       └──────────────┴─────────────┴─────────────┘      │
│                         │                                │
│  ┌──────────────────────┴──────────────────────────┐    │
│  │              FastAPI Application                  │    │
│  │  ┌─────────┐  ┌──────────┐  ┌────────────────┐  │    │
│  │  │ Routes  │  │ Models   │  │ Dependencies   │  │    │
│  │  └────┬────┘  └──────────┘  └────────────────┘  │    │
│  └───────┼──────────────────────────────────────────┘    │
│          │                                               │
│  ┌───────┴──────────────────────────────────────────┐    │
│  │              Core Business Logic                  │    │
│  │  ┌────────┐  ┌────────┐  ┌───────┐  ┌────────┐  │    │
│  │  │ Search │  │ Ingest │  │Convert│  │ Export │  │    │
│  │  └───┬────┘  └───┬────┘  └───┬───┘  └───┬────┘  │    │
│  └──────┼───────────┼───────────┼───────────┼───────┘    │
│         │           │           │           │            │
│  ┌──────┴───────────┴───────────┴───────────┴──────┐    │
│  │              Data Layer                          │    │
│  │  ┌────────────────┐  ┌────────────────────────┐ │    │
│  │  │  PostgreSQL    │  │  Qdrant                │ │    │
│  │  │  (structured)  │  │  (vectors + payloads)  │ │    │
│  │  └────────────────┘  └────────────────────────┘ │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │              Observability                        │    │
│  │  ┌────────────────┐  ┌────────────────────────┐  │    │
│  │  │  Langfuse      │  │  Logging (structlog)   │  │    │
│  │  └────────────────┘  └────────────────────────┘  │    │
│  └──────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## Data Model

### PostgreSQL

```
datasets
├── id (PK)
├── name (unique)
├── source, license, task_type, description
├── stats (JSON)
└── created_at, updated_at

examples
├── id (PK)
├── dataset_id (FK → datasets, CASCADE)
├── question (text), answer, choices (JSON)
├── example_metadata (JSON)
└── created_at

collections
├── id (PK)
├── name, description, user_id
└── created_at, updated_at

collection_examples (join table)
├── id (PK)
├── collection_id (FK → collections)
├── example_id (FK → examples)
├── added_at
└── UNIQUE(collection_id, example_id)
```

### Qdrant

One collection per dataset (e.g., `mmlu_embeddings`):
- **Vector**: embedding from gemini-embedding-001 (3072 dims)
- **Payload**: example_id, dataset_id, question, subject, split, answer

---

## Embedding Strategy

Embeddings are generated per-example by combining question + choices into a single text. The embedding provider is abstracted behind a common interface to allow swapping providers.

**Current provider**: Google `gemini-embedding-001` (3072 dimensions)

**Provider interface**:
```python
class EmbeddingProvider(Protocol):
    def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
    @property
    def dimensions(self) -> int: ...
    @property
    def model_name(self) -> str: ...
```

---

## Search Architecture

### Keyword Search (MVP-0)
PostgreSQL full-text search using `tsvector` and `tsquery`. Fast, exact matching.

### Semantic Search (MVP-1)
Qdrant vector similarity search. Query text is embedded on-the-fly, top-k nearest neighbors returned with similarity scores.

### Hybrid Search (MVP-1)
Combines keyword + semantic results using Reciprocal Rank Fusion (RRF):
- Run both searches in parallel
- Fuse results with configurable weights
- Deduplicate by example ID
- Return merged results with combined scores

---

## Interface Strategy

### REST API (primary)
FastAPI with auto-generated OpenAPI docs. Standard CRUD + search endpoints.

### CLI
Click-based CLI for local operations: ingestion, embedding, search, export.

### MCP Server (planned)
Model Context Protocol server exposing cherry-evals capabilities as tools for AI agents. Key tools:
- `search_examples`: Search across datasets
- `create_collection`: Start a new collection
- `add_to_collection`: Cherry-pick examples
- `export_collection`: Export in specified format

### Web UI (planned)
React + Tailwind frontend for visual browsing, search, and collection management.

---

## Collective Intelligence (Managed Version)

### Curation Traces
Every search → pick → export flow is recorded as a "curation trace":
```json
{
  "trace_id": "...",
  "searches": [{"query": "...", "filters": {...}, "results_shown": 50}],
  "picks": [{"example_id": "...", "rank_when_picked": 3}],
  "skips": [{"example_id": "...", "rank_when_skipped": 1}],
  "collection_id": "...",
  "export_format": "jsonl"
}
```

### Signals Derived
- **Co-selection patterns**: Examples frequently picked together
- **Quality signals**: Examples picked at high rank vs low rank
- **Search refinement**: Query reformulations that led to better picks
- **Collection archetypes**: Common collection compositions (e.g., "reasoning eval suite")

### Application
- Improve search ranking based on historical pick rates
- Suggest "others also picked" recommendations
- Detect collection gaps ("your math eval has no geometry — add these?")
- Surface trending/popular examples and collections

---

## Decision Log

### ADR-001: Google Embeddings as Default
**Decision**: Use Google gemini-embedding-001 (3072 dims) as default embedding model.
**Rationale**: API key available, good quality, generous free tier. Provider interface allows swapping.
**Trade-off**: Fewer dimensions than text-embedding-3-large (3072) but sufficient for eval dataset search. Can upgrade later.

### ADR-002: OSS Core + Managed Architecture
**Decision**: Open-source core with optional managed version.
**Rationale**: OSS drives adoption and trust. Managed version monetizes through convenience and collective intelligence.
**Impact**: Core must work fully standalone. Collective intelligence features are additive, not required.

### ADR-003: Agents as First-Class Users
**Decision**: Expose MCP server and CLI alongside REST API.
**Rationale**: AI agents are increasingly the ones building eval suites. MCP integration means any agent with MCP support can use Cherry Evals. Agent usage generates data that feeds collective intelligence.
