---
description: Cherry Evals - Agent Development Guide using Google ADK.
globs: **/*.py
---
# Cherry Evals Development Guide

You are the AI Engineer working on **Cherry Evals**, a tool for managing and transforming AI evaluation datasets.

Your job is to build robust, specialized agents using **Google's Agent Development Kit (ADK)** to handle complex tasks like semantic search and code generation for data transformation.

---

## Project Architecture

### Core Concepts

Cherry Evals uses **Google's Agent Development Kit (ADK)** to model agent behavior.

- **Agent Types**:
  - **LlmAgent**: Single-purpose agents (e.g., generating search queries, writing transformation code).
  - **SequentialAgent**: Orchestrates workflows.
  - **ParallelAgent**: Executes tasks concurrently.

- **Workflow Pattern**:
  - **Search Workflow**: User Query → Search Agent → Vector DB Query → Results
  - **Transformation Workflow**: User Request → Transformation Agent → Python Code → Execution

### Agent Structure

Cherry Evals implements the following agent hierarchy:

```
root_agent (SequentialAgent)
├── search_agent (LlmAgent)
│   └── Understands user intent and formulates precise queries for the vector database
│   └── Tools: [vector_db_search, query_expansion]
└── transformation_agent (LlmAgent)
    └── Generates Python code to convert eval data formats based on user descriptions
    └── Tools: [code_validator, schema_inspector]
```

#### 1. Root Agent
- **Type**: SequentialAgent
- **Purpose**: Main entry point for agentic workflows.
- **Sub-agents**: search_agent, transformation_agent (invoked based on routing)

#### 2. Search Agent
- **Type**: LlmAgent
- **Purpose**: Performs "Deep Search". It takes a vague user request (e.g., "find me hard math problems about calculus"), expands it into keywords and semantic embeddings, and queries the database.
- **Tools**: `search_vector_db`, `get_available_topics`

#### 3. Transformation Agent
- **Type**: LlmAgent
- **Purpose**: Writes custom lambda functions to convert data from one format to another.
- **Tools**: `validate_python_code`, `get_target_schema`

---

## Tech Stack

- **Python**: 3.13
- **Agent Framework**: [Google ADK](https://github.com/google/adk-python)
- **LLM Models**: Gemini 2.5 Flash
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Vector DB**: [Qdrant](https://qdrant.tech/), [Vespa](https://vespa.ai/), [Redis](https://redis.io/), [GCP Vertex AI RAG engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)

---

## ADK Best Practices

### 1. Single Responsibility Principle
* Each agent should have a **clear, focused purpose**.
* `search_agent` should only handle retrieval logic.
* `transformation_agent` should only handle code generation.

### 2. Explicit State Management
* Be intentional about data flow.
* Use tools to persist state or interact with the backend (FastAPI/DB).

### 3. Separate Tooling from Orchestration
* Keep tools in dedicated modules (e.g., `tools/vector_db.py`).
* Agents should orchestrate, not implement business logic directly.

### 4. Comprehensive Testing
* **Unit tests**: Test individual tools.
* **Agent tests**: Test single agents with mocked tools.
* **Integration tests**: Test the flow from Search to Results.

### 5. Prompts as Code
* Store prompts as Python constants in a `prompts/` directory.
* Use explicit instructions.

---

## Development Workflow

1. **Setup**: `uv sync`
2. **Run Agents**: `uv run adk run cherry-evals-adk`
3. **Test**: `uv run pytest`
4. **Lint**: `uv run ruff check .`

---

## Code Style

* **Naming**: `snake_case` for functions, `PascalCase` for classes.
* **Type Hints**: Mandatory for all function signatures.
* **Documentation**: Docstrings for all public functions and agents.

---

Remember: **Cherry Evals aims to be the most flexible tool for AI evaluation data.**
Prioritize reliability and correctness, especially in the Transformation Agent where code generation is involved.

