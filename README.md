# cherry-evals

Search, cherry-pick, and export examples from public AI evaluation datasets.

## What is this?

Cherry Evals is a platform for discovering and curating custom evaluation collections from public AI benchmark datasets (MMLU, HumanEval, GSM8K, etc.). Instead of writing one-off scripts to filter and convert datasets, use Cherry Evals to:

- **Search** across multiple datasets with keyword, semantic, and hybrid search
- **Cherry-pick** individual examples into curated collections
- **Export** collections to any eval framework format (Langfuse, LangSmith, Inspect AI, JSONL, CSV)

Works for both humans (web UI, CLI) and AI agents (MCP server, REST API).

## Quick Start

```bash
# Clone and install
git clone https://github.com/your-org/cherry-evals.git
cd cherry-evals
uv sync

# Start infrastructure
docker compose up -d

# Run migrations
uv run alembic upgrade head

# Ingest a dataset
uv run python -m cherry_evals.cli ingest mmlu

# Generate embeddings
uv run python -m cherry_evals.cli embed mmlu

# Start the API
uv run fastapi dev api/main.py
```

## Interfaces

| Interface | For | Status |
|-----------|-----|--------|
| REST API | Programmatic access | Available |
| CLI | Local operations | Available |
| MCP Server | AI agent integration | Planned |
| Web UI | Visual browsing | Planned |

## Project Structure

```
cherry-evals/
├── api/                # FastAPI REST API
├── cherry_evals/       # Core package (CLI, ingestion, embeddings)
├── core/               # Business logic (search, convert, export)
├── db/                 # Database layer (PostgreSQL, Qdrant)
├── agents/             # LLM-powered features
├── tests/              # Test suite
└── docs/               # Architecture and vision docs
```

## Development

```bash
uv run pytest                  # Run tests
uv run ruff check .            # Lint
uv run ruff format .           # Format
uv run pre-commit run --all    # All checks
```

See [AGENTS.md](./AGENTS.md) for the full development guide.
See [ROADMAP.md](./ROADMAP.md) for the development roadmap.

## Tech Stack

Python 3.13 | FastAPI | PostgreSQL | Qdrant | Google Embeddings | Anthropic Claude | Langfuse

## License

[Elastic License 2.0](./LICENSE) — free to use and modify, but you may not offer it as a competing hosted service.
