"""Cherry Evals MCP Server.

Exposes Cherry Evals as tools for any MCP-compatible AI agent.
Agents can search evaluation datasets, create curated collections,
and export them — all through the Model Context Protocol.

Usage:
    # stdio (default, for Claude Desktop / local agents)
    uv run mcp_server/server.py

    # HTTP (for remote agents — requires X-Api-Key header when auth_enabled=True)
    uv run mcp_server/server.py --http

    # Test with MCP Inspector
    uv run mcp dev mcp_server/server.py
"""

import hashlib
import json
import logging
import sys
from contextvars import ContextVar

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from agents.search_agent import SearchAgent
from cherry_evals.config import settings
from core.export.formats import to_csv, to_json, to_jsonl
from core.search.hybrid import hybrid_search
from core.search.intelligent import intelligent_search
from core.search.keyword import keyword_search
from core.search.semantic import semantic_search
from db.postgres.base import SessionLocal
from db.postgres.models import (
    ApiKey,
    Collection,
    CollectionExample,
    Dataset,
    Example,
    User,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Auth context variables
# ---------------------------------------------------------------------------

# Holds the authenticated User for the current HTTP request (None in stdio mode)
_current_user: ContextVar[User | None] = ContextVar("_current_user", default=None)
# Transport type: "stdio" or "http"
_current_transport: ContextVar[str] = ContextVar("_current_transport", default="stdio")


def _resolve_user_from_api_key(raw_key: str, db) -> User | None:
    """Look up and return the User associated with a raw API key.

    Hashes the key with SHA-256 and queries the api_keys table.
    Returns None if the key does not exist or is inactive.
    """
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    api_key = db.execute(
        select(ApiKey)
        .options(joinedload(ApiKey.user))
        .where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)  # noqa: E712
    ).scalar_one_or_none()
    if not api_key:
        return None
    return api_key.user


mcp = FastMCP(
    "cherry-evals",
    instructions=(
        "Cherry Evals helps you search, curate, and export examples from "
        "public AI evaluation datasets. Use the tools to find relevant examples, "
        "build collections, and export them for your evaluation pipelines."
    ),
)


def _get_db():
    """Create a database session."""
    return SessionLocal()


# ---------------------------------------------------------------------------
# HTTP auth middleware
# ---------------------------------------------------------------------------


def _build_http_app():
    """Wrap the FastMCP streamable-HTTP ASGI app with API-key auth middleware."""
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    class ApiKeyAuthMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request: Request, call_next):
            # Health checks never require auth
            if request.url.path == "/health":
                return await call_next(request)

            if not settings.auth_enabled:
                return await call_next(request)

            raw_key = request.headers.get("x-api-key", "")
            if not raw_key:
                return JSONResponse({"error": "API key required"}, status_code=401)

            db = SessionLocal()
            try:
                user = _resolve_user_from_api_key(raw_key, db)
            finally:
                db.close()

            if not user:
                return JSONResponse({"error": "Invalid API key"}, status_code=401)

            _current_user.set(user)
            _current_transport.set("http")
            return await call_next(request)

    # FastMCP exposes the Starlette app via streamable_http_app()
    base_app = mcp.streamable_http_app()
    from starlette.applications import Starlette

    app = Starlette()
    app.add_middleware(ApiKeyAuthMiddleware)
    # Mount the MCP app at root
    app.mount("/", base_app)
    return app


# ---------------------------------------------------------------------------
# Dataset tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_datasets() -> str:
    """List all available evaluation datasets.

    Returns a JSON array of datasets with their names, task types, and example counts.
    """
    db = _get_db()
    try:
        datasets = db.execute(select(Dataset).order_by(Dataset.name)).scalars().all()
        result = []
        for ds in datasets:
            count = db.execute(
                select(func.count(Example.id)).where(Example.dataset_id == ds.id)
            ).scalar()
            result.append(
                {
                    "id": ds.id,
                    "name": ds.name,
                    "source": ds.source,
                    "task_type": ds.task_type,
                    "description": ds.description,
                    "example_count": count,
                }
            )
        return json.dumps(result, indent=2)
    finally:
        db.close()


