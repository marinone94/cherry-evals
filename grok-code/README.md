# cherry-evals

Cherry Evals is a comprehensive webapp for collecting, searching, and managing AI model evaluation datasets. It provides researchers, ML engineers, and AI practitioners with powerful tools to discover, curate, and export custom evaluation suites from public benchmark datasets.

The platform starts with text-based evaluations and will expand to support all modalities (images, video, audio, multi-modal). Cherry Evals democratizes access to high-quality evaluation data, making it easier to benchmark and compare AI models across different tasks and domains.

---

## Overview

Cherry Evals addresses the growing need for systematic evaluation dataset management in the AI community:

- **Dataset Discovery**: Comprehensive collection of public evaluation datasets from major AI vendors and research institutions
- **Powerful Search**: Multi-faceted search capabilities combining keyword, semantic, and topic-based discovery
- **Curated Collections**: Manual selection and organization of examples into custom evaluation suites
- **Format Flexibility**: Convert datasets to any format using predefined functions or custom conversion logic
- **Export Integration**: Seamless export to popular evaluation platforms (Langfuse, Arize Phoenix, local files)

Unlike scattered evaluation repositories, Cherry Evals provides a unified platform for the entire evaluation lifecycle — from dataset discovery to deployment.

---

## Core Features

### Dataset Collection & Management
- Comprehensive collection of public evaluation datasets from EleutherAI, DeepEval, BigBench, HELM
- Support for text modality initially, with planned expansion to images, video, audio, and multi-modal data
- Metadata extraction and standardization across different dataset formats
- Quality assessment and dataset validation pipelines

### Advanced Search Capabilities
- **Keyword Search**: Fast text-based search across dataset names, descriptions, and content
- **Semantic Search**: Embedding-based search for conceptual similarity and intent matching
- **Topic-Based Search**: Clustering and categorization for domain-specific discovery
- **Hybrid Search**: Combined keyword and semantic search with intelligent ranking

### Collection Curation
- Manual selection/deselection of search results for precise control
- Custom evaluation collection creation and management
- Collection versioning and collaborative workflows
- Quality scoring and automated suggestions

### Data Format Conversion
- Predefined conversion functions for standard evaluation formats (OpenAI eval, LangChain/LangSmith, Inspect AI, LMMS-Eval, etc.)
- Custom lambda function support for specialized transformations
- LLM-generated conversion functions for complex data mappings
- Format validation and preview capabilities

### Export & Integration
- **Local Export**: Save collections in JSON, CSV, YAML, and other standard formats
- **Langfuse Integration**: Direct export for evaluation tracking and monitoring
- **Arize Phoenix Integration**: Model performance analysis and observability
- **Extensible Architecture**: Easy addition of new export targets and integrations

---

## Tech Stack

