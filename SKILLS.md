# Cherry Evals — Agent Skills Guide

## What is Cherry Evals?

Cherry Evals is a platform for discovering, curating, and exporting examples from public AI evaluation datasets (MMLU, HumanEval, GSM8K, HellaSwag, TruthfulQA, ARC, WinoGrande, PIQA, MBPP, BoolQ). As an agent, you can search across all datasets using keyword, semantic, hybrid, or LLM-powered intelligent search; cherry-pick the examples most relevant to your task into named collections; and export those collections as JSONL, JSON, CSV, or directly into Langfuse. Cherry Evals is purpose-built for both human and agent use — treat it as your evaluation dataset index.

---

## When to Use Cherry Evals

- You need real benchmark examples to test a model on a specific topic (e.g., "find 20 hard math reasoning questions")
- You are building a custom eval suite and want to seed it from vetted public benchmarks
- You want to explore what subjects or task types exist across 10 major benchmarks before committing to a dataset
- You need to export evaluation examples in a format compatible with Langfuse, LangSmith, Inspect AI, or any JSONL-based eval framework
- You want to compare examples across datasets by topic to understand coverage and overlap

---

## Access Methods

### MCP Server (Recommended for Agents)

The MCP server exposes all Cherry Evals functionality as typed tools via the Model Context Protocol. Use stdio transport for local/Claude Desktop integration; use HTTP transport for remote agents.

**Start the server:**
```bash
# stdio (Claude Desktop / local agents)
uv run mcp_server/server.py

# HTTP (remote agents)
uv run mcp_server/server.py --http

# Test with MCP Inspector
uv run mcp dev mcp_server/server.py
```

**Available MCP tools:**

| Tool | Signature | Description |
|------|-----------|-------------|
| `list_datasets` | `() -> str` | List all ingested datasets with example counts |
| `get_dataset` | `(dataset_id: int) -> str` | Get details for one dataset |
| `search_examples` | `(query: str, dataset_name?: str, subject?: str, limit?: int) -> str` | Keyword search |
| `semantic_search_examples` | `(query: str, collection?: str, subject?: str, limit?: int, score_threshold?: float) -> str` | Vector similarity search |
| `hybrid_search_examples` | `(query: str, dataset_name?: str, subject?: str, collection?: str, limit?: int, keyword_weight?: float, semantic_weight?: float) -> str` | Keyword + semantic fusion (RRF) |
| `intelligent_search_examples` | `(query: str, limit?: int, max_iterations?: int, strategy?: str) -> str` | LLM-powered autonomous search agent |
| `list_collections` | `() -> str` | List all collections with example counts |
| `create_collection` | `(name: str, description?: str) -> str` | Create a new curated collection |
| `add_to_collection` | `(collection_id: int, example_ids: list[int]) -> str` | Add examples to a collection |
| `get_collection` | `(collection_id: int) -> str` | Get collection details and all examples |
| `export_collection` | `(collection_id: int, format?: str) -> str` | Export as json, jsonl, or csv |

All tools return JSON strings. Parse the response to extract `results`, `id`, or `error` fields.

---

### REST API

Base URL: `http://localhost:8000` (default local).

**Key endpoints:**

```bash
# Health check
curl http://localhost:8000/health

# List datasets
curl http://localhost:8000/datasets

# Get dataset subjects
curl http://localhost:8000/datasets/1/subjects

# Keyword search
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{"query": "neural network backpropagation", "limit": 10}'

# Semantic search (requires embeddings)
curl -X POST http://localhost:8000/search/semantic \
  -H "Content-Type: application/json" \
  -d '{"query": "gradient descent optimization", "collection": "mmlu_embeddings", "limit": 10}'

# Hybrid search
curl -X POST http://localhost:8000/search/hybrid \
  -H "Content-Type: application/json" \
  -d '{"query": "transformer attention mechanism", "limit": 20}'

# Intelligent search (LLM-powered)
curl -X POST http://localhost:8000/search/intelligent \
  -H "Content-Type: application/json" \
  -d '{"query": "hard science questions requiring multi-step reasoning", "strategy": "agent", "limit": 20}'

# Facet counts (explore available filters)
curl -X POST http://localhost:8000/search/facets \
  -H "Content-Type: application/json" \
  -d '{"query": "biology"}'

# Create collection
curl -X POST http://localhost:8000/collections \
  -H "Content-Type: application/json" \
  -d '{"name": "Math Reasoning Hard", "description": "Difficult multi-step math problems"}'

# Add examples to collection
curl -X POST http://localhost:8000/collections/1/examples \
  -H "Content-Type: application/json" \
  -d '{"example_ids": [42, 107, 883]}'

# Export collection as JSONL
curl -X POST http://localhost:8000/collections/1/export \
  -H "Content-Type: application/json" \
  -d '{"format": "jsonl"}' \
  -o my_eval_suite.jsonl

# Export to Langfuse
curl -X POST http://localhost:8000/collections/1/export \
  -H "Content-Type: application/json" \
  -d '{"format": "langfuse", "langfuse_dataset_name": "math-reasoning-hard"}'

# Analytics: most popular examples
curl http://localhost:8000/analytics/popular?limit=10

# Analytics: co-picked examples (what others pick alongside example 42)
curl http://localhost:8000/analytics/co-picked/42
```

