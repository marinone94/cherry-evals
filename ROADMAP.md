# Cherry Evals Roadmap

## Legend
- [x] Done
- [~] In progress
- [ ] Planned

---

## MVP-0: Foundation

**Goal:** Get one dataset searchable end-to-end with basic API.

### Infrastructure Setup
- [x] Initialize uv project with `pyproject.toml`
- [x] FastAPI project scaffold
- [x] PostgreSQL setup with SQLAlchemy models
- [x] Alembic migrations setup
- [x] Qdrant vector database setup (local Docker)
- [x] Docker Compose for local development (Postgres, Qdrant)
- [x] Pre-commit hooks (ruff check, ruff format)
- [x] Environment configuration (`.env.example`, `pydantic-settings`)

### Data Models
- [x] `Example` schema (question, answer, choices, example_metadata)
- [x] `Dataset` schema (name, source, license, task_type, description, stats)
- [x] `Collection` schema (name, description, user_id, created_at)
- [x] `CollectionExample` join table

### First Dataset: MMLU
- [x] Download MMLU from HuggingFace
- [x] Parse and normalize to internal `Example` schema
- [x] Extract metadata (subject, split, difficulty)
- [x] Store examples in PostgreSQL
- [~] Generate embeddings (migrating from OpenAI to Google text-embedding-004)
- [x] Index embeddings in Qdrant
- [x] Ingestion CLI command

### Basic API Endpoints
- [x] `GET /health` - Health check
- [x] `GET /datasets` - List all datasets
- [x] `GET /datasets/{id}` - Get dataset details with stats
- [x] `GET /examples` - List examples with pagination
- [x] `GET /examples/{id}` - Get single example

### Basic Search
- [x] `POST /search` - Keyword search (PostgreSQL ILIKE)
- [x] Pagination support (offset, limit)
- [x] Filter by dataset, subject

### Testing
- [x] Unit tests for data models
- [x] Unit tests for configuration
- [x] Integration tests for API endpoints
- [x] Integration tests for database operations
- [x] System tests for Docker Compose infrastructure
- [x] Pytest configuration with fixtures

### Success Criteria
- [ ] MMLU dataset fully ingested (~14k examples)
- [x] Can search examples by keyword
- [x] API returns paginated results
- [x] All tests passing
- [x] Docker Compose starts all services

---

## MVP-1: Semantic Search

**Goal:** Add vector search and hybrid search capabilities.

### Semantic Search
- [x] `POST /search/semantic` - Vector similarity search via Qdrant
- [x] Embedding generation on-the-fly for queries (Google text-embedding-004)
- [x] Top-k retrieval with score threshold

### Hybrid Search
- [x] `POST /search/hybrid` - Combined keyword + semantic
- [x] Reciprocal Rank Fusion with configurable weights
- [x] Result deduplication

### Search Improvements
- [ ] Filter by multiple fields (dataset, subject, difficulty)
- [ ] Sort options (relevance, date)
- [ ] Faceted search (count by subject, by dataset)

### Testing
- [x] Unit tests for search functions (RRF)
- [x] Integration tests for search endpoints
- [ ] Search quality evaluation (manual spot checks)

### Success Criteria
- [x] Semantic search returns relevant results
- [x] Hybrid search improves over keyword-only
- [ ] Search latency <500ms for semantic, <100ms for keyword

---

## MVP-2: Collections

**Goal:** Users can create, curate, and manage custom evaluation collections.

### Collection CRUD
- [x] `POST /collections` - Create collection
- [x] `GET /collections` - List collections
- [x] `GET /collections/{id}` - Get collection with stats
- [x] `PUT /collections/{id}` - Update collection metadata
- [x] `DELETE /collections/{id}` - Delete collection

### Collection Examples
- [x] `POST /collections/{id}/examples` - Add examples
- [x] `DELETE /collections/{id}/examples/{example_id}` - Remove example
- [x] `POST /collections/{id}/examples/bulk-remove` - Bulk remove
- [x] `GET /collections/{id}/examples` - List examples in collection

