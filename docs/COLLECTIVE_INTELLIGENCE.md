# Collective Intelligence Architecture

## Vision

The moat is not the search algorithm — it is the accumulated curation wisdom.

Every search query, every example picked, every collection exported is a signal about what makes a great eval suite. The managed platform learns from how the entire community curates, making everyone's eval suites better over time. Self-hosted instances are powerful. The managed platform is smarter.

Cherry Evals is, at its core, a collaborative filtering system for evaluation data. The eval examples are the items. The AI engineers are the users. The curation traces are the interactions. The collective intelligence layer is what transforms a search tool into a platform that gets measurably better with every interaction.

---

## The Bitter Lesson Applied

Richard Sutton's bitter lesson states: general methods that leverage computation will always beat hand-engineered approaches over the long run. The history of AI is littered with clever heuristics that were eventually crushed by models with more data and more compute.

This lesson applies directly to eval curation:

- **Do not hardcode "good eval" heuristics.** Do not decide that difficulty level 3 is better than level 1, or that multi-step reasoning questions are more valuable than factual recall. Learn it from usage. The community's curation behavior is the ground truth.
- **Do not build fixed recommendation rules.** "If the user searches for reasoning, recommend MMLU philosophy" is the kind of rule that degrades over time and never generalizes. Train models on curation patterns instead.
- **Do not assume we know what makes a good eval suite.** The definition changes as models improve, as tasks evolve, as the field moves. A static definition is wrong by construction. Let the community's collective behavior redefine it continuously.
- **The system should get better with every interaction, not with every code change.** A system that requires an engineer to improve is bounded by engineering capacity. A system that learns from data scales with usage.

The design principle that flows from this: invest first in data collection, second in training infrastructure, third in model quality. In that order. Always.

---

## Signal Taxonomy

All signals are already captured by the `CurationEvent` model in `core/traces/events.py`. Every event maps to a learning signal:

| Signal | Event Type | What It Tells Us |
|--------|------------|------------------|
| Search query | `search` | What capabilities engineers want to evaluate |
| Search mode chosen | `search` | Preference for precision (keyword) vs. recall (semantic) |
| Result count returned | `search` | Whether the index covers the domain |
| Example picked | `pick` | This example is valuable for this query context |
| Pick position | `pick` | Higher-ranked picks validate ranking; lower-ranked picks reveal ranking failures |
| Example removed | `remove` | False positive, quality issue, or changed requirements |
| Export triggered | `export` | The collection is complete — all retained examples are validated |
| Export format | `export` | Integration target (Langfuse, raw JSON, CSV) — signals deployment context |
| Collection composition | derived | Which examples belong together — the strongest structural signal |
| Time between pick and remove | derived | Quick removes signal noise; delayed removes signal changing requirements |
| Search-to-export conversion rate | derived | Whether users are finding what they need |

A pick without a subsequent remove is a strong positive signal. A pick followed by a remove is a weak negative signal. An export containing an example is the strongest positive signal — it survived the full curation gauntlet.

---

## Core Algorithms

### 1. Co-Selection Graph

Build a weighted undirected graph where:

- **Nodes** = examples (identified by `example_id`)
- **Edges** = co-occurrence in exported collections (weighted by co-occurrence frequency)
- **Edge weight decay** = recency-weighted so recent co-selections count more

This graph enables:
- "Others who picked X also picked Y" recommendations
- Cluster detection: groups of examples that frequently travel together
- Gap detection: an example is connected to a cluster but never co-selected with one of its members — potential gap in a user's collection
- Graph embeddings (e.g., Node2Vec) that capture latent similarity orthogonal to text/vector similarity

The co-selection graph is complementary to vector similarity. Two examples can be textually similar but rarely co-selected (redundant), or textually dissimilar but frequently co-selected (complementary). Both signals matter.

**Initial implementation**: PostgreSQL materialized view aggregating export co-occurrences.
**Scale-out path**: Neo4j or a dedicated graph database if query latency degrades.

### 2. Quality Scoring

Each example accumulates a quality score derived from curation signals:

```
quality_score = (
    pick_rate         * 0.30   # how often picked vs. seen in search results
  + retention_rate   * 0.35   # picked and NOT subsequently removed
  + export_rate      * 0.25   # appeared in at least one exported collection
  + diversity_bonus  * 0.10   # picked across diverse query contexts
) * recency_weight             # exponential decay favoring recent signals
```

- **Pick rate**: `picks / impressions` (impressions = times appeared in search results)
- **Retention rate**: `(picks - removes) / picks` — survived curation
- **Export rate**: `exports_containing_example / total_exports` — fully validated
- **Diversity bonus**: entropy of query contexts in which the example was picked — a versatile example is more valuable than a narrowly-applicable one
- **Recency weight**: exponential decay with a configurable half-life (default: 90 days) — the community's taste evolves

