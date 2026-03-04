# Cherry Evals — Deployment Plan & Budget Forecast

## TL;DR

We can deploy Cherry Evals to production for **$0/month** using free tiers, scaling to ~$25/month when we outgrow them. The recommended stack is Cloudflare Pages (landing + frontend), Google Cloud Run (API), Neon (Postgres), Qdrant Cloud (vectors), Grafana Cloud (monitoring).

---

## Phase 1: Launch ($0/month)

Get live on free tiers. Prove the product works before spending money.

| Service | Provider | Free Tier | Limit |
|---------|----------|-----------|-------|
| Landing page | Cloudflare Pages | Unlimited bandwidth | 500 builds/month |
| Frontend | Cloudflare Pages | Same account | Same |
| API | Google Cloud Run | 2M requests/month, 180k vCPU-sec | ~1 always-on instance |
| PostgreSQL | Neon | 0.5 GB storage, 100 CU-hours | Auto-suspends on idle |
| Vector DB | Qdrant Cloud | 1 GB RAM cluster | ~50k vectors |
| Embeddings | Google Gemini API | Free for text-embedding | Rate limited |
| LLM (agents) | Google Gemini API | Gemini Flash free tier | 15 RPM |
| Monitoring | Grafana Cloud | 10k metrics, 50GB logs | Generous |
| DNS | Cloudflare | Free | — |
| SSL | Cloudflare | Free | — |

