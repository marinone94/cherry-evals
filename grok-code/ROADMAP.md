# Cherry Evals Roadmap

## Legend
- [✅] Done
- [💬] In progress
- [❌] Not working
- [🔄] In review
- [ ] Planned

## MVP 0 - Core Dataset Collection & Search (Target: Dec 2025)
**Foundation: dataset ingestion, search infrastructure, and basic collection management**

- [ ] **Dataset Ingestion Pipeline**
  - [ ] Collect public evaluation datasets from EleutherAI, DeepEval, BigBench, HELM
  - [ ] Support text modality initially (expand to image/video/audio later)
  - [ ] Standardize dataset formats (JSON, CSV, HuggingFace datasets)
  - [ ] Metadata extraction (dataset name, source, task type, size, quality metrics)

- [ ] **Search Infrastructure**
  - [ ] Basic keyword search across datasets and examples
  - [ ] Semantic search using embeddings (OpenAI/Anthropic/Gemini)
  - [ ] Topic-based clustering and search
  - [ ] Search result ranking and filtering

- [ ] **Collection Management**
  - [ ] Manual selection/deselection of search results
  - [ ] Custom eval collection creation and management
  - [ ] Collection metadata (name, description, purpose, tags)
  - [ ] Basic CRUD operations for collections

- [ ] **Data Format Conversion**
  - [ ] Predefined conversion functions for standard formats (OpenAI eval, Anthropic HH, etc.)
  - [ ] Custom lambda function support (user-coded or LLM-generated)
  - [ ] Format validation and error handling
  - [ ] Preview conversion results before applying

- [ ] **Export Capabilities**
  - [ ] Local file export (JSON, CSV, YAML)
  - [ ] Langfuse integration for evaluation tracking
  - [ ] Arize Phoenix integration for model monitoring
  - [ ] Export configuration and templates

- [ ] **Backend API (FastAPI)**
  - [ ] RESTful API for all core operations
  - [ ] Dataset search endpoints
  - [ ] Collection management endpoints
  - [ ] Data conversion and export endpoints
  - [ ] Async processing for large datasets

- [ ] **Agent Integration (ADK)**
  - [ ] Deep search agent using ADK for complex queries
  - [ ] LLM-powered dataset discovery and recommendations
  - [ ] Custom conversion function generation via agents
  - [ ] Quality assessment and dataset curation agents

- [ ] **RAG Infrastructure**, one of:
  - [ ] Qdrant vector database setup for semantic search
  - [ ] Vespa RAG integration for GPU-accelerated search
  - [ ] Redis RAG integration for GPU-accelerated search
  - [ ] GCP Vertex AI RAG engine integration for GPU-accelerated search
  - [ ] Hybrid search (keyword + semantic) implementation

- [ ] **Data Storage & Persistence**
  - [ ] Local dataset storage with versioning
  - [ ] Collection metadata persistence
  - [ ] Export history and templates
  - [ ] Search query caching and optimization

- [ ] **Testing & Quality Assurance**
  - [ ] Unit tests for search, conversion, and export functions
  - [ ] Integration tests for API endpoints
  - [ ] Dataset quality validation tests
  - [ ] Performance benchmarks for search operations

---

## MVP 0.5 - Enhanced Search & Collections (Target: Jan 2026)
**Advanced search features and collection workflows**

- [ ] **Advanced Search Features**
  - [ ] Multi-modal search expansion (beyond text)
  - [ ] Cross-dataset search with result aggregation
  - [ ] Search result clustering and summarization
  - [ ] Saved search queries and templates

- [ ] **Collection Workflows**
  - [ ] Bulk selection/deselection operations
  - [ ] Collection sharing and collaboration features
  - [ ] Collection versioning and change tracking
  - [ ] Automated quality scoring for collections

- [ ] **Data Processing Pipeline**
  - [ ] Batch conversion for large datasets
  - [ ] Data validation and cleaning agents
  - [ ] Duplicate detection and removal
  - [ ] Data augmentation capabilities

- [ ] **Integration Enhancements**
  - [ ] Additional export targets (Weights & Biases, Comet ML)
  - [ ] API rate limiting and usage monitoring
  - [ ] Background job processing for long-running tasks

---

## MVP 1 - Production Ready (Target: Feb-Mar 2026)
**Scalability, reliability, and user experience polish**

- [ ] **Scalability & Performance**
  - [ ] Distributed search across multiple nodes
  - [ ] Caching layers for frequently accessed datasets
  - [ ] Optimized storage formats for large datasets
  - [ ] Horizontal scaling for API endpoints

