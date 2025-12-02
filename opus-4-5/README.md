# cherry-evals

**Cherry-pick the best evaluation examples from public AI benchmarks.**

cherry-evals is a webapp that aggregates public evaluation datasets used by AI vendors to benchmark their models, enabling researchers and engineers to search, curate, augment and export custom evaluation collections.

---

## Overview

Building robust AI evaluations is hard. Public benchmarks like MMLU, HumanEval, GSM8K, and hundreds of others contain valuable test cases, but they're scattered across formats, repositories, and providers.

cherry-evals solves this by:
- **Aggregating** public evals from major AI vendors into a unified, searchable database
- **Enabling deep search** via keyword, semantic similarity, topic, re-ranking or any combination
- **Allowing curation** of custom eval collections through manual selection/deselection
- **Converting** evaluation data to any format using predefined or custom functions
- **Exporting** to local files, Langfuse, Arize Phoenix, and other eval tools or frameworks

---

## Core Features

### 1. Eval Dataset Collection
- [ ] Aggregate public evals from EleutherAI, DeepEval, BigBench, HELM
- [ ] Text modality first, with support for multi-modal evals planned
- [ ] Automatic metadata extraction (source, license, task type, difficulty)
- [ ] Incremental updates as new benchmarks are released

### 2. Deep Search
- [ ] **Keyword search**: Traditional text matching across questions, answers, and metadata
- [ ] **Semantic search**: Find similar examples by meaning using embeddings
- [ ] **Topic search**: Filter by task type, domain, or custom taxonomies
- [ ] **Re-ranking**: Use LLMs to re-rank retrieved results
- [ ] **Hybrid search**: Combine any of the above for best results
- [ ] ADK agents for intelligent query understanding and refinement

### 3. Custom Collection Curation
- [ ] Browse search results with rich previews
- [ ] Manual select/deselect individual examples
- [ ] Bulk operations (select all matching, exclude by pattern)
- [ ] Organize examples into named collections
- [ ] Add notes and tags to collections

### 4. Format Conversion
- [ ] **Predefined converters** for standard formats:
  - [ ] OpenAI Evals format
  - [ ] LangChain/LangSmith format
  - [ ] Inspect AI format
  - [ ] LMMS-Eval format
  - [ ] Custom JSON/JSONL schemas
- [ ] **Custom converters**:
  - [ ] User-defined lambda functions
  - [ ] LLM-generated conversion code
  - [ ] Template-based transformations

### 5. Export Destinations
- [ ] **Local export**: JSON, JSONL, CSV, Parquet
- [ ] **Langfuse**: Direct integration for AI experiments
- [ ] **Arize Phoenix**: Direct integration for AI experiments
- [ ] Webhook/API push to custom endpoints

---

## Tech Stack

- **Language**: Python 3.13
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Agent Framework**: [Google ADK (Agent Development Kit)](https://github.com/google/adk-python)
- **LLM Models**: TBD
- **Vector Database**: (TBD)[Qdrant](https://qdrant.tech/), Redis, Vespa, ... do some more research here...
- **RAG Options** (to be compared):
  - NVIDIA NIM RAG
  - GCP Native RAG Tools
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff) + [pre-commit](https://pre-commit.com/)
- **Data Storage**: PostgreSQL + Qdrant for evals, JSON for configs
- **Observability**: Langfuse for agent tracing

> **Note**: Frontend, authentication, and pricing will be built separately in Lovable.

---

## Architecture

```
cherry-evals/
├── api/                    # FastAPI application
│   ├── routes/             # API endpoints
│   │   ├── datasets.py     # Dataset CRUD operations
│   │   ├── search.py       # Search endpoints
│   │   ├── collections.py  # Collection management
│   │   ├── convert.py      # Format conversion
│   │   └── export.py       # Export destinations
│   ├── models/             # Pydantic models
│   └── main.py             # FastAPI app entry point
│
├── agents/                 # ADK agent definitions
│   ├── agent.py            # Root agent and sub-agents
│   ├── prompts/            # Agent prompts as code
│   └── tools/              # Agent tools
│
├── core/                   # Business logic
│   ├── ingest/             # Dataset ingestion pipelines
│   ├── search/             # Search implementations
│   ├── convert/            # Format converters
│   └── export/             # Export adapters
│
├── db/                     # Database layer
│   ├── postgres/           # PostgreSQL models & queries
│   └── qdrant/             # Qdrant vector operations
│
├── data/                   # Local data storage
│   ├── raw/                # Raw downloaded datasets
│   ├── processed/          # Normalized dataset cache
│   └── exports/            # User export outputs
│
├── tests/                  # Test suite
│   ├── unit/
│   ├── integration/
│   └── system/
│
├── docs/                   # Documentation
├── AGENTS.md               # Development guide for AI IDEs
├── ROADMAP.md              # Development roadmap
└── README.md               # This file
```

---

## Quick Start

### Prerequisites

- Python **3.13**
- `uv` (package + venv manager)
- `pre-commit` (for git hooks)
- Docker (for Qdrant and PostgreSQL)
- A Google API KEY for Gemini models

### Installation & Setup

```bash
# Clone the repo
git clone https://github.com/marinone94/cherry-evals.git
cd cherry-evals

# Create and sync environment with uv
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Start infrastructure (Qdrant + PostgreSQL)
docker-compose up -d

# Run database migrations
uv run alembic upgrade head
```

### Environment

Create a `.env` file at the project root:

```bash
# Required
GOOGLE_API_KEY=your-google-api-key
DATABASE_URL=postgresql://user:pass@localhost:5432/cherry_evals
QDRANT_URL=http://localhost:6333

# Optional
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
```

### Start the Server

```bash
# Start the FastAPI server
uv run uvicorn api.main:app --reload

# Or with ADK web UI for agent debugging
uv run adk web
```

---

## Development Commands

```bash
# Install dependencies
uv sync

# Add a new dependency
uv add <package>

# Run tests
uv run pytest

# Lint & format
uv run ruff check .
uv run ruff format .

# Run pre-commit hooks
uv run pre-commit run --all-files

# Start FastAPI server
uv run uvicorn api.main:app --reload

# Start ADK web UI
uv run adk web

# Ingest a new dataset (example)
uv run python -m core.ingest.runner --source mmlu
```

---

## Supported Eval Sources (Planned)

| Source | Status | Formats |
|--------|--------|---------|
| MMLU | Planned | Multiple choice |
| HumanEval | Planned | Code generation |
| GSM8K | Planned | Math reasoning |
| HellaSwag | Planned | Commonsense reasoning |
| TruthfulQA | Planned | Truthfulness |
| ARC | Planned | Science QA |
| WinoGrande | Planned | Coreference |
| BIG-Bench | Planned | Various |
| MATH | Planned | Math problems |
| DROP | Planned | Reading comprehension |
| SQuAD | Planned | QA |
| HuggingFace Hub | Planned | Various |
| OpenAI Evals | Planned | Various |

---

## Documentation

For detailed documentation, see:

- **[AGENTS.md](./AGENTS.md)** - Development guide for AI IDE agents
- **[ROADMAP.md](./ROADMAP.md)** - Development roadmap and milestones
- **[docs/architecture.md](./docs/architecture.md)** - Detailed system architecture
- **[docs/api.md](./docs/api.md)** - API reference

---

## Contributing

See [AGENTS.md](./AGENTS.md) for development guidelines and conventions.

---

## License

TBD

---

**Building better AI evaluations, one cherry-picked example at a time.**