Quality scores are stored as a denormalized column on the `Example` table, updated by a background job. They never block user requests.

Zero signals means no score — the example is unranked, not penalized. The system degrades gracefully to pure vector/keyword ranking when signals are sparse.

### 3. Query-Example Relevance Model

Learn a relevance model from (query, example, was_picked) triples. This is the direct application of the bitter lesson to search ranking:

**Phase 1 — Co-occurrence statistics** (requires: ~100 search-pick pairs):
- Build a frequency table: `query_term → example_id → pick_count`
- Boost examples that were historically picked for similar queries
- Simple, interpretable, immediately useful

**Phase 2 — Embedding similarity model** (requires: ~10K search-pick pairs):
- Train a bilinear scoring model: `score = query_embedding · W · example_embedding`
- W is learned from (query_embedding, example_embedding, was_picked) triples
- Captures semantic alignment between what was searched and what was valued
- Can be fine-tuned incrementally as more data accumulates

**Phase 3 — Neural ranker** (requires: ~100K search-pick pairs):
- Full cross-encoder trained on curation data
- Input: concatenated (query, example question, example metadata)
- Output: relevance probability
- Replaces heuristic RRF weights with learned weights
- Can be distilled into a lighter model for latency-sensitive serving

Each phase replaces the previous. Nothing is thrown away — earlier phases generate the training data for later phases.

### 4. Collection Archetypes

Discover common collection patterns by clustering collections at scale:

- Represent each collection as a vector: distribution over dataset, subject, task_type, difficulty
- Cluster collections using k-means or hierarchical clustering
- Label clusters by their dominant characteristics: "reasoning eval suite", "code generation benchmark", "safety and alignment eval", "factual recall test"
- Track how archetypes evolve over time — signals how the field's eval priorities shift

Archetypes enable:
- **Collection templates**: "Start with a reasoning eval suite template (87 commonly co-selected examples)"
- **Gap detection**: "Your collection matches the reasoning archetype but is missing commonsense examples — 94% of similar collections include WinoGrande examples"
- **Completeness score**: "Your collection is 73% complete relative to the reasoning archetype"

### 5. Eval Suite Quality Predictor

Given a collection, predict how well it will evaluate a model across four dimensions:

- **Coverage**: Does it test diverse capabilities? (measured by distribution over subjects and task types)
- **Difficulty calibration**: Is it spread across easy, medium, and hard examples? (uniform distribution is rarely right — depends on target model capability)
- **Redundancy**: Are examples too similar to each other? (pairwise embedding similarity within the collection)
- **Blind spots**: Which capability categories are missing relative to similar collections?

Phase 1 (available now): coverage, redundancy, and blind spots from structural analysis alone.
Phase 2 (requires labeled outcomes): train a predictor on (collection, evaluation_results) pairs — this requires integrating with evaluation platforms like Langfuse. When a user exports a collection, runs it as an eval, and feeds results back, that is gold-standard training data.

---

## Data Flywheel

The reinforcing loop that makes the managed platform defensible:

```
1. User searches
      → we learn what AI engineers need to evaluate
      → we improve query understanding and dataset coverage

2. User picks examples
      → we learn what is considered valuable
      → we improve quality scores and ranking

3. Better ranking → users find good examples faster
      → lower friction → more curations per session
      → more signals per unit time

4. Users export better eval suites
      → they run better evaluations
      → they trust Cherry Evals → they return and refer others

5. More users → more signals → better recommendations → repeat
```

The key structural property: the managed version will always outperform self-hosted because it has the full community's curation data. A self-hosted instance sees only its own users' behavior. The managed platform sees thousands of AI engineers curating simultaneously.

This is the moat. It is not a technical moat — a competitor can replicate the search algorithms. It is a data moat. Replicating years of accumulated curation signals requires years of accumulated users.

---

## Enterprise Signal Sharing

### How It Works

Enterprise self-hosted instances can opt-in to contribute anonymized curation signals to the collective intelligence pool. In return, they receive access to community-derived quality scores and recommendations.

Think of it as federated learning for eval curation: each enterprise keeps its data local, contributes only anonymized signals, and benefits from the collective's accumulated wisdom.

**Signal payload** (what gets transmitted):

```json
{
  "instance_id": "uuid-per-instance",
  "signals": [
    {
      "query_hash": "sha256-of-query-text",
      "example_id": 4521,
      "event": "pick",
      "position": 3,
      "ts": "2026-03-04T10:23:11Z"
    },
    {
      "query_hash": "sha256-of-query-text",
      "example_id": 4521,
      "event": "export",
      "ts": "2026-03-04T10:31:44Z"
    }
  ]
}
```