- [ ] **Quality & Reliability**
  - [ ] Comprehensive dataset validation pipeline
  - [ ] Automated quality metrics calculation
  - [ ] Error recovery and retry mechanisms
  - [ ] Data backup and disaster recovery

- [ ] **Advanced Features**
  - [ ] Custom evaluation metric calculation
  - [ ] Comparative analysis across collections
  - [ ] Dataset drift detection and monitoring
  - [ ] Automated dataset curation suggestions

- [ ] **API & Integration**
  - [ ] GraphQL API for complex queries
  - [ ] Webhook support for real-time updates
  - [ ] OAuth integration for third-party services
  - [ ] SDK for programmatic access

---

## MVP 2 - Multi-Modal & Advanced Analytics (Target: Apr-May 2026)
**Expanding beyond text and adding advanced analytics**

- [ ] **Multi-Modal Support**
  - [ ] Image evaluation datasets (classification, captioning, etc.)
  - [ ] Video evaluation datasets (action recognition, video QA)
  - [ ] Audio evaluation datasets (speech recognition, audio classification)
  - [ ] Multi-modal evaluation datasets

- [ ] **Advanced Analytics**
  - [ ] Dataset difficulty analysis and stratification
  - [ ] Model performance prediction and simulation
  - [ ] Bias detection and fairness analysis
  - [ ] Cross-dataset performance correlation

- [ ] **Collaborative Features**
  - [ ] Team workspaces and permissions
  - [ ] Collection review and approval workflows
  - [ ] Dataset contribution and sharing platform
  - [ ] Community-driven dataset curation

---

## MVP 3 - Enterprise & Scale (Target: Jun-Jul 2026)
**Enterprise features and large-scale deployment**

- [ ] **Enterprise Features**
  - [ ] SSO integration and enterprise security
  - [ ] Audit logs and compliance reporting
  - [ ] Custom dataset hosting and management
  - [ ] Priority support and SLAs

- [ ] **Scale & Performance**
  - [ ] Petabyte-scale dataset handling
  - [ ] Real-time search with sub-second latency
  - [ ] Global CDN for dataset distribution
  - [ ] Advanced caching and optimization

- [ ] **AI-Powered Features**
  - [ ] Automated dataset discovery and ingestion
  - [ ] Intelligent data quality assessment
  - [ ] Predictive analytics for evaluation trends
  - [ ] Auto-generated custom evaluation suites

---

## Future Enhancements (Post-MVP)

### Advanced AI Integration
- [ ] LLM-powered dataset generation and synthesis
- [ ] Automated evaluation pipeline creation
- [ ] Intelligent dataset recommendations
- [ ] Meta-evaluation capabilities

### Platform Extensions
- [ ] Mobile application for dataset browsing
- [ ] Browser extensions for easy dataset collection
- [ ] Integration with popular ML frameworks
- [ ] Plugin architecture for custom tools

### Research & Innovation
- [ ] Novel evaluation methodologies
- [ ] Cross-modal evaluation techniques
- [ ] Longitudinal evaluation tracking
- [ ] Evaluation benchmark standardization

---

## Technical Debt & Infrastructure

### Code Quality
- [ ] Comprehensive test coverage (>90%)
- [ ] Performance benchmarking suite
- [ ] Security audit and penetration testing
- [ ] Code documentation and API reference

### Infrastructure
- [ ] CI/CD pipeline with automated testing
- [ ] Monitoring and alerting system
- [ ] Disaster recovery and backup systems
- [ ] Multi-region deployment capability

### Community & Ecosystem
- [ ] Open-source dataset contributions
- [ ] Community forum and support channels
- [ ] Documentation and tutorial library
- [ ] Academic and research partnerships

---

## Timeline Philosophy

**Quality over speed:**
- Core search and collection functionality must be rock-solid
- Performance benchmarks must be met before scaling
- Better to launch with fewer features than with bugs

**Decision points:**
- Dec 2025: Core dataset collection working → proceed to search features
- Jan 2026: Basic collections working → expand to advanced workflows
- Feb 2026: Production ready → plan multi-modal expansion
- Mar 2026: User feedback received → iterate or scale

**Success metrics:**
- MVP 0: Developers can easily find and collect evaluation datasets
- MVP 1: Teams can create and manage custom evaluation suites
- MVP 2: Organizations can run comprehensive model evaluations
- MVP 3: Industry standard for evaluation dataset management

**Remember:** Start with text, perfect the experience, then expand modalities.
