"""Manage collections from the CLI."""

import json
import sys

import click
from sqlalchemy import func, select

from core.export.formats import to_csv, to_json, to_jsonl
from db.postgres.base import SessionLocal
from db.postgres.models import Collection, CollectionExample, Dataset, Example


def _get_example_count(db, collection_id: int) -> int:
    """Return the number of examples in a collection."""
    return db.execute(
        select(func.count(CollectionExample.id)).where(
            CollectionExample.collection_id == collection_id
        )
    ).scalar()


def _collection_to_dict(db, collection: Collection) -> dict:
    """Convert a Collection ORM object to a plain dict."""
    return {
        "id": collection.id,
        "name": collection.name,
        "description": collection.description,
        "example_count": _get_example_count(db, collection.id),
        "created_at": collection.created_at.isoformat(),
        "updated_at": collection.updated_at.isoformat(),
    }


@click.group()
def collections() -> None:
    """Manage collections."""


@collections.command("list")
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Output as JSON (machine-parseable)",
)
def list_collections(json_output: bool) -> None:
    """List all collections."""
    db = SessionLocal()
    try:
        all_collections = (
            db.execute(select(Collection).order_by(Collection.created_at.desc())).scalars().all()
        )
        data = [_collection_to_dict(db, c) for c in all_collections]

        if json_output:
            click.echo(json.dumps({"status": "success", "total": len(data), "collections": data}))
        else:
            if not data:
                click.echo("No collections found.")
                return
            click.echo(f"{'ID':<6} {'NAME':<40} {'EXAMPLES':<10} DESCRIPTION")
            click.echo("-" * 75)
            for c in data:
                desc = (c["description"] or "")[:30]
                click.echo(f"{c['id']:<6} {c['name']:<40} {c['example_count']:<10} {desc}")
    except Exception as e:
        if json_output:
            click.echo(
                json.dumps({"status": "error", "message": f"Failed to list collections: {e}"})
            )
            raise SystemExit(1)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    finally:
        db.close()


@collections.command("create")
@click.argument("name")
@click.option("--description", default=None, help="Optional description for the collection")
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Output as JSON (machine-parseable)",
)
def create_collection(name: str, description: str | None, json_output: bool) -> None:
    """Create a new collection.

    NAME: Name for the new collection.
    """
    db = SessionLocal()
    try:
        collection = Collection(name=name, description=description)
        db.add(collection)
        db.commit()
        db.refresh(collection)
        data = _collection_to_dict(db, collection)

        if json_output:
            click.echo(json.dumps({"status": "success", **data}))
        else:
            click.echo(f"Created collection '{name}' (id={collection.id})")
            if description:
                click.echo(f"Description: {description}")
    except Exception as e:
        if json_output:
            click.echo(
                json.dumps({"status": "error", "message": f"Failed to create collection: {e}"})
            )
            raise SystemExit(1)
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    finally:
        db.close()


@collections.command("export")
@click.argument("collection_id", type=int)
@click.option(
    "--format",
    "fmt",
    default="jsonl",
    type=click.Choice(["json", "jsonl", "csv"]),
    help="Output format (default: jsonl)",
)
@click.option(
    "--output",
    "-o",
    default=None,
    help="Output file path (default: stdout)",
)
def export_collection(collection_id: int, fmt: str, output: str | None) -> None:
    """Export a collection to a file or stdout.

    COLLECTION_ID: ID of the collection to export.
    """
    db = SessionLocal()
    try:
        collection = db.get(Collection, collection_id)
        if not collection:
            click.echo(f"Error: Collection {collection_id} not found.", err=True)
            raise SystemExit(1)

        rows = db.execute(
            select(Example, CollectionExample.added_at)
            .join(CollectionExample, CollectionExample.example_id == Example.id)
            .where(CollectionExample.collection_id == collection_id)
            .order_by(CollectionExample.added_at)
        ).all()

        examples = [row[0] for row in rows]

        # Build dataset name lookup
        dataset_ids = {ex.dataset_id for ex in examples}
        dataset_names: dict[int, str] = {}
        for did in dataset_ids:
            ds = db.get(Dataset, did)
            if ds:
                dataset_names[did] = ds.name

        if fmt == "json":
            content = to_json(examples, dataset_names)
        elif fmt == "csv":
            content = to_csv(examples, dataset_names)
        else:
            content = to_jsonl(examples, dataset_names)

        if output:
            with open(output, "w", encoding="utf-8") as f:
                f.write(content)
            click.echo(
                f"Exported {len(examples)} examples from collection '{collection.name}' to {output}"
            )
        else:
            sys.stdout.write(content)

    except SystemExit:
        raise
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()
    finally:
        db.close()
