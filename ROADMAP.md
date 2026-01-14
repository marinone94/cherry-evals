# Cherry Evals Roadmap

## Legend
- [x] Done
- [~] In progress
- [ ] Planned
- [!] Blocked / Failed

---

## MVP-0: Foundation

**Goal:** Get one dataset searchable end-to-end with basic API.

This is the minimum viable foundation. No agents, no fancy features — just the plumbing that everything else builds on.

### Infrastructure Setup
- [ ] Initialize uv project with `pyproject.toml`
- [ ] FastAPI project scaffold (`api/main.py`, `api/routes/`, `api/models/`)
- [ ] PostgreSQL setup with SQLAlchemy models
- [ ] Alembic migrations setup
- [ ] Qdrant vector database setup (local Docker)
- [ ] Docker Compose for local development (postgres, qdrant)
- [ ] Pre-commit hooks (ruff check, ruff format)
- [ ] Environment configuration (`.env.example`, `pydantic-settings`)

### Data Models
- [ ] `Example` schema (question, answer, choices, metadata)
- [ ] `Dataset` schema (name, source, license, task_type, description, stats)
- [ ] `Collection` schema (name, description, user_id, created_at)
- [ ] `CollectionExample` join table (collection_id, example_id, added_at)

### First Dataset: MMLU
- [ ] Download MMLU from HuggingFace
- [ ] Parse and normalize to internal `Example` schema
- [ ] Extract metadata (subject, split, difficulty)
- [ ] Store examples in PostgreSQL
- [ ] Generate embeddings (start with `text-embedding-3-small` or similar)
- [ ] Index embeddings in Qdrant
- [ ] Ingestion CLI command: `uv run python -m cherry_evals.cli ingest mmlu`

### Basic API Endpoints
- [ ] `GET /health` - Health check
- [ ] `GET /datasets` - List all datasets
- [ ] `GET /datasets/{id}` - Get dataset details with stats
- [ ] `GET /examples` - List examples with pagination
- [ ] `GET /examples/{id}` - Get single example

### Basic Search
- [ ] `POST /search` - Keyword search (PostgreSQL full-text)
- [ ] Pagination support (offset, limit)
- [ ] Filter by dataset, subject

### Testing
- [ ] Unit tests for data models
- [ ] Unit tests for ingestion pipeline
- [ ] Integration tests for API endpoints
- [ ] Pytest configuration with fixtures

### Success Criteria
- [ ] MMLU dataset fully ingested (~14k examples)
- [ ] Can search examples by keyword
- [ ] API returns paginated results
- [ ] All tests passing
- [ ] Docker Compose starts all services

---

## MVP-1: Semantic Search

**Goal:** Add vector search and hybrid search capabilities.

### Semantic Search
- [ ] Qdrant search endpoint
- [ ] `POST /search/semantic` - Vector similarity search
- [ ] Embedding generation on-the-fly for queries
- [ ] Top-k retrieval with score threshold

### Hybrid Search
- [ ] `POST /search/hybrid` - Combined keyword + semantic
- [ ] Configurable weights (keyword vs semantic)
- [ ] Result fusion and deduplication
- [ ] Relevance scoring

### Search Improvements
- [ ] Filter by multiple fields (dataset, subject, difficulty)
- [ ] Sort options (relevance, date, alphabetical)
- [ ] Faceted search (count by subject, by dataset)
- [ ] Search result highlighting

### Testing
- [ ] Unit tests for search functions
- [ ] Integration tests for search endpoints
- [ ] Search quality evaluation (manual spot checks)

### Success Criteria
- [ ] Semantic search returns relevant results
- [ ] Hybrid search improves over keyword-only
- [ ] Search latency <500ms for semantic, <100ms for keyword

---

## MVP-2: Collections

**Goal:** Users can create, curate, and manage custom evaluation collections.

### Collection CRUD
- [ ] `POST /collections` - Create collection
- [ ] `GET /collections` - List collections
- [ ] `GET /collections/{id}` - Get collection with example count
- [ ] `PUT /collections/{id}` - Update collection metadata
- [ ] `DELETE /collections/{id}` - Delete collection

