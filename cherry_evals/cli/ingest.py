"""Ingest datasets into Cherry Evals."""

import io
import json
import sys

import click

from cherry_evals.ingestion.ingest import ingest_dataset
from cherry_evals.ingestion.registry import ADAPTER_REGISTRY

_DATASET_CHOICES = sorted(ADAPTER_REGISTRY.keys()) + ["all"]


@click.command()
@click.argument("dataset", type=click.Choice(_DATASET_CHOICES, case_sensitive=False))
@click.option(
    "--batch-size",
    default=1000,
    help="Batch size for database inserts",
    type=int,
)
@click.option(
    "--limit",
    default=None,
    help="Limit number of examples to ingest (for testing)",
    type=int,
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    default=False,
    help="Output result as JSON (machine-parseable)",
)
def ingest(dataset: str, batch_size: int, limit: int | None, json_output: bool) -> None:
    """Ingest a dataset into Cherry Evals.

    DATASET: Name of the dataset to ingest, or 'all' to ingest every dataset.
    """
    dataset_lower = dataset.lower()

    if dataset_lower == "all":
        if json_output:
            # Suppress all intermediate print() output from ingestion functions
            _null = io.StringIO()
            results = []
            try:
                for name, adapter_cls in ADAPTER_REGISTRY.items():
                    adapter = adapter_cls()
                    old_stdout = sys.stdout
                    sys.stdout = _null
                    try:
                        stats = ingest_dataset(adapter, batch_size=batch_size, limit=limit)
                    finally:
                        sys.stdout = old_stdout
                    results.append({"status": "success", **stats})
                click.echo(json.dumps({"status": "success", "datasets": results}))
            except Exception as e:
                sys.stdout = sys.__stdout__
                click.echo(json.dumps({"status": "error", "message": f"Failed to ingest: {e}"}))
                raise SystemExit(1)
        else:
            click.echo(
                f"Starting ingestion for all datasets (batch_size={batch_size}, limit={limit})"
            )
            for name, adapter_cls in ADAPTER_REGISTRY.items():
                click.echo(f"\n--- Ingesting {name} ---")
                adapter = adapter_cls()
                stats = ingest_dataset(adapter, batch_size=batch_size, limit=limit)
                click.echo(f"Ingestion complete: {stats}")
            click.echo("\nAll datasets ingested.")
        return

    adapter_cls = ADAPTER_REGISTRY.get(dataset_lower)
    if adapter_cls is None:
        if json_output:
            click.echo(json.dumps({"status": "error", "message": f"Unknown dataset: {dataset}"}))
            raise SystemExit(1)
        click.echo(f"Unknown dataset: {dataset}")
        raise click.Abort()

    adapter = adapter_cls()

    if json_output:
        _null = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = _null
        try:
            stats = ingest_dataset(adapter, batch_size=batch_size, limit=limit)
        except Exception as e:
            sys.stdout = old_stdout
            click.echo(json.dumps({"status": "error", "message": f"Failed to ingest: {e}"}))
            raise SystemExit(1)
        finally:
            sys.stdout = old_stdout
        click.echo(json.dumps({"status": "success", **stats}))
    else:
        click.echo(f"Starting {adapter.name} ingestion (batch_size={batch_size}, limit={limit})")
        stats = ingest_dataset(adapter, batch_size=batch_size, limit=limit)
        click.echo(f"Ingestion complete: {stats}")
