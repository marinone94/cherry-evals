# cherry-evals Roadmap

## Legend
- [✅] Done
- [💬] In progress
- [❌] Not working
- [🔄] In review
- [ ] Planned

---

## Phase 0 - Foundation (Target: 2 weeks)
**Infrastructure, data models, and first dataset**

### Infrastructure Setup
- [ ] FastAPI project scaffold
- [ ] PostgreSQL setup with Alembic migrations
- [ ] Qdrant vector database setup
- [ ] Docker Compose for local development
- [ ] Pre-commit hooks (ruff, uv lock)

### Data Models
- [ ] Eval example schema (question, answer, metadata)
- [ ] Dataset schema (source, license, task type, stats)
- [ ] Collection schema (name, description, examples)
- [ ] Export job schema (format, destination, status)

### First Dataset Ingestion
- [ ] MMLU dataset ingestion pipeline
- [ ] Raw data download and caching
- [ ] Normalization to internal schema
- [ ] Metadata extraction (subject, difficulty)
- [ ] Embedding generation for semantic search
- [ ] Index in Qdrant

### Basic API
- [ ] `GET /datasets` - List all datasets
- [ ] `GET /datasets/{id}` - Get dataset details
- [ ] `GET /examples` - List examples with pagination
- [ ] `GET /examples/{id}` - Get single example

---

## Phase 1 - Search (Target: 2 weeks)
**Keyword, semantic, and hybrid search**

### Option 1 - [Qdrant](https://qdrant.tech/) Search Infrastructure
- [ ] Qdrant collection setup with proper indexes
- [ ] Embedding model selection and integration
- [ ] Full-text search with PostgreSQL

### Option 2 - [Redis](https://redis.io/) Search Infrastructure
- [ ] Redis collection setup with proper indexes
- [ ] Embedding model selection and integration
- [ ] Full-text search with Redis

### Option 3 - [Vespa](https://vespa.ai/) Search Infrastructure
- [ ] Vespa collection setup with proper indexes
- [ ] Embedding model selection and integration
- [ ] Full-text search with Vespa

### Option 4 - GCP Vertex AI [RAG engine](https://docs.cloud.google.com/vertex-ai/generative-ai/docs/rag-engine/rag-overview)
- [ ] GCP Vertex AI RAG engine setup with proper indexes
- [ ] Full-text search with PostgreSQL

### Search Endpoints
- [ ] `POST /search/keyword` - Traditional text search
- [ ] `POST /search/semantic` - Vector similarity search
- [ ] `POST /search/hybrid` - Combined search with configurable weights
- [ ] Search result pagination and sorting
- [ ] Faceted search (by dataset, task type, difficulty)

### ADK Search Agent
- [ ] Query understanding agent
- [ ] Query expansion/refinement suggestions
- [ ] Natural language to structured query conversion

### RAG Comparison
- [ ] Benchmark comparison (latency, quality, cost)
- [ ] Select winner for production use

---

## Phase 2 - Collections (Target: 2 weeks)
**Custom eval collection management**

### Collection CRUD
- [ ] `POST /collections` - Create collection
- [ ] `GET /collections` - List user collections
- [ ] `GET /collections/{id}` - Get collection details
- [ ] `PUT /collections/{id}` - Update collection metadata
- [ ] `DELETE /collections/{id}` - Delete collection

### Collection Examples
- [ ] `POST /collections/{id}/examples` - Add examples to collection
- [ ] `DELETE /collections/{id}/examples` - Remove examples
- [ ] `POST /collections/{id}/examples/bulk` - Bulk add/remove
- [ ] `GET /collections/{id}/examples` - List collection examples

### Selection UI Support
- [ ] Search results include selection state
- [ ] Persist selection state in session
- [ ] Select/deselect all matching current query
- [ ] Exclude examples by pattern

### Collection Features
- [ ] Tags and notes on collections
- [ ] Collection versioning (save snapshots)
- [ ] Duplicate/fork collections
- [ ] Collection statistics (size, coverage, distribution)

---

## Phase 3 - Export (Target: 2 weeks)
**Export to local, Langfuse, Arize Phoenix**

### Local Export
- [ ] JSON file export
- [ ] JSONL file export (streaming for large datasets)
- [ ] CSV file export
- [ ] Parquet file export
- [ ] ZIP archive with metadata

### Langfuse Integration
- [ ] Langfuse API client
- [ ] Dataset creation in Langfuse
- [ ] Example upload with metadata
- [ ] Export progress tracking
- [ ] Error handling and retry

### Arize Phoenix Integration
- [ ] Phoenix API client
- [ ] Dataset creation in Phoenix
- [ ] Example upload with embeddings
- [ ] Export progress tracking