**Search request fields (keyword and hybrid):**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | required | Search text |
| `dataset` | string | null | Filter by dataset name (e.g. "MMLU") |
| `subject` | string | null | Filter by subject (e.g. "anatomy") |
| `task_type` | string | null | Filter by task type (e.g. "multiple_choice") |
| `limit` | int | 20 | Max results (1–100) |
| `offset` | int | 0 | Pagination offset |
| `sort_by` | string | "relevance" | "relevance", "newest", or "dataset" |

**Intelligent search extra fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `strategy` | string | "agent" | "agent" (iterative) or "pipeline" (fixed DAG) |
| `max_iterations` | int | 3 | Agent iterations (1–5, only for strategy="agent") |

---

### CLI

The CLI is for data setup (ingestion and embedding generation). It does not support searching or collection management.

```bash
# Ingest a single dataset
uv run python -m cherry_evals.cli ingest mmlu

# Ingest all datasets
uv run python -m cherry_evals.cli ingest all

# Ingest with limits (for testing)
uv run python -m cherry_evals.cli ingest gsm8k --limit 500

# Generate embeddings for semantic search
uv run python -m cherry_evals.cli embed mmlu

# Generate embeddings with custom batch size
uv run python -m cherry_evals.cli embed mmlu --batch-size 50

# Available dataset names: mmlu, humaneval, gsm8k, hellaswag, truthfulqa,
#                          arc, winogrande, piqa, mbpp, boolq, all
```

---

## Common Workflows

### 1. Find Examples for a Specific Topic

**Goal:** Retrieve relevant benchmark examples on a topic for use in an eval or prompt test.

```
1. Call intelligent_search_examples(query="your topic", limit=20)
   - The agent tries multiple search strategies automatically
   - Check final_evaluation in the response for quality assessment

2. Review results — each result has:
   - id: use this to add to a collection
   - question, answer, choices: the actual content
   - example_metadata: subject, split, difficulty, etc.
   - score: relevance score (higher is better)

3. Filter by score threshold if needed:
   - Scores above 0.7 are generally high quality matches
   - Scores below 0.3 are likely poor matches

4. Use the IDs from results to add to a collection or pass directly to your eval
```

**MCP example:**
```
intelligent_search_examples(query="calculus integration techniques", limit=15)
```

---

### 2. Build a Custom Eval Suite

**Goal:** Create a named, exportable collection of hand-picked examples.

```
1. create_collection(name="My Eval Suite", description="Purpose and criteria")
   - Returns collection_id — save it

2. Search for relevant examples:
   search_examples(query="topic", dataset_name="MMLU", subject="mathematics")
   hybrid_search_examples(query="topic", limit=50)

3. Review the results and select example IDs you want

4. add_to_collection(collection_id=<id>, example_ids=[<list of ids>])
   - Duplicates are skipped automatically
   - Response reports added and skipped counts

5. Repeat steps 2–4 with different queries to diversify the collection

6. Verify: get_collection(collection_id=<id>) shows all examples in the set

7. Export when ready (see Workflow 3)
```

---

### 3. Export to an Eval Framework

**Goal:** Export a collection to a file format or push it to Langfuse.

```
For JSONL (most eval frameworks including Inspect AI, LangSmith, custom):
  export_collection(collection_id=<id>, format="jsonl")
  - Returns newline-delimited JSON, one example per line
  - Each line: {"id", "question", "answer", "choices", "dataset_name", "metadata"}

For JSON (full array):
  export_collection(collection_id=<id>, format="json")

For CSV:
  export_collection(collection_id=<id>, format="csv")

For Langfuse (direct push via API):
  POST /collections/<id>/export  with {"format": "langfuse", "langfuse_dataset_name": "my-dataset"}
  - Requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in environment
  - Returns {"dataset_name": "...", "items_exported": N}
```

---

### 4. Discover Available Datasets

**Goal:** Understand what data is available before searching.

```
1. list_datasets()
   - Returns all ingested datasets with example counts
   - If count is 0, the dataset has not been ingested yet

2. get_dataset(dataset_id=<id>)
   - Returns description, task_type, stats (e.g. per-subject counts for MMLU)

3. GET /datasets/<id>/subjects
   - Returns subject breakdown with counts (useful for MMLU filtering)

4. POST /search/facets with {"query": "your topic"}
   - Returns matching counts broken down by dataset, subject, and task_type
   - Use this to understand where your topic has the most coverage before searching
```

---

## Best Practices

