---
description: Cherry Evals - Agent runtime for AI evaluation dataset management using Google ADK. Expert guidance for Python, ADK, uv, and agentic evaluation workflows.
globs: **/*.py
---
# Cherry Evals Development Guide

You are the Lead AI Engineer working on **Cherry Evals**, a comprehensive platform for collecting, searching, and managing AI model evaluation datasets.

Cherry Evals is built to be:
- **Research focused**
- **Transparent and reproducible**
- **Extensible across modalities and evaluation formats**

Your job is to keep the codebase **simple, explicit, and reliable**, and to follow agentic best practices when working with Google's Agent Development Kit (ADK).

---

## Project Architecture

### Core Concepts

Cherry Evals uses **Google's Agent Development Kit (ADK)** to model evaluation dataset management as a **hierarchical structure of specialized agents**:

- **Agent Types**:
  - **LlmAgent**: Single-purpose agents that perform specific evaluation tasks using an LLM
  - **SequentialAgent**: Orchestrates multiple sub-agents in a fixed sequence for complex workflows
  - **ParallelAgent**: Executes multiple sub-agents concurrently for efficiency (e.g., multiple export targets)

- **Agent Properties**:
  - **Model**: The LLM model to use (e.g., `gemini-2.5-flash`)
  - **Name**: Unique identifier for the agent
  - **Description**: Clear explanation of the agent's purpose in evaluation workflows
  - **Instruction**: Detailed prompt defining the agent's behavior for dataset management
  - **Tools**: List of callable tools/functions for data operations
  - **Sub-agents**: Child agents for single/sequential/parallel invocation

- **Workflow Pattern, Agentic Behavior**:
  - The overall pipeline follows a **search → curate → convert → export** sequential workflow
  - Inside specific agents, we use LLMs to make **local decisions** (dataset quality assessment, format conversion logic, search query understanding)
  - Sub-workflows can run in **parallel** for efficiency (e.g., multiple export destinations)

- **Prompts**:
  - Prompts are stored in the `cherry_evals/prompts/` directory as Python constants
  - Each agent has a `DESCRIPTION` constant and LLM agents have also an `INSTRUCTIONS` constant
  - Prompts should be explicit, not contradictory nor ambiguous
  - Use **bold** and CAPITAL letters to increase attention on specific words or phrases

### Agent Structure

Cherry Evals implements the following agent hierarchy:

```
root_agent (SequentialAgent)
├── search_agent (LlmAgent)
│   └── Handles complex multi-faceted search queries across evaluation datasets
│   └── Tools: [semantic_search, keyword_search, topic_clustering]
├── collection_agent (LlmAgent)
│   └── Manages evaluation collection curation and quality assessment
│   └── Tools: [collection_management, quality_scoring]
├── conversion_agent (LlmAgent)
│   └── Generates and applies data format conversion functions
│   └── Tools: [format_converter, validation_checker]
└── export_agent (ParallelAgent)
    ├── local_export_agent (Tool-based)
    │   └── Handles local file exports (JSON, CSV, YAML)
    │   └── Tools: [file_writer]
    ├── langfuse_export_agent (LlmAgent)
    │   └── Manages Langfuse evaluation dataset uploads
    │   └── Tools: [langfuse_client]
    └── arize_export_agent (LlmAgent)
        └── Handles Arize Phoenix dataset integration
        └── Tools: [arize_client]
```

#### 1. Root Agent
- **Type**: SequentialAgent
- **Purpose**: Main orchestrator that coordinates the entire evaluation dataset workflow
- **Sub-agents**: search_agent → collection_agent → conversion_agent → export_agent
- **File**: `cherry_evals/agent.py`
- **Prompt**: `cherry_evals/prompts/root_agent.py`

#### 2. Search Agent
- **Type**: LlmAgent
- **Purpose**: Intelligently searches across evaluation datasets using keyword, semantic, and topic-based approaches
- **Tools**: semantic_search, keyword_search, topic_clustering, dataset_retrieval
- **File**: `cherry_evals/agent.py`
- **Prompt**: `cherry_evals/prompts/search_agent.py`

#### 3. Collection Agent
- **Type**: LlmAgent
- **Purpose**: Curates evaluation collections by assessing dataset quality and managing selection/deselection
- **Tools**: collection_crud, quality_assessment, duplicate_detection
- **File**: `cherry_evals/agent.py`
- **Prompt**: `cherry_evals/prompts/collection_agent.py`

#### 4. Conversion Agent
- **Type**: LlmAgent
- **Purpose**: Handles data format conversion using predefined functions and LLM-generated custom logic
- **Tools**: format_converter, lambda_generator, validation_checker
- **File**: `cherry_evals/agent.py`
- **Prompt**: `cherry_evals/prompts/conversion_agent.py`

#### 5. Export Agent
- **Type**: ParallelAgent
- **Purpose**: Orchestrates parallel exports to multiple evaluation platforms
- **Sub-agents**: local_export_agent, langfuse_export_agent, arize_export_agent
- **File**: `cherry_evals/agent.py`
- **Prompt**: `cherry_evals/prompts/export_agent.py`

#### 6. Local Export Agent
- **Type**: Tool-based (deterministic)
- **Purpose**: Handles local file exports with format validation
- **Tools**: file_writer, format_validator
- **File**: `cherry_evals/agent.py`

#### 7. Langfuse Export Agent
- **Type**: LlmAgent
- **Purpose**: Manages export to Langfuse evaluation platform
- **Tools**: langfuse_client, dataset_formatter
- **File**: `cherry_evals/agent.py`
- **Prompt**: `cherry_evals/prompts/langfuse_export_agent.py`

#### 8. Arize Export Agent
- **Type**: LlmAgent
- **Purpose**: Handles Arize Phoenix dataset integration and upload
- **Tools**: arize_client, schema_mapper
- **File**: `cherry_evals/agent.py`
- **Prompt**: `cherry_evals/prompts/arize_export_agent.py`

---

## Tech Stack

- **Python**: 3.13
- **Agent Framework**: [Google ADK (Agent Development Kit)](https://github.com/google/adk-python)
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) for REST APIs
- **Vector Search**: [Qdrant](https://qdrant.tech/) for semantic search
- **RAG Solutions**: NIM RAG and GCP Native RAG for evaluation dataset search
- **LLM Models**: Gemini 2.5 Flash (via ADK native integration)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff) + [pre-commit](https://pre-commit.com/)
- **Data Storage**: JSON/Parquet files with versioning, PostgreSQL for metadata
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
uv pip list

# Run the API server
uv run uvicorn cherry_evals.api:app --reload --host 0.0.0.0 --port 8000

# Run the agent locally (CLI mode)
uv run adk run cherry_evals

# Run the agent with web UI
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

* Inspect the existing agents under `cherry_evals/`
* Check [README.md](./README.md) and the relevant docs for the latest instructions
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
  *"Should the semantic search use embeddings from all LLM providers or just Gemini?"*
* Avoid guessing when design decisions affect:
  * data model
  * public APIs
  * agent behavior
  * agent hierarchy

### 5. Test thoroughly
Always run tests after any code change:

* Add/modify/delete **unit tests** for any new function or class
* Add/modify/delete **integration tests** for agents and tools
* Add/modify/delete **system tests** for the entire agent workflow with simple, medium, and complex evaluation scenarios

Keep tests fast (whenever possible) and **always** deterministic.
Ensure to test dataset search, collection curation, AND export operations in system tests.

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

### 1. Single Responsibility Principle

* Each agent should have a **clear, focused purpose** in the evaluation workflow
* Avoid creating "god agents" that handle multiple evaluation stages
* If an agent's instructions become too complex (>100 lines), consider splitting it
* Example:
  * ✅ GOOD: `search_agent` only handles dataset discovery
  * ❌ BAD: `search_agent` also manages collections and exports

### 2. Explicit State Management

* **Be intentional** about how evaluation data flows between agents
* Use agent descriptions to clearly document WHEN the agent should be used in evaluation workflows
* Use agent instructions to clearly document WHAT the agent should do with evaluation data

* Limit implicit state passing and avoid hidden dependencies
* ADK agents communicate via:
  * Sequential flow: output of agent N becomes input of agent N+1
  * Parallel flow: all agents receive same input, outputs are merged
  * Tool calls: agents can invoke tools to retrieve/persist evaluation data

### 3. Appropriate Autonomy

* Assign agents only the **level of autonomy they require** for evaluation tasks
* For deterministic tasks → use tools/functions, not agents
* Tools should prevent unauthorized evaluation data access
* For LLM-powered decisions → use LlmAgent (dataset quality, conversion logic)
* For orchestration → use SequentialAgent/ParallelAgent
* Example:
  * ✅ GOOD: Use tool for "export collection to JSON"
  * ❌ BAD: Create an agent for "export collection to JSON"
  * ✅ GOOD: Tool validates collection schema before export
  * ❌ BAD: Export agent handles both validation and file writing

### 4. Controlled Delegation

* Use parent-child relationships **deliberately** with clear instructions for evaluation workflows
* Each sub-agent should have a clear, narrow responsibility in the evaluation pipeline
* Document the orchestration flow clearly

### 5. Start with a Small Agent Hierarchy, Then Evolve

* Begin with simple, flat structures (1-2 levels)
* Add layers as new evaluation features require it
* Avoid prematurely splitting into many specialized agents
* Current Cherry Evals structure (3 levels) is appropriate for MVP

### 6. Separate Tooling from Orchestration

* Keep **tools** and **data management** in dedicated modules
* Agents should orchestrate evaluation workflows, not implement business logic directly
* This simplifies testing:
  * Unit-test tools/managers without agents
  * Integration-test agents with mocked tools
  * System-test full evaluation workflow end-to-end

Example structure:
```python
# tools/dataset_manager.py
def search_datasets(query: str, search_type: str) -> list[dict]:
    """Pure Python tool for dataset search"""
    ...

# agent.py
search_agent = LlmAgent(
    ...,
    tools=[search_datasets],  # Agent uses tool, doesn't implement it
)
```

### 7. Comprehensive Testing

* **Unit tests**: Test individual tools/functions for evaluation operations
* **Agent tests**: Test single agents with mocked evaluation data
* **Integration tests**: Test agent workflows (sequential/parallel) for evaluation pipelines
* **System tests**: Test entire root_agent end-to-end with real evaluation scenarios

### 8. Version track evaluation datasets and collections

* Ensure edited JSON/Parquet files (datasets, collections, metadata) are version tracked
* Changes should be easy to inspect and revert
* Use git for versioning, not custom solutions

### 9. Prompts as Code

* Store prompts as Python constants in `prompts/` directory
* Each agent should have:
  * `{AGENT_NAME}_DESCRIPTION`: Brief purpose statement (when to use it in evaluation workflows)
  * `{AGENT_NAME}_INSTRUCTIONS`: Detailed behavior specification (what it should do with evaluation data, and how)
* Use XML-like tags in instructions for structure when needed
* Keep prompts explicit, unambiguous, and well-formatted

### 10. Security and Data Privacy

* When agents use tools to interact with external evaluation platforms:
  * Use the agent's own identity, not impersonation
  * Explicitly authorize the agent in external access policies
  * Constrain actions to evaluation data operations only
* Never expose API keys or sensitive evaluation data in prompts
* Sanitize inputs before passing to external evaluation tools

---

## Code Style & Organization

* **Naming**:
  * `snake_case` for functions, variables, and tools
  * `PascalCase` for classes and Pydantic models
  * `SCREAMING_SNAKE_CASE` for constants (including prompts)
  * Agent names: `{purpose}_agent` (e.g., `search_agent`)

* **Files**:
  * One main concept per file
  * Agent definitions: `cherry_evals/agent.py`
  * Prompts: `cherry_evals/prompts/{agent_name}.py`
  * Tools: `cherry_evals/tools/{tool_category}.py`
  * Keep functions under ~100–150 lines if possible

* **Imports**:
  * Use absolute imports for ADK and external packages
  * Use relative imports within `cherry_evals/` package
  * Group imports: stdlib → third-party → local
  * Sort them by import pkg.module, then from pkg.module import fcn
  * Then, sort alphabetically
  * Subgroup imports of each group and add comments on top (e.g. "# adk imports", "# cherry evals prompt imports", ...)

* **Comments**:
  * Explain *why* something is done, not *what* it does
  * Exception: Explain *what* when using complex third-party APIs
  * Add docstrings for all public functions, classes, and agents

* **Type Hints**:
  * Use type hints for all function signatures
  * Use Pydantic models for structured evaluation data
  * Use `TypedDict` for simple dictionaries with known keys

---

## Extending Cherry Evals (Post-MVP Patterns)

When adding new evaluation features:

### Adding New Agents

1. **Create prompt file**: `cherry_evals/prompts/new_agent.py`
   ```python
   NEW_AGENT_DESCRIPTION = """..."""
   NEW_AGENT_INSTRUCTIONS = """..."""
   ```

2. **Define agent**: In `cherry_evals/agent.py`
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

* For complex evaluation features, consider:
  * **SequentialAgent**: When evaluation tasks must happen in order (search → curate → convert)
  * **ParallelAgent**: When evaluation tasks can run concurrently (multiple exports)
  * **Loop agents**: When sub agents need to be invoked repeatedly (batch processing)

* Document agent relationships clearly

### Export Integrations

* For new evaluation platforms:
  * Create dedicated export agent with platform-specific logic
  * Add authentication and rate limiting
  * Include platform-specific data format conversions
  * Add comprehensive error handling and retry logic

---

## Environment & Workflow

### Environment Variables

```bash
# LLM API Keys (choose your provider)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Vector Database Configuration
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=your-qdrant-key

# RAG Solutions (optional)
NIM_RAG_ENDPOINT=your-nim-endpoint
GCP_PROJECT_ID=your-gcp-project

# Export Integrations
LANGFUSE_PUBLIC_KEY=your-langfuse-key
LANGFUSE_SECRET_KEY=your-langfuse-secret
ARIZE_API_KEY=your-arize-key

# Data Storage
CHERRY_EVALS_DATA_DIR=~/.cherry-evals
CHERRY_EVALS_LOG_LEVEL=INFO
```

### Development Workflow

1. **Setup**: `uv sync` to ensure dependencies are up to date, add/remove with `uv add`, `uv remove`
2. **Branch**: Create a feature branch for your evaluation work
3. **Implement**: Make small, focused changes to agents/tools/prompts for evaluation workflows
4. **Test**: Run tests locally (`uv run pytest`)
5. **Lint**: Run `uv run ruff check . && uv run ruff format .`
6. **Vibe test**: Run `uv run adk run cherry_evals` or `uv run uvicorn cherry_evals.api:app --reload`
7. **Document**: Update relevant docs (`AGENTS.md`, docstrings)
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
      feat(search): Add semantic search for evaluation datasets
      fix(export): Prevent duplicate exports to Langfuse
      refactor(agents): Unify error handling across export agents
      ```
    * **Rationale:** Conventional commits enable automated changelog generation and version management.

9. **Pre-commit**: Hooks will run automatically on commit
10. **Review**: Create PR and request review

---

## Common Pitfalls

### 1. Over-Engineering Agent Hierarchies

**Problem**: Creating too many specialized agents for evaluation tasks too early.

**Solution**: Start simple. Only add agents when evaluation complexity justifies it.

**Example**:
* ❌ BAD: 10 micro-agents for different export formats
* ✅ GOOD: 1 `export_agent` with parallel sub-agents for different platforms

### 2. Unclear Agent Boundaries

**Problem**: Agents with overlapping responsibilities in evaluation workflows.

**Solution**: Define clear, non-overlapping purposes in agent descriptions.

**Example**:
* ❌ BAD: Both `search_agent` and `collection_agent` assess dataset quality
* ✅ GOOD: Only `collection_agent` assesses quality, `search_agent` finds datasets

### 3. Excessive Delegation

**Problem**: Too many levels of agent nesting, creating communication overhead in evaluation pipelines.

**Solution**: Keep hierarchy shallow (<4 levels). Use tools instead of agents for deterministic evaluation tasks.

**Example**:
* ❌ BAD: `root → search_orchestrator → search_coordinator → search_worker → search_executor`
* ✅ GOOD: `root → search_agent → collection_agent → export_agent (parallel)`

### 4. State Management Confusion

**Problem**: Unclear evaluation data flow between agents, leading to lost or inconsistent evaluation collections.

**Solution**: Document inputs/outputs clearly. Use tools for evaluation data persistence.

**Example**:
* ❌ BAD: Agents modify shared global evaluation state
* ✅ GOOD: Agents receive input, call tools to persist evaluation changes, return output

### 5. Ignoring Error Handling

**Problem**: Agents fail silently or crash evaluation workflows.

**Solution**: Implement proper error handling at agent and tool level for evaluation operations.

**Example**:
```python
# In tools
def search_datasets(query: str) -> list[dict]:
    try:
        return perform_search(query)
    except ConnectionError:
        logger.warning(f"Search failed for query: {query}")
        return []  # Return empty results instead of crashing

# In agent instructions
"""
If the dataset search fails:
- Log the error with query details
- Return empty search results
- Continue with the evaluation workflow
"""
```

### 6. Skipping Logging

**Problem**: Debugging evaluation workflows is impossible without logs.

**Solution**: Log at key decision points in agents and tools. Log almost every evaluation step at DEBUG level.

**Example**:
```python
logger.info(f"Search agent: Found {len(results)} datasets for query '{query}'")
logger.debug(f"Search results: {results}")
logger.warning(f"Search agent: No datasets found for complex query")
```

### 7. Hidden Side-Effects

**Problem**: Tools performing file I/O or network calls for evaluation data without clear documentation.

**Solution**: Document side effects clearly. Make them visible at agent level.

**Example**:
```python
def export_to_langfuse(collection_id: str, config: dict) -> None:
    """
    Exports evaluation collection to Langfuse platform.

    Side effects:
    - Creates dataset in Langfuse project '{config.project_name}'
    - Uploads all examples in collection
    - May incur API costs based on dataset size
    """
    ...
```

### 8. Prompt Drift

**Problem**: Prompts becoming inconsistent for evaluation tasks.

**Solution**: Store prompts as code. Review regularly for evaluation workflow consistency.

**Example**:
* ❌ BAD: Hardcoded strings scattered across evaluation codebase
* ✅ GOOD: Constants in `prompts/` directory, version controlled

### 9. Tool vs Agent Confusion

**Problem**: Creating agents for deterministic evaluation tasks that should be tools.

**Solution**: Use this decision tree:
* Needs LLM reasoning for evaluation? → Agent (quality assessment, format conversion)
* Deterministic evaluation logic? → Tool (file export, data validation)
* Orchestration of evaluation tasks? → Sequential/Parallel Agent

**Example**:
* ❌ BAD: `json_export_agent = LlmAgent(...)` for exporting JSON
* ✅ GOOD: `export_json(path, data)` tool

### 10. Premature Optimization

**Problem**: Optimizing evaluation search before understanding bottlenecks.

**Solution**: Build working evaluation workflows first, measure, then optimize.

**Example**:
1. Build working search → curate → convert → export pipeline
2. Instrument with logging/tracing for evaluation operations
3. Identify slow agents/tools in evaluation workflows
4. Optimize specific bottlenecks (caching, parallelization, indexing)

---

## Testing Strategy

### Unit Tests

Test individual tools and functions in isolation:

```python
def test_dataset_search():
    """Test dataset search tool"""
    results = search_datasets("code generation")
    assert len(results) > 0
    assert all("code" in r["description"].lower() for r in results)
```

### Agent Tests

Test individual agents with mocked evaluation dependencies:

```python
@pytest.mark.asyncio
async def test_collection_agent():
    """Test collection curation agent with mock tools"""
    agent = collection_agent
    input_data = {"examples": [...], "criteria": "high_quality"}

    # Mock tools
    with patch("tools.assess_quality", return_value=[True, False, True]):
        with patch("tools.update_collection") as mock_update:
            result = await agent.run(input_data)

            # Verify agent called quality assessment
            mock_update.assert_called_once()
            # Verify only high-quality examples kept
            assert len(mock_update.call_args[0][1]) == 2
```

### Integration Tests

Test agent workflows (sequential/parallel):

```python
@pytest.mark.asyncio
async def test_export_workflow():
    """Test parallel export to multiple platforms"""
    export_agent = export_agent  # ParallelAgent
    input_data = {"collection_id": "test_collection", "targets": ["local", "langfuse"]}

    result = await export_agent.run(input_data)

    # Both sub-agents should have run
    assert "local_export" in result
    assert "langfuse_export" in result
```

### System Tests

Test entire root_agent end-to-end:

```python
@pytest.mark.asyncio
async def test_full_evaluation_workflow():
    """Test complete evaluation dataset workflow"""
    root = root_agent
    user_request = "Create a code generation evaluation suite"

    result = await root.run({"request": user_request})

    # Verify all stages completed
    assert "search_results" in result
    assert "collection" in result
    assert "converted_data" in result
    assert "exports" in result

    # Verify evaluation quality
    assert len(result["collection"]["examples"]) > 0
    assert result["exports"]["success"] == True
```

---

## Debugging Tips

### 1. Enable Verbose Logging

```bash
export CHERRY_EVALS_LOG_LEVEL=DEBUG
uv run uvicorn cherry_evals.api:app --reload
```

### 2. Use ADK Web UI for Tracing

```bash
uv run adk web
```

Navigate to the UI to see:
* Agent execution traces for evaluation workflows
* Input/output for each evaluation agent
* Tool calls and results
* Execution times for evaluation operations

### 3. Langfuse for Production Monitoring

Set up local Langfuse server for:
* End-to-end tracing of evaluation pipelines
* Latency analysis for search and export operations
* Agent performance metrics
* Cost tracking for evaluation workflows

### 4. Add Breakpoints in Agent Logic

Since agents are Python code, you can use standard debugging:

```python
# In agent.py or tools
import pdb; pdb.set_trace()
```

### 5. Test Prompts Independently

Before integrating into evaluation agents, test prompts directly:

```python
from google import genai

client = genai.Client(api_key="...")
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="Find code generation evaluation datasets",
    config={
        "system_instruction": YOUR_SEARCH_PROMPT_INSTRUCTIONS,
    }
)
print(response.text)
```

---

## Additional Resources

* **ADK Documentation**: [github.com/google/adk-python](https://github.com/google/adk-python)
* **ADK Samples**: [github.com/google/adk-samples](https://github.com/google/adk-samples)
* **Gemini API Docs**: [ai.google.dev/gemini-api/docs](https://ai.google.dev/gemini-api/docs)
* **Cherry Evals Roadmap**: [ROADMAP.md](./ROADMAP.md)
* **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com/)
* **Qdrant Documentation**: [qdrant.tech/documentation](https://qdrant.tech/documentation/)

---

Remember: **Cherry Evals' value comes from enabling comprehensive and reproducible AI evaluation.**

Prioritize clarity over cleverness, traceability over magic, and small safe steps over big refactors.

**Build evaluation tools that serve researchers — never the other way around.**
