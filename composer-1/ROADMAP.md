# Cherry-evals Roadmap

## Legend
- [✅] Done
- [💬] In progress
- [❌] Not working
- [🔄] In review
- [ ] Planned

## MVP 0 - Core Dataset Collection & Search (Target: TBD)
**Foundation: dataset collection, indexing, and basic search**

- [ ] **Dataset Collection**
  - [ ] Identify public eval datasets from EleutherAI, DeepEval, BigBench, HELM
  - [ ] Implement dataset ingestion pipeline
  - [ ] Parse common eval formats (JSONL, CSV, etc.)
  - [ ] Extract and store metadata (source, date, model tested, metrics)

- [ ] **Data Storage & Indexing**
  - [ ] Set up vector database (Qdrant/Vespa/Redis/GCP Vertex AI RAG engine, try one) for semantic search
  - [ ] Index dataset examples with embeddings
  - [ ] Store metadata and collections in JSON files
  - [ ] Version tracking for datasets

- [ ] **Basic Search**
  - [ ] Keyword search implementation
  - [ ] Semantic search via vector database
  - [ ] Topic-based clustering (basic)
  - [ ] Search result ranking and filtering

- [ ] **ADK Agent Integration**
  - [ ] Deep search agent using ADK
  - [ ] LLM-powered query understanding and expansion
  - [ ] Agent orchestration for complex searches

- [ ] **Backend API (FastAPI)**
  - [ ] Dataset endpoints (list, get, search)
  - [ ] Collection endpoints (create, update, delete)
  - [ ] Search endpoints (keyword, semantic, hybrid)
  - [ ] Basic error handling and validation

- [ ] **Testing**
  - [ ] Unit tests for dataset ingestion
  - [ ] Integration tests for search functionality
  - [ ] System tests for end-to-end workflows

---

## MVP 0.5 - Collection Management & Format Conversion (Target: TBD)
**2-3 weeks to add curation and conversion features**

- [ ] **Collection Management**
  - [ ] Create custom eval collections
  - [ ] Add/remove examples from collections
  - [ ] Collection metadata (name, description, tags)
  - [ ] Collection persistence and retrieval

- [ ] **Format Conversion**
  - [ ] Predefined converters:
    - [ ] JSONL format
    - [ ] CSV format
    - [ ] Langfuse format
    - [ ] Arize Phoenix format
  - [ ] Custom lambda function support
  - [ ] LLM-generated converter functions
  - [ ] Conversion validation and error handling

- [ ] **Export Functionality**
  - [ ] Export to local filesystem
  - [ ] Export to Langfuse
  - [ ] Export to Arize Phoenix
  - [ ] Batch export operations

- [ ] **UI Integration (Lovable)**
  - [ ] Search interface
  - [ ] Collection builder UI
  - [ ] Export interface
  - [ ] Basic navigation

- [ ] **Testing**
  - [ ] Test collection operations
  - [ ] Test format conversions
  - [ ] Test export workflows
  - [ ] Integration with Lovable frontend

---

## MVP 1 - Advanced Search & RAG Comparison (Target: TBD)
**Enhanced search capabilities and RAG backend evaluation**

- [ ] **Advanced Search**
  - [ ] Hybrid search (keyword + semantic + topic)
  - [ ] Advanced filtering (dataset, model, metric, date)
  - [ ] Search result faceting
  - [ ] Saved searches

- [ ] **RAG Backend Comparison**
  - [ ] Implement Qdrant integration
  - [ ] Implement Vespa RAG integration
  - [ ] Implement Redis RAG integration
  - [ ] Implement GCP Vertex AI RAG engine integration
  - [ ] Performance benchmarking
  - [ ] Feature comparison
  - [ ] Documentation of trade-offs

- [ ] **Agent Enhancements**
  - [ ] Multi-agent search orchestration
  - [ ] LLM-powered query refinement
  - [ ] Intelligent collection suggestions
  - [ ] Conversion function generation

