# cherry-evals

**cherry-evals** is a comprehensive tool to manage AI model evaluations. It allows users to discover, curate, transform, and export evaluation datasets for benchmarking AI models.

The goal is to simplify the process of creating custom evaluation suites by leveraging public datasets, powerful search capabilities, and flexible data transformation tools.

---

## Core Features

### 1. Evaluation Collection & Discovery
- **Public Evals Aggregation**: Collects public evaluation datasets from EleutherAI, DeepEval, BigBench, HELM.
- **Multi-modality Support**: Starts with text-based evals, with planned support for image, video, and audio.
- **Deep Search**: Search datasets and individual examples via:
    - Keyword search
    - Semantic search
    - Topic-based filtering
    - Agentic deep search
    - Hybrid search combinations

### 2. Curation & Customization
- **Manual Selection**: granular control to select or deselect specific examples from search results.
- **Custom Collections**: Group selected examples into named evaluation sets.

### 3. Data Transformation
- **Standard Converters**: Predefined functions to convert data into common formats.
- **Custom Lambdas**: Support for user-defined transformation functions.
- **LLM-Generated Converters**: AI-assisted generation of transformation code for complex formats.

### 4. Export & Integration
- **Local Export**: Save datasets to local files (JSON, CSV, Parquet).
- **Observability Integration**: Direct export to Langfuse and Arize Phoenix.

---

## Tech Stack

- **Language**: Python (FastAPI for Backend)
- **Agent Runtime**: [Google ADK](https://github.com/google/adk-python)
- **Vector Database**: [Qdrant](https://qdrant.tech/), [Vespa](https://vespa.ai/), [Redis](https://redis.io/), [GCP Vertex AI RAG engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)
- **LLM Models**: Gemini (via ADK)
- **Package Manager**: [uv](https://docs.astral.sh/uv/)
- **Frontend**: Lovable (planned)

---

## Quick Start

### Prerequisites
- Python 3.13
- `uv` package manager
- Google API Key (for ADK agents)

### Installation

```bash
# Navigate to the directory
cd cherry-evals

# Install dependencies
uv sync

# Run the API server (FastAPI)
uv run fastapi dev main.py
```

### Agent Development

```bash
# Run ADK agents
uv run adk run cherry-evals-adk
```

---

## Documentation

- **[AGENTS.md](./AGENTS.md)**: Agent architecture and development guidelines.
- **[ROADMAP.md](./ROADMAP.md)**: Project roadmap and milestones.

