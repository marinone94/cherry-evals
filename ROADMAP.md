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
- [ ] `GET /datasets` - List all datasets
- [ ] `GET /datasets/{id}` - Get dataset details with stats
- [ ] `GET /examples` - List examples with pagination
- [ ] `GET /examples/{id}` - Get single example

### Basic Search
- [ ] `POST /search` - Keyword search (PostgreSQL full-text)
- [ ] Pagination support (offset, limit)
- [ ] Filter by dataset, subject

### Testing
- [x] Unit tests for data models
- [x] Unit tests for configuration
- [x] Integration tests for API endpoints
- [x] Integration tests for database operations
- [x] System tests for Docker Compose infrastructure
- [x] Pytest configuration with fixtures

### Success Criteria
- [ ] MMLU dataset fully ingested (~14k examples)
- [ ] Can search examples by keyword
- [ ] API returns paginated results
- [x] All tests passing
- [x] Docker Compose starts all services

---

## MVP-1: Semantic Search

**Goal:** Add vector search and hybrid search capabilities.

### Semantic Search
- [ ] `POST /search/semantic` - Vector similarity search via Qdrant
- [ ] Embedding generation on-the-fly for queries (Google text-embedding-004)
- [ ] Top-k retrieval with score threshold

### Hybrid Search
- [ ] `POST /search/hybrid` - Combined keyword + semantic
- [ ] Reciprocal Rank Fusion with configurable weights
- [ ] Result deduplication

### Search Improvements
- [ ] Filter by multiple fields (dataset, subject, difficulty)
- [ ] Sort options (relevance, date)
- [ ] Faceted search (count by subject, by dataset)

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
- [ ] `GET /collections/{id}` - Get collection with stats
- [ ] `PUT /collections/{id}` - Update collection metadata
- [ ] `DELETE /collections/{id}` - Delete collection

### Collection Examples
- [ ] `POST /collections/{id}/examples` - Add examples
- [ ] `DELETE /collections/{id}/examples/{example_id}` - Remove example
- [ ] `POST /collections/{id}/examples/bulk` - Bulk add/remove
- [ ] `GET /collections/{id}/examples` - List examples in collection

### Success Criteria
- [ ] Can create and populate a collection from search
- [ ] Collection persists across sessions
- [ ] Bulk operations work correctly

---

## MVP-3: Export

**Goal:** Export collections to local files and external platforms.

### Local Export
- [ ] JSON, JSONL, CSV format export
- [ ] Download endpoint

### Langfuse Integration
- [ ] Export collection as Langfuse dataset
- [ ] Progress tracking

### Success Criteria
- [ ] Can export collection to JSONL
- [ ] Can export collection to Langfuse

---

## MVP-4: MCP Server

**Goal:** AI agents can use Cherry Evals as a tool via MCP.

### MCP Tools
- [ ] `search_examples` - Search across datasets
- [ ] `create_collection` - Start a new collection
- [ ] `add_to_collection` - Cherry-pick examples
- [ ] `export_collection` - Export in specified format
- [ ] `list_datasets` - Available datasets

### Success Criteria
- [ ] Any MCP-compatible agent can search and curate eval sets
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