**What stays local** (never transmitted):
- Raw query text (only SHA-256 hash)
- Collection names and descriptions
- User identifiers
- Organization or project metadata
- The structure of specific collections

### Privacy Guarantees

- Query text is hashed (SHA-256) before transmission — the managed platform never sees raw queries, only the hash. Two instances that issue identical queries will share the same hash, enabling cross-instance signal aggregation without revealing the query.
- Example IDs are universal: the same example has the same ID across all Cherry Evals instances because datasets are immutable and centrally indexed.
- No user identifiers are transmitted. Signals are attributed only to the instance, never to individuals.
- Enterprise can inspect and audit the exact signal payload in the admin UI before enabling opt-in.
- Signal transmission is one-directional from enterprise to managed. The managed platform does not pull or read from enterprise instances.

### API Contract

**Signal ingestion** (enterprise → managed):

```
POST /api/v1/signals/ingest
Authorization: Bearer <enterprise-api-key>

{
  "instance_id": "uuid",
  "signals": [
    {"query_hash": "sha256...", "example_id": 123, "event": "pick", "position": 2, "ts": "..."},
    {"query_hash": "sha256...", "example_id": 456, "event": "remove", "ts": "..."},
    {"query_hash": "sha256...", "example_id": 123, "event": "export", "ts": "..."}
  ]
}

Response 200:
{
  "accepted": 3,
  "rejected": 0
}
```

**Score retrieval** (enterprise ← managed):

```
GET /api/v1/signals/scores?example_ids=123,456,789
Authorization: Bearer <enterprise-api-key>

Response 200:
{
  "example_scores": [
    {"example_id": 123, "quality_score": 0.87, "pick_rate": 0.34, "export_rate": 0.21},
    {"example_id": 456, "quality_score": 0.61, "pick_rate": 0.18, "export_rate": 0.09},
    {"example_id": 789, "quality_score": 0.43, "pick_rate": 0.11, "export_rate": 0.04}
  ]
}
```

**Co-selection recommendations** (enterprise ← managed):

```
GET /api/v1/signals/co-selected?example_id=123&limit=10
Authorization: Bearer <enterprise-api-key>

Response 200:
{
  "example_id": 123,
  "co_selected": [
    {"example_id": 891, "co_occurrence_rate": 0.62, "confidence": "high"},
    {"example_id": 334, "co_occurrence_rate": 0.48, "confidence": "medium"}
  ]
}
```

---

## Architecture Phases

### Phase 1: Foundation (Current)

**Status**: CurationEvent tracking is implemented.

- `CurationEvent` model: search, pick, remove, export events captured in PostgreSQL
- Basic analytics endpoints: `/analytics/stats`, `/analytics/popular`, `/analytics/co-picked/{id}`
- Simple counters and aggregations
- No ML, no graph operations — pure SQL aggregations

**Signals required**: 0 (infrastructure is live)
**Timeline**: Now

---

### Phase 2: Graph Intelligence

**Trigger**: ~1,000 exported collections accumulated.

- Build co-selection graph from export events using PostgreSQL materialized views
- "Others also picked" recommendations surfaced in search results (below the ranked list)
- Quality scores computed from pick/retention/export rates, stored on `Example` table
- Collection gap detection: "Your collection looks like a reasoning eval suite — you might also want WinoGrande examples (picked by 78% of similar collections)"
- Diversity bonus integrated into quality scoring

**New infrastructure**: Background job (Celery or simple cron) to refresh materialized views and quality scores.
**New API endpoints**: `/recommendations/co-selected`, `/recommendations/gaps`

---

### Phase 3: Learned Ranking

**Trigger**: ~10,000 (query, example, was_picked) triples accumulated.

- Train Phase 2 embedding similarity model on accumulated curation data
- Integrate learned relevance scores into hybrid search RRF weights
- Personalized ranking: if a user's curation history is available (opt-in), adjust ranking based on their past preferences
- A/B testing infrastructure: compare learned ranking against heuristic RRF

**New infrastructure**: Model training pipeline (can run on the same machine as the API initially). MLflow or simple artifact storage for model versioning.
**Compute**: ~1 GPU-hour per training run at this data scale.

---

### Phase 4: Generative Intelligence

**Trigger**: ~100,000 curation events accumulated.

- LLM-generated eval suggestions: "Based on your collection's composition, consider adding examples from TruthfulQA — your current collection covers reasoning and code but has no factual grounding tests."
- Automatic collection templates for common eval archetypes, derived from clustering
- Eval suite quality reports with actionable recommendations (coverage, calibration, redundancy, blind spots)
- Archetype detection: classify a collection into known archetypes at creation time