### Collection Examples
- [ ] `POST /collections/{id}/examples` - Add examples by ID
- [ ] `DELETE /collections/{id}/examples/{example_id}` - Remove example
- [ ] `POST /collections/{id}/examples/bulk` - Bulk add/remove
- [ ] `GET /collections/{id}/examples` - List examples in collection

### Search + Selection
- [ ] Search results include `in_collection` flag for active collection
- [ ] `POST /collections/{id}/examples/from-search` - Add all from search query
- [ ] Selection state in search response

### Collection Features
- [ ] Collection tags
- [ ] Collection notes/description
- [ ] Collection stats (size, subject distribution)
- [ ] Duplicate detection within collection

### Testing
- [ ] Unit tests for collection operations
- [ ] Integration tests for collection API
- [ ] System test: create collection, add examples, verify

### Success Criteria
- [ ] Can create and populate a collection from search
- [ ] Collection persists across sessions
- [ ] Bulk operations work correctly

---

## MVP-3: Export

**Goal:** Export collections to local files and external platforms.

### Local Export
- [ ] `POST /export/local` - Export to file
- [ ] JSON format export
- [ ] JSONL format export (streaming)
- [ ] CSV format export
- [ ] `GET /export/{job_id}/download` - Download exported file

### Export Jobs
- [ ] Export job model (id, status, format, progress)
- [ ] Background job processing (start with sync, add async later)
- [ ] `GET /export/jobs` - List export jobs
- [ ] `GET /export/jobs/{id}` - Get job status

### Langfuse Integration
- [ ] Langfuse client setup
- [ ] `POST /export/langfuse` - Export to Langfuse dataset
- [ ] Map collection to Langfuse dataset format
- [ ] Progress tracking for Langfuse upload
- [ ] Error handling and retry

### Arize Phoenix Integration
- [ ] Phoenix client setup
- [ ] `POST /export/phoenix` - Export to Phoenix
- [ ] Map collection to Phoenix format
- [ ] Include embeddings in export

### Testing
- [ ] Unit tests for format converters
- [ ] Integration tests for export endpoints
- [ ] Integration tests for Langfuse/Phoenix (mocked)
- [ ] System test: search → collect → export → verify file

### Success Criteria
- [ ] Can export collection to JSONL
- [ ] Can export collection to Langfuse
- [ ] Export job status is trackable

---

## MVP-4: ADK Search Agent

**Goal:** Add intelligent search with query understanding and expansion.

### Query Understanding Agent
- [ ] Agent definition in `agents/agent.py`
- [ ] Prompt in `agents/prompts/query_understanding_agent.py`
- [ ] Parse natural language queries
- [ ] Extract structured filters (dataset, subject, difficulty)
- [ ] Identify search intent

### Query Expansion Agent
- [ ] Agent definition
- [ ] Expand query with synonyms
- [ ] Add related concepts
- [ ] Generate alternative phrasings

### Result Ranking Agent
- [ ] Agent definition
- [ ] Re-rank results by relevance
- [ ] Diversify results (not all from same subject)
- [ ] Explain ranking decisions

### Search Agent Orchestration
- [ ] `SequentialAgent` combining all three
- [ ] `POST /search/agentic` - Agent-powered search
- [ ] Langfuse tracing for agent calls
- [ ] Fallback to hybrid search on agent failure

### Testing
- [ ] Agent unit tests with mocked LLM
- [ ] Integration tests for agentic search
- [ ] Quality comparison: agentic vs hybrid

### Success Criteria
- [ ] Agent search handles natural language queries
- [ ] Agent search quality >= hybrid search
- [ ] Agent traces visible in Langfuse

---

## MVP-5: Format Conversion

**Goal:** Convert collections to various evaluation framework formats.

### Predefined Converters
- [ ] OpenAI Evals format
- [ ] LangChain/LangSmith format
- [ ] Inspect AI format
- [ ] LMMS-Eval format
- [ ] Generic JSON with schema mapping

