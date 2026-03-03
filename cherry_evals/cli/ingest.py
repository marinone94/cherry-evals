"""Ingest datasets into Cherry Evals."""

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
def ingest(dataset: str, batch_size: int, limit: int | None) -> None:
    """Ingest a dataset into Cherry Evals.

    DATASET: Name of the dataset to ingest, or 'all' to ingest every dataset.
    """
    dataset_lower = dataset.lower()

    if dataset_lower == "all":
        click.echo(f"Starting ingestion for all datasets (batch_size={batch_size}, limit={limit})")
        for name, adapter_cls in ADAPTER_REGISTRY.items():
            click.echo(f"\n--- Ingesting {name} ---")
            adapter = adapter_cls()
            stats = ingest_dataset(adapter, batch_size=batch_size, limit=limit)
            click.echo(f"Ingestion complete: {stats}")
        click.echo("\nAll datasets ingested.")
        return

    adapter_cls = ADAPTER_REGISTRY.get(dataset_lower)
    if adapter_cls is None:
        click.echo(f"Unknown dataset: {dataset}")
        raise click.Abort()

    adapter = adapter_cls()
    click.echo(f"Starting {adapter.name} ingestion (batch_size={batch_size}, limit={limit})")
    stats = ingest_dataset(adapter, batch_size=batch_size, limit=limit)
    click.echo(f"Ingestion complete: {stats}")