- [ ] **Backend Improvements**
  - [ ] Caching for search results
  - [ ] Pagination and result limits
  - [ ] Rate limiting
  - [ ] Performance optimization

- [ ] **Testing**
  - [ ] Compare RAG backends
  - [ ] Test advanced search features
  - [ ] Performance testing
  - [ ] Load testing

---

## MVP 2 - Multi-Modal Support (Target: TBD)
**Expand beyond text to support images, audio, video**

- [ ] **Multi-Modal Dataset Collection**
  - [ ] Image-based evaluations
  - [ ] Audio evaluations
  - [ ] Video evaluations
  - [ ] Multi-modal (text + image, etc.)

- [ ] **Multi-Modal Search**
  - [ ] Image similarity search
  - [ ] Audio similarity search
  - [ ] Cross-modal search (text → image, etc.)

- [ ] **Multi-Modal Conversion**
  - [ ] Format converters for multi-modal data
  - [ ] Custom converters for multi-modal formats

- [ ] **Backend Updates**
  - [ ] Multi-modal embedding support
  - [ ] Storage for binary assets
  - [ ] Efficient retrieval of multi-modal examples

- [ ] **Testing**
  - [ ] Test multi-modal ingestion
  - [ ] Test multi-modal search
  - [ ] Test multi-modal conversion

---

## MVP 3 - Advanced Features & Polish (Target: TBD)
**Production-ready features and optimizations**

- [ ] **Dataset Management**
  - [ ] Automatic dataset updates
  - [ ] Dataset versioning and diff
  - [ ] Dataset quality metrics
  - [ ] Dataset recommendations

- [ ] **Collection Features**
  - [ ] Collection templates
  - [ ] Collection sharing (export/import)
  - [ ] Collection analytics
  - [ ] Collection collaboration (future)

- [ ] **Conversion Enhancements**
  - [ ] Conversion pipeline builder
  - [ ] Conversion testing and validation
  - [ ] Conversion performance optimization
  - [ ] Pre-built conversion templates

- [ ] **Observability & Monitoring**
  - [ ] Langfuse integration for tracing
  - [ ] Performance metrics
  - [ ] Usage analytics
  - [ ] Error tracking and reporting

- [ ] **Documentation**
  - [ ] API documentation
  - [ ] User guides
  - [ ] Developer documentation
  - [ ] Example workflows

- [ ] **Testing & Quality**
  - [ ] Comprehensive test coverage
  - [ ] Performance benchmarks
  - [ ] Security audit
  - [ ] User acceptance testing

---

## Future Enhancements

### Collaboration Features
- [ ] Team workspaces
- [ ] Collection sharing and collaboration
- [ ] Comments and annotations on examples
- [ ] Version control for collections

### Advanced Analytics
- [ ] Dataset comparison tools
- [ ] Evaluation result visualization
- [ ] Trend analysis across datasets
- [ ] Model performance tracking

### Integration Ecosystem
- [ ] More export targets (Weights & Biases, MLflow, etc.)
- [ ] API integrations with eval platforms
- [ ] Webhook support
- [ ] CLI tool

### Performance & Scale
- [ ] Distributed search
- [ ] Caching strategies
- [ ] CDN for dataset assets
- [ ] Horizontal scaling

---

## Timeline Philosophy

**Flexibility built in:**
- Core functionality is non-negotiable
- Features can be prioritized based on user feedback
- Better to launch small and solid than big and broken

**Decision points:**
- MVP 0: Is dataset collection and search working? → Yes: add curation, No: focus on core
- MVP 0.5: Are collections and conversions working? → Yes: add advanced features, No: iterate
- MVP 1: Is RAG comparison complete? → Yes: choose backend, No: continue evaluation

**Success metrics:**
- MVP 0: Can search and find relevant eval examples
- MVP 0.5: Can build and export custom collections
- MVP 1: Search is fast and accurate with chosen RAG backend
- MVP 2: Multi-modal datasets are supported
- MVP 3: Production-ready and user-friendly

**Remember:** Build, ship, test, repeat.

