---
description: Cherry-evals - Evaluation dataset management using Google ADK. Expert guidance for Python, ADK, uv, and agentic application design.
globs: **/*.py
---
# Cherry-evals Development Guide

You are the Lead AI Engineer working on **Cherry-evals**, a tool for collecting, searching, and managing AI evaluation datasets.

Cherry-evals is built to be:
- **Transparent and debuggable**: All operations are traceable and observable
- **Extensible**: Easy to add new data sources, converters, and export targets
- **Agent-powered**: Uses Google ADK for intelligent search and LLM integration

Your job is to keep the codebase **simple, explicit, and reliable**, and to follow agentic best practices when working with Google's Agent Development Kit (ADK).

---

## Project Architecture

### Core Concepts

Cherry-evals uses **Google's Agent Development Kit (ADK)** to model agent behavior as a **hierarchical structure of specialized agents**:

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
  - Inside specific agents, we use LLMs to make **local decisions** (query understanding, search strategy selection, format conversion)
  - Sub-workflows can run in **parallel** for efficiency (e.g., multiple search strategies)

- **Prompts**:
  - Prompts are stored in the `cherry_evals/prompts/` directory as Python constants
  - Each agent has a `DESCRIPTION` constant and LLM agents have also an `INSTRUCTIONS` constant
  - Prompts should be explicit, not contradictory nor ambiguous
  - Use **bold** and CAPITAL letters to increase attention on specific words or phrases

### Agent Structure

Cherry-evals implements the following agent hierarchy (to be expanded):

```
root_search_agent (SequentialAgent)
├── query_understanding_agent (LlmAgent)
│   └── Understands user search intent and expands queries
│   └── Tools: [query analysis, intent classification]
├── search_orchestration_agent (ParallelAgent)
│   ├── keyword_search_agent (LlmAgent)
│   │   └── Performs keyword-based search
│   │   └── Tools: [keyword_search, dataset_filtering]
│   ├── semantic_search_agent (LlmAgent)
│   │   └── Performs semantic search via RAG backend
│   │   └── Tools: [vector_search, embedding_generation]
│   └── topic_search_agent (LlmAgent)
│       └── Performs topic-based clustering and filtering
│       └── Tools: [topic_clustering, topic_filtering]
└── result_merging_agent (LlmAgent)
    └── Merges and ranks results from multiple search strategies
    └── Tools: [result_ranking, deduplication]
```

#### 1. Root Search Agent
- **Type**: SequentialAgent
- **Purpose**: Main orchestrator for search operations
- **Sub-agents**: query_understanding_agent → search_orchestration_agent → result_merging_agent
- **File**: `cherry_evals/agents/search.py`
- **Prompt**: `cherry_evals/prompts/search_agent.py`

#### 2. Query Understanding Agent
- **Type**: LlmAgent
- **Purpose**: Understands user search intent and expands queries for better results
- **Tools**: Query analysis, intent classification
- **File**: `cherry_evals/agents/search.py`
- **Prompt**: `cherry_evals/prompts/query_understanding_agent.py`

#### 3. Search Orchestration Agent
- **Type**: ParallelAgent
- **Purpose**: Executes multiple search strategies in parallel
- **Sub-agents**: keyword_search_agent, semantic_search_agent, topic_search_agent
- **File**: `cherry_evals/agents/search.py`
- **Prompt**: `cherry_evals/prompts/search_orchestration_agent.py`

#### 4. Result Merging Agent
- **Type**: LlmAgent
- **Purpose**: Merges results from multiple search strategies and ranks them
- **Tools**: Result ranking, deduplication
- **File**: `cherry_evals/agents/search.py`
- **Prompt**: `cherry_evals/prompts/result_merging_agent.py`

#### 5. Format Conversion Agent (Future)
- **Type**: LlmAgent
- **Purpose**: Converts evaluation data between formats using predefined or custom converters
- **Tools**: Format converters, validation
- **File**: `cherry_evals/agents/conversion.py`
- **Prompt**: `cherry_evals/prompts/conversion_agent.py`

---

## Tech Stack

- **Python**: 3.13
- **Agent Framework**: [Google ADK (Agent Development Kit)](https://github.com/google/adk-python)
- **LLM Models**: Gemini 2.5 Flash (via ADK native integration)
- **Backend**: FastAPI
- **RAG Solutions** (to be compared):
  - Qdrant (vector database)
  - Nim RAG
  - GCP RAG engine
  - Redis
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff) + [pre-commit](https://pre-commit.com/)
- **Data Storage**: JSON files for collections, metadata, and configuration
- **Observability**: Local Langfuse server for tracing, latency monitoring, agent steps

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

# Run ADK agents directly (for testing)
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

## Key Development Principles

### 1. Strictly follow the latest user instructions

The IDE agent (you) will see a lot of context and may try to "help" too much.

* **Do not** add features, agents, or files that were not explicitly requested
* **Do not** refactor large areas of the codebase unless explicitly asked
* When in doubt, **prefer smaller, targeted changes**

### 2. Always check the codebase and docs first

Before designing or implementing anything:

* Inspect the existing agents under `cherry_evals/agents/`
* Check [README.md](./README.md) and the relevant docs under `docs/` for the latest instructions:
  - [docs/architecture.md](./docs/architecture.md) (when created)
  - [docs/features/](./docs/features/) (when created)
  - [docs/files.md](./docs/files.md) (when created)
  - [ROADMAP.md](./ROADMAP.md)
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
  *"Should the semantic search use Qdrant or GCP native RAG for this implementation?"*
* Avoid guessing when design decisions affect:
  * data model
  * public APIs
  * agent behavior
  * agent hierarchy

### 5. Test thoroughly
Always run tests after any code change:

* Add/modify/delete **unit tests** for any new function or class
* Add/modify/delete **integration tests** for agents and tools
* Add/modify/delete **system tests** for the entire agent workflow with simple, medium, and complex scenarios

Keep tests fast (whenever possible) and **always** deterministic.
Ensure to test search results AND conversion outputs in system tests.

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

## ADK Best Practices (Cherry-evals-Specific)

Referencing community and official guidance on ADK usage.

### 1. Single Responsibility Principle

* Each agent should have a **clear, focused purpose**
* Avoid creating "god agents" that do too many things
* If an agent's instructions become too complex (>100 lines), consider splitting it
* Example:
  * ✅ GOOD: `keyword_search_agent` only performs keyword search
  * ❌ BAD: `search_agent` also handles format conversion

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
  * ✅ GOOD: Use tool for "save collection to file"
  * ❌ BAD: Create an agent for "save collection to file"
  * ✅ GOOD: Tool has hard coded subdir `data/collections/{collection_id}` where collection_id comes from `auth`
  * ❌ BAD: Tool has hard coded subdir `data/collections/{collection_id}` where collection_id comes from `parent_agent`

### 4. Controlled Delegation

* Use parent-child relationships **deliberately** with clear instructions
* Each sub-agent should have a clear, narrow responsibility
* Document the orchestration flow clearly

### 5. Start with a Small Agent Hierarchy, Then Evolve

* Begin with simple, flat structures (1-2 levels)
* Add layers as new features require it
* Avoid prematurely splitting into many specialized agents
* Current cherry-evals structure (3 levels) is appropriate for MVP

### 6. Separate Tooling from Orchestration

* Keep **tools** and **data management** in dedicated modules
* Agents should orchestrate, not implement business logic directly
* This simplifies testing:
  * Unit-test tools/managers without agents
  * Integration-test agents with mocked tools
  * System-test full workflow end-to-end

Example structure:
```python
# tools/search.py
def keyword_search(query: str, dataset_id: str | None = None) -> list[dict]:
    """Pure Python tool for keyword search"""
    ...

# agents/search.py
keyword_search_agent = LlmAgent(
    ...,
    tools=[keyword_search],  # Agent uses tool, doesn't implement it
)
```

### 7. Comprehensive Testing

* **Unit tests**: Test individual tools/functions
* **Agent tests**: Test single agents with mocked dependencies
* **Integration tests**: Test agent workflows (sequential/parallel)
* **System tests**: Test entire root_search_agent end-to-end

### 8. Version track collections and other JSON files

* Ensure edited JSON files (collections, metadata, config, etc.) are version tracked
* Changes should be easy to inspect and revert
* Use git for versioning, not custom solutions

### 9. Prompts as Code

* Store prompts as Python constants in `prompts/` directory
* Each agent should have:
  * `{AGENT_NAME}_DESCRIPTION`: Brief purpose statement (when to use it)
  * `{AGENT_NAME}_INSTRUCTIONS`: Detailed behavior specification (what it should do, and how)
* Use XML-like tags in instructions for structure when needed
* Keep prompts explicit, unambiguous, and well-formatted

### 10. Security and Identity

* When agents use tools to interact with external systems:
  * Use the agent's own identity, not impersonation
  * Explicitly authorize the agent in external access policies
  * Constrain actions to those intended by the developer
* Never expose user credentials or sensitive data in prompts
* Sanitize inputs before passing to external tools

---

## Code Style & Organization

* **Naming**:
  * `snake_case` for functions, variables, and tools
  * `PascalCase` for classes and Pydantic models
  * `SCREAMING_SNAKE_CASE` for constants (including prompts)
  * Agent names: `{purpose}_agent` (e.g., `keyword_search_agent`)

* **Files**:
  * One main concept per file
  * Agent definitions: `cherry_evals/agents/{category}.py`
  * Prompts: `cherry_evals/prompts/{agent_name}.py`
  * Tools: `cherry_evals/tools/{tool_category}.py`
  * Keep functions under ~100–150 lines if possible

* **Imports**:
  * Use absolute imports for ADK and external packages
  * Use relative imports within `cherry_evals/` package
  * Group imports: stdlib → third-party → local
  * Sort them by import pkg.module, then from pkg.module import fcn
  * Then, sort alphabetically
  * Subgroup imports of each group and add comments on top (e.g. "# adk imports", "# cherry-evals prompt imports", ...)

* **Comments**:
  * Explain *why* something is done, not *what* it does
  * Exception: Explain *what* when using complex third-party APIs
  * Add docstrings for all public functions, classes, and agents

* **Type Hints**:
  * Use type hints for all function signatures
  * Use Pydantic models for structured data
  * Use `TypedDict` for simple dictionaries with known keys

---

## Extending Cherry-evals (Post-MVP Patterns)

When adding new features:

### Adding New Agents

1. **Create prompt file**: `cherry_evals/prompts/new_agent.py`
   ```python
   NEW_AGENT_DESCRIPTION = """..."""
   NEW_AGENT_INSTRUCTIONS = """..."""
   ```

2. **Define agent**: In `cherry_evals/agents/{category}.py`
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

1. **Create tool file**: `cherry_evals/tools/{category}.py`
2. **Implement function**: Pure Python, well-typed, with docstring
3. **Register with agent**: Add to `tools=[...]` list
4. **Test**: Write unit tests for the tool

### Multi-Agent Structures

* For complex features, consider:
  * **SequentialAgent**: When tasks must happen in order
  * **ParallelAgent**: When tasks can run concurrently
  * **Loop agents**: When sub agents need to be invoked repeatedly

* Document agent relationships clearly

### RAG Backend Integration

* Support multiple RAG backends (Qdrant, Nim, GCP)
* Use environment variables to select backend
* Abstract backend differences behind a common interface
* Compare performance and features across backends

---

## Environment & Workflow

### Environment Variables

```bash
# Google Gemini API Key (required)
GOOGLE_API_KEY=your-google-api-key
GOOGLE_GENAI_USE_VERTEXAI=0

# RAG backend selection
CHERRY_RAG_BACKEND=qdrant  # Options: qdrant, nim, gcp
QDRANT_URL=http://localhost:6333  # If using Qdrant
# GCP credentials via gcloud CLI or service account JSON

# Optional overrides
CHERRY_DATA_DIR=~/.cherry-evals  # Default data directory
CHERRY_LOG_LEVEL=INFO            # Logging level
```

### Development Workflow

1. **Setup**: `uv sync` to ensure dependencies are up to date, add/remove with `uv add`, `uv remove`
2. **Branch**: Create a feature branch for your work
3. **Implement**: Make small, focused changes to agents/tools/prompts
4. **Test**: Run tests locally (`uv run pytest`)
5. **Lint**: Run `uv run ruff check . && uv run ruff format .`
6. **Vibe test**: Run `uv run uvicorn cherry_evals.api.main:app --reload` or `uv run adk web`
7. **Document**: Update relevant docs (`AGENTS.md`, `docs/`, docstrings)
8. **Commit**: **All commits must** follow [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) format.
    * **Format:**
      ```
      <type>(<scope>): <description>
      [optional body]
      [optional footer]
      ```
    * **Common types:** `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `style`, `build`, `ci`, `revert`
    * **Examples:**
      ```
      feat(agents): Add semantic search agent with Qdrant backend
      fix(search): Prevent duplicate results in merged search
      refactor(tools): Unify RAG backend interface
      ```
    * **Rationale:** Conventional commits enable automated changelog generation and version management.

9. **Pre-commit**: Hooks will run automatically on commit
10. **Review**: Create PR and request review

---

## Common Pitfalls

### 1. Over-Engineering Agent Hierarchies

**Problem**: Creating too many specialized agents too early.

**Solution**: Start simple. Only add agents when complexity justifies it.

**Example**:
* ❌ BAD: 10 micro-agents for search
* ✅ GOOD: 1 `search_orchestration_agent` with clear instructions

### 2. Unclear Agent Boundaries

**Problem**: Agents with overlapping or unclear responsibilities.

**Solution**: Define clear, non-overlapping purposes in agent descriptions.

**Example**:
* ❌ BAD: Both `query_understanding_agent` and `search_orchestration_agent` perform search
* ✅ GOOD: Only `query_understanding_agent` understands queries, `search_orchestration_agent` executes searches

### 3. Excessive Delegation

**Problem**: Too many levels of agent nesting, creating communication overhead.

**Solution**: Keep hierarchy shallow (<4 levels). Use tools instead of agents for deterministic tasks.

**Example**:
* ❌ BAD: `root → orchestrator → coordinator → worker → executor`
* ✅ GOOD: `root → query_understanding → search_orchestration (parallel) → result_merging`

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
def keyword_search(query: str, dataset_id: str | None = None) -> list[dict]:
    try:
        return perform_search(query, dataset_id)
    except SearchError as e:
        logger.warning(f"Search failed: {e}")
        return []  # Return empty results instead of crashing

# In agent instructions
"""
If the search fails:
- Log the error
- Return empty results
- Continue with the workflow
"""
```

### 6. Skipping Logging

**Problem**: Debugging is impossible without logs.

**Solution**: Log at key decision points in agents and tools. Log almost every step at DEBUG level.

**Example**:
```python
logger.info(f"Query understanding agent: Processed query '{query}'")
logger.debug(f"Expanded query: {expanded_query}")
logger.warning(f"Search agent: No results found for query")
```

### 7. Hidden Side-Effects

**Problem**: Tools performing file I/O or network calls without clear documentation.

**Solution**: Document side effects clearly. Make them visible at agent level.

**Example**:
```python
def save_collection(collection_id: str, examples: list[dict]) -> None:
    """
    Saves collection to disk.

    Side effects:
    - Writes to {CHERRY_DATA_DIR}/collections/{collection_id}.json
    - Creates backup in {CHERRY_DATA_DIR}/collections/backups/
    """
    ...
```

### 8. Prompt Drift

**Problem**: Prompts becoming inconsistent, contradictory, or outdated.

**Solution**: Store prompts as code. Review regularly. Keep them explicit.

**Example**:
* ❌ BAD: Hardcoded strings scattered across codebase
* ✅ GOOD: Constants in `prompts/` directory, version controlled

### 9. Tool vs Agent Confusion

**Problem**: Creating agents for deterministic tasks that should be tools.

**Solution**: Use this decision tree:
* Needs LLM reasoning? → Agent
* Deterministic logic? → Tool
* Orchestration needed? → Sequential/Parallel Agent

**Example**:
* ❌ BAD: `file_save_agent = LlmAgent(...)` for saving JSON
* ✅ GOOD: `save_collection(path, data)` tool

### 10. Premature Optimization

**Problem**: Optimizing before understanding bottlenecks.

**Solution**: Build first, measure, then optimize. Use Langfuse for observability.

**Example**:
1. Build working agent workflow
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
    results = keyword_search("test query", dataset_id="test_dataset")
    assert len(results) > 0
    assert "test" in results[0]["text"].lower()
```

### Agent Tests

Test individual agents with mocked dependencies:

```python
@pytest.mark.asyncio
async def test_keyword_search_agent():
    """Test keyword search agent with mock tools"""
    agent = keyword_search_agent
    input_data = {"query": "test query", "dataset_id": "test_dataset"}

    # Mock tools
    with patch("tools.keyword_search", return_value=[{"id": "1", "text": "test"}]):
        result = await agent.run(input_data)

        # Verify agent called search tool
        assert len(result["results"]) > 0
```

### Integration Tests

Test agent workflows (sequential/parallel):

```python
@pytest.mark.asyncio
async def test_search_workflow():
    """Test parallel search orchestration"""
    search_agent = search_orchestration_agent  # ParallelAgent
    input_data = {"query": "test query"}

    result = await search_agent.run(input_data)

    # All sub-agents should have run
    assert "keyword_results" in result
    assert "semantic_results" in result
    assert "topic_results" in result
```

### System Tests

Test entire root_search_agent end-to-end:

```python
@pytest.mark.asyncio
async def test_full_search_flow():
    """Test complete search workflow"""
    root = root_search_agent
    query = "test evaluation query"

    result = await root.run({"query": query})

    # Verify all stages completed
    assert "understood_query" in result
    assert "search_results" in result
    assert "merged_results" in result

    # Verify result quality
    assert len(result["merged_results"]) > 0
```

---

## Debugging Tips

### 1. Enable Verbose Logging

```bash
export CHERRY_LOG_LEVEL=DEBUG
uv run uvicorn cherry_evals.api.main:app --reload
```

### 2. Use ADK Web UI for Tracing

```bash
uv run adk web
```

Navigate to the UI to see:
* Agent execution traces
* Input/output for each agent
* Tool calls and results
* Execution times

### 3. Langfuse for Production Monitoring

Set up local Langfuse server for:
* End-to-end tracing
* Latency analysis
* Agent performance metrics
* Cost tracking

### 4. Add Breakpoints in Agent Logic

Since agents are Python code, you can use standard debugging:

```python
# In agents or tools
import pdb; pdb.set_trace()
```

### 5. Test Prompts Independently

Before integrating into agents, test prompts directly:

```python
from google import genai

client = genai.Client(api_key="...")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Test query",
    config={
        "system_instruction": YOUR_PROMPT_INSTRUCTIONS,
    }
)
print(response.text)
```

---

## Additional Resources

* **ADK Documentation**: [github.com/google/adk-python](https://github.com/google/adk-python)
* **ADK Samples**: [github.com/google/adk-samples](https://github.com/google/adk-samples)
* **Gemini API Docs**: [ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)
* **Cherry-evals Roadmap**: [ROADMAP.md](./ROADMAP.md)
* **Qdrant Docs**: [qdrant.tech/documentation](https://qdrant.tech/documentation)
* **FastAPI Docs**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)

---

Remember: **Cherry-evals' value comes from being transparent and reliable.**

Prioritize clarity over cleverness, traceability over magic, and small safe steps over big refactors.

**Build agents that serve the user's search and evaluation needs — never the other way around.**

