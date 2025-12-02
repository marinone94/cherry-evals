# cherry-evals

Cherry-evals is a webapp for collecting, searching, and managing AI evaluation datasets used by vendors to benchmark their models.

Cherry-evals helps researchers and practitioners:
- Discover public evaluation datasets
- Search datasets and examples using multiple strategies (keyword, semantic, topic, or combinations)
- Build custom evaluation collections by selecting relevant examples
- Convert evaluation data to any format using predefined converters or custom lambda functions
- Export evaluations to local storage, Langfuse, or Arize Phoenix

The tool is built to be:
- **Transparent and debuggable**: All operations are traceable and observable
- **Extensible**: Easy to add new data sources, converters, and export targets
- **Agent-powered**: Uses Google ADK for intelligent search and LLM integration

---

## Overview

Cherry-evals aggregates public evaluation datasets from AI vendors (starting with text-based evaluations, expanding to multi-modal support). Users can search through datasets using various strategies, manually curate examples into custom collections, and export them in formats suitable for their evaluation workflows.

Key capabilities:
- **Dataset Collection**: Automatically collects and indexes public eval datasets from AI vendors
- **Multi-Strategy Search**: Keyword, semantic, topic-based, or hybrid search across datasets
- **Manual Curation**: Select/deselect examples to build custom eval collections
- **Format Conversion**: Convert between standard formats or use custom lambda functions (including LLM-generated converters)
- **Multi-Target Export**: Export to local files, Langfuse, or Arize Phoenix

---

## Core Features

### Dataset Management
- [ ] Collect public evaluation datasets from EleutherAI, DeepEval, BigBench, HELM (text-first, then multi-modal)
- [ ] Index datasets with metadata (source, date, model tested, metrics)
- [ ] Track dataset versions and updates
- [ ] Support for standard eval formats (JSONL, CSV, etc.)

### Search Capabilities
- [ ] Keyword search across datasets and examples
- [ ] Semantic search using embeddings
- [ ] Topic-based clustering and filtering
- [ ] Hybrid search combining multiple strategies
- [ ] Advanced filtering (by dataset, model, metric, date range)

### Collection Management
- [ ] Create custom eval collections
- [ ] Add/remove examples from collections
- [ ] Organize collections with tags and metadata
- [ ] Share collections (future: export/import)

### Format Conversion
- [ ] Predefined converters for standard formats (JSONL, CSV, Langfuse, Phoenix, etc.)
- [ ] Custom lambda functions for user-defined conversions
- [ ] LLM-generated converters based on natural language descriptions
- [ ] Validation and error handling for conversions

### Export & Integration
- [ ] Export to local filesystem (JSON, JSONL, CSV)
- [ ] Export to Langfuse (structured eval runs)
- [ ] Export to Arize Phoenix (evaluation datasets)
- [ ] Batch export operations

---

## Tech Stack

- **Language**: Python 3.13
- **Agent Framework**: [Google ADK (Agent Development Kit)](https://github.com/google/adk-python)
- **LLM Models**: Gemini 2.5 Flash (via ADK native integration)
- **Backend**: FastAPI
- **RAG Solutions** (to be compared):
  - [Qdrant](https://qdrant.tech/)
  - [Vespa](https://vespa.ai/)
  - [Redis](https://redis.io/)
  - [GCP Vertex AI RAG engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff) + [pre-commit](https://pre-commit.com/)
- **Data Storage**: JSON files for collections, metadata, and configuration
- **Observability**: Local Langfuse server for tracing, latency monitoring, agent steps

---

## Quick Start

### Prerequisites

- Python **3.13**
- `uv` (package + venv manager)
- `pre-commit` (for git hooks)
- A Google API KEY for Gemini models
- (Optional) Qdrant, GCP credentials, or Nim RAG setup for RAG features

### Installation & Setup

```bash
# Clone the repo (when moved to its own repository)
git clone https://github.com/your-org/cherry-evals.git
cd cherry-evals

# Create and sync environment with uv (installs deps from pyproject.toml)
uv sync

# Install pre-commit hooks (ruff, uv lock, etc.)
uv run pre-commit install
```

### Environment

Create a `.env` file at the project root (or configure your environment) with:

```bash
# Google Gemini API Key (required for ADK agents)
GOOGLE_API_KEY=your-api-key-here
GOOGLE_GENAI_USE_VERTEXAI=0

# Optional: RAG backend selection
CHERRY_RAG_BACKEND=qdrant  # Options: qdrant, nim, gcp
QDRANT_URL=http://localhost:6333  # If using Qdrant
# GCP credentials via gcloud CLI or service account JSON

# Optional overrides
CHERRY_DATA_DIR=~/.cherry-evals  # Default data directory
CHERRY_LOG_LEVEL=INFO            # Logging level
```

### Start the Backend

```bash
# Run FastAPI server
uv run uvicorn cherry_evals.api.main:app --reload

# Or run ADK agents directly (for testing)
uv run adk run cherry-evals-adk
uv run adk web
```

---

## Development Commands

```bash
# Install dependencies (creates venv + syncs)
uv sync

# Add a new dependency
uv add <package>

# Remove a dependency
uv remove <package>

# Update a dependency
uv add --upgrade <package>

# List dependencies
uv run uv pip list

# Run the FastAPI backend
uv run uvicorn cherry_evals.api.main:app --reload

# Run ADK agents (for testing)
uv run adk run cherry-evals-adk
uv run adk web

# Run the test suite
uv run pytest

# Lint & format with Ruff
uv run ruff check .
uv run ruff format .

# Install pre-commit hooks
uv run pre-commit install

# Run all pre-commit hooks manually
uv run pre-commit run --all-files
```

---

## Architecture

Cherry-evals uses **Google's Agent Development Kit (ADK)** for intelligent search and LLM-powered operations:

- **Search Agents**: Deep semantic search across evaluation datasets
- **Conversion Agents**: LLM-powered format conversion and validation
- **Collection Agents**: Intelligent suggestions for collection curation

For details about the architecture, see [`AGENTS.md`](./AGENTS.md) and future `docs/architecture.md`.

---

## Roadmap

For future MVPs and long-term roadmap, see [`ROADMAP.md`](./ROADMAP.md).

---

## Contributing

This project follows agentic best practices and ADK patterns. See [`AGENTS.md`](./AGENTS.md) for detailed development guidelines.

**Building cherry-evals, the evaluation dataset management tool for AI practitioners**