@mcp.tool()
def get_dataset(dataset_id: int) -> str:
    """Get details about a specific dataset.

    Args:
        dataset_id: The ID of the dataset to retrieve.
    """
    db = _get_db()
    try:
        ds = db.get(Dataset, dataset_id)
        if not ds:
            return json.dumps({"error": f"Dataset {dataset_id} not found"})
        count = db.execute(
            select(func.count(Example.id)).where(Example.dataset_id == ds.id)
        ).scalar()
        return json.dumps(
            {
                "id": ds.id,
                "name": ds.name,
                "source": ds.source,
                "task_type": ds.task_type,
                "description": ds.description,
                "stats": ds.stats,
                "example_count": count,
            }
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Search tools
# ---------------------------------------------------------------------------


@mcp.tool()
def search_examples(
    query: str,
    dataset_name: str | None = None,
    subject: str | None = None,
    limit: int = 20,
) -> str:
    """Search for examples across evaluation datasets by keyword.

    Searches question and answer text. Returns matching examples with their
    dataset info, choices, and metadata.

    Args:
        query: The search query (matches against question and answer text).
        dataset_name: Optional filter to search only within a specific dataset.
        subject: Optional filter by subject (e.g. "math", "history").
        limit: Maximum number of results to return (default 20, max 100).
    """
    limit = min(limit, 100)
    db = _get_db()
    try:
        results, total = keyword_search(
            db, query, dataset_name=dataset_name, subject=subject, limit=limit
        )
        return json.dumps({"results": results, "total": total}, indent=2)
    finally:
        db.close()


@mcp.tool()
def semantic_search_examples(
    query: str,
    collection: str = "mmlu_embeddings",
    subject: str | None = None,
    limit: int = 20,
    score_threshold: float | None = None,
) -> str:
    """Search for examples using semantic (vector) similarity.

    Embeds the query and finds nearest neighbors in the vector database.
    Requires embeddings to be generated for the target collection.

    Args:
        query: Natural language search query.
        collection: Qdrant collection to search (default: mmlu_embeddings).
        subject: Optional filter by subject in payload.
        limit: Maximum number of results to return (default 20, max 100).
        score_threshold: Minimum similarity score threshold (0-1).
    """
    limit = min(limit, 100)
    try:
        results = semantic_search(
            query=query,
            collection_name=collection,
            limit=limit,
            score_threshold=score_threshold,
            subject=subject,
        )
        return json.dumps({"results": results, "total": len(results)}, indent=2)
    except Exception:
        logger.exception("Semantic search failed in MCP")
        return json.dumps({"error": "Semantic search temporarily unavailable"})


@mcp.tool()
def hybrid_search_examples(
    query: str,
    dataset_name: str | None = None,
    subject: str | None = None,
    collection: str = "mmlu_embeddings",
    limit: int = 20,
    keyword_weight: float = 0.4,
    semantic_weight: float = 0.6,
) -> str:
    """Search for examples using hybrid keyword + semantic search.

    Combines keyword matching and vector similarity using Reciprocal Rank
    Fusion (RRF). Falls back to keyword-only if semantic search is unavailable.

    Args:
        query: The search query string.
        dataset_name: Optional filter to search only within a specific dataset.
        subject: Optional filter by subject.
        collection: Qdrant collection to search (default: mmlu_embeddings).
        limit: Maximum number of results to return (default 20, max 100).
        keyword_weight: Weight for keyword results (0-1, default 0.4).
        semantic_weight: Weight for semantic results (0-1, default 0.6).
    """
    limit = min(limit, 100)
    db = _get_db()
    try:
        results, total = hybrid_search(
            db=db,
            query=query,
            dataset_name=dataset_name,
            subject=subject,
            limit=limit,
            offset=0,
            keyword_weight=keyword_weight,
            semantic_weight=semantic_weight,
            collection_name=collection,
        )
        return json.dumps({"results": results, "total": total}, indent=2)
    except Exception as exc:
        # Fall back to keyword search
        logger.warning("Hybrid search fell back to keyword: %s", exc)
        results, total = keyword_search(
            db=db, query=query, dataset_name=dataset_name, subject=subject, limit=limit
        )
        return json.dumps(
            {"results": results, "total": total, "fallback": "semantic unavailable"},
            indent=2,
        )
    finally:
        db.close()


@mcp.tool()
def intelligent_search_examples(
    query: str,
    limit: int = 20,
    max_iterations: int = 3,
    strategy: str = "agent",
) -> str:
    """Search for examples using the autonomous LLM-powered search agent.

    By default uses the autonomous search agent (strategy='agent') which
    iterates and refines the search up to max_iterations times. Set
    strategy='pipeline' for the original fixed parse→search→rerank flow.

    The response includes a full iteration trace showing what the agent
    tried and its quality evaluation at each step.

    Falls back gracefully if LLM calls or semantic search are unavailable.

    Args:
        query: Natural language search query (e.g. "hard science questions").
        limit: Maximum number of results to return (default 20, max 100).
        max_iterations: Max agent iterations for strategy='agent' (1-5, default 3).
        strategy: 'agent' (default) or 'pipeline' (original fixed DAG).
    """
    limit = min(limit, 100)
    max_iterations = max(1, min(max_iterations, 5))
    db = _get_db()
    try:
        if strategy == "pipeline":
            results, total, metadata = intelligent_search(
                db=db,
                query=query,
                limit=limit,
                offset=0,
            )
            return json.dumps(
                {
                    "results": results,
                    "total": total,
                    "strategy_used": "pipeline",
                    "metadata": metadata,
                },
                indent=2,
            )

        # strategy == "agent" (default)
        agent = SearchAgent(db=db, max_iterations=max_iterations)
        agent_result = agent.search(query=query, limit=limit)

        iterations_out = [
            {
                "tool_used": it.tool_used,
                "query": it.query,
                "filters": it.filters,
                "result_count": it.result_count,
                "evaluation": it.evaluation,
            }
            for it in agent_result.iterations
        ]

        return json.dumps(
            {
                "results": agent_result.results,
                "total": agent_result.total,
                "strategy_used": "agent",
                "iterations": iterations_out,
                "final_evaluation": agent_result.final_evaluation,
                "query_understanding": agent_result.query_understanding,
            },
            indent=2,
        )
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Collection tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_collections() -> str:
    """List existing collections with their example counts.

    In HTTP mode with auth enabled, only returns collections owned by the
    authenticated user. In stdio mode, all collections are returned.
    """
    db = _get_db()
    try:
        user = _current_user.get()
        query = select(Collection).order_by(Collection.created_at.desc())
        if user is not None:
            query = query.where(Collection.user_id == user.supabase_id)
        collections = db.execute(query).scalars().all()
        result = []
        for coll in collections:
            count = db.execute(
                select(func.count(CollectionExample.id)).where(
                    CollectionExample.collection_id == coll.id
                )
            ).scalar()
            result.append(
                {
                    "id": coll.id,
                    "name": coll.name,
                    "description": coll.description,
                    "example_count": count,
                }
            )
        return json.dumps(result, indent=2)
    finally:
        db.close()


@mcp.tool()
def create_collection(name: str, description: str | None = None) -> str:
    """Create a new collection to curate evaluation examples.

    Collections group cherry-picked examples for export. Create one, then
    use add_to_collection to populate it with examples from search results.

    Args:
        name: Name for the collection (e.g. "Math reasoning hard").
        description: Optional description of the collection's purpose.
    """
    db = _get_db()
    try:
        user = _current_user.get()
        user_id = user.supabase_id if user is not None else None
        coll = Collection(name=name, description=description, user_id=user_id)
        db.add(coll)
        db.commit()
        db.refresh(coll)
        return json.dumps(
            {
                "id": coll.id,
                "name": coll.name,
                "description": coll.description,
                "message": f"Collection '{name}' created successfully.",
            }
        )
    finally:
        db.close()


@mcp.tool()
def add_to_collection(collection_id: int, example_ids: list[int]) -> str:
    """Add examples to a collection by their IDs.

    Use search_examples to find examples, then add them here by ID.
    Duplicates are automatically skipped.

    Args:
        collection_id: The ID of the collection to add examples to.
        example_ids: List of example IDs to add.
    """
    db = _get_db()
    try:
        coll = db.get(Collection, collection_id)
        if not coll:
            return json.dumps({"error": f"Collection {collection_id} not found"})

        user = _current_user.get()
        if user is not None and coll.user_id != user.supabase_id:
            return json.dumps({"error": f"Collection {collection_id} not found"})

        existing = set(
            db.execute(
                select(CollectionExample.example_id).where(
                    CollectionExample.collection_id == collection_id,
                    CollectionExample.example_id.in_(example_ids),
                )
            )
            .scalars()
            .all()
        )

        added = 0
        not_found = 0
        for eid in example_ids:
            if eid in existing:
                continue
            example = db.get(Example, eid)
            if not example:
                not_found += 1
                continue
            db.add(CollectionExample(collection_id=collection_id, example_id=eid))
            added += 1

        db.commit()
        return json.dumps(
            {
                "added": added,
                "skipped_duplicates": len(example_ids) - added - not_found,
                "not_found": not_found,
            }
        )
    finally:
        db.close()


@mcp.tool()
def get_collection(collection_id: int) -> str:
    """Get details about a collection, including its examples.

    Args:
        collection_id: The ID of the collection.
    """
    db = _get_db()
    try:
        coll = db.get(Collection, collection_id)
        if not coll:
            return json.dumps({"error": f"Collection {collection_id} not found"})

        user = _current_user.get()
        if user is not None and coll.user_id != user.supabase_id:
            return json.dumps({"error": f"Collection {collection_id} not found"})

        rows = (
            db.execute(
                select(Example)
                .join(CollectionExample, CollectionExample.example_id == Example.id)
                .where(CollectionExample.collection_id == collection_id)
                .order_by(CollectionExample.added_at)
            )
            .scalars()
            .all()
        )

        examples = []
        for ex in rows:
            examples.append(
                {
                    "id": ex.id,
                    "dataset_id": ex.dataset_id,
                    "question": ex.question,
                    "answer": ex.answer,
                    "choices": ex.choices,
                    "metadata": ex.example_metadata,
                }
            )

        return json.dumps(
            {
                "id": coll.id,
                "name": coll.name,
                "description": coll.description,
                "example_count": len(examples),
                "examples": examples,
            },
            indent=2,
        )
    finally:
        db.close()


@mcp.tool()
def export_collection(
    collection_id: int,
    format: str = "jsonl",
) -> str:
    """Export a collection to a file format.

    Supported formats: json, jsonl, csv.
    Returns the file content as a string.

    Args:
        collection_id: The ID of the collection to export.
        format: Export format — "json", "jsonl", or "csv" (default: "jsonl").
    """
    if format not in ("json", "jsonl", "csv"):
        return json.dumps({"error": f"Unsupported format: {format}. Use json, jsonl, or csv."})

    db = _get_db()
    try:
        coll = db.get(Collection, collection_id)
        if not coll:
            return json.dumps({"error": f"Collection {collection_id} not found"})

        user = _current_user.get()
        if user is not None and coll.user_id != user.supabase_id:
            return json.dumps({"error": f"Collection {collection_id} not found"})

        examples = (
            db.execute(
                select(Example)
                .join(CollectionExample, CollectionExample.example_id == Example.id)
                .where(CollectionExample.collection_id == collection_id)
                .order_by(CollectionExample.added_at)
            )
            .scalars()
            .all()
        )

        # Build dataset name mapping
        dataset_ids = {ex.dataset_id for ex in examples}
        dataset_names = {}
        if dataset_ids:
            datasets = (
                db.execute(select(Dataset).where(Dataset.id.in_(dataset_ids))).scalars().all()
            )
            dataset_names = {ds.id: ds.name for ds in datasets}

        converters = {"json": to_json, "jsonl": to_jsonl, "csv": to_csv}
        content = converters[format](examples, dataset_names)
        return content
    finally:
        db.close()


# ---------------------------------------------------------------------------
# Agentic ingestion tools
# ---------------------------------------------------------------------------


@mcp.tool()
def discover_dataset(description: str) -> str:
    """Discover a HuggingFace dataset matching a natural language description.

    Uses an LLM to find the best matching dataset. You can also pass a direct
    HuggingFace dataset ID (e.g. "openai/gsm8k") to skip discovery.

    Args:
        description: What kind of dataset you're looking for, or a direct HF ID.
    """
    from agents.ingestion_agent import IngestionAgent

    agent = IngestionAgent()
    result = agent.discover_dataset(description)
    if not result:
        return json.dumps({"error": "No matching dataset found."})
    return json.dumps(result, indent=2)


@mcp.tool()
def ingest_discovered_dataset(
    description: str,
    hf_dataset_id: str | None = None,
    hf_config: str | None = None,
    max_examples: int | None = None,
) -> str:
    """Ingest an arbitrary HuggingFace dataset using LLM-generated parsing logic.

    The agent discovers the dataset (or uses the provided ID), inspects its
    schema, generates a parser, validates it, and runs ingestion.

    For known datasets (mmlu, humaneval, etc.), use the CLI ingest command
    instead — it uses hand-tuned adapters.

    Args:
        description: What kind of dataset to ingest, or a plain description.
        hf_dataset_id: Optional direct HuggingFace dataset ID (skips discovery).
        hf_config: Optional HuggingFace config/subset name.
        max_examples: Optional limit on number of examples to ingest.
    """
    from agents.ingestion_agent import IngestionAgent

    agent = IngestionAgent(max_examples=max_examples)
    result = agent.ingest(
        description=description,
        hf_dataset_id=hf_dataset_id,
        hf_config=hf_config,
    )

    output = {
        "success": result.success,
        "dataset_name": result.dataset_name,
        "total_examples": result.total_examples,
        "splits": result.splits,
    }
    if result.errors:
        output["errors"] = result.errors
    if result.plan:
        output["explanation"] = result.plan.explanation
    if result.adapter_code:
        output["adapter_code_available"] = True

    return json.dumps(output, indent=2)


# ---------------------------------------------------------------------------
# Agentic export tools
# ---------------------------------------------------------------------------


@mcp.tool()
def export_collection_custom(
    collection_id: int,
    format_description: str,
) -> str:
    """Export a collection to any format using LLM-generated conversion logic.

    For standard formats (json, jsonl, csv), use export_collection instead.
    This tool handles custom formats like "Inspect AI", "LangSmith",
    "EleutherAI harness", or any user-described schema.

    Args:
        collection_id: The ID of the collection to export.
        format_description: Target format (e.g. "Inspect AI dataset format",
            "LangSmith", or a detailed format specification).
    """
    from agents.export_agent import ExportAgent

    db = _get_db()
    try:
        coll = db.get(Collection, collection_id)
        if not coll:
            return json.dumps({"error": f"Collection {collection_id} not found"})

        user = _current_user.get()
        if user is not None and coll.user_id != user.supabase_id:
            return json.dumps({"error": f"Collection {collection_id} not found"})

        examples = (
            db.execute(
                select(Example)
                .join(CollectionExample, CollectionExample.example_id == Example.id)
                .where(CollectionExample.collection_id == collection_id)
                .order_by(CollectionExample.added_at)
            )
            .scalars()
            .all()
        )

        dataset_ids = {ex.dataset_id for ex in examples}
        dataset_names = {}
        if dataset_ids:
            datasets = (
                db.execute(select(Dataset).where(Dataset.id.in_(dataset_ids))).scalars().all()
            )
            dataset_names = {ds.id: ds.name for ds in datasets}

        agent = ExportAgent()
        result = agent.export(examples, format_description, dataset_names)

        output = {
            "success": result.success,
            "num_examples": result.num_examples,
            "file_extension": result.file_extension,
            "content_type": result.content_type,
        }
        if result.success:
            output["content"] = result.content
        if result.errors:
            output["errors"] = result.errors
        if result.plan:
            output["explanation"] = result.plan.explanation

        return json.dumps(output, indent=2)
    finally:
        db.close()


if __name__ == "__main__":
    if "--http" in sys.argv:
        import uvicorn

        if settings.auth_enabled:
            logger.info("MCP HTTP mode: API key authentication is ENABLED (X-Api-Key required)")
        else:
            logger.warning(
                "MCP HTTP mode: auth_enabled=False — running WITHOUT authentication. "
                "Set AUTH_ENABLED=True and SUPABASE_JWT_SECRET for production."
            )
        _current_transport.set("http")
        http_app = _build_http_app()
        uvicorn.run(http_app, host="0.0.0.0", port=8001)
    else:
        _current_transport.set("stdio")
        mcp.run(transport="stdio")
