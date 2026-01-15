"""Ingest datasets into Cherry Evals."""

import click

from cherry_evals.ingestion.mmlu import ingest_mmlu


@click.command()
@click.argument("dataset", type=click.Choice(["mmlu"], case_sensitive=False))
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
def ingest(dataset: str, batch_size: int, limit: int | None):
    """Ingest a dataset into Cherry Evals.

    DATASET: Name of the dataset to ingest (e.g., mmlu)
    """
    if dataset.lower() == "mmlu":
        click.echo(f"Starting MMLU ingestion (batch_size={batch_size}, limit={limit})")
        stats = ingest_mmlu(batch_size=batch_size, limit=limit)
        click.echo(f"✓ MMLU ingestion complete: {stats}")
    else:
        click.echo(f"✗ Unknown dataset: {dataset}")
        raise click.Abort()