### Export API
- [ ] `POST /export/local` - Export to local file
- [ ] `POST /export/langfuse` - Export to Langfuse
- [ ] `POST /export/phoenix` - Export to Arize Phoenix
- [ ] `GET /export/jobs` - List export jobs
- [ ] `GET /export/jobs/{id}` - Get export job status
- [ ] `GET /export/jobs/{id}/download` - Download local export


---

## Phase 4 - Format Conversion (Target: 2 weeks)
**Convert evals to any format**

### Predefined Converters
- [ ] OpenAI Evals format converter
- [ ] LangChain/LangSmith format converter
- [ ] Inspect AI format converter
- [ ] LMMS-Eval format converter
- [ ] Generic JSON/JSONL with custom schema
- [ ] CSV export

### Custom Converters
- [ ] Lambda function definition UI (code editor)
- [ ] Lambda validation and sandboxed execution
- [ ] LLM-generated converters from natural language
- [ ] Template-based converters (Jinja2)
- [ ] Converter library (save and reuse)

### Conversion API
- [ ] `GET /converters` - List available converters
- [ ] `POST /converters` - Create custom converter
- [ ] `POST /convert/preview` - Preview conversion on sample
- [ ] `POST /convert` - Convert full collection

---

## Phase 5 - More Datasets (Target: 3 weeks)
**Expand dataset coverage**

### Priority Datasets
- [ ] HumanEval - Code generation
- [ ] GSM8K - Math reasoning
- [ ] HellaSwag - Commonsense
- [ ] TruthfulQA - Truthfulness
- [ ] ARC - Science QA
- [ ] WinoGrande - Coreference

### Additional Datasets
- [ ] BIG-Bench (selected tasks)
- [ ] MATH
- [ ] DROP
- [ ] SQuAD
- [ ] HuggingFace Hub integration (top datasets)

### Multi-Modal Support
- [ ] Image+text datasets (VQA, image captioning)
- [ ] Dataset schema extension for multi-modal
- [ ] Storage for images/media
- [ ] Preview support for images

### Ingestion Pipeline
- [ ] Automated ingestion scheduler
- [ ] New dataset detection (HuggingFace, papers)
- [ ] Community dataset requests
- [ ] Dataset quality checks

---

## Phase 6 - Advanced Features (Target: 4 weeks)
**Power user features and optimizations**

### Advanced Search
- [ ] Search within collections
- [ ] Saved searches
- [ ] Search history
- [ ] Similar example discovery
- [ ] Clustering visualization

### Advanced Collections
- [ ] Collection comparison (diff view)
- [ ] Smart deduplication across collections
- [ ] Auto-tagging with LLM
- [ ] Difficulty estimation
- [ ] Coverage analysis (what's missing)

### Performance
- [ ] Query caching (Redis)
- [ ] Async job processing (Celery/ARQ)
- [ ] Batch embedding generation
- [ ] Search result caching

### API Improvements
- [ ] GraphQL API (optional)
- [ ] Webhook notifications
- [ ] Rate limiting
- [ ] API versioning

---

## Future Considerations

### Authentication & Multi-tenancy
- [ ] User authentication (to be built in Lovable)
- [ ] Team/organization support
- [ ] Shared collections
- [ ] Access control for collections

### Monetization
- [ ] Free tier with limits
- [ ] Pro tier with higher limits
- [ ] Enterprise tier with SLA
- [ ] API access tiers

### Community
- [ ] Public collection sharing
- [ ] Leaderboard of popular collections
- [ ] Dataset quality ratings
- [ ] Community-contributed converters

### Integrations
- [ ] GitHub Actions for eval CI/CD
- [ ] Weights & Biases export
- [ ] MLflow export
- [ ] Custom webhook destinations

---

## Success Metrics

### Phase 0-1 (Foundation)
- [ ] 1 dataset fully searchable (MMLU)
- [ ] <100ms keyword search latency
- [ ] <500ms semantic search latency

### Phase 2-3 (Collections & Conversion)
- [ ] Create and export a custom collection end-to-end
- [ ] All predefined converters working
- [ ] Custom lambda converter working

### Phase 4-5 (Export & Datasets)
- [ ] Successful export to Langfuse
- [ ] Successful export to Arize Phoenix
- [ ] 10+ datasets indexed
- [ ] 100k+ examples searchable

### Phase 6+ (Scale)
- [ ] <200ms hybrid search at 1M examples
- [ ] 50+ active users
- [ ] 100+ custom collections created

---

## Timeline Philosophy

**Flexibility built in:**
- Core search must work well before adding datasets
- Quality over quantity for initial datasets
- API stability before adding integrations

**Decision points:**
- After Phase 1: Is search quality good enough? → Yes: continue, No: iterate
- After Phase 3: Are converters flexible enough? → Yes: continue, No: add more options
- After Phase 5: Which RAG solution won? → Document and commit

**Remember:** Ship early, iterate often. A working search on 3 datasets beats a broken search on 50.

