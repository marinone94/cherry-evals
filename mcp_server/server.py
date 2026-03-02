"""Cherry Evals MCP Server.

Exposes Cherry Evals as tools for any MCP-compatible AI agent.
Agents can search evaluation datasets, create curated collections,
and export them — all through the Model Context Protocol.

Usage:
    # stdio (default, for Claude Desktop / local agents)
    uv run mcp_server/server.py

    # HTTP (for remote agents)
    uv run mcp_server/server.py --http

    # Test with MCP Inspector
    uv run mcp dev mcp_server/server.py
"""

import json
import sys

from mcp.server.fastmcp import FastMCP
from sqlalchemy import func, select

from core.export.formats import to_csv, to_json, to_jsonl
from core.search.keyword import keyword_search
from db.postgres.base import SessionLocal
from db.postgres.models import (
    Collection,
    CollectionExample,
    Dataset,
    Example,
)

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


# ---------------------------------------------------------------------------
# Collection tools
# ---------------------------------------------------------------------------


@mcp.tool()
def list_collections() -> str:
    """List all existing collections with their example counts."""
    db = _get_db()
    try:
        collections = (
            db.execute(select(Collection).order_by(Collection.created_at.desc())).scalars().all()
        )
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
        coll = Collection(name=name, description=description)
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


if __name__ == "__main__":
    transport = "streamable-http" if "--http" in sys.argv else "stdio"
    mcp.run(transport=transport)
