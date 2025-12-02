---
description: cherry-evals - AI eval curation platform. Expert guidance for Python, FastAPI, ADK, Qdrant, and eval dataset management.
globs: **/*.py
---
# cherry-evals Development Guide

You are the Lead AI Engineer working on **cherry-evals**, a webapp for curating custom AI evaluation collections from public benchmarks.

cherry-evals is built to be:
- **Searchable**: Deep search across thousands of eval examples
- **Flexible**: Any format, any destination
- **Extensible**: Easy to add new datasets, converters, and export targets

Your job is to keep the codebase **simple, explicit, and reliable**, and to follow best practices when working with FastAPI, Google's Agent Development Kit (ADK), and Qdrant.

---

## Project Architecture

### Core Concepts

cherry-evals has four main subsystems:

1. **Ingestion**: Download, normalize, and index public eval datasets
2. **Search**: Keyword, semantic, and hybrid search across all indexed examples
3. **Collections**: User-curated collections of cherry-picked examples
4. **Export**: Convert and export to various formats and destinations

### Agent Integration

cherry-evals uses **Google's Agent Development Kit (ADK)** for intelligent search features:

- **Agent Types**:
  - **LlmAgent**: Single-purpose agents that perform specific tasks using an LLM
  - **SequentialAgent**: Orchestrates multiple sub-agents in a fixed sequence
  - **ParallelAgent**: Executes multiple sub-agents concurrently for efficiency

- **Agent Properties**:
  - **Model**: The LLM model to use (e.g., `gemini-2.5-flash`)
  - **Name**: Unique identifier for the agent
  - **Description**: Clear explanation of the agent's purpose
  - **Instruction**: Detailed prompt defining the agent's behavior
  - **Tools**: List of callable tools/functions the agent can use
  - **Sub-agents**: Child agents for single/sequential/parallel invocation

- **Workflow Pattern**:
  - Agents are used for **intelligent search** (query understanding, expansion)
  - Agents are used for **LLM-powered conversion** (natural language to converter code)
  - Deterministic operations (CRUD, export) use **pure Python tools**

- **Prompts**:
  - Prompts are stored in the `agents/prompts/` directory as Python constants
  - Each agent has a `DESCRIPTION` constant and LLM agents have also an `INSTRUCTIONS` constant
  - Prompts should be explicit, not contradictory nor ambiguous
  - Use **bold** and CAPITAL letters to increase attention on specific words or phrases

### Agent Structure

cherry-evals implements the following agent hierarchy:

```
search_agent (SequentialAgent)
├── query_understanding_agent (LlmAgent)
│   └── Parses user query intent and extracts structured filters
│   └── Tools: [taxonomy lookup, dataset metadata]
├── query_expansion_agent (LlmAgent)
│   └── Expands query with synonyms and related concepts
│   └── Tools: [embedding similarity]
└── result_ranking_agent (LlmAgent)
    └── Re-ranks results based on relevance and diversity
    └── Tools: [result scoring]

converter_agent (LlmAgent)
└── Generates custom converter code from natural language description
└── Tools: [code validation, sandbox execution]
```

### File Structure

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
│   │   ├── dataset.py      # Dataset schemas
│   │   ├── example.py      # Example schemas
│   │   ├── collection.py   # Collection schemas
│   │   ├── search.py       # Search request/response
│   │   └── export.py       # Export job schemas
│   ├── deps.py             # Dependency injection
│   └── main.py             # FastAPI app entry point
│
├── agents/                 # ADK agent definitions
│   ├── agent.py            # Root agent and sub-agents
│   ├── prompts/            # Agent prompts as code
│   │   ├── query_understanding.py
│   │   ├── query_expansion.py
│   │   ├── result_ranking.py
│   │   └── converter.py
│   └── tools/              # Agent tools
│       ├── taxonomy.py
│       ├── embeddings.py
│       └── code_sandbox.py
│
├── core/                   # Business logic
│   ├── ingest/             # Dataset ingestion pipelines
│   │   ├── base.py         # Base ingestion class
│   │   ├── mmlu.py         # MMLU-specific ingestion
│   │   ├── humaneval.py    # HumanEval-specific ingestion
│   │   └── runner.py       # CLI for running ingestion
│   ├── search/             # Search implementations
│   │   ├── keyword.py      # Full-text search
│   │   ├── semantic.py     # Vector similarity search
│   │   └── hybrid.py       # Combined search
│   ├── convert/            # Format converters
│   │   ├── base.py         # Base converter interface
│   │   ├── openai.py       # OpenAI Evals format
│   │   ├── langchain.py    # LangChain format
│   │   ├── inspect.py      # Inspect AI format
│   │   └── custom.py       # Custom lambda converters
│   └── export/             # Export adapters
│       ├── local.py        # File export
│       ├── langfuse.py     # Langfuse integration
│       └── phoenix.py      # Arize Phoenix integration
│
├── db/                     # Database layer
│   ├── postgres/           # PostgreSQL
│   │   ├── models.py       # SQLAlchemy models
│   │   ├── queries.py      # Query functions
│   │   └── migrations/     # Alembic migrations
│   └── qdrant/             # Qdrant vector DB
│       ├── client.py       # Qdrant client wrapper
│       ├── collections.py  # Collection management
│       └── search.py       # Vector search operations
│
├── data/                   # Local data storage
│   ├── raw/                # Raw downloaded datasets
│   ├── processed/          # Normalized dataset cache
│   └── exports/            # User export outputs
│
├── tests/                  # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── system/             # End-to-end tests
│
├── docs/                   # Documentation
├── AGENTS.md               # This file
├── ROADMAP.md              # Development roadmap
└── README.md               # Project overview
```

---

## Tech Stack

- **Python**: 3.13
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Agent Framework**: [Google ADK (Agent Development Kit)](https://github.com/google/adk-python)
- **LLM Models**: Gemini 2.5 Flash (via ADK native integration)
- **Vector Database**: [Qdrant](https://qdrant.tech/)
- **Relational Database**: PostgreSQL with SQLAlchemy
- **RAG Options** (to be compared):
  - NVIDIA NIM RAG
  - GCP Native RAG Tools
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff) + [pre-commit](https://pre-commit.com/)
- **Observability**: Langfuse for agent tracing

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
uv pip list

# Start FastAPI server
uv run uvicorn api.main:app --reload

# Start ADK web UI for agent debugging
uv run adk web

# Run the test suite
uv run pytest

# Run specific test file
uv run pytest tests/unit/test_search.py

# Lint & format with Ruff
uv run ruff check .
uv run ruff format .

# Install pre-commit hooks
uv run pre-commit install

# Run all pre-commit hooks manually
uv run pre-commit run --all-files

# Run database migrations
uv run alembic upgrade head

# Create new migration
uv run alembic revision --autogenerate -m "description"

# Ingest a dataset
uv run python -m core.ingest.runner --source mmlu
```

---

## Key Development Principles

### 1. Strictly follow the latest user instructions

The IDE agent (you) will see a lot of context and may try to "help" too much.

* **Do not** add features, agents, or files that were not explicitly requested
* **Do not** refactor large areas of the codebase unless explicitly asked
* When in doubt, **prefer smaller, targeted changes**

### 2. Always check the codebase and docs first

Before designing or implementing anything:

* Inspect the existing code structure
* Check [README.md](./README.md) and the relevant docs under `docs/`
* Maintain consistency with:
  * naming conventions
  * logging patterns
  * API structure
  * agent hierarchy

### 3. Always present an action plan before working on something new

Before starting to work on something new:
* Present an action plan to the user
* The plan should be a list of steps to be taken, each step should be a single, clear, and atomic action
* **Do not write code diffs** in the action plan

### 4. Ask for clarification when needed

If requirements are ambiguous:

* Ask a focused question:
  *"Should the semantic search use cosine similarity or dot product?"*
* Avoid guessing when design decisions affect:
  * data model
  * public APIs
  * agent behavior
  * search quality

### 5. Test thoroughly

Always run tests after any code change:

* Add/modify/delete **unit tests** for any new function or class
* Add/modify/delete **integration tests** for API endpoints
* Add/modify/delete **system tests** for end-to-end workflows

Keep tests fast (whenever possible) and **always** deterministic.

**DO NOT CHEAT** if the tests fail. If the issue lies in the code, you MUST fix the code and not loosen the tests.

### 6. Use temp TDD to validate assumptions

If you are unsure about whether a function / code section works as expected:

* create temporary unit tests to validate it
* add it to the test suite if the code is kept
* clean it up if the code is not used

### 7. Type safety and style

* Ensure `ruff check` and `ruff format` pass before committing
* Keep functions small and focused
* Use type hints consistently

---

## ADK Best Practices

### 1. Single Responsibility Principle

* Each agent should have a **clear, focused purpose**
* Avoid creating "god agents" that do too many things
* If an agent's instructions become too complex (>100 lines), consider splitting it
* Example:
  * ✅ GOOD: `query_understanding_agent` only parses intent
  * ❌ BAD: `query_understanding_agent` also runs the search

### 2. Explicit State Management

* **Be intentional** about how data flows between agents
* Use agent descriptions to clearly document WHEN the agent should be used
* Use agent instructions to clearly document WHAT the agent should do
* Limit implicit state passing and avoid hidden dependencies

### 3. Appropriate Autonomy

* Assign agents only the **level of autonomy they require**
* For deterministic tasks → use tools/functions, not agents
* For LLM-powered decisions → use LlmAgent
* For orchestration → use SequentialAgent/ParallelAgent
* Example:
  * ✅ GOOD: Use tool for "fetch examples from Qdrant"
  * ❌ BAD: Create an agent for "fetch examples from Qdrant"

### 4. Controlled Delegation

* Use parent-child relationships **deliberately** with clear instructions
* Each sub-agent should have a clear, narrow responsibility
* Document the orchestration flow clearly

### 5. Start with a Small Agent Hierarchy, Then Evolve

* Begin with simple, flat structures (1-2 levels)
* Add layers as new features require it
* Avoid prematurely splitting into many specialized agents

### 6. Separate Tooling from Orchestration

* Keep **tools** and **data management** in dedicated modules
* Agents should orchestrate, not implement business logic directly
* This simplifies testing:
  * Unit-test tools/managers without agents
  * Integration-test agents with mocked tools
  * System-test full workflow end-to-end

### 7. Prompts as Code

* Store prompts as Python constants in `agents/prompts/` directory
* Each agent should have:
  * `{AGENT_NAME}_DESCRIPTION`: Brief purpose statement (when to use it)
  * `{AGENT_NAME}_INSTRUCTIONS`: Detailed behavior specification (what it should do, and how)
* Use XML-like tags in instructions for structure when needed
* Keep prompts explicit, unambiguous, and well-formatted

---

## FastAPI Best Practices

### 1. Route Organization

* Group related endpoints in dedicated route files
* Use APIRouter for route grouping
* Keep route handlers thin - delegate to service layer

```python
# api/routes/search.py
from fastapi import APIRouter, Depends
from api.models.search import SearchRequest, SearchResponse
from core.search.hybrid import hybrid_search

router = APIRouter(prefix="/search", tags=["search"])

@router.post("/hybrid", response_model=SearchResponse)
async def search_hybrid(request: SearchRequest):
    """Hybrid search combining keyword and semantic."""
    return await hybrid_search(request)
```

### 2. Pydantic Models

* Use Pydantic models for all request/response schemas
* Keep models in `api/models/`
* Use clear, descriptive field names
* Add validation where appropriate

```python
# api/models/search.py
from pydantic import BaseModel, Field

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    dataset_ids: list[str] | None = None
    limit: int = Field(default=20, ge=1, le=100)
    semantic_weight: float = Field(default=0.5, ge=0, le=1)
```

### 3. Dependency Injection

* Use FastAPI's dependency injection for shared resources
* Keep dependencies in `api/deps.py`

```python
# api/deps.py
from functools import lru_cache
from db.qdrant.client import QdrantClient

@lru_cache
def get_qdrant_client() -> QdrantClient:
    return QdrantClient()
```

### 4. Error Handling

* Use HTTPException for API errors
* Return meaningful error messages
* Log errors appropriately

```python
from fastapi import HTTPException

if not dataset:
    raise HTTPException(status_code=404, detail=f"Dataset {dataset_id} not found")
```

---

## Qdrant Best Practices

### 1. Collection Design

* One collection per major entity type (examples, datasets)
* Use payload filtering for metadata queries
* Store embeddings with minimal metadata in Qdrant
* Store full data in PostgreSQL, reference by ID

### 2. Embedding Strategy

* Use consistent embedding model across all examples
* Store embedding model version in metadata
* Plan for re-embedding when model changes

### 3. Search Optimization

* Use appropriate distance metric (cosine for normalized embeddings)
* Set proper HNSW parameters based on dataset size
* Use payload indexes for frequently filtered fields

```python
# db/qdrant/collections.py
from qdrant_client.models import Distance, VectorParams, PayloadSchemaType

EXAMPLES_COLLECTION = "eval_examples"
VECTOR_SIZE = 768  # Depends on embedding model

def create_examples_collection(client):
    client.create_collection(
        collection_name=EXAMPLES_COLLECTION,
        vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
    )
    # Create payload indexes for filtering
    client.create_payload_index(
        collection_name=EXAMPLES_COLLECTION,
        field_name="dataset_id",
        field_schema=PayloadSchemaType.KEYWORD,
    )
```

---

## Code Style & Organization

* **Naming**:
  * `snake_case` for functions, variables, and tools
  * `PascalCase` for classes and Pydantic models
  * `SCREAMING_SNAKE_CASE` for constants (including prompts)
  * Agent names: `{purpose}_agent` (e.g., `query_understanding_agent`)

* **Files**:
  * One main concept per file
  * API routes: `api/routes/{resource}.py`
  * Pydantic models: `api/models/{resource}.py`
  * Agent definitions: `agents/agent.py`
  * Prompts: `agents/prompts/{agent_name}.py`
  * Tools: `agents/tools/{tool_category}.py`
  * Keep functions under ~100–150 lines if possible

* **Imports**:
  * Use absolute imports for external packages
  * Use relative imports within packages
  * Group imports: stdlib → third-party → local
  * Sort alphabetically within groups

* **Comments**:
  * Explain *why* something is done, not *what* it does
  * Exception: Explain *what* when using complex third-party APIs
  * Add docstrings for all public functions, classes, and endpoints

* **Type Hints**:
  * Use type hints for all function signatures
  * Use Pydantic models for structured data
  * Use `TypedDict` for simple dictionaries with known keys

---

## Environment & Workflow

### Environment Variables

```bash
# Required
GOOGLE_API_KEY=your-google-api-key
DATABASE_URL=postgresql://user:pass@localhost:5432/cherry_evals
QDRANT_URL=http://localhost:6333

# Optional - Langfuse for tracing
LANGFUSE_HOST=http://localhost:3000
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key

# Optional - Export destinations
LANGFUSE_EXPORT_KEY=your-export-key
PHOENIX_API_KEY=your-phoenix-key
```

### Development Workflow

1. **Setup**: `uv sync` to ensure dependencies are up to date
2. **Branch**: Create a feature branch for your work
3. **Implement**: Make small, focused changes
4. **Test**: Run tests locally (`uv run pytest`)
5. **Lint**: Run `uv run ruff check . && uv run ruff format .`
6. **Manual test**: Start server and test endpoints
7. **Document**: Update relevant docs and docstrings
8. **Commit**: Follow [Conventional Commits](https://www.conventionalcommits.org/) format
    * **Format:**
      ```
      <type>(<scope>): <description>
      [optional body]
      [optional footer]
      ```
    * **Common types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`, `build`, `ci`, `revert`
    * **Examples:**
      ```
      feat(search): Add hybrid search endpoint
      fix(ingest): Handle missing metadata in MMLU
      refactor(export): Unify export adapter interface
      ```
9. **Pre-commit**: Hooks will run automatically on commit
10. **Review**: Create PR and request review

---

## Common Pitfalls

### 1. Over-Engineering Agent Hierarchies

**Problem**: Creating too many specialized agents too early.

**Solution**: Start simple. Only add agents when complexity justifies it.

### 2. Mixing Search Concerns

**Problem**: Putting search logic directly in API routes.

**Solution**: Keep search logic in `core/search/`, routes just call it.

### 3. N+1 Queries

**Problem**: Fetching related data one-by-one in loops.

**Solution**: Use batch queries and eager loading where appropriate.

### 4. Ignoring Error Handling

**Problem**: Agents or tools fail silently.

**Solution**: Implement proper error handling at all levels.

### 5. Skipping Logging

**Problem**: Debugging is impossible without logs.

**Solution**: Log at key decision points. Log almost every step at DEBUG level.

### 6. Embedding Model Lock-in

**Problem**: Changing embedding models requires re-indexing everything.

**Solution**: Version embeddings, plan for migration from the start.

### 7. Missing Pagination

**Problem**: APIs return unbounded result sets.

**Solution**: Always paginate list endpoints with sensible defaults.

---

## Testing Strategy

### Unit Tests

Test individual functions in isolation:

```python
def test_keyword_search_filters_by_dataset():
    """Test keyword search with dataset filter"""
    results = keyword_search(
        query="math problem",
        dataset_ids=["gsm8k"],
        limit=10,
    )
    assert all(r.dataset_id == "gsm8k" for r in results)
```

### Integration Tests

Test API endpoints with database:

```python
@pytest.mark.asyncio
async def test_search_endpoint(client, populated_db):
    """Test hybrid search endpoint"""
    response = await client.post("/search/hybrid", json={
        "query": "multiple choice question about history",
        "limit": 5,
    })
    assert response.status_code == 200
    data = response.json()
    assert len(data["results"]) <= 5
```

### System Tests

Test complete workflows:

```python
@pytest.mark.asyncio
async def test_full_collection_workflow(client):
    """Test create collection → search → add examples → export"""
    # Create collection
    collection = await create_collection(client, "My Custom Eval")

    # Search for examples
    results = await search(client, "reasoning problems")

    # Add to collection
    await add_examples(client, collection.id, [r.id for r in results[:10]])

    # Export
    export = await export_collection(client, collection.id, format="openai")
    assert export["status"] == "completed"
```

---

## Debugging Tips

### 1. Enable Verbose Logging

```bash
export LOG_LEVEL=DEBUG
uv run uvicorn api.main:app --reload
```

### 2. Use ADK Web UI for Agent Tracing

```bash
uv run adk web
```

### 3. Inspect Qdrant Directly

```python
from qdrant_client import QdrantClient
client = QdrantClient("localhost", port=6333)
print(client.get_collection("eval_examples"))
```

### 4. Test Search Quality

```python
# Quick script to test search quality
results = hybrid_search("math word problems", limit=10)
for i, r in enumerate(results):
    print(f"{i+1}. [{r.score:.3f}] {r.question[:100]}...")
```

---

## Additional Resources

* **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
* **Qdrant Documentation**: [qdrant.tech/documentation](https://qdrant.tech/documentation/)
* **ADK Documentation**: [github.com/google/adk-python](https://github.com/google/adk-python)
* **Gemini API Docs**: [ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)
* **cherry-evals Roadmap**: [ROADMAP.md](./ROADMAP.md)

---

Remember: **cherry-evals helps researchers build better evaluations.**

Prioritize search quality, data accuracy, and format flexibility.

**Make it easy to find the perfect examples for any evaluation task.**