**New infrastructure**: Async LLM calls for report generation. Report caching (expensive to generate, cheap to serve).

---

### Phase 5: Ecosystem Intelligence

**Trigger**: ~1,000,000 events, plus external integration data.

- **Cross-platform feedback loop**: When users export to Langfuse and run evaluations, feed model performance results back as quality signals. An example that reliably discriminates between strong and weak models is more valuable than one where all models score similarly.
- **Model-specific recommendations**: "For evaluating Claude 4, this eval suite configuration catches capability regressions with 94% reliability based on 312 previous runs by the community."
- **Eval suite evolution tracking**: Track how community-preferred benchmark compositions change over time as models improve. When a benchmark becomes saturated (all models score >95%), surface this and recommend harder alternatives.
- **Community-contributed quality labels**: Allow trusted users to annotate examples with quality labels (ambiguous, outdated, incorrect answer). Aggregate labels into the quality score.
- **Enterprise signal sharing API**: Full federated learning pipeline operational.

**New infrastructure**: Integration adapters for Langfuse, HuggingFace Evaluate, and other eval platforms. Time-series database for benchmark saturation tracking.

---

## Technical Implementation Notes

### Storage

| Data | Storage | Rationale |
|------|---------|-----------|
| `CurationEvent` rows | PostgreSQL | Already exists; append-only; great for time-series aggregation |
| Quality scores | Denormalized column on `Example` | Fast reads; updated by background job |
| Co-selection graph | PostgreSQL materialized view | No extra infra for Phase 2 |
| Co-selection graph (scale) | Neo4j | Only if PostgreSQL query latency exceeds 200ms at scale |
| Trained ranking models | File system / object storage | Versioned artifacts; loaded at startup |
| Collection archetype clusters | PostgreSQL | Cluster assignments as a simple join table |

### Compute

- **Phase 1-2**: All PostgreSQL. No additional infrastructure.
- **Phase 3**: One background worker process for model training. Training can be triggered by a cron job or event threshold. Does not need to be real-time — weekly retraining is sufficient at this scale.
- **Phase 4+**: Async LLM calls for generative features. Consider a task queue (Celery + Redis) if synchronous FastAPI workers become a bottleneck.

All heavy computation is async. User-facing requests never wait for model training or graph recomputation.

### Scaling Properties

- **Signals are append-only**: Write-once, read-many. Well-suited for partitioned tables, time-series databases, and streaming systems at scale.
- **Aggregations are incrementally updatable**: Quality scores and co-occurrence counts can be updated incrementally without reprocessing history. Maintain running totals.
- **Graph operations are parallelizable**: Node2Vec random walks, community detection, and embedding updates can all be parallelized across nodes.
- **The bitter lesson applies to infrastructure too**: More signals + more compute beats clever distributed algorithms. Start simple. Add infra only when benchmarks demand it.

---

## Design Principles

**1. Every interaction is a training example.**
Design data collection first, algorithms second. Before building any feature, ask: what signal does this generate? How will we use it? If a feature generates no signal, reconsider whether to build it.

**2. Degrade gracefully.**
Zero signals → no recommendations, not errors. 10 signals → simple frequency heuristics. 1,000 signals → co-selection graph. 10,000 signals → learned model. The system is useful at every scale. New deployments are not penalized for being new.

**3. Transparency builds trust.**
Users should see why something was recommended: "87% of AI engineers who picked this example also picked the following 3 examples." Show the signal, not just the output. Opaque recommendations erode trust. Transparent recommendations invite engagement.

**4. Privacy by design.**
Never require PII. Hash queries before storage or transmission. Anonymize all signals. Enterprise controls exactly what they share and can audit the payload. Privacy is not a compliance checkbox — it is a prerequisite for earning the community's trust, which is the prerequisite for getting their signals.

**5. The bitter lesson.**
Resist the urge to hand-engineer quality heuristics. "A good eval example is one that is unambiguous, has a clear correct answer, and is difficult for current models" sounds right but is wrong in 3 years when models are smarter. Let the community's behavior define quality. Invest in data collection and let models learn.

**6. Composability.**
Each phase builds on the previous. Phase 1 data trains Phase 2 models. Phase 2 graph structures inform Phase 3 ranking features. Phase 3 relevance scores feed Phase 4 generative features. Nothing is thrown away. The architecture accumulates value.

**7. The managed platform is the product.**
The OSS core is the distribution mechanism. The managed platform, fed by the community's collective curation data, is the product. Every design decision should ask: does this increase the quality and quantity of curation signals flowing into the managed platform? If not, deprioritize it.
