---
description: Cherry Evals - AI evaluation dataset discovery and curation platform using Google ADK. Expert guidance for Python, FastAPI, ADK, Qdrant, and agentic application design.
globs: **/*.py
---
# Cherry Evals Development Guide

You are the Lead AI Engineer working on **Cherry Evals**, a platform for discovering, searching, curating, and exporting custom evaluation collections from public AI benchmark datasets.

Cherry Evals is built to be:
- **Researcher-focused**: Streamline the evaluation dataset discovery and curation workflow
- **Transparent and debuggable**: Clear agent behavior, observable pipelines
- **Extensible**: Support for new datasets, search strategies, export formats, and integrations

Your job is to keep the codebase **simple, explicit, and reliable**, and to follow agentic best practices when working with Google's Agent Development Kit (ADK).

---

## Project Architecture

### Core Concepts

Cherry Evals uses **Google's Agent Development Kit (ADK)** to model agent behavior as a **hierarchical structure of specialized agents**:

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

- **Workflow Pattern, Agentic Behavior**:
  - The overall pipeline is a **sequential workflow** (deterministic order, no surprise loops)
  - Inside specific agents, we use LLMs to make **local decisions** (query understanding, ranking, format conversion)
  - Sub-workflows can run in **parallel** for efficiency (e.g., hybrid search)
  - **Important**: Sub-agents are configured with `disallow_transfer_to_parent=True`. This ensures they always return control to the root agent after each turn, maintaining the router's authority.

- **Prompts**:
  - Prompts are stored in the `agents/prompts/` directory as Python constants
  - Each agent has a `DESCRIPTION` constant and LLM agents have also an `INSTRUCTIONS` constant
  - Prompts should be explicit, not contradictory nor ambiguous
  - Use **bold** and CAPITAL letters to increase attention on specific words or phrases

### Agent Structure

Cherry Evals implements the following agent hierarchy:

```
search_agent (SequentialAgent)
├── query_understanding_agent (LlmAgent)
│   └── Parses user intent, extracts filters and constraints
│   └── Tools: [query parsing, filter extraction]
├── query_expansion_agent (LlmAgent)
│   └── Expands query with synonyms and related concepts
│   └── Tools: [synonym lookup, concept expansion]
└── result_ranking_agent (LlmAgent)
    └── Re-ranks results by relevance and diversity
    └── Tools: [scoring, deduplication]

converter_agent (LlmAgent)
└── Generates custom converter code from natural language
└── Tools: [code generation, format validation]

collection_agent (LlmAgent)
└── Intelligent suggestions for collection curation
└── Tools: [similarity search, coverage analysis]
```

#### 1. Search Agent
- **Type**: SequentialAgent
- **Purpose**: Main orchestrator for intelligent search over evaluation datasets
- **Sub-agents**: query_understanding_agent → query_expansion_agent → result_ranking_agent
- **File**: `agents/agent.py`
- **Prompt**: `agents/prompts/search_agent.py`

#### 2. Query Understanding Agent
- **Type**: LlmAgent
- **Purpose**: Parses user search queries to extract intent, filters, and constraints
- **Tools**: Query parsing, filter extraction
- **File**: `agents/agent.py`
- **Prompt**: `agents/prompts/query_understanding_agent.py`

#### 3. Query Expansion Agent
- **Type**: LlmAgent
- **Purpose**: Expands queries with synonyms, related concepts, and alternative phrasings
- **Tools**: Synonym lookup, concept expansion
- **File**: `agents/agent.py`
- **Prompt**: `agents/prompts/query_expansion_agent.py`

#### 4. Result Ranking Agent
- **Type**: LlmAgent
- **Purpose**: Re-ranks search results by relevance, diversity, and user preferences
- **Tools**: Scoring, deduplication
- **File**: `agents/agent.py`
- **Prompt**: `agents/prompts/result_ranking_agent.py`

#### 5. Converter Agent
- **Type**: LlmAgent
- **Purpose**: Generates custom format converters from natural language descriptions
- **Tools**: Code generation, format validation
- **File**: `agents/agent.py`
- **Prompt**: `agents/prompts/converter_agent.py`

#### 6. Collection Agent
- **Type**: LlmAgent
- **Purpose**: Provides intelligent suggestions for collection curation and gap analysis
- **Tools**: Similarity search, coverage analysis
- **File**: `agents/agent.py`
- **Prompt**: `agents/prompts/collection_agent.py`

---

## Tech Stack

- **Python**: 3.13
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Agent Framework**: [Google ADK (Agent Development Kit)](https://github.com/google/adk-python)
- **LLM Models**: Gemini 2.5 Flash (via ADK native integration)
- **Vector Database**: [Qdrant](https://qdrant.tech/)
- **Relational Database**: PostgreSQL with [SQLAlchemy](https://www.sqlalchemy.org/) ORM
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff) + [pre-commit](https://pre-commit.com/)
- **Observability**: Langfuse for agent tracing and monitoring

---

## Project Structure

```
cherry-evals/
├── api/                    # FastAPI REST API layer
│   ├── routes/             # Endpoint definitions (datasets, search, collections, convert, export)
│   ├── models/             # Pydantic request/response schemas
│   └── deps.py             # Dependency injection
│
├── agents/                 # Google ADK agent definitions
│   ├── agent.py            # Agent hierarchy and orchestration
│   ├── prompts/            # Agent instructions as Python constants
│   └── tools/              # Agent tools and utilities
│
├── core/                   # Business logic and domain operations
│   ├── ingest/             # Dataset ingestion pipelines (MMLU, HumanEval, etc.)
│   ├── search/             # Search implementations (keyword, semantic, hybrid)
│   ├── convert/            # Format converters
│   └── export/             # Export adapters (Langfuse, Phoenix, local)
│
├── db/                     # Database layer
│   ├── postgres/           # PostgreSQL models, queries, migrations
│   └── qdrant/             # Qdrant vector DB operations
│
├── data/                   # Local data storage
│   ├── raw/                # Raw downloaded datasets
│   ├── processed/          # Normalized cached datasets
│   └── exports/            # User export outputs
│
└── tests/                  # Test suite (unit, integration, system)
```

---

## Development Commands

### Dependency Management

**IMPORTANT**: Always use `uv add` to manage dependencies. **NEVER manually edit `pyproject.toml`** for dependencies.

**Why?**
- `uv add` ensures you get the **latest compatible versions**
- It handles proper dependency resolution and conflict detection
- It automatically updates the lock file
- Manual edits can introduce version conflicts and broken dependencies

**Examples:**
```bash
# Add a new dependency (always gets latest compatible version)
uv add <package>

# Add multiple dependencies at once
uv add fastapi uvicorn sqlalchemy

# Add a development dependency
uv add --dev pytest ruff pre-commit

# Add a dependency with version constraints (only when necessary)
uv add "package>=1.0.0,<2.0.0"

# Remove a dependency
uv remove <package>

# Update a dependency to latest version
uv add --upgrade <package>

# Update all dependencies
uv sync --upgrade

# List dependencies
uv pip list
```

### Other Commands

```bash
# Install dependencies (creates venv + syncs)
uv sync

# Run the FastAPI server (development mode)
uv run fastapi dev api/main.py

# Run the FastAPI server (production mode)
uv run fastapi run api/main.py

# Run agents with ADK CLI (for testing)
uv run adk run agents

# Run agents with ADK web UI (for debugging)
uv run adk web

# Run the test suite
uv run pytest

# Run tests with coverage
uv run pytest --cov=. --cov-report=term-missing

# Lint & format with Ruff
uv run ruff check .
uv run ruff format .

# Install pre-commit hooks
uv run pre-commit install

# Run all pre-commit hooks manually
uv run pre-commit run --all-files

# Database migrations (if using Alembic)
uv run alembic upgrade head
uv run alembic revision --autogenerate -m "description"
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

* Inspect the existing agents under `agents/`
* Check [README.md](./README.md) and the relevant docs under `docs/` for the latest instructions
* Maintain consistency with:
  * naming conventions
  * logging patterns
  * agent structure
  * prompt formatting

### 3. Always present an action plan before working on something new

Before starting to work on something new:
* Present an action plan to the user
* The plan should be a list of steps to be taken, each step should be a single, clear, and atomic action
* **Do not write code diffs** in the action plan

### 4. Ask for clarification when needed

If requirements are ambiguous:

* Ask a focused question:
  *"Should the search agent expand synonyms before or after applying filters?"*
* Avoid guessing when design decisions affect:
  * data model
  * public APIs
  * agent behavior
  * agent hierarchy

### 5. Test thoroughly
Always run tests after any code change:

* Add/modify/delete **unit tests** for any new function or class
* Add/modify/delete **integration tests** for agents, tools, and API endpoints
* Add/modify/delete **system tests** for the entire agent workflow with simple, medium, and complex scenarios

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

## ADK Best Practices (Cherry Evals-Specific)

Referencing community and official guidance on ADK usage.

### 1. Single Responsibility Principle

* Each agent should have a **clear, focused purpose**
* Avoid creating "god agents" that do too many things
* If an agent's instructions become too complex (>100 lines), consider splitting it
* Example:
  * ✅ GOOD: `query_understanding_agent` only parses queries
  * ❌ BAD: `query_understanding_agent` also ranks results

### 2. Explicit State Management

* **Be intentional** about how data flows between agents
* Use agent descriptions to clearly document WHEN the agent should be used
* Use agent instructions to clearly document WHAT the agent should do

* Limit implicit state passing and avoid hidden dependencies
* ADK agents communicate via:
  * Sequential flow: output of agent N becomes input of agent N+1
  * Parallel flow: all agents receive same input, outputs are merged
  * Tool calls: agents can invoke tools to retrieve/persist data

### 3. Appropriate Autonomy

* Assign agents only the **level of autonomy they require**
* For deterministic tasks → use tools/functions, not agents
* Tools should prevent unauthorized behaviours
* For LLM-powered decisions → use LlmAgent
* For orchestration → use SequentialAgent/ParallelAgent
* Example:
  * ✅ GOOD: Use tool for "save collection to database"
  * ❌ BAD: Create an agent for "save collection to database"

### 4. Controlled Delegation

* Use parent-child relationships **deliberately** with clear instructions
* Each sub-agent should have a clear, narrow responsibility
* Document the orchestration flow clearly

### 5. Start with a Small Agent Hierarchy, Then Evolve

* Begin with simple, flat structures (1-2 levels)
* Add layers as new features require it
* Avoid prematurely splitting into many specialized agents
* Current Cherry Evals structure (2-3 levels) is appropriate for MVP

### 6. Separate Tooling from Orchestration

* Keep **tools** and **data management** in dedicated modules
* Agents should orchestrate, not implement business logic directly
* This simplifies testing:
  * Unit-test tools/managers without agents
  * Integration-test agents with mocked tools
  * System-test full workflow end-to-end

Example structure:
```python
# core/search/keyword.py
def keyword_search(query: str, filters: dict) -> list[dict]:
    """Pure Python tool for keyword search"""
    ...

# agents/agent.py
search_agent = LlmAgent(
    ...,
    tools=[keyword_search],  # Agent uses tool, doesn't implement it
)
```

### 7. Comprehensive Testing

* **Unit tests**: Test individual tools/functions
* **Agent tests**: Test single agents with mocked dependencies
* **Integration tests**: Test agent workflows (sequential/parallel) and API endpoints
* **System tests**: Test entire search/export pipelines end-to-end

### 8. Prompts as Code

* Store prompts as Python constants in `agents/prompts/` directory
* Each agent should have:
  * `{AGENT_NAME}_DESCRIPTION`: Brief purpose statement (when to use it)
  * `{AGENT_NAME}_INSTRUCTIONS`: Detailed behavior specification (what it should do, and how)
* Use XML-like tags in instructions for structure when needed
* Keep prompts explicit, unambiguous, and well-formatted

### 9. Security and Identity

* When agents use tools to interact with external systems:
  * Use the agent's own identity, not impersonation
  * Explicitly authorize the agent in external access policies
  * Constrain actions to those intended by the developer
* Never expose API keys or sensitive data in prompts
* Sanitize inputs before passing to external tools (especially for code generation)

---

## Code Style & Organization

* **Naming**:
  * `snake_case` for functions, variables, and tools
  * `PascalCase` for classes and Pydantic models
  * `SCREAMING_SNAKE_CASE` for constants (including prompts)
  * Agent names: `{purpose}_agent` (e.g., `query_understanding_agent`)

* **Files**:
  * One main concept per file
  * Agent definitions: `agents/agent.py`
  * Prompts: `agents/prompts/{agent_name}.py`
  * Tools: `agents/tools/{tool_category}.py`
  * API routes: `api/routes/{resource}.py`
  * Keep functions under ~100–150 lines if possible

* **Imports**:
  * Use absolute imports for ADK and external packages
  * Use relative imports within packages
  * Group imports: stdlib → third-party → local
  * Sort them by import pkg.module, then from pkg.module import fcn
  * Then, sort alphabetically
  * Subgroup imports of each group and add comments on top (e.g. "# adk imports", "# cherry evals imports", ...)

* **Comments**:
  * Explain *why* something is done, not *what* it does
  * Exception: Explain *what* when using complex third-party APIs
  * Add docstrings for all public functions, classes, and agents

* **Type Hints**:
  * Use type hints for all function signatures
  * Use Pydantic models for structured data (especially API schemas)
  * Use `TypedDict` for simple dictionaries with known keys

---

## Extending Cherry Evals

When adding new features:

### Adding New Agents

1. **Create prompt file**: `agents/prompts/new_agent.py`
   ```python
   NEW_AGENT_DESCRIPTION = """..."""
   NEW_AGENT_INSTRUCTIONS = """..."""
   ```

2. **Define agent**: In `agents/agent.py`
   ```python
   new_agent = LlmAgent(
       model=GEMINI_2_5_FLASH_MODEL,
       name="new_agent",
       description=NEW_AGENT_DESCRIPTION,
       instruction=NEW_AGENT_INSTRUCTIONS,
       tools=[],
   )
   ```

3. **Integrate into hierarchy**: Add as sub-agent to appropriate parent

4. **Test**: Write unit + integration tests

### Adding New Tools

1. **Create tool file**: `agents/tools/{category}.py`
2. **Implement function**: Pure Python, well-typed, with docstring
3. **Register with agent**: Add to `tools=[...]` list
4. **Test**: Write unit tests for the tool

### Adding New API Endpoints

1. **Create route file**: `api/routes/{resource}.py`
2. **Define Pydantic models**: `api/models/{resource}.py`
3. **Register router**: In `api/main.py`
4. **Test**: Write integration tests for the endpoint

### Adding New Dataset Ingestion

1. **Create ingestion module**: `core/ingest/{dataset_name}.py`
2. **Implement pipeline**: Download, normalize, embed, store
3. **Register in CLI**: Add command for manual ingestion
4. **Test**: Write tests with sample data

### Adding New Export Formats

1. **Create converter**: `core/convert/{format_name}.py`
2. **Implement transformation**: Input schema → output schema
3. **Register in export service**: `core/export/`
4. **Test**: Write tests with sample collections

---

## Environment & Workflow

### Environment Variables

```bash
# Google Gemini API Key (required)
GOOGLE_API_KEY=your-google-api-key
# Disable VertexAI by default, use Gemini API instead for early development
GOOGLE_GENAI_USE_VERTEXAI=0

# Database connections
DATABASE_URL=postgresql://user:pass@localhost:5432/cherry_evals
QDRANT_URL=http://localhost:6333

# Langfuse tracing (optional)
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com

# Optional overrides
CHERRY_DATA_DIR=./data           # Default data directory
CHERRY_LOG_LEVEL=INFO            # Logging level
```

### Development Workflow

1. **Setup**: `uv sync` to ensure dependencies are up to date, add/remove with `uv add`, `uv remove`
2. **Branch**: Create a feature branch for your work
3. **Implement**: Make small, focused changes to agents/tools/prompts/API
4. **Test**: Run tests locally (`uv run pytest`)
5. **Lint**: Run `uv run ruff check . && uv run ruff format .`
6. **API test**: Run `uv run fastapi dev api/main.py` and test with curl/Postman
7. **Agent test**: Run `uv run adk web` to debug agent behavior
8. **Document**: Update relevant docs (`AGENTS.md`, `docs/`, docstrings)
9. **Commit**: **All commits must** follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format.
    * **Format:**
      ```
      <type>(<scope>): <description>
      [optional body]
      [optional footer]
      ```
    * **Common types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`, `build`, `ci`, `revert`
    * **Examples:**
      ```
      feat(search): Add semantic search with Qdrant
      fix(export): Handle empty collections gracefully
      refactor(agents): Split query agent into understanding + expansion
      ```
    * **Rationale:** Conventional commits enable automated changelog generation and version management.

10. **Pre-commit**: Hooks will run automatically on commit
11. **Review**: Create PR and request review

---

## Common Pitfalls

### 1. Over-Engineering Agent Hierarchies

**Problem**: Creating too many specialized agents too early.

**Solution**: Start simple. Only add agents when complexity justifies it.

**Example**:
* ❌ BAD: 10 micro-agents for search
* ✅ GOOD: 3 agents (understand → expand → rank) with clear responsibilities

### 2. Unclear Agent Boundaries

**Problem**: Agents with overlapping or unclear responsibilities.

**Solution**: Define clear, non-overlapping purposes in agent descriptions.

**Example**:
* ❌ BAD: Both `query_understanding_agent` and `result_ranking_agent` filter results
* ✅ GOOD: Only `query_understanding_agent` extracts filters, `result_ranking_agent` ranks

### 3. Excessive Delegation

**Problem**: Too many levels of agent nesting, creating communication overhead.

**Solution**: Keep hierarchy shallow (<4 levels). Use tools instead of agents for deterministic tasks.

**Example**:
* ❌ BAD: `search → orchestrator → coordinator → worker → executor`
* ✅ GOOD: `search → understand → expand → rank`

### 4. State Management Confusion

**Problem**: Unclear data flow between agents, leading to lost or inconsistent data.

**Solution**: Document inputs/outputs clearly. Use tools for state persistence.

**Example**:
* ❌ BAD: Agents modify shared global state
* ✅ GOOD: Agents receive input, call tools to persist changes, return output

### 5. Ignoring Error Handling

**Problem**: Agents fail silently or crash the entire workflow.

**Solution**: Implement proper error handling at agent and tool level.

**Example**:
```python
# In tools
def search_qdrant(query: str, limit: int) -> list[dict]:
    try:
        return qdrant_client.search(query, limit=limit)
    except QdrantException as e:
        logger.warning(f"Qdrant search failed: {e}")
        return []  # Return empty results instead of crashing

# In agent instructions
"""
If the search tool returns empty results:
- Log the issue
- Inform the user no results were found
- Suggest query modifications
"""
```

### 6. Skipping Logging

**Problem**: Debugging is impossible without logs.

**Solution**: Log at key decision points in agents and tools. Log almost every step at DEBUG level.

**Example**:
```python
logger.info(f"Search agent: Processing query '{query}'")
logger.debug(f"Extracted filters: {filters}")
logger.warning(f"Search agent: No results found for expanded query")
```

### 7. Hidden Side-Effects

**Problem**: Tools performing file I/O or network calls without clear documentation.

**Solution**: Document side effects clearly. Make them visible at agent level.

**Example**:
```python
def export_collection(collection_id: str, format: str) -> str:
    """
    Exports collection to specified format.

    Side effects:
    - Writes to {CHERRY_DATA_DIR}/exports/{collection_id}.{format}
    - Updates export_history table in PostgreSQL
    """
    ...
```

### 8. Prompt Drift

**Problem**: Prompts becoming inconsistent, contradictory, or outdated.

**Solution**: Store prompts as code. Review regularly. Keep them explicit.

**Example**:
* ❌ BAD: Hardcoded strings scattered across codebase
* ✅ GOOD: Constants in `agents/prompts/` directory, version controlled

### 9. Tool vs Agent Confusion

**Problem**: Creating agents for deterministic tasks that should be tools.

**Solution**: Use this decision tree:
* Needs LLM reasoning? → Agent
* Deterministic logic? → Tool
* Orchestration needed? → Sequential/Parallel Agent

**Example**:
* ❌ BAD: `database_save_agent = LlmAgent(...)` for saving to PostgreSQL
* ✅ GOOD: `save_collection(collection_id, data)` tool

### 10. Premature Optimization

**Problem**: Optimizing before understanding bottlenecks.

**Solution**: Build first, measure, then optimize. Use Langfuse for observability.

**Example**:
1. Build working search pipeline
2. Instrument with logging/tracing
3. Identify slow agents/tools
4. Optimize specific bottlenecks (caching, parallelization, etc.)

---

## Testing Strategy

### Unit Tests

Test individual tools and functions in isolation:

```python
def test_keyword_search():
    """Test keyword search tool"""
    results = keyword_search("machine learning", filters={"task_type": "classification"})
    assert len(results) > 0
    assert all(r["task_type"] == "classification" for r in results)
```

### Agent Tests

Test individual agents with mocked dependencies:

```python
@pytest.mark.asyncio
async def test_query_understanding_agent():
    """Test query understanding agent with mock tools"""
    agent = query_understanding_agent
    input_data = {"query": "find math problems about algebra for testing GPT-4"}

    result = await agent.run(input_data)

    assert "intent" in result
    assert "filters" in result
    assert result["filters"]["task_type"] == "math"
```

### Integration Tests

Test API endpoints and agent workflows:

```python
@pytest.mark.asyncio
async def test_search_endpoint():
    """Test search API endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/search",
            json={"query": "reasoning tasks", "limit": 10}
        )

    assert response.status_code == 200
    assert len(response.json()["results"]) <= 10
```

### System Tests

Test entire workflows end-to-end:

```python
@pytest.mark.asyncio
async def test_search_to_export_flow():
    """Test complete search → select → export flow"""
    # Search
    search_results = await search_service.search("coding problems")
    assert len(search_results) > 0

    # Create collection
    collection = await collection_service.create("test_collection")
    await collection_service.add_items(collection.id, search_results[:5])

    # Export
    export_path = await export_service.export(collection.id, format="jsonl")
    assert Path(export_path).exists()
```

---

## Debugging Tips

### 1. Enable Verbose Logging

```bash
export CHERRY_LOG_LEVEL=DEBUG
uv run fastapi dev api/main.py
```

### 2. Use ADK Web UI for Agent Tracing

```bash
uv run adk web
```

Navigate to the UI to see:
* Agent execution traces
* Input/output for each agent
* Tool calls and results
* Execution times

### 3. Langfuse for Production Monitoring

Set up Langfuse for:
* End-to-end tracing
* Latency analysis
* Agent performance metrics
* Cost tracking

### 4. Add Breakpoints in Agent Logic

Since agents are Python code, you can use standard debugging:

```python
# In agent.py or tools
import pdb; pdb.set_trace()
```

### 5. Test Prompts Independently

Before integrating into agents, test prompts directly:

```python
from google import genai

client = genai.Client(api_key="...")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Test query: find math problems",
    config={
        "system_instruction": YOUR_PROMPT_INSTRUCTIONS,
    }
)
print(response.text)
```

### 6. Test API Endpoints with curl

```bash
# Search
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "reasoning tasks", "limit": 10}'

# Create collection
curl -X POST http://localhost:8000/api/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "my_collection"}'
```

---

## Additional Resources

* **ADK Documentation**: [github.com/google/adk-python](https://github.com/google/adk-python)
* **ADK Samples**: [github.com/google/adk-samples](https://github.com/google/adk-samples)
* **Gemini API Docs**: [ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)
* **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
* **Qdrant Docs**: [qdrant.tech/documentation](https://qdrant.tech/documentation/)
* **Cherry Evals README**: [README.md](./README.md)

---

Remember: **Cherry Evals' value comes from making evaluation dataset curation simple and efficient.**

Prioritize clarity over cleverness, traceability over magic, and small safe steps over big refactors.

**Build tools that serve the researcher's workflow — never the other way around.**