**What this supports:** ~100 daily active users, ~10k searches/day, full dataset (~50k examples in Qdrant, unlimited in Postgres via Neon's suspend).

### Limitations at $0
- Cloud Run cold starts (~2-3s first request after idle)
- Neon suspends after inactivity (~5s wake-up)
- Qdrant 1 GB cap → fits ~50k embeddings (our 10 datasets are ~100k+, so we'd need to prioritize which datasets get embeddings, or use Qdrant's quantization)
- Gemini free tier: 15 requests/minute → agentic search may queue
- No redundancy, single region

---

## Phase 2: Growth (~$25/month)

When free tiers become limiting. Triggered by: sustained daily usage, cold start complaints, or vector storage limits.

| Service | Provider | Plan | Cost/month |
|---------|----------|------|-----------|
| API | Cloud Run | Pay-as-you-go past free tier | ~$5 |
| PostgreSQL | Neon | Launch ($19) — 10GB, always-on | $19 |
| Vector DB | Qdrant Cloud | Pay-as-you-go past 1GB | ~$5 |
| LLM | Gemini Flash | $0.10/M input, $0.40/M output | ~$1 |
| Others | Same free tiers | — | $0 |

**What this supports:** ~1k DAU, ~100k searches/day, all datasets embedded.

---

## Phase 3: Scale (~$100-200/month)

When we have real traction. Triggered by: >1k DAU or enterprise interest.

| Service | Change | Cost/month |
|---------|--------|-----------|
| API | Cloud Run with min instances (no cold starts) | ~$30 |
| PostgreSQL | Neon Scale ($69) or Supabase Pro ($25) | $25-69 |
| Vector DB | Qdrant Cloud dedicated | ~$50 |
| LLM | Higher throughput | ~$10 |
| Monitoring | Grafana Pro (if needed) | $0-29 |

---

## Cost Drivers & Projections

### LLM API Costs (Gemini Flash 2.0)
- Query understanding: ~500 tokens in, ~200 out per search
- Agentic search (3 iterations): ~3k tokens in, ~1k out
- Agentic ingestion: ~2k tokens in, ~1k out
- Agentic export: ~1k tokens in, ~500 out

At **1,000 searches/day** (mix of keyword and agentic):
- ~30% use agentic search → 300 × 4k tokens = 1.2M tokens/day
- Monthly: ~36M input tokens + ~12M output tokens
- Cost: $3.60 input + $4.80 output = **~$8.40/month**
- With free tier: probably **$0-2/month** for a while

### Embedding Costs
- text-embedding-004 is free via Gemini API (but see migration note below)
- 100k examples × ~100 tokens each = 10M tokens one-time
- Cost: **$0** (free tier) or **$1** on paid tier

### Storage Costs
- PostgreSQL: 10 datasets × ~100k examples = ~50MB (trivial)
- Qdrant: 100k vectors × 768 dims × 4 bytes = ~300MB
- Both well within free tiers for Phase 1

---

## ⚠️ URGENT: Embedding Model Migration

**`text-embedding-004` was scheduled for discontinuation on November 18, 2025.**

We are currently using it. We need to migrate to one of:
1. **`text-embedding-005`** — drop-in replacement, same API
2. **`gemini-embedding-001`** — newer, may have better quality

**Impact:** All existing embeddings in Qdrant need to be regenerated (you can't mix embedding models). This is a one-time operation.

**Action required:** Migrate before first deployment. Update `cherry_evals/config.py` and `cherry_evals/embeddings/` to use the new model.

---

## Recommended Deployment Architecture

```
                    ┌─────────────────────┐
                    │   Cloudflare DNS     │
                    │   cherryevals.com    │
                    └──────┬──────────────┘
                           │
              ┌────────────┼────────────────┐
              │            │                │
              ▼            ▼                ▼
     ┌───────────┐  ┌───────────┐  ┌──────────────┐
     │ CF Pages  │  │ CF Pages  │  │  Cloud Run   │
     │ Landing   │  │ Frontend  │  │  API + MCP   │
     │ /         │  │ /app      │  │  /api        │
     └───────────┘  └───────────┘  └──────┬───────┘
                                          │
                              ┌───────────┼───────────┐
                              │           │           │
                              ▼           ▼           ▼
                       ┌──────────┐ ┌──────────┐ ┌────────┐
                       │   Neon   │ │  Qdrant  │ │ Gemini │
                       │ Postgres │ │  Cloud   │ │  API   │
                       └──────────┘ └──────────┘ └────────┘
```

### Why this stack?

- **Cloudflare Pages** — unlimited bandwidth, instant deploys from GitHub, free SSL, global CDN
- **Cloud Run** — scales to zero (pay nothing when idle), Docker-ready (we have the Dockerfile), $300 free credits for new accounts
- **Neon** — serverless Postgres that auto-suspends, generous free tier, compatible with SQLAlchemy
- **Qdrant Cloud** — managed vector DB, 1GB free, same API as local
- **Grafana Cloud** — industry standard, free tier is genuinely generous

### Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Fly.io | Good DX, Machines API | No hobby plan for new customers, managed PG starts at $38/month |
| Railway | Simple, good free tier | $5/month after trial, less mature |
| Supabase | Postgres + auth bundled | We don't need auth yet, 500MB limit |
| Self-hosted (VPS) | Full control | $5-10/month even when idle, ops burden |

---

## Monitoring Dashboard Plan

### Grafana Cloud (free tier)

**Infrastructure metrics:**
- Cloud Run request count, latency (p50/p95/p99), error rate
- Neon connection count, query time, storage usage
- Qdrant search latency, collection sizes, memory usage

**Application metrics** (via FastAPI middleware → Prometheus):
- Search requests by mode (keyword/hybrid/intelligent/agent)
- Search latency by mode
- Ingestion events (dataset, examples/sec)
- Export events by format
- LLM call latency and error rate
- Agentic search iterations per query

**Business metrics** (via curation events table):
- DAU (unique session_ids)
- Searches per day
- Pick rate (picks / search impressions)
- Collections created per day
- Exports per day by format
- Popular datasets and subjects

**Alerts:**
- API error rate > 5% → Slack/email
- Search latency p95 > 2s → investigate
- Qdrant storage > 80% of limit → plan upgrade
- LLM error rate > 20% → fallback working, but investigate

### Implementation
1. Add `prometheus-fastapi-instrumentator` to FastAPI (auto-exposes /metrics)
2. Configure Grafana Cloud agent to scrape Cloud Run /metrics endpoint
3. Import pre-built Cloud Run dashboard + custom Cherry Evals dashboard
4. Business metrics: SQL queries against curation_events table, visualized in Grafana

---

## Deployment Steps (ordered)

### Step 1: Embedding model migration
- [ ] Update to `text-embedding-005` or `gemini-embedding-001`
- [ ] Test embedding generation locally
- [ ] Update Qdrant collection dimensions if changed

### Step 2: Landing page deploy
- [ ] Owner connects Cloudflare account to GitHub repo
- [ ] Configure CF Pages: build command = none, output dir = `landing/`
- [ ] Point cherryevals.com DNS to CF Pages
- [ ] Verify live

### Step 3: API deploy to Cloud Run
- [ ] Owner creates GCP project (or reuses existing)
- [ ] Enable Cloud Run, Artifact Registry APIs
- [ ] Push Docker image to Artifact Registry
- [ ] Deploy Cloud Run service with env vars
- [ ] Verify /health endpoint

### Step 4: Database setup
- [ ] Create Neon project (free tier)
- [ ] Run Alembic migrations against Neon
- [ ] Create Qdrant Cloud cluster (free tier, 1GB)

### Step 5: Data ingestion
- [ ] Run `cherry-evals ingest all` against production DBs
- [ ] Run `cherry-evals embed all` to generate embeddings
- [ ] Verify search works end-to-end

### Step 6: Frontend deploy
- [ ] Configure CF Pages for frontend: build = `npm run build`, dir = `dist`
- [ ] Set API proxy to Cloud Run URL
- [ ] Deploy and verify

### Step 7: Monitoring
- [ ] Add prometheus instrumentation to FastAPI
- [ ] Connect Grafana Cloud to Cloud Run metrics
- [ ] Set up basic alerts

### Step 8: DNS & routing
- [ ] cherryevals.com → landing page
- [ ] app.cherryevals.com → frontend
- [ ] api.cherryevals.com → Cloud Run

---

## Owner Actions Required

Only you need to do these (account creation / billing):

1. **Cloudflare** — connect GitHub repo to CF Pages (you already have the account)
2. **Google Cloud** — create project, enable billing (free credits), enable Cloud Run + Artifact Registry
3. **Neon** — sign up, create project (free, no credit card)
4. **Qdrant Cloud** — sign up, create cluster (free, no credit card)
5. **Grafana Cloud** — sign up (free, no credit card)

Total time: ~20 minutes of account setup. I handle all configuration after.