### Conversion API
- [ ] `GET /converters` - List available converters
- [ ] `POST /convert/preview` - Preview conversion on sample
- [ ] `POST /convert` - Convert full collection
- [ ] Converter validation (schema check)

### Custom Converters
- [ ] Lambda function support (sandboxed execution)
- [ ] Template-based converters (Jinja2)
- [ ] `POST /converters/custom` - Create custom converter
- [ ] Converter storage and retrieval

### LLM-Generated Converters
- [ ] Converter agent definition
- [ ] `POST /converters/generate` - Generate converter from description
- [ ] Generated code validation
- [ ] Human review before execution

### Testing
- [ ] Unit tests for each predefined converter
- [ ] Integration tests for conversion API
- [ ] Security tests for custom converter sandbox

### Success Criteria
- [ ] Can convert collection to OpenAI Evals format
- [ ] Custom converter works safely
- [ ] LLM can generate working converters

---

## MVP-6: More Datasets

**Goal:** Expand dataset coverage beyond MMLU.

### Priority Datasets
- [ ] HumanEval (code generation)
- [ ] GSM8K (math reasoning)
- [ ] HellaSwag (commonsense)
- [ ] TruthfulQA (truthfulness)
- [ ] ARC (science QA)

### Ingestion Pipeline
- [ ] Generic ingestion interface
- [ ] Dataset-specific adapters
- [ ] CLI: `uv run python -m cherry_evals.cli ingest <dataset>`
- [ ] Ingestion status tracking
- [ ] Re-ingestion support (update existing)

### Dataset Management
- [ ] `POST /datasets/ingest` - Trigger ingestion (admin only)
- [ ] `GET /datasets/{id}/status` - Ingestion status
- [ ] Dataset versioning (track updates)

### Testing
- [ ] Unit tests for each dataset adapter
- [ ] Integration tests for ingestion pipeline
- [ ] Data quality checks (schema validation)

### Success Criteria
- [ ] 5+ datasets indexed
- [ ] 50k+ examples searchable
- [ ] Ingestion is repeatable and idempotent

---

## Future: Advanced Features

### Advanced Search
- [ ] Search within collections
- [ ] Saved searches
- [ ] Search history
- [ ] Similar example discovery
- [ ] Clustering visualization

### Multi-Modal Support
- [ ] Image+text datasets (VQA, image captioning)
- [ ] Schema extension for multi-modal
- [ ] Image storage and retrieval
- [ ] Multi-modal embeddings

### Performance & Scale
- [ ] Query caching (Redis)
- [ ] Async job processing
- [ ] Batch embedding generation
- [ ] Search result caching

### RAG Backend Comparison
- [ ] Vespa integration
- [ ] Redis vector search integration
- [ ] GCP Vertex AI RAG engine
- [ ] Benchmark comparison (latency, quality, cost)
- [ ] Select winner, document decision

### Frontend (Lovable)
- [ ] Search interface
- [ ] Collection builder
- [ ] Export wizard
- [ ] User authentication

### Deployment
- [ ] Production Docker setup
- [ ] Cloud Run or similar
- [ ] CI/CD pipeline
- [ ] Monitoring and alerting

---

## Future: Monetization & Community

### Authentication & Multi-tenancy
- [ ] User authentication
- [ ] Team/organization support
- [ ] Shared collections
- [ ] Access control

### Monetization
- [ ] Free tier with limits
- [ ] Pro tier
- [ ] API access tiers

### Community
- [ ] Public collection sharing
- [ ] Community-contributed converters
- [ ] Dataset quality ratings

### Integrations
- [ ] Weights & Biases export
- [ ] MLflow export
- [ ] GitHub Actions for eval CI/CD
- [ ] Webhook destinations

---

## Philosophy

**Simple, working steps:**
- Get one thing working before adding the next
- Quality over quantity (3 good datasets > 50 broken ones)
- Ship early, iterate often

**Decision points:**
- After MVP-1: Is search quality acceptable? Iterate if not.
- After MVP-4: Is agent search better than hybrid? Keep hybrid as fallback.
- After RAG comparison: Document decision and commit.

**Success = a working tool that researchers actually use.**
