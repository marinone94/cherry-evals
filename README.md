# cherry-evals 🍒
Cherry-evals is a webapp for collecting, searching, cherry-picking examples from public evaluation datasets and creating and managing your own evaluation collections.

## Motivation
There is not an easy way to search across public evaluation datasets and cherry-pick the best examples for your own experiments, so why not build it?
Here we can learn:
- deep agentic search
- LLM-powered code generation
- RAG with different vector dbs
- integration with other eval tools and frameworks
- UI/UX design
- deployment
- observability
- security
- scalability
- and anything more we want to explore

Currently a private repo, might make sense to open-source it later, but for now we can keep it private, so no pressure, we can always create a new one and remove commits.

## Project Structure

```
cherry-evals/
├── README.md           # This file
├── ROADMAP.md          # Development roadmap and milestones
├── AGENTS.md           # AI agent development guidelines
├── api/                # FastAPI REST API (coming in MVP-0)
├── agents/             # Google ADK agent definitions (coming in MVP-4)
├── core/               # Business logic
├── db/                 # Database layer (PostgreSQL, Qdrant)
└── tests/              # Test suite
```

See [ROADMAP.md](./ROADMAP.md) for the full development plan.

## Approach
The general principle to be followed - in my opinion - is to add simple, working steps for each part of the tool:
- select and ingest 1 dataset
- select and set 1 vector db
- implement embedding and retrieval with 1 model
- add endpoints to select and export collections as they are
- set integration with langfuse for our own observability
- set a simple docker-compose to start services with ease for local development

Second, build UI and user mgmt with lovable.

Deploy Frontend and backend in the easiest way possible, tools for deployment TBD (vercel? cloud run? what else?)

And once everything works, expand on each:
- more datasets
- different vector dbs to test and compare
- different embedding models
- add agentic search
- add agentic code generation for conversion
- no-code data augmentation
- allow custom lambda functions for conversion
- integrate with other eval tools and frameworks
- improve UI
- teams view, collaboration features
- export to other formats, different targets, ...

## Remember
- when we start developing, we use branches, not main
- always use conventional commits, it will simplify releases

LFG!