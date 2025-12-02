# cherry-evals
Cherry-evals is a webapp for collecting, searching, and managing AI evaluation datasets used by vendors to benchmark their models.

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

Right now private repo, might make sense to open-source it later, but for now we can keep it private, so no pressure, we can always create a new one and remove commits.

## Init structure
Different proposals from agents on how to approach the project can be found under each agents' directory in `AGENTS.md`, `ROADMAP.md` and `README.md` docs.

I did not have time yet to go in detail through each of them, the first task is to compare and combine to get the most reasonable features, roadmap and agents instructions.

The final initial end state is to have a clean aggregated directory with:
cherry-evals/
├── README.md
├── ROADMAP.md
├── AGENTS.md

Immediately after, init uv project and set env etc (see AGENTS.md for details)

## Suggested approach
The general principle to be followed - in my opinion - is to add simple, working steps for each part of the tool:
- select and ingest 1 dataset
- select and set 1 vector db
- implement embedding and retrieval with 1 model
- add endpoints to select and export collections as they are
- add simple conversion
- one format export
- set integration with langfuse for our own observability
- set a simple docker-compose to start services with ease for local development

Second, build UI and user mgmt with lovable.

Deploy Frontend and backend in the easiest way possible, tools TBD (vercel? cloud run? what else?)

And once everything works, expand on each:
- more datasets
- different vector dbs to test and compare
- different embedding models
- add agentic search
- add agentic code generation for conversion
- allow custom lambda functions for conversion
- integrate with other eval tools and frameworks
- improve UI
- teams view, collaboration features
- export to other formats, different targets, ...

## Remember
- when we start developing, we use branches, not main
- always use conventional commits, it will simplify releases

LFG!