- **Language**: Python 3.13
- **Agent Framework**: [Google ADK (Agent Development Kit)](https://github.com/google/adk-python) for deep search and LLM integration
- **Backend Framework**: [FastAPI](https://fastapi.tiangolo.com/) for high-performance REST APIs
- **RAG Solutions**: [Qdrant](https://qdrant.tech/), [Vespa](https://vespa.ai/), [Redis](https://redis.io/), [GCP Vertex AI RAG engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview) for semantic search and embeddings comparison
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Linting/Formatting**: [Ruff](https://github.com/astral-sh/ruff) + [pre-commit](https://pre-commit.com/)
- **Data Storage**: JSON/Parquet files with versioning, PostgreSQL for metadata
- **Observability**: Local Langfuse server for tracing, latency monitoring, agent steps

---

## Quick Start

### Prerequisites

- Python **3.13**
- `uv` (package + venv manager)
- `pre-commit` (for git hooks)
- API keys for LLM providers (OpenAI/Anthropic/Google) and vector databases

### Installation & Setup

```bash
# Clone the repo
git clone https://github.com/your-org/cherry-evals.git
cd cherry-evals

# Create and sync environment with uv (installs deps from pyproject.toml)
uv sync

# Install pre-commit hooks (ruff, uv lock, etc.)
uv run pre-commit install
```

### Environment Configuration

Create a `.env` file at the project root with:

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
```

### Start the API Server

```bash
# Run the FastAPI server
uv run uvicorn cherry_evals.api:app --reload --host 0.0.0.0 --port 8000

# Access the API documentation at http://localhost:8000/docs
```

### Run Agents with ADK

```bash
# Run search agent for dataset discovery
uv run adk run cherry_evals.agents.search_agent

# Run conversion agent for data transformation
uv run adk run cherry_evals.agents.conversion_agent

# Run collection management agent
uv run adk run cherry_evals.agents.collection_agent
```

---

## Development Commands

```bash
# Add a new dependency
uv add <package>

# Remove a dependency
uv remove <package>

# Update a dependency
uv add --upgrade <package>

# List dependencies
uv pip list

# Run the API server
uv run uvicorn cherry_evals.api:app --reload

# Run the agent locally (CLI mode)
uv run adk run cherry_evals.agents

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

## API Examples

### Search Datasets

```python
import requests

# Keyword search
response = requests.post("http://localhost:8000/search", json={
    "query": "code generation",
    "search_type": "keyword",
    "limit": 50
})

# Semantic search
response = requests.post("http://localhost:8000/search", json={
    "query": "mathematical reasoning tasks",
    "search_type": "semantic",
    "limit": 25
})
```

### Create Collection

```python
# Create a new evaluation collection
response = requests.post("http://localhost:8000/collections", json={
    "name": "Code Generation Benchmark",
    "description": "Comprehensive code generation evaluation suite",
    "tags": ["coding", "generation", "benchmark"]
})

collection_id = response.json()["id"]

# Add examples to collection
requests.post(f"http://localhost:8000/collections/{collection_id}/examples", json={
    "example_ids": ["example_1", "example_2", "example_3"],
    "operation": "add"
})
```

### Convert and Export

```python
# Convert collection to OpenAI eval format
response = requests.post(f"http://localhost:8000/collections/{collection_id}/convert", json={
    "target_format": "openai_eval",
    "custom_functions": []  # or provide custom lambda functions
})

# Export to Langfuse
requests.post(f"http://localhost:8000/collections/{collection_id}/export", json={
    "target": "langfuse",
    "config": {
        "project_name": "code-generation-eval",
        "dataset_name": "cherry-code-bench"
    }
})
```

---

## Architecture

Cherry Evals implements a multi-agent architecture using Google ADK for intelligent dataset discovery and processing:

```
root_agent (SequentialAgent)
├── search_agent (LlmAgent)
│   └── Handles complex multi-faceted search queries
│   └── Uses RAG for semantic understanding
├── collection_agent (LlmAgent)
│   └── Manages collection curation and quality assessment
│   └── Provides intelligent suggestions for dataset inclusion
├── conversion_agent (LlmAgent)
│   └── Generates custom conversion functions
│   └── Validates data transformations
└── export_agent (ParallelAgent)
    ├── langfuse_export_agent (LlmAgent)
    │   └── Handles Langfuse-specific formatting and upload
    └── arize_export_agent (LlmAgent)
        └── Manages Arize Phoenix integration and data mapping
```

### Key Components

- **Search Engine**: Hybrid keyword + semantic search powered by Qdrant
- **Collection Manager**: Versioned dataset collections with metadata tracking
- **Format Converter**: Extensible conversion system with LLM-generated functions
- **Export Pipeline**: Parallel export to multiple evaluation platforms
- **Quality Assurance**: Automated validation and quality scoring

---

## Roadmap

For detailed development roadmap and upcoming features, see [ROADMAP.md](./ROADMAP.md).

Key milestones:
- **MVP 0 (Dec 2025)**: Core dataset collection, search, and basic collection management
- **MVP 1 (Feb-Mar 2026)**: Production-ready with comprehensive export capabilities
- **MVP 2 (Apr-May 2026)**: Multi-modal support and advanced analytics

---

## Contributing

Cherry Evals welcomes contributions from the AI evaluation community:

1. **Dataset Contributions**: Help expand our collection of public evaluation datasets
2. **Format Converters**: Implement conversion functions for new evaluation formats
3. **Search Improvements**: Enhance search algorithms and user experience
4. **Export Integrations**: Add support for additional evaluation platforms

See [AGENTS.md](./AGENTS.md) for detailed development guidelines and agent architecture.

---

## License

Cherry Evals is open-source software released under the MIT License. See LICENSE file for details.

---

**Democratizing AI evaluation through comprehensive dataset management and intelligent curation.**
