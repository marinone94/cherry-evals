# Cherry Evals — Vision

## Mission

Cherry Evals makes it trivially easy to discover, search, curate, and export evaluation examples from public AI benchmark datasets.

The core thesis: **collective curation intelligence > any search algorithm**.

AI models are commoditized. Search algorithms improve every year. What makes Cherry Evals irreplaceable is the accumulated knowledge of *what experienced researchers and AI agents actually cherry-pick* — which examples work together, which collections produce meaningful evaluations, which patterns separate signal from noise.

---

## The Problem

Evaluation datasets are scattered across HuggingFace, academic repos, and proprietary collections. A researcher who wants to build a custom eval suite today must:

1. Find relevant datasets (manually browsing HuggingFace)
2. Understand their format (reading docs, inspecting samples)
3. Filter and select examples (writing one-off scripts)
4. Convert to their eval framework's format (more scripts)
5. Repeat for every new experiment

This workflow is slow, manual, and produces no reusable knowledge. Every researcher starts from zero.

## The Solution

Cherry Evals provides:

- **Unified search** across all major eval datasets (keyword, semantic, hybrid)
- **Cherry-picking** — select individual examples into curated collections
- **Export** to any eval framework format (Langfuse, LangSmith, Inspect AI, custom)
- **MCP + CLI interfaces** so AI agents can curate eval sets programmatically
- **Collective intelligence** — the managed version learns from how everyone curates, making search and recommendations better for all users

---

## Design Philosophy

### 1. Data Flywheel > Intelligence Moat

Every interaction is a signal:
- What someone searches for reveals what matters
- What they cherry-pick reveals quality judgment
- What they export together reveals coherent evaluation strategies
- What they skip or remove reveals noise

The managed version aggregates these signals (anonymized) to improve ranking, suggest similar examples, and recommend collection compositions. This flywheel is the moat — it gets stronger with every user.

### 2. Agents Are First-Class Users

Cherry Evals is designed for both humans (web UI, CLI) and AI agents (MCP server, API). Agents should be able to:

- Search for evaluation examples matching criteria
- Build collections programmatically
- Export in any format
- Report what worked and what didn't (feedback loop)

The MCP interface means any AI coding agent can use Cherry Evals as a tool, generating usage data that feeds the collective intelligence flywheel.

### 3. Structure That Serves Learning

Following the Bitter Lesson: don't hardcode curation strategies. Instead, build infrastructure that captures signals and lets the system discover what works. The search ranking should improve from usage patterns, not from hand-tuned heuristics.

Concrete implications:
- Track every search → pick → export flow as a "curation trace"
- Use curation traces to learn co-selection patterns (examples often picked together)
- Surface these patterns as recommendations and improved ranking
- Let the system evolve its own notion of "example quality" from collective behavior

### 4. OSS Core + Managed Version

**Open-source core** (self-hosted):
- Full search, curation, and export capabilities
- Local PostgreSQL + Qdrant
- CLI + API
- No telemetry, no external dependencies beyond the databases

**Managed version** (hosted):
- Everything in OSS, plus:
- Collective intelligence (aggregated usage patterns improve search for everyone)
- Pre-indexed datasets (no need to run ingestion yourself)
- Hosted infrastructure (no Docker setup)
- Team collaboration features
- API access tiers

The managed version wins on convenience and collective intelligence. The OSS version wins on control and privacy.

### 5. Simple, Working Steps

Get one thing working before adding the next. Quality over quantity. Ship early, iterate often.

The right amount of complexity is the minimum needed for the current task. Three similar lines of code is better than a premature abstraction.

---

## Competitive Landscape

**HuggingFace Datasets**: The source of truth for raw datasets, but no curation, no cross-dataset search, no collection management. Cherry Evals sits on top of HuggingFace as a curation layer.

**Eval frameworks** (Langfuse, LangSmith, Inspect AI, LMMS-Eval): These are eval *runners*. They need datasets as input. Cherry Evals is the dataset *curator* that feeds into these frameworks. Complementary, not competitive.

**Custom scripts**: What most researchers do today. Cherry Evals replaces the script-per-experiment workflow with a reusable platform.

---

## What Cherry Evals Is Not

- **Not an eval runner** — we curate datasets, not run evaluations
- **Not a model benchmark** — we help you build custom evals, not standardized leaderboards
- **Not a data labeling tool** — we work with existing public datasets
- **Not a replacement for domain expertise** — collective intelligence augments judgment, doesn't replace it

---

## Success Metrics

**OSS adoption**: GitHub stars, forks, contributors, PyPI downloads
**Managed version**: Active users, collections created, exports completed, MCP integrations
**Collective intelligence**: Search quality improvement over time (measured by click-through on recommended examples)
**Revenue**: Managed version subscriptions, API access tiers

**Ultimate success = researchers and AI agents use Cherry Evals as their default starting point for building custom eval suites.**
