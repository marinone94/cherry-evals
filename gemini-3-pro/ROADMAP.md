# Cherry Evals Roadmap

## Legend
- [✅] Done
- [💬] In progress
- [ ] Planned

---

## MVP 1: Core Backend & Search (Target: Q1 2025)
**Foundation for data ingestion and search**

- [ ] **Data Pipeline**
  - [ ] Scrapers/Ingestors for major public eval repositories from EleutherAI, DeepEval, BigBench, HELM
  - [ ] Data normalization schema for text evals

- [ ] **Search Engine**
  - [ ] Vector Database setup (Qdrant)
  - [ ] Embedding pipeline for eval examples
  - [ ] Hybrid search implementation (Keyword + Semantic)
  - [ ] **Deep Search Agent** (ADK): Agent to refine complex user search queries into database queries

- [ ] **Backend API**
  - [ ] FastAPI setup
  - [ ] Endpoints for search, retrieve, and listing datasets

---

## MVP 2: Curation & Transformation (Target: Q2 2025)
**Tools for building custom datasets**

- [ ] **Curation Logic**
  - [ ] Session management for user selections
  - [ ] "Shopping Cart" logic for eval examples
  - [ ] Collection management (CRUD)

- [ ] **Transformation Engine**
  - [ ] Standard format converters (Alpaca, OpenAI, ShareGPT)
  - [ ] Lambda function execution sandbox
  - [ ] **Transformation Agent** (ADK): LLM agent to write custom conversion code based on user requirements

- [ ] **Export Integrations**
  - [ ] Local file export (JSONL, CSV)
  - [ ] Langfuse API integration
  - [ ] Arize Phoenix integration

---

## MVP 3: Advanced Features & UI (Target: Q3 2025)
**Full application experience**

- [ ] **Frontend (Lovable)**
  - [ ] Web interface for search and selection
  - [ ] Dashboard for collections
  - [ ] No-code converter builder

- [ ] **Advanced RAG & Modality**
  - [ ] Compare RAG implementations (NIM vs GCP vs Qdrant)
  - [ ] Support for Image and Multi-modal evals
  - [ ] Video eval support

---

## Future
- [ ] Community sharing features
- [ ] Direct benchmark execution against endpoints
- [ ] Automated dataset improvement suggestions