### Success Criteria
- [x] Can create and populate a collection from search
- [x] Collection persists across sessions
- [x] Bulk operations work correctly

---

## MVP-3: Export

**Goal:** Export collections to local files and external platforms.

### Local Export
- [x] JSON, JSONL, CSV format export
- [x] Download endpoint with Content-Disposition headers

### Langfuse Integration
- [x] Export collection as Langfuse dataset
- [x] Graceful error when credentials not configured

### Success Criteria
- [x] Can export collection to JSON, JSONL, CSV
- [x] Can export collection to Langfuse

---

## MVP-4: MCP Server

**Goal:** AI agents can use Cherry Evals as a tool via MCP.

### MCP Tools
- [x] `search_examples` - Search across datasets (keyword)
- [x] `create_collection` - Start a new collection
- [x] `add_to_collection` - Cherry-pick examples
- [x] `export_collection` - Export in specified format (JSON/JSONL/CSV)
- [x] `list_datasets` - Available datasets
- [x] `get_dataset` - Dataset details
- [x] `list_collections` - List existing collections
- [x] `get_collection` - Collection details with examples

### Success Criteria
- [x] Any MCP-compatible agent can search and curate eval sets
- [ ] Agent usage generates curation traces for collective intelligence

---

## MVP-5: Frontend

**Goal:** Web UI for visual browsing, search, and collection management.

### Core UI
- [ ] Search interface with filters
- [ ] Example detail view
- [ ] Collection builder (drag-and-drop or click-to-add)
- [ ] Export wizard

### Tech
- [ ] React + Tailwind
- [ ] Connected to REST API

### Success Criteria
- [ ] Non-technical researchers can use Cherry Evals through the browser

---

## MVP-6: More Datasets

**Goal:** Expand beyond MMLU.

### Priority Datasets
- [ ] HumanEval (code generation)
- [ ] GSM8K (math reasoning)
- [ ] HellaSwag (commonsense)
- [ ] TruthfulQA (truthfulness)
- [ ] ARC (science QA)

### Ingestion Pipeline
- [ ] Generic ingestion interface
- [ ] Dataset-specific adapters
- [ ] Re-ingestion support

### Success Criteria
- [ ] 5+ datasets indexed
- [ ] 50k+ examples searchable

---

## MVP-7: Intelligent Search (Agent-Powered)

**Goal:** LLM-powered query understanding and result ranking.

### Query Understanding
- [ ] Parse natural language queries
- [ ] Extract structured filters
- [ ] Query expansion with related concepts

### Result Ranking
- [ ] Re-rank results by relevance and diversity
- [ ] Explain ranking decisions

### Success Criteria
- [ ] Natural language queries return high-quality results
- [ ] Agent search quality >= hybrid search

---

## Future: Collective Intelligence

### Curation Traces
- [ ] Track search → pick → export flows
- [ ] Co-selection pattern detection
- [ ] Quality signals from pick rates

### Recommendations
- [ ] "Others also picked" suggestions
- [ ] Collection gap detection
- [ ] Improved ranking from usage data

---

## Future: Production & Monetization

### Auth & Multi-tenancy
- [ ] User authentication
- [ ] Team/organization support
- [ ] Shared collections

### Deployment
- [ ] Production Docker setup
- [ ] Cloud deployment (Cloud Run or similar)
- [ ] CI/CD pipeline

### Monetization
- [ ] Free tier with limits
- [ ] Pro tier
- [ ] API access tiers

---

## Philosophy

**Simple, working steps:**
- Get one thing working before adding the next
- Quality over quantity
- Ship early, iterate often

**Data flywheel > intelligence moat:**
- Every interaction is a signal
- Collective curation intelligence is the real product
- The managed version wins on accumulated wisdom

**Success = researchers and AI agents use Cherry Evals as their default eval curation tool.**