- Use `intelligent_search_examples` with `strategy="agent"` for open-ended or complex queries — the agent iterates and self-evaluates
- Use `search_examples` (keyword) for exact term matching (e.g. specific formula names, function names)
- Use `semantic_search_examples` when you know the concept but not specific wording
- Use `hybrid_search_examples` as the balanced default when unsure — it falls back to keyword if Qdrant is unavailable
- Always check result `score` fields — higher scores indicate better relevance; use `score_threshold` to filter low-quality matches in semantic search
- Export as JSONL for most eval frameworks — it is the most widely supported format
- Use collections to organize examples by theme, difficulty, or use case; name them clearly since the name becomes the export filename
- When building a diverse suite, run multiple searches with varied queries and subject filters, then add to the same collection — duplicates are silently skipped
- Pass `X-Session-Id` header in REST API calls to enable analytics tracking across your session (optional but useful for co-picked recommendations)
- Use `GET /analytics/co-picked/<example_id>` to discover related examples that other users commonly pick together — good for expanding an eval set

---

## Available Datasets

| Dataset | CLI Name | Task Type | Description |
|---------|----------|-----------|-------------|
| MMLU | `mmlu` | `multiple_choice` | 57-subject multitask knowledge benchmark (~14K test examples across science, humanities, social science, STEM) |
| HumanEval | `humaneval` | `code_generation` | 164 hand-written Python programming problems with canonical solutions and test harnesses |
| GSM8K | `gsm8k` | `math_reasoning` | ~8.5K grade-school math word problems with chain-of-thought solutions |
| HellaSwag | `hellaswag` | `commonsense_reasoning` | Sentence completion benchmark for grounded commonsense inference (~40K train, 10K validation) |
| TruthfulQA | `truthfulqa` | `truthfulness` | 817 questions designed to test whether models produce truthful answers vs. common misconceptions |
| ARC | `arc` | `science_qa` | ARC-Challenge: harder subset of grade-school science questions (~1.2K test examples) |
| WinoGrande | `winogrande` | `commonsense_reasoning` | Large-scale Winograd Schema coreference challenges (~44K train, 1.3K validation) |
| PIQA | `piqa` | `physical_intuition` | Physical intuition questions about everyday goals and processes (~16K train, 2K validation) |
| MBPP | `mbpp` | `code_generation` | ~1K crowd-sourced Python programming problems with solutions and automated tests |
| BoolQ | `boolq` | `reading_comprehension` | Yes/no questions paired with Wikipedia passages (~9.4K train, 3.3K validation) |

**Note:** A dataset must be ingested before it can be searched. Call `list_datasets()` to check which datasets have examples. Run `uv run python -m cherry_evals.cli ingest <name>` to ingest a missing dataset, then `uv run python -m cherry_evals.cli embed <name>` to enable semantic search on it.

---

## Tips for Effective Searching

- **Start broad, then narrow:** first run `intelligent_search_examples` on the topic, then refine with subject or dataset filters based on what you find
- **Use dataset filters for targeted retrieval:** if you specifically want coding problems, filter to `dataset_name="HumanEval"` or `dataset_name="MBPP"` from the start
- **MMLU subject filtering:** MMLU has 57 subjects (e.g. "abstract_algebra", "anatomy", "college_physics"). Use `GET /datasets/<id>/subjects` to see all subjects and their counts, then filter searches with `subject=<name>`
- **Combine strategies:** run both keyword and semantic search on the same query and merge results for maximum recall — the `hybrid` search does this automatically with RRF
- **Score calibration:**
  - Keyword search scores are based on text match weight (higher = more term overlap)
  - Semantic scores are cosine similarity (0–1 range; above 0.7 is strong)
  - Hybrid scores are fused ranks — absolute values are not meaningful, relative order is
- **Task type filtering:** use `task_type` filter in keyword/hybrid search to constrain to a specific capability (e.g. `task_type="math_reasoning"` for only GSM8K examples)
- **Pagination:** for large result sets, use `offset` and `limit` to page through; `total` in the response shows how many matched

---

## Error Handling

| Error | Cause | Recovery |
|-------|-------|----------|
| `{"error": "Dataset N not found"}` | Invalid dataset_id | Call `list_datasets()` to get valid IDs |
| `{"error": "Collection N not found"}` | Invalid collection_id | Call `list_collections()` to get valid IDs |
| `{"error": "Semantic search unavailable: ..."}` | Qdrant not running or embeddings not generated | Fall back to `search_examples` (keyword); start Qdrant with `docker compose up -d` and run `embed` CLI command |
| `{"fallback": "..."}` in hybrid search | Semantic component failed; keyword results returned | Results are still valid keyword matches; resolve Qdrant issue for full hybrid support |
| HTTP 503 on `/search/semantic` | Qdrant unreachable | Same as above; use keyword or intelligent search as fallback |
| HTTP 502 on `/collections/<id>/export` with langfuse format | Langfuse credentials missing or API unreachable | Check `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, and `LANGFUSE_BASE_URL` environment variables |
| `added: 0, not_found: N` from `add_to_collection` | Example IDs do not exist | Re-run search to get valid IDs from the current dataset |
| Empty results on intelligent search | LLM providers unavailable or topic too narrow | Check `GOOGLE_API_KEY` and `ANTHROPIC_API_KEY`; try keyword search with simpler terms |

**General rule:** if an MCP tool returns a JSON object with an `"error"` key, read the message, diagnose the root cause from the table above, and retry with corrected parameters or fallback strategy. Cherry Evals degrades gracefully — keyword search always works as long as PostgreSQL is running.
